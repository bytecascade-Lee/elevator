#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
Description:

JAR dependency analyzer - Extract Maven dependencies and compute SHA256.
"""

import sys
from pathlib import Path

from util.cmd_exec import run_command
from util.common import log
from util.io import read_text_from_file, write_text_to_file, sha256


def get_maven_deps(deps_file_path: Path) -> int:
    """Run mvn dependency:list and return exit code."""
    log("INFO", "Executing Maven dependency:list...")
    returncode, _, stderr = run_command(
        cmd=[
            "mvn", "dependency:list",
            "-DincludeScope=runtime",
            "-Dstyle.color=never",
            f"-DoutputFile={deps_file_path}"
        ],
        capture=True,
        check=False,
        error_msg="Maven command failed"
    )

    if returncode != 0:
        log("ERROR", f"Maven command failed with exit code: {returncode}")
        if stderr:
            log("ERROR", f"Stderr: {stderr}")

    return returncode


def parse_deps_file(deps_file_path: Path) -> list:
    """Parse dependency file and extract artifactId:version."""
    dependencies_list = []
    line_count = 0

    log("INFO", f"Parsing dependency file: {deps_file_path}")
    content = read_text_from_file(deps_file_path, encoding="UTF-8")

    for line in content.splitlines():
        line_count += 1
        line = line.strip()
        if not line:
            continue

        parts = line.split(':')
        if len(parts) >= 4:
            dependencies_list.append(f"{parts[1]}:{parts[3]}")

    log("INFO", f"Total lines processed: {line_count}")
    log("INFO", f"Total dependencies extracted: {len(dependencies_list)}")

    return dependencies_list


def deduplicate_deps(dependencies_list: list) -> list:
    """Remove duplicates and log statistics."""
    unique = sorted(set(dependencies_list))
    duplicate_count = len(dependencies_list) - len(unique)

    if duplicate_count > 0:
        log("WARN", "Duplicate dependencies found, please check pom.xml for repeated jar imports.")

    log("INFO", f"After deduplication: {len(unique)} unique dependencies (removed {duplicate_count} duplicates)")

    return unique


def save_hash_if_changed(value: str, file: Path) -> None:
    """Save hash to file only if it has changed."""
    file_exists = file.exists()

    if file_exists:
        old_hash = read_text_from_file(file, encoding="UTF-8").strip()

        if old_hash == value:
            log("INFO", "Hash unchanged, dependencies haven't changed, skipping write.")
            return
        else:
            log("INFO", "Hash changed, dependencies have changed, updating file.")
            log("INFO", f"Old hash: {old_hash}")
            log("INFO", f"New hash: {value}")
    else:
        log("WARN", "Original SHA256 file not found, creating new one.")

    write_text_to_file(file, value, encoding="UTF-8", no_newline=True)
    log("INFO", f"Hash saved to: {file}")


def main() -> int:
    log("INFO", f"Current working directory: {Path.cwd()}")

    deps_file = Path("jar-dependencies.txt")
    hash_file = Path("jar-dependencies.sha256")

    # Step 1: Get Maven dependencies
    ret = get_maven_deps(deps_file)
    if ret != 0:
        return ret

    if not deps_file.exists():
        log("ERROR", f"Dependency file not found: {deps_file}")
        return 1

    # Step 2: Parse and deduplicate
    try:
        deps_list = parse_deps_file(deps_file)
        unique_deps = deduplicate_deps(deps_list)
    except Exception as e:
        log("ERROR", f"Failed to parse dependency file: {e}")
        return 1

    # Step 3: Calculate SHA256
    log("INFO", "Calculating SHA256 hash...")
    deps_text = "\n".join(unique_deps)
    hash_hex = sha256(deps_text)
    log("RESULT", f"SHA256: {hash_hex}")

    # Step 4: Save hash
    save_hash_if_changed(hash_hex, hash_file)

    log("INFO", "Script completed successfully.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
