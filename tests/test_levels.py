"""The levels shipped with the package."""

from importlib import resources

import pytest

from helpers import reference_distance
from rushhour.level import bundled_level, bundled_names, format_level
from rushhour.solver import replay, solve


@pytest.mark.parametrize("name", bundled_names())
def test_bundled_level_is_solvable_within_its_limit(name: str) -> None:
    level = bundled_level(name)
    solution = solve(level.puzzle, level.start)
    assert solution is not None
    assert len(solution) <= level.max_moves
    assert level.puzzle.is_solved(replay(level.puzzle, level.start, solution.moves)[-1])


@pytest.mark.parametrize("name", bundled_names())
def test_bundled_level_file_is_canonical(name: str) -> None:
    level = bundled_level(name)
    assert not level.puzzle.is_solved(level.start)
    entry = resources.files("rushhour") / "levels" / f"{name}.txt"
    assert format_level(level) == entry.read_text(encoding="utf-8")


def test_levels_get_harder() -> None:
    lengths = []
    for name in bundled_names():
        level = bundled_level(name)
        solution = solve(level.puzzle, level.start)
        assert solution is not None
        lengths.append(len(solution))
    assert lengths[:4] == sorted(lengths[:4])


@pytest.mark.parametrize("name", ["01", "03"])
def test_bundled_solutions_match_the_reference(name: str) -> None:
    level = bundled_level(name)
    solution = solve(level.puzzle, level.start)
    assert solution is not None
    assert len(solution) == reference_distance(level.puzzle, level.start)
