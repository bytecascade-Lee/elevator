#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
Description:
构建产物清理工具。

提供正则匹配的 exe/ini 文件清理，供 build_portable 和 build_install 复用。
"""

import re
from pathlib import Path


def clean_exe_files(bin_dir: Path, app_name: str, app_version: str) -> None:
    """
    删除 bin 目录中匹配 {app_name}-{app_version}*.exe / *.l4j.ini 的文件。

    Args:
        bin_dir: 目标 bin 目录
        app_name: 应用名称（如 Pilot）
        app_version: 应用版本（如 0.1.0）
    """
    bin_dir = Path(bin_dir)
    if not bin_dir.exists():
        return

    pattern = re.compile(
        rf'^{re.escape(app_name)}-{re.escape(app_version)}.*\.(?:exe|l4j\.ini)$'
    )

    for p in bin_dir.iterdir():
        if p.is_file() and pattern.match(p.name):
            p.unlink()
