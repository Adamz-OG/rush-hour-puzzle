r"""Read one key press without waiting for Enter, with the standard library only.

* Linux and macOS: the terminal is put in raw mode with :mod:`termios` and
  :mod:`tty`. An arrow key sends three bytes (``ESC [ A``); a lone ``ESC``
  is told apart by waiting a few milliseconds for the rest of a sequence.
* Windows: :mod:`msvcrt` returns arrows as a prefix (``\x00`` or ``\xe0``)
  followed by a scan code.

The decoding is done by pure functions, tested without a terminal.
"""

from __future__ import annotations

import importlib
import os
import select
import sys
from types import ModuleType

ESCAPE = "ESCAPE"
ANSI_ARROWS = {"A": "UP", "B": "DOWN", "C": "RIGHT", "D": "LEFT"}
WINDOWS_ARROWS = {"H": "UP", "P": "DOWN", "M": "RIGHT", "K": "LEFT"}
WINDOWS_PREFIXES = ("\x00", "\xe0")
INTERRUPT = "\x03"
SEQUENCE_DELAY = 0.05


def decode_ansi(keys: str) -> str:
    """Key name of what a POSIX terminal sent for one key press."""
    if keys in ("\x1b", INTERRUPT):
        return ESCAPE
    if len(keys) == 3 and keys[:2] in ("\x1b[", "\x1bO"):
        return ANSI_ARROWS.get(keys[2], keys)
    return keys


def decode_windows(first: str, second: str = "") -> str:
    """Key name of what :func:`msvcrt.getwch` returned for one key press."""
    if first in WINDOWS_PREFIXES:
        return WINDOWS_ARROWS.get(second, first + second)
    if first in ("\x1b", INTERRUPT):
        return ESCAPE
    return first


def read_key() -> str:
    """Wait for one key press on the terminal and return its name."""
    if os.name == "nt":  # pragma: no cover - checked on Windows only
        return read_windows_key(importlib.import_module("msvcrt"))
    return read_posix_key(sys.stdin.fileno())


def read_windows_key(msvcrt: ModuleType) -> str:
    """One key from the Windows console through ``msvcrt``."""
    first = msvcrt.getwch()
    second = msvcrt.getwch() if first in WINDOWS_PREFIXES else ""
    return decode_windows(first, second)


def read_posix_key(fd: int) -> str:
    """One key from the terminal ``fd``, in raw mode for the time of the read."""
    import termios
    import tty

    saved = termios.tcgetattr(fd)
    try:
        tty.setraw(fd, termios.TCSANOW)  # keep keys typed in advance
        data = os.read(fd, 1)
        if data == b"\x1b":
            data += _rest_of_sequence(fd)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
    return decode_ansi(data.decode("utf-8", errors="replace"))


def _rest_of_sequence(fd: int) -> bytes:
    """Up to two more bytes if they arrive quickly, as in ``ESC [ A``."""
    rest = b""
    while len(rest) < 2 and select.select([fd], [], [], SEQUENCE_DELAY)[0]:
        rest += os.read(fd, 1)
    return rest
