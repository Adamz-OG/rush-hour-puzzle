import random
from pathlib import Path

import pytest

from helpers import SMALL, TRAFFIC, random_parking, small
from rushhour.board import Car
from rushhour.level import (
    Level,
    LevelError,
    bundled_level,
    bundled_names,
    find_level,
    format_level,
    load_level,
    parse_level,
)


def test_parse_small_level() -> None:
    level = small()
    assert (level.puzzle.width, level.puzzle.height) == (6, 4)
    assert level.puzzle.cars == (Car(True, 2, 2), Car(False, 2, 2), Car(True, 2, 0))
    assert level.start == (0, 1, 2)
    assert level.max_moves == 12 and level.name == "small"


def test_parse_accepts_surrounding_blank_lines() -> None:
    assert parse_level("\n\n" + SMALL + "\n\n").start == small().start


@pytest.mark.parametrize("text", [SMALL, TRAFFIC])
def test_format_is_the_inverse_of_parse(text: str) -> None:
    assert format_level(parse_level(text)) == text


def test_format_at_another_state() -> None:
    text = format_level(small(), (4, 0, 3))
    assert "|....AA." in text and "|..BCC.|" in text


@pytest.mark.parametrize("seed", range(30))
def test_random_parkings_round_trip(seed: int) -> None:
    puzzle, state = random_parking(random.Random(seed), width=7, height=6, cars=10)
    level = Level(puzzle, state, 50)
    again = parse_level(format_level(level))
    assert again.puzzle == puzzle and again.start == state


def _replace(old: str, new: str) -> str:
    assert old in SMALL
    return SMALL.replace(old, new)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("+--+\n12\n", "border, at least one row"),
        (_replace("12", "twelve"), "move limit"),
        (_replace("12", "0"), "positive"),
        (_replace("+------+\n|..CC", "+-----+\n|..CC"), r"\+---\+ border"),
        (_replace("|..B...|", "|..B...."), "exactly one exit"),
        (_replace("|AAB....", "|AAB...|"), "exactly one exit"),
        (_replace("|..B...|", "|..B..|"), "must look like"),
        (_replace("|..B...|", "#..B...|"), "must look like"),
        (_replace("|..B...|", "|..b...|"), "unexpected character 'b'"),
        (_replace("CC", "DD"), "no car C"),
        (_replace("|......|", "|.C....|"), "car C must be a straight line"),
        (_replace("|..CC..|", "|..C.C.|"), "car C must be a straight line"),
        (_replace("|..CC..|", "|...C..|"), "car C must be a straight line"),
    ],
)
def test_invalid_levels(text: str, message: str) -> None:
    with pytest.raises(LevelError, match=message):
        parse_level(text)


def test_exit_must_be_on_row_of_a() -> None:
    text = SMALL.replace("|..B...|", "|..B....").replace("|AAB....", "|AAB...|")
    with pytest.raises(LevelError, match="row of car A"):
        parse_level(text)


def test_car_a_must_be_horizontal() -> None:
    text = "+---+\n|A..|\n|A...\n+---+\n5\n"
    with pytest.raises(LevelError, match="horizontal"):
        parse_level(text)


def test_load_level_from_file(tmp_path: Path) -> None:
    path = tmp_path / "mine.txt"
    path.write_text(SMALL, encoding="utf-8")
    level = load_level(path)
    assert level.name == "mine" and level.start == small().start
    assert find_level(str(path)).start == small().start


def test_load_missing_file(tmp_path: Path) -> None:
    with pytest.raises(LevelError, match="cannot read"):
        load_level(tmp_path / "missing.txt")


def test_bundled_levels_are_listed_in_order() -> None:
    names = bundled_names()
    assert names == sorted(names) and len(names) >= 5
    assert bundled_level("1").name == names[0]
    assert find_level("1").start == bundled_level("01").start


def test_unknown_bundled_level() -> None:
    with pytest.raises(LevelError, match="no level named"):
        bundled_level("99")
    with pytest.raises(LevelError, match="no level named"):
        find_level("nope")
