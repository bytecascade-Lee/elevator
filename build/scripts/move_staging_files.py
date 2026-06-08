#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
将 Maven 打包/过滤后的文件复制到期望的位置

staging/inno/ -> build/inno/
staging/launch4j/ -> build/launch4j/
staging/scripts/ -> build/scripts/
staging/*.jar -> dist/lib/
"""

from pathlib import Path

from util.common import log
from util.io import copy_dir, copy_file, ensure_dir

PROJECT_ROOT = Path().cwd()
STAGING_DIR = PROJECT_ROOT / "staging"


def _move_inno() -> None:
    """staging/inno/ -> build/inno/"""
    src = STAGING_DIR / "inno"
    dest = PROJECT_ROOT / "build" / "inno"
    ensure_dir(dest)
    log("INFO", f"复制 Inno Setup 文件: {src} -> {dest}")
    copy_dir(src, dest)


def _move_launch4j() -> None:
    """staging/launch4j/ -> build/launch4j/"""
    src = STAGING_DIR / "launch4j"
    dest = PROJECT_ROOT / "build" / "launch4j"
    ensure_dir(dest)
    log("INFO", f"复制 Launch4j 配置文件: {src} -> {dest}")
    copy_dir(src, dest)


def _move_scripts() -> None:
    """staging/scripts/ -> build/scripts/"""
    src = STAGING_DIR / "scripts"
    dest = PROJECT_ROOT / "build" / "scripts"
    ensure_dir(dest)
    log("INFO", f"复制构建脚本: {src} -> {dest}")
    copy_dir(src, dest)


def _move_jars() -> None:
    """staging/*.jar -> dist/lib/"""
    dest = PROJECT_ROOT / "dist" / "lib"
    ensure_dir(dest)
    for jar in STAGING_DIR.glob("*.jar"):
        if jar.is_file():
            log("INFO", f"复制 JAR 文件: {jar.name} -> {dest}")
            copy_file(jar, dest / jar.name)


def move_staging_files() -> None:
    """将 staging 目录下的所有文件移动到各自的目标位置。"""
    _move_inno()
    _move_launch4j()
    _move_scripts()
    _move_jars()
    log("SUCCESS", "staging目录下的文件移动完成")


if __name__ == "__main__":
    move_staging_files()
