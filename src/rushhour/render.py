"""Text drawing of the parking, with or without ANSI colors.

Car ``A`` is white; the other cars take red, green, yellow, blue, magenta
and cyan in turn, so ``B`` and ``H`` share the same color. The functions
only build strings: printing is left to the caller.
"""

from __future__ import annotations

from rushhour.board import Puzzle, State, car_name

RESET = "\x1b[0m"
WHITE = "\x1b[47m"
CYCLE = ("\x1b[41m", "\x1b[42m", "\x1b[43m", "\x1b[44m", "\x1b[45m", "\x1b[46m")
DARK_TEXT = "\x1b[30m"
LIGHT_TEXT = "\x1b[97m"
_DARK_ON = {WHITE, "\x1b[42m", "\x1b[43m", "\x1b[46m"}
EXIT_MARK = "→"


def car_color(index: int) -> str:
    """ANSI background code of a car."""
    return WHITE if index == 0 else CYCLE[(index - 1) % len(CYCLE)]


def render_board(
    puzzle: Puzzle, state: State, color: bool = True, selected: int | None = None
) -> str:
    """Draw the parking inside its border, the exit marked with an arrow.

    Each cell takes three characters. The selected car is drawn ``[B]``.
    """
    border = "+" + "---" * puzzle.width + "+"
    lines = [border]
    for y, row in enumerate(puzzle.grid(state)):
        cells = "".join(_cell(car, color, selected) for car in row)
        right = f" {EXIT_MARK}" if y == puzzle.exit_row else "|"
        lines.append("|" + cells + right)
    lines.append(border)
    return "\n".join(lines)


def render_status(moves: int, max_moves: int) -> str:
    """Return the line with the moves played, allowed and left."""
    left = max(max_moves - moves, 0)
    return f"moves: {moves} / {max_moves}   left: {left}"


def _cell(car: int | None, color: bool, selected: int | None) -> str:
    if car is None:
        return " . "
    name = car_name(car)
    text = f"[{name}]" if car == selected else f" {name} "
    if not color:
        return text
    background = car_color(car)
    ink = DARK_TEXT if background in _DARK_ON else LIGHT_TEXT
    return f"{background}{ink}{text}{RESET}"
