"""Thin, safe wrappers around :mod:`subprocess`.

The helpers here never raise for a missing program or a non-zero exit status;
callers get a :class:`subprocess.CompletedProcess` they can inspect.  This keeps
desktop-environment probing robust on systems where helper tools are absent.
"""

from __future__ import annotations

import os
import subprocess
from typing import Dict, List, Optional, Sequence, Union

from distromod.utils.logging import logger

Command = Union[str, Sequence[str]]


def _clean_env() -> Dict[str, str]:
    """Return a copy of the environment with problematic loader vars removed.

    ``LD_PRELOAD`` entries that cannot be loaded (for example 32-bit injection
    libraries) make every child process print warnings to stderr.  They are
    irrelevant to the tools we invoke, so we drop them.
    """
    env = dict(os.environ)
    env.pop("LD_PRELOAD", None)
    return env


def run(
    cmd: Command,
    timeout: float = 15.0,
    input_text: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """Run ``cmd`` and return the completed process without raising.

    Args:
        cmd: Argument vector (preferred) or a shell-free string.
        timeout: Maximum number of seconds to wait.
        input_text: Optional text fed to the process' stdin.

    Returns:
        A :class:`subprocess.CompletedProcess` with ``text=True``.
    """
    argv: List[str] = [cmd] if isinstance(cmd, str) else list(cmd)
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_text,
            env=_clean_env(),
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(argv, 127, "", f"{argv[0]}: not found")
    except subprocess.TimeoutExpired:
        logger.debug("Command timed out: %s", argv)
        return subprocess.CompletedProcess(argv, 124, "", "timeout")
    except OSError as exc:  # pragma: no cover - defensive
        logger.debug("Command failed to start %s: %s", argv, exc)
        return subprocess.CompletedProcess(argv, 126, "", str(exc))


def capture(cmd: Command, timeout: float = 15.0) -> str:
    """Run ``cmd`` and return stripped stdout (empty string on failure)."""
    result = run(cmd, timeout=timeout)
    return (result.stdout or "").strip()


def ok(cmd: Command, timeout: float = 15.0) -> bool:
    """Return ``True`` when ``cmd`` exits with status 0."""
    return run(cmd, timeout=timeout).returncode == 0


def spawn(cmd: Command) -> bool:
    """Launch ``cmd`` detached from the current process.

    Used for tools that stay resident (for example ``swaybg``).  Returns
    ``True`` if the process was started.
    """
    argv: List[str] = [cmd] if isinstance(cmd, str) else list(cmd)
    try:
        subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=_clean_env(),
        )
        return True
    except OSError as exc:
        logger.debug("Could not spawn %s: %s", argv, exc)
        return False
