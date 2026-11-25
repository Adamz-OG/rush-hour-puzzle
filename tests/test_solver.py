import random

import pytest

from helpers import random_parking, reference_distance, small, traffic
from rushhour.board import Car, Move, Puzzle
from rushhour.solver import describe, distances, replay, solve


def test_small_level_solution() -> None:
    level = small()
    solution = solve(level.puzzle, level.start)
    assert solution is not None
    assert solution.moves == (Move(2, 1), Move(1, -1)) + (Move(0, 1),) * 4
    assert len(solution) == 6 and solution.explored > len(solution)


def test_already_solved() -> None:
    puzzle = Puzzle(4, 1, (Car(True, 2, 0),))
    solution = solve(puzzle, (2,))
    assert solution is not None and solution.moves == () and solution.explored == 1


def test_unsolvable_returns_none() -> None:
    # a horizontal car C sits between A and the exit, on the same row
    puzzle = Puzzle(6, 2, (Car(True, 2, 0), Car(False, 2, 5), Car(True, 2, 0)))
    assert solve(puzzle, (0, 0, 2)) is None


def test_solution_replays_to_a_solved_position() -> None:
    level = traffic()
    solution = solve(level.puzzle, level.start)
    assert solution is not None
    states = replay(level.puzzle, level.start, solution.moves)
    assert len(states) == len(solution) + 1
    assert level.puzzle.is_solved(states[-1])
    assert not any(level.puzzle.is_solved(s) for s in states[:-1])


def test_replay_rejects_illegal_moves() -> None:
    level = small()
    with pytest.raises(ValueError, match="illegal move A\\+"):
        replay(level.puzzle, level.start, (Move(0, 1),))


def test_distances_from_start() -> None:
    level = small()
    seen = distances(level.puzzle, level.start)
    assert seen[level.start] == 0
    solved = [d for s, d in seen.items() if level.puzzle.is_solved(s)]
    assert min(solved) == 6
    assert all(d >= 0 for d in seen.values())


def test_describe_groups_equal_moves() -> None:
    puzzle = small().puzzle
    moves = (Move(2, 1), Move(1, -1), Move(0, 1), Move(0, 1), Move(1, 1))
    assert describe(moves, puzzle) == "C→ B↑ A→2 B↓"
    assert describe(moves) == "C+ B- A+2 B+"
    assert describe(()) == ""


@pytest.mark.parametrize("seed", range(60))
def test_bfs_is_optimal_against_a_fixed_point_reference(seed: int) -> None:
    puzzle, start = random_parking(random.Random(seed), width=5, height=5, cars=6)
    solution = solve(puzzle, start)
    expected = reference_distance(puzzle, start)
    if solution is None:
        assert expected is None
    else:
        assert len(solution) == expected
        assert puzzle.is_solved(replay(puzzle, start, solution.moves)[-1])


@pytest.mark.parametrize("seed", range(20))
def test_bfs_length_is_the_distance_to_the_nearest_solved_position(seed: int) -> None:
    puzzle, start = random_parking(random.Random(seed), width=6, height=6, cars=8)
    seen = distances(puzzle, start)
    solved = [d for s, d in seen.items() if puzzle.is_solved(s)]
    solution = solve(puzzle, start)
    assert (solution is None) == (not solved)
    if solution is not None:
        assert len(solution) == min(solved)
        assert solution.explored <= len(seen)
