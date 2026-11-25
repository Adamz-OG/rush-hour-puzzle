"""Shortest solutions by breadth-first search.

Every move slides one car by one cell, exactly like one key press in the
game, so the solution found is the shortest one in the move count shown to
the player. Breadth-first search visits positions in order of distance from
the start: the first solved position it meets is at minimal distance.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from rushhour.board import Move, Puzzle, State, car_name


@dataclass(frozen=True)
class Solution:
    """Shortest list of moves, and the number of positions discovered."""

    moves: tuple[Move, ...]
    explored: int

    def __len__(self) -> int:
        """Return the number of moves of the solution."""
        return len(self.moves)


def solve(puzzle: Puzzle, start: State) -> Solution | None:
    """Shortest sequence of moves that solves ``start``, or ``None``."""
    if puzzle.is_solved(start):
        return Solution((), 1)
    parents: dict[State, tuple[State, Move] | None] = {start: None}
    frontier = deque([start])
    while frontier:
        state = frontier.popleft()
        for move in puzzle.moves(state):
            child = puzzle.apply(state, move)
            if child in parents:
                continue
            parents[child] = (state, move)
            if puzzle.is_solved(child):
                return Solution(_path(parents, child), len(parents))
            frontier.append(child)
    return None


def distances(puzzle: Puzzle, start: State) -> dict[State, int]:
    """Distance in moves from ``start`` to every reachable position."""
    seen = {start: 0}
    frontier = deque([start])
    while frontier:
        state = frontier.popleft()
        depth = seen[state] + 1
        for move in puzzle.moves(state):
            child = puzzle.apply(state, move)
            if child not in seen:
                seen[child] = depth
                frontier.append(child)
    return seen


def replay(puzzle: Puzzle, start: State, moves: tuple[Move, ...]) -> list[State]:
    """Every position of a solution, from ``start`` to the last move.

    Raises ``ValueError`` if one of the moves is not legal.
    """
    states = [start]
    for move in moves:
        if not puzzle.can_move(states[-1], move):
            raise ValueError(f"illegal move {describe([move])}")
        states.append(puzzle.apply(states[-1], move))
    return states


def describe(moves: list[Move] | tuple[Move, ...], puzzle: Puzzle | None = None) -> str:
    """Short text of a list of moves, consecutive equal moves grouped.

    With a puzzle the arrows follow the orientation of each car
    (``B↓2 C←``); without it, ``+`` and ``-`` give the direction.
    """
    groups: list[tuple[Move, int]] = []
    for move in moves:
        if groups and groups[-1][0] == move:
            groups[-1] = (move, groups[-1][1] + 1)
        else:
            groups.append((move, 1))
    return " ".join(_group_text(move, count, puzzle) for move, count in groups)


def _group_text(move: Move, count: int, puzzle: Puzzle | None) -> str:
    if puzzle is None:
        arrow = "+" if move.step > 0 else "-"
    else:
        arrow = ARROWS[puzzle.cars[move.car].direction(move.step).name]
    return f"{car_name(move.car)}{arrow}{count if count > 1 else ''}"


ARROWS = {"UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→"}


Parents = dict[State, tuple[State, Move] | None]


def _path(parents: Parents, end: State) -> tuple[Move, ...]:
    moves: list[Move] = []
    link = parents[end]
    while link is not None:
        state, move = link
        moves.append(move)
        link = parents[state]
    return tuple(reversed(moves))
