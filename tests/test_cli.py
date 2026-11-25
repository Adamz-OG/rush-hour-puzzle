import runpy
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from helpers import SMALL
from rushhour.cli import CLEAR, main
from rushhour.level import bundled_names


def reader(sequence: list[str]) -> Callable[[], str]:
    stream = iter(sequence)
    return lambda: next(stream)


@pytest.fixture
def small_file(tmp_path: Path) -> str:
    path = tmp_path / "small.txt"
    path.write_text(SMALL, encoding="utf-8")
    return str(path)


def test_play_and_win(small_file: str, capsys: pytest.CaptureFixture[str]) -> None:
    sequence = ["c", "RIGHT", "b", "UP", "a", "RIGHT", "RIGHT", "RIGHT", "RIGHT"]
    assert main(["play", small_file], read=reader(sequence)) == 0
    out = capsys.readouterr().out
    assert "small  (6x4, 3 cars)" in out and "solved in 6 moves" in out
    assert CLEAR not in out and "\x1b[" not in out  # not a terminal: no colors


def test_play_and_abandon(small_file: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["play", small_file], read=reader(["ESCAPE"])) == 2
    assert "game abandoned" in capsys.readouterr().out


def test_play_in_a_terminal_clears_and_colors(
    small_file: str, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert main(["play", small_file], read=reader(["ESCAPE"])) == 2
    out = capsys.readouterr().out
    assert out.startswith(CLEAR) and "\x1b[47m" in out


def test_no_color_option(
    small_file: str, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    main(["play", small_file, "--no-color"], read=reader(["ESCAPE"]))
    assert "\x1b[" not in capsys.readouterr().out


def test_play_bundled_level_by_default(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["play"], read=reader(["ESCAPE"])) == 2
    assert capsys.readouterr().out.startswith(bundled_names()[0])


def test_solve(small_file: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["solve", small_file]) == 0
    out = capsys.readouterr().out
    assert "shortest solution: 6 moves (limit 12)" in out
    assert "moves: C→ B↑ A→4" in out
    assert out.count("+------------------+") == 4  # start and final boards
    assert "start:" in out and "after the solution:" in out


def test_solve_unsolvable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "stuck.txt"
    path.write_text("+------+\n|AA.CC..\n|.....B|\n|.....B|\n+------+\n9\n")
    assert main(["solve", str(path)]) == 1
    assert "no solution" in capsys.readouterr().out


def test_levels_table(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["levels"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["level", "size", "cars", "limit", "best", "states"]
    assert len(lines) == len(bundled_names()) + 1


def test_errors_go_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["solve", "missing.txt"]) == 1
    assert "error: cannot read missing.txt" in capsys.readouterr().err


def test_command_is_required(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main([])
    assert "usage: rushhour" in capsys.readouterr().err


def test_python_dash_m(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["rushhour", "levels"])
    with pytest.raises(SystemExit) as stop:
        runpy.run_module("rushhour", run_name="__main__")
    assert stop.value.code == 0
    assert "level" in capsys.readouterr().out
