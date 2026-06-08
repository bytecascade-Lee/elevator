#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
Release 构建入口 — 用户友好的发布包构建脚本。

根据参数或交互式输入选择构建模式，自动定位 Launch4j / Inno Setup，
调用构建模块完成打包。

用法:
    release -p                     # 生成便携版
    release -i                     # 生成安装包
    release -b                     # 两者都生成
    release                        # 交互式选择

Maven 占位符由 maven-resources-plugin 在 prepare-package 阶段过滤替换。
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

from build_install import package_install
from build_portable import package_portable
from prepare_for_building import build_base_exes, initialize_build_dir, prepare_bin_for_mode, cleanup_temp
from util.cleaner import clean_exe_files
from util.common import log

# Maven 过滤占位符 — 构建时由 maven-resources-plugin 替换为实际值
APP_NAME = "${project.name}"
APP_VERSION = "${project.version}"

BIN_DIR = Path("dist/bin").resolve()

# Launch4j / Inno Setup 常见安装路径（Windows）
_LAUNCH4J_CANDIDATES = [
    Path(r".\tools\Launch4j\launch4jc.exe"),
    Path(r"C:\Program Files\Launch4j\launch4jc.exe"),
    Path(r"C:\Program Files (x86)\Launch4j\launch4jc.exe"),
]
_INNO_CANDIDATES = [
    Path(r".\tools\Inno Setup 6\iscc.exe"),
    Path(r"C:\Program Files (x86)\Inno Setup 6\iscc.exe"),
    Path(r"C:\Program Files\Inno Setup 6\iscc.exe"),
    Path(r"C:\Program Files (x86)\Inno Setup\iscc.exe"),
]


def _find_tool(name: str, candidates: list[Path]) -> Path:
    """优先 PATH 查找，其次检查常见安装路径。"""
    found = shutil.which(name)
    if found:
        return Path(found)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"找不到 {name}")


def _validate_maven_filtering() -> None:
    if "${" in APP_NAME:
        log("ERROR", "Maven 占位符未被替换，请通过 Maven 构建运行（mvn package）")
        sys.exit(1)


def _prompt_mode() -> str:
    """无参数时交互式选择构建模式。"""
    print()
    print("请选择构建模式：")
    print("  1) 生成便携版 (ZIP)")
    print("  2) 生成安装包 (Installer)")
    print("  3) 两者都生成")
    choice = input("请输入 (1/2/3)：").strip()
    return {"1": "portable", "2": "install", "3": "both"}.get(choice, "portable")


def _prompt_yesno(prompt: str, default: bool = False) -> bool:
    """交互式 yes / no。"""
    hint = "Y/n" if default else "y/N"
    raw = input(f"{prompt} ({hint})：").strip().lower()
    if raw in ("y", "yes"):
        return True
    if raw in ("n", "no"):
        return False
    return default


def _ensure_launch4j(args_path: str) -> Path:
    if args_path:
        return Path(args_path)
    found = _find_tool("launch4jc", _LAUNCH4J_CANDIDATES)
    if found:
        log("INFO", f"自动找到 Launch4j: {found}")
        return found
    log("ERROR", "未找到 Launch4j，请通过 --launch4j-path 指定路径")
    sys.exit(1)


def _ensure_inno(args_path: str) -> Path:
    if args_path:
        return Path(args_path)
    found = _find_tool("iscc", _INNO_CANDIDATES)
    if found:
        log("INFO", f"自动找到 Inno Setup: {found}")
        return found
    log("ERROR", "未找到 Inno Setup，请通过 --inno-setup-path 指定路径")
    sys.exit(1)


def main() -> int:
    _validate_maven_filtering()

    parser = argparse.ArgumentParser(description="构建 Pilot 发布包")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("-p", "--portable", action="store_true", help="生成便携版 ZIP")
    mode_group.add_argument("-i", "--install", action="store_true", help="生成安装包")
    mode_group.add_argument("-b", "--both", action="store_true", help="同时生成便携版和安装包")
    parser.add_argument("--include-jre", action="store_true", help="捆绑 JRE")
    parser.add_argument("--launch4j-path", help="Launch4j 可执行文件路径（默认自动查找）")
    parser.add_argument("--inno-setup-path", help="Inno Setup 编译器路径（默认自动查找）")
    args = parser.parse_args()

    # 无参数 → 交互式
    if not any([args.portable, args.install, args.both]):
        mode = _prompt_mode()
        if not args.include_jre:
            args.include_jre = _prompt_yesno("是否捆绑 JRE", default=False)
    else:
        mode = "both" if args.both else ("portable" if args.portable else "install")

    # 解析工具路径
    launch4j = _ensure_launch4j(args.launch4j_path)
    inno = None
    if mode in ("install", "both"):
        inno = _ensure_inno(args.inno_setup_path)

    start_time = time.time()
    log("INFO", f"模式: {mode}, 捆绑JRE: {args.include_jre}")

    # 阶段 1: 生成 EXE + 初始化目录
    log("INFO", "阶段 1/3: 生成启动器 EXE 并初始化构建目录")
    build_base_exes(launch4j)
    initialize_build_dir(args.include_jre)

    # 阶段 2: 各模式打包
    modes = ["install", "portable"] if mode == "both" else [mode]
    for m in modes:
        log("INFO", f"阶段 2/3: 构建 mode={m}")
        clean_exe_files(BIN_DIR, APP_NAME, APP_VERSION)
        prepare_bin_for_mode(m)
        if m == "portable":
            package_portable(args.include_jre)
        elif m == "install":
            package_install(inno, args.include_jre)
        log("SUCCESS", f"Mode={m} 构建完成")

    # 阶段 3: 清理
    log("INFO", "阶段 3/3: 清理临时文件")
    cleanup_temp()

    elapsed = time.time() - start_time
    log("SUCCESS", f"全部构建完成，耗时 {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
