"""Level files: reading, writing and the levels shipped with the package.

A level file draws the parking inside a border, with one letter per car and
``.`` for an empty cell. The exit is a gap in the right border, on the row
of car ``A``. The last line gives the number of moves allowed::

    +------+
    |..B...|
    |AAB....
    |..CCC.|
    +------+
    12
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from rushhour.board import BoardError, Car, Puzzle, State, car_name

EMPTY = "."
WALL = "|"
CORNER = "+"
EDGE = "-"


class LevelError(ValueError):
    """Raised when a level file cannot be read."""


@dataclass(frozen=True)
class Level:
    """A puzzle, its starting position and the number of moves allowed."""

    puzzle: Puzzle
    start: State
    max_moves: int
    name: str = ""


# ---------------------------------------------------------------- reading
def parse_level(text: str, name: str = "") -> Level:
    """Read a level from the text of a level file."""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    if len(lines) < 4:
        raise LevelError("a level needs a border, at least one row and a move limit")
    max_moves = _parse_limit(lines[-1])
    rows, exit_row = _parse_grid(lines[:-1])
    cars, start = _find_cars(rows)
    try:
        puzzle = Puzzle(len(rows[0]), len(rows), tuple(cars))
    except BoardError as error:
        raise LevelError(str(error)) from error
    if puzzle.exit_row != exit_row:
        raise LevelError("the exit must be on the row of car A")
    return Level(puzzle, start, max_moves, name)


def load_level(path: str | Path) -> Level:
    """Read a level file."""
    file = Path(path)
    try:
        with open(file, encoding="utf-8") as stream:
            text = stream.read()
    except (OSError, UnicodeDecodeError) as error:
        raise LevelError(f"cannot read {file}: {error}") from error
    return parse_level(text, file.stem)


def _parse_limit(line: str) -> int:
    try:
        limit = int(line.strip())
    except ValueError:
        raise LevelError(f"last line must be the move limit, got {line!r}") from None
    if limit <= 0:
        raise LevelError("the move limit must be positive")
    return limit


def _parse_grid(lines: list[str]) -> tuple[list[str], int]:
    """Cells of every row, and the row of the exit."""
    top, *middle, bottom = lines
    width = len(top) - 2
    border = CORNER + EDGE * width + CORNER
    if width < 2 or top != border or bottom != border:
        raise LevelError("the parking must start and end with a +---+ border")
    rows, exits = [], []
    for y, line in enumerate(middle):
        if len(line) != width + 2 or line[0] != WALL or line[-1] not in (WALL, EMPTY):
            raise LevelError(f"row {y + 1} must look like |{EMPTY * width}|")
        if line[-1] == EMPTY:
            exits.append(y)
        rows.append(line[1:-1])
    if len(exits) != 1:
        raise LevelError("the right border must have exactly one exit")
    return rows, exits[0]


def _find_cars(rows: list[str]) -> tuple[list[Car], State]:
    """Cars named A, B, C... and their offsets, from the cells of the grid."""
    cells: dict[str, list[tuple[int, int]]] = {}
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char in string.ascii_uppercase:
                cells.setdefault(char, []).append((x, y))
            elif char != EMPTY:
                raise LevelError(f"unexpected character {char!r} in row {y + 1}")
    names = sorted(cells)
    expected = [car_name(i) for i in range(len(names))]
    if names != expected:
        missing = next(letter for letter in expected if letter not in cells)
        raise LevelError(f"cars must be named A, B, C... in order (no car {missing})")
    cars, start = [], []
    for name in names:
        car, offset = _car_from_cells(name, cells[name])
        cars.append(car)
        start.append(offset)
    return cars, tuple(start)


def _car_from_cells(name: str, cells: list[tuple[int, int]]) -> tuple[Car, int]:
    xs = sorted({x for x, _ in cells})
    ys = sorted({y for _, y in cells})
    horizontal = len(ys) == 1
    along = xs if horizontal else ys
    straight = len(xs) == 1 or len(ys) == 1
    contiguous = along == list(range(along[0], along[0] + len(cells)))
    if len(cells) < 2 or not straight or not contiguous:
        raise LevelError(f"car {name} must be a straight line of at least 2 cells")
    line = ys[0] if horizontal else xs[0]
    return Car(horizontal, len(cells), line), along[0]


# ---------------------------------------------------------------- writing
def format_level(level: Level, state: State | None = None) -> str:
    """Text of a level file for ``level`` (at ``state`` if given)."""
    puzzle = level.puzzle
    grid = puzzle.grid(level.start if state is None else state)
    border = CORNER + EDGE * puzzle.width + CORNER
    lines = [border]
    for y, row in enumerate(grid):
        cells = "".join(EMPTY if car is None else car_name(car) for car in row)
        right = EMPTY if y == puzzle.exit_row else WALL
        lines.append(WALL + cells + right)
    lines += [border, str(level.max_moves)]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------- bundled levels
def bundled_names() -> list[str]:
    """Names of the levels shipped with the package, in order."""
    folder = resources.files("rushhour") / "levels"
    return sorted(
        entry.name.removesuffix(".txt")
        for entry in folder.iterdir()
        if entry.name.endswith(".txt")
    )


def bundled_level(name: str) -> Level:
    """Load a level shipped with the package (``"1"`` and ``"01"`` both work)."""
    key = name.zfill(2) if name.isdigit() else name
    if key not in bundled_names():
        raise LevelError(f"no level named {name!r} (try: {', '.join(bundled_names())})")
    entry = resources.files("rushhour") / "levels" / f"{key}.txt"
    return parse_level(entry.read_text(encoding="utf-8"), key)


def find_level(spec: str) -> Level:
    """Load the bundled level named ``spec``, or the level file at ``spec``."""
    if Path(spec).suffix or Path(spec).exists():
        return load_level(spec)
    return bundled_level(spec)
