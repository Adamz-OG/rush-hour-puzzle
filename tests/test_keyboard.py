import os
import pty
import sys
import termios
from collections.abc import Iterator
from types import SimpleNamespace

import pytest

from rushhour import keyboard
from rushhour.keyboard import (
    ESCAPE,
    decode_ansi,
    decode_windows,
    read_key,
    read_posix_key,
    read_windows_key,
)


@pytest.mark.parametrize(
    ("keys", "name"),
    [
        ("\x1b[A", "UP"),
        ("\x1b[B", "DOWN"),
        ("\x1b[C", "RIGHT"),
        ("\x1b[D", "LEFT"),
        ("\x1bOA", "UP"),
        ("\x1b", ESCAPE),
        ("\x03", ESCAPE),
        ("a", "a"),
        ("?", "?"),
        ("\x1b[Z", "\x1b[Z"),
    ],
)
def test_decode_ansi(keys: str, name: str) -> None:
    assert decode_ansi(keys) == name


@pytest.mark.parametrize(
    ("first", "second", "name"),
    [
        ("\xe0", "H", "UP"),
        ("\x00", "P", "DOWN"),
        ("\xe0", "M", "RIGHT"),
        ("\xe0", "K", "LEFT"),
        ("\xe0", "S", "\xe0S"),
        ("\x1b", "", ESCAPE),
        ("\x03", "", ESCAPE),
        ("b", "", "b"),
    ],
)
def test_decode_windows(first: str, second: str, name: str) -> None:
    assert decode_windows(first, second) == name


def fake_msvcrt(chars: str) -> SimpleNamespace:
    stream = iter(chars)
    return SimpleNamespace(getwch=lambda: next(stream))


def test_read_windows_key() -> None:
    console = fake_msvcrt("\xe0Hb\x1b")
    assert read_windows_key(console) == "UP"  # type: ignore[arg-type]
    assert read_windows_key(console) == "b"  # type: ignore[arg-type]
    assert read_windows_key(console) == ESCAPE  # type: ignore[arg-type]


@pytest.fixture
def terminal() -> Iterator[tuple[int, int]]:
    main, child = pty.openpty()
    yield main, child
    os.close(main)
    os.close(child)


@pytest.mark.parametrize(
    ("sent", "name"),
    [(b"\x1b[A", "UP"), (b"\x1b[D", "LEFT"), (b"\x1b", ESCAPE), (b"c", "c")],
)
def test_read_posix_key_from_a_pseudo_terminal(
    terminal: tuple[int, int], sent: bytes, name: str
) -> None:
    main, child = terminal
    before = termios.tcgetattr(child)
    os.write(main, sent)
    assert read_posix_key(child) == name
    assert termios.tcgetattr(child) == before  # terminal mode restored


def test_read_key_uses_standard_input(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[int] = []

    def fake_read(fd: int) -> str:
        seen.append(fd)
        return "a"

    monkeypatch.setattr(sys, "stdin", SimpleNamespace(fileno=lambda: 7))
    monkeypatch.setattr(keyboard, "read_posix_key", fake_read)
    assert read_key() == "a" and seen == [7]
