"""The interface asked by the assignment, on a ``game`` dictionary.

The assignment describes a game as a dictionary::

    {"width": 6, "height": 6, "max_moves": 40,
     "cars": [[(0, 2), "h", 2], [(2, 0), "v", 3], ...]}

where each car is ``[(x, y) of its top-left cell, "h" or "v", length]``,
and asks for five functions with fixed names. They are kept here with the
same signatures, on top of :mod:`rushhour.board` and :mod:`rushhour.game`.
Only the positions of the cars are ever changed in the dictionary.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from rushhour.board import Car, Direction, Puzzle, State
from rushhour.game import Game
from rushhour.keyboard import read_key
from rushhour.level import Level, load_level
from rushhour.render import render_board, render_status

GameDict = dict[str, Any]


def parse_game(game_file_path: str) -> GameDict:
    """Read a level file into a ``game`` dictionary."""
    return to_dict(load_level(game_file_path))


def get_game_str(game: GameDict, current_move_number: int) -> str:
    """Text of the colored board and of the move counters."""
    puzzle, state = from_dict(game)
    board = render_board(puzzle, state)
    return board + "\n" + render_status(current_move_number, game["max_moves"])


def move_car(game: GameDict, car_index: int, direction: str) -> bool:
    """Move one car by one cell if the move is legal, and say if it was."""
    if direction not in Direction.__members__:
        return False
    puzzle, state = from_dict(game)
    move = puzzle.move_for(car_index, Direction[direction])
    if move is None or not puzzle.can_move(state, move):
        return False
    _store(game, puzzle, puzzle.apply(state, move))
    return True


def is_win(game: GameDict) -> bool:
    """Whether car ``A`` has reached the exit."""
    puzzle, state = from_dict(game)
    return puzzle.is_solved(state)


def play_game(
    game: GameDict,
    getkey: Callable[[], str] = read_key,
    render: Callable[[GameDict, int], str] = get_game_str,
    show: Callable[[str], None] = print,
) -> int:
    """Play in the terminal; 0 if won, 1 if out of moves, 2 if abandoned."""
    puzzle, state = from_dict(game)
    session = Game(Level(puzzle, state, game["max_moves"]))
    show(render(game, session.moves))
    while True:
        outcome = session.press(getkey())
        _store(game, puzzle, session.state)
        show(render(game, session.moves))
        if session.message:
            show(session.message)
        if outcome is not None:
            return int(outcome)


# ------------------------------------------------------------ conversion
def to_dict(level: Level) -> GameDict:
    """``game`` dictionary of a level, at its starting position."""
    puzzle = level.puzzle
    cars = [
        [car.origin(offset), "h" if car.horizontal else "v", car.length]
        for car, offset in zip(puzzle.cars, level.start, strict=True)
    ]
    return {
        "width": puzzle.width,
        "height": puzzle.height,
        "cars": cars,
        "max_moves": level.max_moves,
    }


def from_dict(game: GameDict) -> tuple[Puzzle, State]:
    """Puzzle and position described by a ``game`` dictionary."""
    cars, state = [], []
    for (x, y), orientation, length in game["cars"]:
        horizontal = orientation == "h"
        cars.append(Car(horizontal, length, y if horizontal else x))
        state.append(x if horizontal else y)
    return Puzzle(game["width"], game["height"], tuple(cars)), tuple(state)


def _store(game: GameDict, puzzle: Puzzle, state: State) -> None:
    """Write the positions of ``state`` back into ``game``."""
    for entry, car, offset in zip(game["cars"], puzzle.cars, state, strict=True):
        entry[0] = car.origin(offset)
