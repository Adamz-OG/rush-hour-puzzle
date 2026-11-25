"""Shared helpers: small levels, random parkings and a reference solver."""

from __future__ import annotations

import random
from collections.abc import Iterator

from rushhour.board import Car, Move, Puzzle, State
from rushhour.level import Level, parse_level

SMALL = """\
+------+
|..CC..|
|..B...|
|AAB....
|......|
+------+
12
"""
"""B blocks A and C blocks B: C right, B up, then A right 4 times (6 moves)."""

TRAFFIC = """\
+------+
|.BCCC.|
|.B..D.|
|AA..D..
|EFF.D.|
|E..GG.|
|HHH...|
+------+
30
"""


def small() -> Level:
    return parse_level(SMALL, "small")


def traffic() -> Level:
    return parse_level(TRAFFIC, "traffic")


def random_parking(
    rng: random.Random, width: int = 5, height: int = 5, cars: int = 6
) -> tuple[Puzzle, State]:
    """Random valid parking: car A on row 2, other cars placed where they fit."""
    placed = [Car(True, 2, 2)]
    state = [rng.randint(0, width - 3)]
    taken = set(placed[0].cells(state[0]))
    for _ in range(200):
        if len(placed) == cars:
            break
        horizontal = rng.random() < 0.5
        length = rng.choice((2, 2, 3))
        size, other = (width, height) if horizontal else (height, width)
        line = rng.randrange(other)
        if horizontal and line == 2:
            continue
        car = Car(horizontal, length, line)
        offset = rng.randint(0, size - length)
        cells = car.cells(offset)
        if taken.isdisjoint(cells):
            placed.append(car)
            state.append(offset)
            taken.update(cells)
    return Puzzle(width, height, tuple(placed)), tuple(state)


def random_walk(
    rng: random.Random, puzzle: Puzzle, state: State, steps: int
) -> Iterator[tuple[State, Move]]:
    """Random legal moves from ``state``: every position with its move."""
    for _ in range(steps):
        moves = list(puzzle.moves(state))
        if not moves:
            return
        move = rng.choice(moves)
        yield state, move
        state = puzzle.apply(state, move)


def reference_moves(puzzle: Puzzle, state: State) -> set[Move]:
    """Legal moves computed cell by cell on a grid, independently of the masks."""
    grid = puzzle.grid(state)
    legal = set()
    for index, (car, offset) in enumerate(zip(puzzle.cars, state, strict=True)):
        for step in (-1, 1):
            head = offset - 1 if step < 0 else offset + car.length
            x, y = (head, car.line) if car.horizontal else (car.line, head)
            inside = 0 <= x < puzzle.width and 0 <= y < puzzle.height
            if inside and grid[y][x] is None:
                legal.add(Move(index, step))
    return legal


def reference_distance(puzzle: Puzzle, start: State) -> int | None:
    """Shortest solution length by fixed-point iteration, without a queue.

    Every reachable position is listed with :func:`reference_moves`, then the
    distance of each position is lowered to ``1 + distance of a neighbour``
    until nothing changes (Bellman-Ford with unit costs).
    """
    neighbours: dict[State, list[State]] = {}
    todo = [start]
    while todo:
        state = todo.pop()
        if state in neighbours:
            continue
        neighbours[state] = [
            puzzle.apply(state, m) for m in reference_moves(puzzle, state)
        ]
        todo.extend(neighbours[state])
    infinity = len(neighbours) + 1
    dist = {s: 0 if puzzle.is_solved(s) else infinity for s in neighbours}
    changed = True
    while changed:
        changed = False
        for state, around in neighbours.items():
            best = min((dist[n] + 1 for n in around), default=infinity)
            if best < dist[state]:
                dist[state] = best
                changed = True
    return None if dist[start] >= infinity else dist[start]
