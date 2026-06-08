#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
便携版打包脚本 — 将 dist/ 目录打包为 ZIP 便携版。

Maven 占位符由 maven-resources-plugin 在 prepare-package 阶段过滤替换。
"""

import shutil
import sys
from pathlib import Path

from util.common import log

# Maven 过滤占位符 — 构建时由 maven-resources-plugin 替换为实际值
APP_NAME = "${project.name}"
APP_VERSION = "${project.version}"

# 路径常量
DIST_DIR = Path("dist").resolve()
RELEASE_DIR = Path("release").resolve()
BIN_DIR = DIST_DIR / "bin"


def package_portable(include_jre: bool = False) -> str:
    """
    将 dist/ 目录打包为便携版 ZIP。

    打包前清理 bin 中遗留的 exe/ini 文件。

    ZIP 命名格式: {AppName}-{AppVersion}-win-x64-{jre_mode}-portable.zip

    Args:
        include_jre: 是否包含捆绑 JRE（影响 ZIP 文件名）

    Returns:
        生成的 ZIP 文件绝对路径
    """
    jre_mode = "include-jre" if include_jre else "without-jre"
    zip_basename = f"{APP_NAME}-{APP_VERSION}-win-x64-{jre_mode}-portable"

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    log("INFO", f"正在创建便携版压缩包: {zip_basename}.zip ...")
    archive_path = shutil.make_archive(
        base_name=str(RELEASE_DIR / zip_basename),
        format="zip",
        root_dir=str(DIST_DIR),
    )

    log("SUCCESS", f"便携版压缩包已创建: {archive_path}")
    return archive_path


# 独立入口（供直接调用测试）

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="创建便携版 ZIP 压缩包")
    parser.add_argument("--include-jre", action="store_true", help="包含捆绑 JRE")
    args = parser.parse_args()

    if "${" in APP_NAME:
        log("ERROR", "Maven 占位符未被替换，请通过 Maven 构建运行")
        sys.exit(1)

    package_portable(args.include_jre)
