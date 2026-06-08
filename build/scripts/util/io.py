#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
IO operations utilities for JRE build and dependency analysis scripts. \n

   - ensure_dir()：Create directory if it does not exist (including parents).
   - get_dir_size()：Calculate total size (in bytes) of all files under a directory.
   - format_size()：Convert bytes to human-readable string (MB, GB, etc.).
   - backup_path()：Move src to a backup location with a timestamp suffix.
   - read_text_from_file()：Read the content of a text file.
   - write_text_to_file()：Write content to a text file.
   - sha256()：Calculate the sha256 hash value of a string.
"""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from util.common import log


def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist (including parents)."""
    path.mkdir(parents=True, exist_ok=True)


def get_dir_size(path: Path) -> int:
    """
    Calculate total size (in bytes) of all files under a directory.
    Does not follow symbolic links.
    """
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a directory")
    total = 0
    for entry in path.rglob('*'):
        if entry.is_file():
            total += entry.stat().st_size
    return total


def format_size(size: int) -> str:
    """Convert bytes to human-readable string (MB, GB, etc.)."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def backup(src: Path, dest_dir: Path, suffix_format: str = "%Y%m%d-%H%M%S") -> Path:
    """
    Move src to a backup location with a timestamp suffix.

    Args:
        src: Original file or directory to be moved.
        dest_dir: Destination directory for backup. If None, use src.parent.
        suffix_format: Format for timestamp suffix (using datetime.strftime).

    Returns:
        The new backup path.

    Example:
        backup_path(Path("build/jre")) -> Path("build/jre-bak-20260321-153045")
    """
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"Cannot backup {src}: does not exist")

    dest_dir = Path(dest_dir)
    ensure_dir(dest_dir)

    timestamp = datetime.now().strftime(suffix_format)
    backup_name = f"{src.name}-bak-{timestamp}"
    path = dest_dir / backup_name

    shutil.move(str(src), str(path))
    return path


def read_text_from_file(file_path: Path, encoding: str = "UTF-8") -> str:
    """Read entire file as string."""
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def write_text_to_file(file_path: Path, content: str, encoding: str = "UTF-8", no_newline: bool = False) -> None:
    """
    Write content to a text file.

    Args:
        no_newline: If True, do not add trailing newline at end of file.
        no_newline:
        encoding:
        content:
        file_path:
    """
    ensure_dir(file_path.parent)
    with open(file_path, "w", encoding=encoding, newline='') as f:
        f.write(content)
        if not no_newline and content and not content.endswith('\n'):
            f.write('\n')


def copy_dir(src: Path, dest: Path) -> None:
    """Recursively copy all contents from the source directory to the target directory."""
    src = Path(src)
    if not src.exists():
        log("WARN", f"源目录不存在，跳过: {src}")
        return
    ensure_dir(dest)
    for item in src.iterdir():
        if item.is_dir():
            shutil.copytree(item, dest / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest / item.name)


def copy_file(src: Path, dest: Path) -> None:
    """Copy a single file and automatically create a parent directory."""
    ensure_dir(dest.parent)
    shutil.copy2(src, dest)
    log("DEBUG", f"复制文件{src}到{dest}成功")


def sha256(text: str) -> str:
    """Return lowercase hex digest of SHA256 hash of the given string (UTF-8 encoded)."""
    return hashlib.sha256(text.encode("UTF-8")).hexdigest()
