#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# @Author  : Serene Lee
# @Date    : 2026/6/6

"""
Command execution utilities for JRE build and dependency analysis scripts.\n

   - run_command()：Execute a command and return its exit code, stdout, and stderr.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Union, Optional, Tuple, List

from util.common import log


def run_command(
        cmd: Union[str, List[str]],
        capture: bool = True,
        check: bool = False,
        cwd: Optional[Path] = None,
        error_msg: Optional[str] = None,
) -> Tuple[int, str, str]:
    """
    Execute a command and return its exit code, stdout, and stderr.

    Args:
        cmd: Command as a string (will be split by shell) or list of arguments.
        capture: If True, capture stdout/stderr; otherwise, stream to console.
        check: If True, raise subprocess.CalledProcessError on non-zero exit code.
        cwd: Working directory (as Path or str) for the command.
        error_msg: Optional custom error message to log on failure.

    Returns:
        Tuple of (returncode, stdout, stderr). stdout/stderr are strings.
    """
    # On Windows, resolve executables via shutil.which() so that .cmd/.bat files
    # (e.g. mvn.cmd) are found. subprocess.run without shell=True only finds .exe.
    if isinstance(cmd, list) and cmd:
        resolved = shutil.which(cmd[0])
        if resolved:
            cmd = [resolved] + cmd[1:]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            cwd=str(cwd) if cwd else None,
            encoding='UTF-8',
            errors='replace',
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        returncode = proc.returncode
    except subprocess.CalledProcessError as e:
        # Should not happen if check=False, but keep for completeness
        returncode = e.returncode
        stdout = e.stdout or ""
        stderr = e.stderr or ""
    except Exception as e:
        log("ERROR", f"Failed to run command '{cmd}': {e}")
        if error_msg:
            log("ERROR", error_msg)
        return 1, "", str(e)

    if check and returncode != 0:
        raise subprocess.CalledProcessError(returncode, cmd, output=stdout, stderr=stderr)

    if returncode != 0 and error_msg:
        log("ERROR", f"{error_msg} (exit code {returncode})")

    return returncode, stdout, stderr
