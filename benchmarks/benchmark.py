"""Benchmark: shortest solution and search cost of every bundled level.

The solver is compared with a straightforward breadth-first search written
on the assignment's representation (a ``game`` dictionary copied with
``deepcopy`` for every new position, a grid rebuilt to test each move), to
measure what the tuple positions and the bit masks bring.

Usage::

    python benchmarks/benchmark.py            # table in the terminal
    python benchmarks/benchmark.py --json out.json

Times are the median of several runs, so the results can be reproduced.
"""

from __future__ import annotations

import argparse
import copy
import json
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rushhour.compat import GameDict, to_dict  # noqa: E402
from rushhour.level import bundled_level, bundled_names  # noqa: E402
from rushhour.solver import distances, solve  # noqa: E402

Row = dict[str, float | int | str]
STEPS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}


def naive_children(game: GameDict) -> list[GameDict]:
    """Every position one move away, each one a full copy of ``game``."""
    width, height = game["width"], game["height"]
    grid = [[False] * width for _ in range(height)]
    for (x, y), orientation, length in game["cars"]:
        for i in range(length):
            if orientation == "h":
                grid[y][x + i] = True
            else:
                grid[y + i][x] = True
    children = []
    for index, ((x, y), orientation, length) in enumerate(game["cars"]):
        for name, (dx, dy) in STEPS.items():
            if (orientation == "h") != (name in ("LEFT", "RIGHT")):
                continue
            ahead = length if dx + dy > 0 else -1  # cell the car moves into
            cx, cy = (x + ahead, y) if dx else (x, y + ahead)
            if 0 <= cx < width and 0 <= cy < height and not grid[cy][cx]:
                child = copy.deepcopy(game)
                child["cars"][index][0] = (x + dx, y + dy)
                children.append(child)
    return children


def naive_solve(game: GameDict) -> int:
    """Length of a shortest solution, by a breadth-first search on dictionaries."""

    def key(state: GameDict) -> tuple[tuple[int, int], ...]:
        return tuple(car[0] for car in state["cars"])

    def solved(state: GameDict) -> bool:
        (x, _), _, length = state["cars"][0]
        return bool(x + length == state["width"])

    seen = {key(game): 0}
    frontier = [game]
    while frontier:
        following = []
        for state in frontier:
            depth = seen[key(state)] + 1
            for child in naive_children(state):
                if key(child) in seen:
                    continue
                seen[key(child)] = depth
                if solved(child):
                    return depth
                following.append(child)
        frontier = following
    raise ValueError("no solution")


def median_time(function: Callable[[], object], repeat: int) -> float:
    """Median duration of ``function()`` in seconds."""
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        function()
        samples.append(time.perf_counter() - start)
    return statistics.median(samples)


def measure_level(name: str, repeat: int) -> Row:
    """Size, shortest solution, positions explored and time of one level."""
    level = bundled_level(name)
    puzzle, start = level.puzzle, level.start
    solution = solve(puzzle, start)
    assert solution is not None, name
    seconds = median_time(lambda: solve(puzzle, start), repeat)
    reachable = distances(puzzle, start)
    naive_start = time.perf_counter()
    assert naive_solve(to_dict(level)) == len(solution)
    naive_seconds = time.perf_counter() - naive_start
    return {
        "level": name,
        "size": f"{puzzle.width}x{puzzle.height}",
        "cars": len(puzzle.cars),
        "limit": level.max_moves,
        "shortest": len(solution),
        "explored": solution.explored,
        "reachable": len(reachable),
        "farthest": max(reachable.values()),
        "solve_ms": seconds * 1000,
        "positions_per_s": solution.explored / seconds,
        "naive_ms": naive_seconds * 1000,
        "speedup": naive_seconds / seconds,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="also write the results here")
    parser.add_argument("--repeat", type=int, default=5)
    args = parser.parse_args()
    rows = [measure_level(name, args.repeat) for name in bundled_names()]
    header = (
        f"{'level':<6}{'size':>6}{'cars':>6}{'limit':>7}{'best':>6}"
        f"{'explored':>10}{'reachable':>11}{'time':>11}{'naive BFS':>12}"
    )
    print(header)
    for row in rows:
        print(
            f"{row['level']:<6}{row['size']:>6}{row['cars']:>6}{row['limit']:>7}"
            f"{row['shortest']:>6}{row['explored']:>10}{row['reachable']:>11}"
            f"{row['solve_ms']:>8.1f} ms{row['naive_ms']:>9.0f} ms"
        )
    if args.json:
        args.json.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
