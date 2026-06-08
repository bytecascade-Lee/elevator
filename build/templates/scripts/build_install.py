#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
安装版打包脚本 — 编译 Inno Setup 安装程序。

仅支持 Windows 平台。

Maven 占位符由 maven-resources-plugin 在 prepare-package 阶段过滤替换。
"""

import sys
from pathlib import Path

from util.cmd_exec import run_command
from util.common import log, is_windows

# Maven 过滤占位符 — 构建时由 maven-resources-plugin 替换为实际值
APP_NAME = "${project.name}"
APP_VERSION = "${project.version}"

# 路径常量
BUILD_DIR = Path("build").resolve()
DIST_DIR = Path("dist").resolve()
BIN_DIR = DIST_DIR / "bin"


def package_install(inno_setup_path: Path, include_jre: bool = False) -> None:
    """
    编译 Inno Setup 安装程序。

    仅支持 Windows。打包前清理 bin 中遗留的 exe/ini 文件。

    Args:
        inno_setup_path: Inno Setup 编译器路径 (iscc.exe)
        include_jre: 是否包含捆绑 JRE（传递给 Inno Setup 的 /DMode 参数）

    Raises:
        OSError: 如果不在 Windows 平台上运行
        FileNotFoundError: 如果 Inno Setup 脚本不存在
    """
    if not is_windows():
        raise OSError("build_install is only supported on Windows. "
                      "Inno Setup installer can only be built on Windows.")

    iss_script = BUILD_DIR / "inno" / "setup.iss"
    if not iss_script.exists():
        raise FileNotFoundError(f"Inno Setup 脚本不存在: {iss_script}")

    jre_mode = "include-jre" if include_jre else "without-jre"

    log("INFO", f"正在编译安装程序 (JRE={jre_mode}) ...")
    rc, _, stderr = run_command(
        cmd=[str(inno_setup_path), "/Q", f"/DMode={jre_mode}", str(iss_script)],
        capture=False,
        check=False,
        error_msg="Inno Setup 编译失败",
    )

    if rc == 0:
        log("SUCCESS", "安装程序编译成功")
    else:
        log("ERROR", f"Inno Setup 退出码 {rc}")
        if stderr:
            log("ERROR", stderr)


# 独立入口（供直接调用测试）

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="编译 Inno Setup 安装程序")
    parser.add_argument("--inno-setup-path", required=True,
                        help="Inno Setup 编译器路径 (iscc.exe)")
    parser.add_argument("--include-jre", action="store_true", help="包含捆绑 JRE")
    args = parser.parse_args()

    if "${" in APP_NAME:
        log("ERROR", "Maven 占位符未被替换，请通过 Maven 构建运行")
        sys.exit(1)

    try:
        package_install(args.inno_setup_path, args.include_jre)
    except OSError as e:
        log("ERROR", str(e))
        sys.exit(1)
