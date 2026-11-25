"""The assignment's interface, checked on levels written for these tests."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from helpers import SMALL, TRAFFIC, traffic
from rushhour.compat import (
    from_dict,
    get_game_str,
    is_win,
    move_car,
    parse_game,
    play_game,
    to_dict,
)
from rushhour.solver import solve


@pytest.fixture
def game(tmp_path: Path) -> dict[str, Any]:
    path = tmp_path / "small.txt"
    path.write_text(SMALL, encoding="utf-8")
    return parse_game(str(path))


def reader(sequence: list[str]) -> Callable[[], str]:
    stream = iter(sequence)
    return lambda: next(stream)


def test_parse_game(game: dict[str, Any]) -> None:
    assert game == {
        "width": 6,
        "height": 4,
        "cars": [[(0, 2), "h", 2], [(2, 1), "v", 2], [(2, 0), "h", 2]],
        "max_moves": 12,
    }


def test_dict_round_trip() -> None:
    level = traffic()
    puzzle, state = from_dict(to_dict(level))
    assert puzzle == level.puzzle and state == level.start


def test_get_game_str(game: dict[str, Any]) -> None:
    text = get_game_str(game, 5)
    for name in "ABC":
        assert name in text
    assert "\x1b[47m" in text and "\x1b[41m" in text and "\x1b[42m" in text
    assert "moves: 5 / 12   left: 7" in text


def test_move_car_updates_only_the_position(game: dict[str, Any]) -> None:
    assert move_car(game, 2, "RIGHT")
    assert game["cars"][2] == [(3, 0), "h", 2]
    assert move_car(game, 1, "UP")
    assert game["cars"][1] == [(2, 0), "v", 2]


@pytest.mark.parametrize(
    ("car", "direction"),
    [
        (0, "RIGHT"),
        (0, "LEFT"),
        (0, "UP"),
        (2, "UP"),
        (1, "RIGHT"),
        (7, "UP"),
        (1, "up"),
        (1, "NORTH"),
    ],
)
def test_move_car_refuses(game: dict[str, Any], car: int, direction: str) -> None:
    before = [list(entry) for entry in game["cars"]]
    assert not move_car(game, car, direction)
    assert game["cars"] == before


def test_is_win(game: dict[str, Any]) -> None:
    assert not is_win(game)
    game["cars"][0][0] = (3, 2)
    assert not is_win(game)
    game["cars"][0][0] = (4, 2)
    assert is_win(game)


def test_play_game_codes(game: dict[str, Any]) -> None:
    win = ["c", "RIGHT", "b", "UP", "a", "RIGHT", "RIGHT", "RIGHT", "RIGHT"]
    shown: list[str] = []
    assert play_game(game, reader(win), show=shown.append) == 0
    assert game["cars"][0][0] == (4, 2)
    assert any("solved" not in line and "moves: 6 / 12" in line for line in shown)


def test_play_game_lost_and_abandoned(tmp_path: Path) -> None:
    path = tmp_path / "traffic.txt"
    path.write_text(TRAFFIC.replace("\n30\n", "\n2\n"), encoding="utf-8")
    lost = parse_game(str(path))
    assert play_game(lost, reader(["h", "RIGHT", "LEFT"]), show=lambda _: None) == 1
    quit_game = parse_game(str(path))
    assert play_game(quit_game, reader(["ESCAPE"]), show=lambda _: None) == 2


def test_render_is_called_after_every_key(game: dict[str, Any]) -> None:
    calls: list[tuple[tuple[int, int], int]] = []

    def render(state: dict[str, Any], moves: int) -> str:
        calls.append((state["cars"][2][0], moves))
        return ""

    play_game(game, reader(["c", "RIGHT", "z", "ESCAPE"]), render, lambda _: None)
    assert calls == [((2, 0), 0), ((2, 0), 0), ((3, 0), 1), ((3, 0), 1), ((3, 0), 1)]


def test_dict_levels_are_solvable(game: dict[str, Any]) -> None:
    puzzle, state = from_dict(game)
    solution = solve(puzzle, state)
    assert solution is not None and len(solution) == 6
