"""Rush Hour sliding puzzle for the terminal, with a breadth-first solver.

Basic use::

    >>> from rushhour import bundled_level, solve
    >>> level = bundled_level("1")
    >>> len(solve(level.puzzle, level.start))
    10
"""

from rushhour.board import BoardError, Car, Direction, Move, Puzzle, State
from rushhour.game import Game, Outcome, play
from rushhour.level import (
    Level,
    LevelError,
    bundled_level,
    bundled_names,
    format_level,
    load_level,
    parse_level,
)
from rushhour.solver import Solution, describe, distances, replay, solve

__all__ = [
    "BoardError",
    "Car",
    "Direction",
    "Game",
    "Level",
    "LevelError",
    "Move",
    "Outcome",
    "Puzzle",
    "Solution",
    "State",
    "bundled_level",
    "bundled_names",
    "describe",
    "distances",
    "format_level",
    "load_level",
    "parse_level",
    "play",
    "replay",
    "solve",
]
__version__ = "1.0.0"
