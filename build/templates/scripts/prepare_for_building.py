#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
Description:
构建准备脚本 — 复制资源文件、使用 Launch4j 生成启动器 EXE。

Maven 占位符由 maven-resources-plugin 在 prepare-package 阶段过滤替换。
"""

import shutil
import sys
from pathlib import Path

from util.cmd_exec import run_command
from util.common import log
from util.io import ensure_dir, read_text_from_file, write_text_to_file, copy_dir, copy_file

# Maven 过滤占位符 — 构建时由 maven-resources-plugin 替换为实际值
APP_NAME = "${project.name}"
APP_VERSION = "${project.version}"

# 路径常量
BUILD_DIR = Path("build").resolve()
TEMP_DIR = Path("temp").resolve()
DIST_DIR = Path("dist").resolve()
BIN_DIR = DIST_DIR / "bin"
LAUNCH4J_TEMPLATE = BUILD_DIR / "launch4j" / "launch4j.xml"


def build_base_exes(launch4j_path: Path) -> None:
    """
    使用 Launch4j 生成基础 EXE（gui.exe 和 console.exe）。

    步骤:
        1. 读取 launch4j.xml 模板
        2. 将 {{HEAD-TYPE}} 替换为 gui/console，{{APPLICATION-NAME}} 替换为输出文件名
        3. 将配置写入 temp/ 并调用 Launch4j 编译

    Args:
        launch4j_path: Launch4j 可执行文件路径
    """
    ensure_dir(TEMP_DIR)
    l4j_template = read_text_from_file(LAUNCH4J_TEMPLATE)

    for head_type in ("gui", "console"):
        exe_name = f"{head_type}.exe"
        log("INFO", f"正在生成 {exe_name} ...")

        config_xml = (
            l4j_template.replace("{{HEAD-TYPE}}", head_type)
            .replace("{{APPLICATION-NAME}}", exe_name)
        )
        if head_type == "gui":
            config_xml = config_xml.replace("<instanceAlreadyExistsMsg>程序已在其他地方运行</instanceAlreadyExistsMsg>", "")

        config_path = TEMP_DIR / f"launch4j-{head_type}.xml"
        write_text_to_file(config_path, config_xml)

        rc, stdout, stderr = run_command(
            cmd=[str(launch4j_path), str(config_path)],
            capture=False,
            check=False,
            error_msg=f"Launch4j 生成 {exe_name} 失败",
        )

        if rc != 0:
            log("ERROR", f"Launch4j 退出码 {rc} (head_type={head_type})")
            if stderr:
                log("ERROR", stderr)
            sys.exit(1)

        log("SUCCESS", f"生成 {exe_name} -> {TEMP_DIR / exe_name}")


def initialize_build_dir(include_jre: bool = False) -> None:
    """
    初始化构建目录结构并复制依赖文件。

    - 创建 dist/bin, dist/lib, dist/help, dist/license
    - 复制 docs/help/ 和 docs/license/（如存在）
    - 复制 elevator 二进制及 JAR
    - 可选复制 build/jre/ 到 dist/jre/

    Args:
        include_jre: 是否包含捆绑 JRE
    """
    for subdir in ("bin", "lib", "help", "license"):
        ensure_dir(DIST_DIR / subdir)

    copy_dir(Path("docs/help"), DIST_DIR / "help")
    copy_dir(Path("docs/license"), DIST_DIR / "license")

    if include_jre:
        copy_dir(BUILD_DIR / "jre", DIST_DIR / "jre")

    log("INFO", "构建目录结构初始化完成")


def prepare_bin_for_mode(mode: str) -> None:
    """
    为指定构建模式准备 bin 目录。

    每个模式会生成两套文件:
        - GUI:   AppName-Version-{mode_char}.exe + .l4j.ini
        - Console: AppName-Version-console-{mode_char}.exe + .l4j.ini

    Args:
        mode: 构建模式 ("install" 或 "portable")
    """
    mode_char = mode[0]
    ensure_dir(BIN_DIR)

    # 从 .vmoptions 生成 .l4j.ini 内容（替换 MODE 占位符）
    vmoptions = read_text_from_file(Path(".vmoptions"))
    ini_content = vmoptions.replace("{{MODE}}", f"-Dapp.env={mode}")

    # GUI ini
    gui_ini_name = f"{APP_NAME}-{APP_VERSION}-{mode_char}.l4j.ini"
    write_text_to_file(BIN_DIR / gui_ini_name, ini_content, no_newline=True)

    # Console ini
    console_ini_name = f"{APP_NAME}-{APP_VERSION}-console-{mode_char}.l4j.ini"
    write_text_to_file(BIN_DIR / console_ini_name, ini_content, no_newline=True)

    # 复制 EXE（从 temp 到 dist/bin 并重命名）
    copy_file(TEMP_DIR / "gui.exe", BIN_DIR / f"{APP_NAME}-{APP_VERSION}-{mode_char}.exe")
    copy_file(TEMP_DIR / "console.exe", BIN_DIR / f"{APP_NAME}-{APP_VERSION}-console-{mode_char}.exe")

    log("SUCCESS", f"Mode={mode} bin 目录准备完成 (ini + exe)")


def cleanup_temp() -> None:
    """删除临时构建目录 (temp/)。"""
    # if TEMP_DIR.exists():
    #     shutil.rmtree(TEMP_DIR)
    #     log("INFO", "临时目录已清理")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="准备构建目录及 Launch4j 启动器")
    parser.add_argument("--launch4j-path", required=True, help="Launch4j 可执行文件路径")
    parser.add_argument("--include-jre", action="store_true", help="包含捆绑 JRE")
    parser.add_argument("--mode", choices=["install", "portable"], default="install",
                        help="目标构建模式")

    args = parser.parse_args()

    if "${" in APP_NAME:
        log("ERROR", "Maven 占位符未被替换，请通过 Maven 构建运行")
        sys.exit(1)

    build_base_exes(args.launch4j_path)
    initialize_build_dir(args.include_jre)
    prepare_bin_for_mode(args.mode)
    cleanup_temp()
