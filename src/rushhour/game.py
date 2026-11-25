"""A game in progress, driven by key names, without any terminal code.

:class:`Game` turns key names (``"b"``, ``"UP"``, ``"ESCAPE"``...) into
moves and messages. It never reads the keyboard and never prints, so a
whole game can be played in a test from a list of keys. :func:`play` adds
the loop around it, with the key reader and the display passed in.

Keys:

* a letter selects a car (``a`` and ``A`` both select car ``A``);
* an arrow moves the selected car by one cell, and further arrows keep
  moving the same car until another letter is pressed;
* ``?`` shows the first move of a shortest solution (it is not counted);
* ``ESCAPE`` abandons the game.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import IntEnum

from rushhour.board import Direction, Puzzle, State, car_name
from rushhour.level import Level
from rushhour.render import render_board, render_status
from rushhour.solver import describe, solve

ESCAPE = "ESCAPE"
HINT = "?"


class Outcome(IntEnum):
    """End of a game, with the return codes of the assignment."""

    WON = 0
    LOST = 1
    ABANDONED = 2


@dataclass
class Game:
    """Current position, move counter and selected car of a game."""

    level: Level
    state: State = field(default=())
    moves: int = 0
    selected: int | None = None
    message: str = ""

    def __post_init__(self) -> None:
        """Start from the level's position unless another one is given."""
        if not self.state:
            self.state = self.level.start
        self.puzzle.check(self.state)

    @property
    def puzzle(self) -> Puzzle:
        """The parking being played."""
        return self.level.puzzle

    @property
    def outcome(self) -> Outcome | None:
        """``WON`` or ``LOST`` once the game is over, ``None`` before."""
        if self.puzzle.is_solved(self.state):
            return Outcome.WON
        if self.moves >= self.level.max_moves:
            return Outcome.LOST
        return None

    def move(self, car: int, direction: Direction) -> bool:
        """Move ``car`` one cell towards ``direction``; ``False`` if impossible."""
        move = self.puzzle.move_for(car, direction)
        if move is None or not self.puzzle.can_move(self.state, move):
            return False
        self.state = self.puzzle.apply(self.state, move)
        self.moves += 1
        return True

    def press(self, key: str) -> Outcome | None:
        """Handle one key and return the outcome if the game is now over."""
        self.message = ""
        if key == ESCAPE:
            self.message = "game abandoned"
            return Outcome.ABANDONED
        if key in Direction.__members__:
            self._arrow(Direction[key])
        elif len(key) == 1 and key.isascii() and key.isalpha():
            self._select(key.upper())
        elif key == HINT:
            self._hint()
        else:
            self.message = f"unknown key {key!r}"
        return self.outcome

    def _select(self, letter: str) -> None:
        index = ord(letter) - ord("A")
        if index >= len(self.puzzle.cars):
            self.message = f"there is no car {letter}"
            return
        self.selected = index
        self.message = f"car {letter} selected"

    def _arrow(self, direction: Direction) -> None:
        if self.selected is None:
            self.message = "choose a car first (press its letter)"
            return
        name = car_name(self.selected)
        car = self.puzzle.cars[self.selected]
        if car.horizontal != direction.horizontal:
            axis = "left or right" if car.horizontal else "up or down"
            self.message = f"car {name} only moves {axis}"
        elif not self.move(self.selected, direction):
            self.message = f"car {name} is blocked"

    def _hint(self) -> None:
        solution = solve(self.puzzle, self.state)
        if solution is None:
            self.message = "no solution from this position"
        else:
            steps = len(solution)
            first = describe(solution.moves[:1], self.puzzle)
            self.message = f"hint: {first} ({steps} moves to the exit)"

    def screen(self, color: bool = True) -> str:
        """Board, counters and last message, as shown to the player."""
        board = render_board(self.puzzle, self.state, color, self.selected)
        lines = [board, render_status(self.moves, self.level.max_moves)]
        if self.message:
            lines.append(self.message)
        return "\n".join(lines)


def play(
    game: Game,
    read_key: Callable[[], str],
    show: Callable[[Game], None],
) -> Outcome:
    """Play until the game is over; ``show`` is called after every key."""
    show(game)
    outcome = game.outcome
    while outcome is None:
        outcome = game.press(read_key())
        if outcome is Outcome.WON:
            game.message = f"well done, solved in {game.moves} moves"
        elif outcome is Outcome.LOST:
            game.message = "no moves left, game lost"
        show(game)
    return outcome
