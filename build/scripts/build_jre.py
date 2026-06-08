#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
Description:

JRE builder - Generate custom JRE using jlink.
"""

import sys
import time
from pathlib import Path

from util.cmd_exec import run_command
from util.common import log, find_exec
from util.io import ensure_dir, format_size, backup


def find_jlink() -> Path:
    """Locate jlink executable in PATH."""
    jlink_path = find_exec("jlink")
    if not jlink_path:
        log("ERROR", "jlink command not found. Please ensure JDK is installed and in PATH.")
        sys.exit(1)
    return jlink_path


def get_jmods_path(jlink_path: Path) -> Path:
    """Get jmods directory path from JDK installation."""
    # jlink is typically in JDK_HOME/bin/jlink
    jdk_home = jlink_path.parent.parent
    jmods_path = jdk_home / "jmods"

    if not jmods_path.exists():
        log("ERROR", f"JMODS directory not found: {jmods_path}")
        sys.exit(1)

    return jmods_path


def read_modules(modules_file: Path) -> str:
    """Read and validate module list file."""
    if not modules_file.exists():
        log("ERROR", f"Module list file not found: {modules_file}")
        log("ERROR", "Please run analyse-jdeps.py first.")
        sys.exit(1)

    content = modules_file.read_text(encoding='ascii').strip()

    if not content:
        log("ERROR", f"Module list file is empty: {modules_file}")
        sys.exit(1)

    return content


def handle_existing_output(output_dir: Path) -> None:
    """Handle existing output directory by backing up or deleting."""
    if not output_dir.exists():
        return

    # Check if directory is empty
    if not any(output_dir.iterdir()):
        output_dir.rmdir()
        log("WARN", f"The JRE directory exists, but its content is empty. It has been automatically deleted: {output_dir}")
    else:
        backup(output_dir, output_dir.parent, suffix_format="%Y%m%d-%H%M%S")
        log("WARN", f"The JRE directory exists and is not empty. It has been backed up.")


def build_jre(jlink_path: Path, jmods_path: Path, modules: str, output_dir: Path) -> bool:
    """Execute jlink to build custom JRE."""
    cmd = [
        str(jlink_path),
        "--module-path", str(jmods_path),
        "--add-modules", modules,
        "--output", str(output_dir),
        "--strip-debug",
        "--compress=2",
        "--no-header-files",
        "--no-man-pages"
    ]

    log("INFO", f"Generating custom JRE to: {output_dir}")
    log("INFO", "This may take a moment...")

    returncode, stdout, stderr = run_command(
        cmd=cmd,
        capture=False,  # Stream output to console
        check=False,
        error_msg="jlink execution failed"
    )

    if returncode == 0:
        return True
    else:
        log("ERROR", f"jlink execution failed with exit code: {returncode}")
        log("ERROR", "Please check module list for correctness.")
        if stderr:
            log("ERROR", f"Error details: {stderr}")
        return False


def calculate_jre_size(output_dir: Path) -> int:
    """Calculate total size of JRE directory."""
    total = 0
    for entry in output_dir.rglob('*'):
        if entry.is_file():
            total += entry.stat().st_size
    return total


def main() -> int:
    """Main function."""
    start_time = time.time()

    log("INFO", f"Current working directory: {Path.cwd()}")

    # Find jlink
    jlink_path = find_jlink()
    log("INFO", f"Found jlink at: {jlink_path}")

    # Get jmods path
    jmods_path = get_jmods_path(jlink_path)
    log("INFO", f"Using module path: {jmods_path}")

    # Read modules
    modules_file = Path("jdk-modules.txt")
    modules = read_modules(modules_file)
    log("INFO", f"Loaded modules: {modules}")

    # Setup output directory
    output_dir = Path("build/jre")
    handle_existing_output(output_dir)
    ensure_dir(output_dir)

    # Build JRE
    success = build_jre(jlink_path, jmods_path, modules, output_dir)

    if not success:
        return 1

    # Calculate statistics
    end_time = time.time()
    elapsed = end_time - start_time

    jre_size = calculate_jre_size(output_dir)

    log("INFO", "Custom JRE generated successfully!")
    log("INFO", f"Location: {output_dir}")
    log("INFO", f"Size: {format_size(jre_size)}")
    log("INFO", f"Total time: {elapsed:.2f} seconds")

    return 0


if __name__ == "__main__":
    sys.exit(main())
