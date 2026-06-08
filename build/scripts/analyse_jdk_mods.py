#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
Description:

JDK dependency analyzer - Extract JDK module dependencies from JAR files.
"""

import sys
from pathlib import Path

from util.cmd_exec import run_command
from util.common import log, find_exec


def find_jdeps() -> Path:
    """Locate jdeps executable in PATH."""
    jdeps_path = find_exec("jdeps")
    if not jdeps_path:
        log("ERROR", "jdeps command not found.")
        sys.exit(1)
    return jdeps_path


def analyze_jar(jdeps_path: Path, jar_path: Path) -> tuple:
    """Run jdeps on a single JAR and return (success, module_list, error_msg)."""
    cmd = [
        str(jdeps_path),
        "--ignore-missing-deps",
        "--multi-release", "21",
        "--print-module-deps",
        str(jar_path)
    ]

    returncode, stdout, stderr = run_command(
        cmd=cmd,
        capture=True,
        check=False,
        error_msg=f"Failed to analyze: {jar_path.name}"
    )

    # Check for errors
    if returncode != 0:
        return False, [], stderr or "Unknown error"

    # Check if output contains error indicators
    output = stdout.strip()
    if not output or "Error" in output or "Exception" in output:
        return False, [], output if output else "Unknown error"

    # Parse module list
    modules = []
    if output:
        for mod in output.split(','):
            mod = mod.strip()
            if mod:
                modules.append(mod)

    return True, modules, None


def main() -> int:
    """Main function."""
    log("INFO", f"Current working directory: {Path.cwd()}")

    # Check lib directory
    lib_path = Path("dist/lib")
    if not lib_path.exists():
        log("ERROR", f"Directory not found: {lib_path}")
        return 1

    # Find jdeps
    jdeps_path = find_jdeps()
    log("INFO", f"Found jdeps at: {jdeps_path}")

    # Get all JAR files
    jar_files = list(lib_path.glob("*.jar"))
    total_count = len(jar_files)
    log("INFO", f"Found {total_count} jar files to analyze.")

    # Analyze each JAR
    modules = set()
    failed_jars = []

    for idx, jar_path in enumerate(jar_files, 1):
        log("INFO", f"({idx}/{total_count}) Analyzing: {jar_path.name}")

        success, module_list, error_msg = analyze_jar(jdeps_path, jar_path)

        if not success:
            log("ERROR", f"Failed to analyze: {jar_path.name} - {error_msg}")
            failed_jars.append(jar_path.name)
            continue

        if not module_list:
            log("WARN", f"No JDK module dependencies found in: {jar_path.name}")
            continue

        # Add modules to set
        modules.update(module_list)

    # Check for failures
    if failed_jars:
        log("ERROR", f"{len(failed_jars)} jar(s) failed to analyze, cannot generate module list.")
        log("ERROR", f"Failed jars: {', '.join(failed_jars)}")
        return 1

    # Remove java.compiler module
    modules.discard("java.compiler")

    # Sort and format
    sorted_modules = sorted(modules)
    modules_list = ','.join(sorted_modules)

    # Save to file (no newline)
    output_file = Path("jdk-modules.txt")
    output_file.write_text(modules_list, encoding='ascii')

    log("INFO", f"Module list saved to {output_file}")
    log("INFO", f"Total unique modules: {len(modules)}")
    log("INFO", f"Module list: {modules_list}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
