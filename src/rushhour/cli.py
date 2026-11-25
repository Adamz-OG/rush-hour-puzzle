"""Command line interface: ``rushhour play | solve | levels``."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable, Sequence

from rushhour.game import Game, play
from rushhour.keyboard import read_key
from rushhour.level import Level, LevelError, bundled_level, bundled_names, find_level
from rushhour.render import render_board
from rushhour.solver import describe, distances, replay, solve

CLEAR = "\x1b[2J\x1b[H"
HELP = "letter: choose a car   arrows: move it   ?: hint   Esc: quit"


def main(argv: Sequence[str] | None = None, read: Callable[[], str] = read_key) -> int:
    """Run the command line tool and return the exit code."""
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "play":
            return _run_play(args, read)
        if args.command == "solve":
            return _run_solve(args)
        return _run_levels()
    except LevelError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rushhour", description="Rush Hour sliding puzzle and BFS solver."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("play", "play a level in the terminal"),
        ("solve", "print a shortest solution of a level"),
    ):
        command = commands.add_parser(name, help=text)
        command.add_argument(
            "level", nargs="?", default="1", help="bundled level number or file path"
        )
        command.add_argument("--no-color", action="store_true", help="plain text")
    commands.add_parser("levels", help="list the bundled levels")
    return parser


def _color(args: argparse.Namespace) -> bool:
    return not args.no_color and sys.stdout.isatty()


def _run_play(args: argparse.Namespace, read: Callable[[], str]) -> int:
    level = find_level(args.level)
    color = _color(args)

    def show(game: Game) -> None:
        clear = CLEAR if color else ""
        print(f"{clear}{_title(level)}\n{game.screen(color)}\n{HELP}", flush=True)

    return int(play(Game(level), read, show))


def _run_solve(args: argparse.Namespace) -> int:
    level = find_level(args.level)
    puzzle, color = level.puzzle, _color(args)
    start = time.perf_counter()
    solution = solve(puzzle, level.start)
    elapsed = time.perf_counter() - start
    print(_title(level))
    print("start:")
    print(render_board(puzzle, level.start, color))
    if solution is None:
        print("no solution")
        return 1
    final = replay(puzzle, level.start, solution.moves)[-1]
    print("after the solution:")
    print(render_board(puzzle, final, color))
    print(f"shortest solution: {len(solution)} moves (limit {level.max_moves})")
    print(f"positions explored: {solution.explored} in {elapsed:.3f} s")
    print(f"moves: {describe(solution.moves, puzzle)}")
    return 0


def _run_levels() -> int:
    print(f"{'level':<6}{'size':>6}{'cars':>6}{'limit':>7}{'best':>6}{'states':>9}")
    for name in bundled_names():
        level = bundled_level(name)
        puzzle = level.puzzle
        solution = solve(puzzle, level.start)
        best = "-" if solution is None else str(len(solution))
        reachable = len(distances(puzzle, level.start))
        size = f"{puzzle.width}x{puzzle.height}"
        print(
            f"{name:<6}{size:>6}{len(puzzle.cars):>6}{level.max_moves:>7}"
            f"{best:>6}{reachable:>9}"
        )
    return 0


def _title(level: Level) -> str:
    puzzle = level.puzzle
    name = level.name or "level"
    return f"{name}  ({puzzle.width}x{puzzle.height}, {len(puzzle.cars)} cars)"
