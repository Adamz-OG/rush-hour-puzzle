import re

from helpers import small, traffic
from rushhour.render import (
    CYCLE,
    RESET,
    WHITE,
    car_color,
    render_board,
    render_status,
)

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def test_colors_follow_the_assignment_cycle() -> None:
    assert car_color(0) == WHITE
    assert [car_color(i) for i in range(1, 7)] == list(CYCLE)
    assert car_color(7) == car_color(1) == "\x1b[41m"  # B and H are red
    assert car_color(13) == car_color(7)


def test_plain_board() -> None:
    level = small()
    text = render_board(level.puzzle, level.start, color=False)
    assert text.splitlines() == [
        "+------------------+",
        "| .  .  C  C  .  . |",
        "| .  .  B  .  .  . |",
        "| A  A  B  .  .  .  →",
        "| .  .  .  .  .  . |",
        "+------------------+",
    ]


def test_colored_board_has_one_code_per_car_cell() -> None:
    level = traffic()
    text = render_board(level.puzzle, level.start)
    cells = sum(car.length for car in level.puzzle.cars)
    assert text.count(RESET) == cells
    assert ANSI.sub("", text) == render_board(level.puzzle, level.start, color=False)
    for index in range(len(level.puzzle.cars)):
        assert car_color(index) in text


def test_selected_car_is_framed() -> None:
    level = small()
    text = render_board(level.puzzle, level.start, color=False, selected=1)
    assert text.count("[B]") == 2 and "[A]" not in text


def test_text_stays_readable_on_every_background() -> None:
    level = traffic()
    text = render_board(level.puzzle, level.start)
    assert "\x1b[47m\x1b[30m A " in text  # dark text on white
    assert "\x1b[41m\x1b[97m B " in text  # light text on red


def test_status_line() -> None:
    assert render_status(3, 40) == "moves: 3 / 40   left: 37"
    assert render_status(45, 40).endswith("left: 0")
