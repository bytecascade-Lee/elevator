#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
Description:
构建主脚本。

整合:
  - prepare_for_building: Launch4j 启动器生成 + 资源目录初始化
  - build_portable: 便携版 ZIP 打包
  - build_install: 安装版程序打包，使用Inno Setup编译

用法:
    python build.py --launch4j-path=<path> [--mode=both] [--include-jre] [--inno-setup-path=<path>]

Maven 占位符由 maven-resources-plugin 在 prepare-package 阶段过滤替换。
"""

import argparse
import sys
import time
from pathlib import Path

from build_install import package_install
from build_portable import package_portable
from prepare_for_building import build_base_exes, initialize_build_dir, prepare_bin_for_mode, cleanup_temp
from util.common import log

# Maven 过滤占位符 — 构建时由 maven-resources-plugin 替换为实际值
APP_NAME = "${project.name}"

# 常量
BUILD_DIR = Path("build").resolve()


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="Pilot Windows 构建脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python build.py --launch4j-path=C:\\launch4j\\launch4j.exe --mode=both --include-jre\n"
            "  python build.py --launch4j-path=C:\\launch4j\\launch4j.exe --inno-setup-path=C:\\Inno\\iscc.exe\n"
        ),
    )
    parser.add_argument(
        "--mode", choices=["install", "portable", "both"], default="install",
        help="构建模式: install / portable / both (默认: install)",
    )
    parser.add_argument(
        "--include-jre", action="store_true", default=False,
        help="是否包含捆绑 JRE",
    )
    parser.add_argument(
        "--launch4j-path", required=True,
        help="Launch4j 可执行文件路径 (launch4j.exe)",
    )
    parser.add_argument(
        "--inno-setup-path", default="",
        help="Inno Setup 编译器路径 (iscc.exe，install 模式必需)",
    )
    return parser.parse_args()


def _validate_maven_filtering() -> None:
    """校验 Maven 占位符是否已被替换。"""
    if "${" in APP_NAME:
        log("ERROR", "Maven 占位符未被替换，请通过 Maven 构建运行（mvn package）")
        sys.exit(1)


def main() -> int:
    """构建主流程。"""
    _validate_maven_filtering()
    args = parse_args()
    start_time = time.time()

    log("INFO", f"当前工作目录: {Path.cwd()}")
    log("INFO", f"参数: mode={args.mode}, include_jre={args.include_jre}")
    log("INFO", f"     launch4j={args.launch4j_path}, inno={args.inno_setup_path or '(未指定)'}")

    if not args.launch4j_path:
        log("ERROR", "必须指定 --launch4j-path")
        return 1

    if args.mode in ("install", "both") and not args.inno_setup_path:
        log("ERROR", "install/both 模式必须指定 --inno-setup-path")
        return 1

    # 阶段 1: Launch4j 生成 EXE + 资源目录初始化
    log("INFO", "阶段 1/3: 生成启动器 EXE 并初始化构建目录")
    build_base_exes(args.launch4j_path)
    initialize_build_dir(args.include_jre)

    # 阶段 2: 遍历各模式打包
    modes = ["install", "portable"] if args.mode == "both" else [args.mode]

    for mode in modes:
        log("INFO", f"阶段 2/3: 构建 mode={mode}")

        prepare_bin_for_mode(mode)

        if mode == "portable":
            package_portable(args.include_jre)
        elif mode == "install":
            package_install(args.inno_setup_path, args.include_jre)

        log("SUCCESS", f"Mode={mode} 构建完成")

    # 阶段 3: 清理临时文件
    log("INFO", "阶段 3/3: 清理临时文件")
    cleanup_temp()

    elapsed = time.time() - start_time
    log("SUCCESS", f"全部构建完成，耗时 {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
