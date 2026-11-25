import random

import pytest

from helpers import random_parking, random_walk, reference_moves, small, traffic
from rushhour.board import MAX_CARS, BoardError, Car, Direction, Move, Puzzle, car_name


def test_direction_properties() -> None:
    assert Direction.LEFT.horizontal and Direction.RIGHT.horizontal
    assert not Direction.UP.horizontal and not Direction.DOWN.horizontal
    assert [d.step for d in Direction] == [-1, 1, -1, 1]


def test_car_cells_and_origin() -> None:
    horizontal, vertical = Car(True, 3, 2), Car(False, 2, 4)
    assert horizontal.cells(1) == [(1, 2), (2, 2), (3, 2)]
    assert vertical.cells(0) == [(4, 0), (4, 1)]
    assert horizontal.origin(1) == (1, 2) and vertical.origin(3) == (4, 3)


def test_car_direction_follows_orientation() -> None:
    assert Car(True, 2, 0).direction(1) is Direction.RIGHT
    assert Car(True, 2, 0).direction(-1) is Direction.LEFT
    assert Car(False, 2, 0).direction(1) is Direction.DOWN
    assert Car(False, 2, 0).direction(-1) is Direction.UP


def test_car_names() -> None:
    assert [car_name(i) for i in (0, 1, 25)] == ["A", "B", "Z"]


def test_grid_and_occupancy() -> None:
    level = small()
    grid = level.puzzle.grid(level.start)
    assert grid[2][:3] == [0, 0, 1] and grid[0][2:4] == [2, 2]
    cells = sum(car.length for car in level.puzzle.cars)
    assert bin(level.puzzle.occupancy(level.start)).count("1") == cells


def test_limits_and_exit_row() -> None:
    puzzle = small().puzzle
    assert puzzle.exit_row == 2
    assert [puzzle.limit(car) for car in puzzle.cars] == [4, 2, 4]


def test_moves_in_small_level() -> None:
    level = small()
    moves = set(level.puzzle.moves(level.start))
    assert moves == {Move(1, 1), Move(2, -1), Move(2, 1)}


def test_can_move_rejects_bad_input() -> None:
    level = small()
    puzzle, start = level.puzzle, level.start
    assert not puzzle.can_move(start, Move(0, 1))  # blocked by B
    assert not puzzle.can_move(start, Move(0, -1))  # left edge
    assert not puzzle.can_move(start, Move(9, 1))  # no such car
    assert not puzzle.can_move(start, Move(1, 2))  # not a single step
    assert puzzle.can_move(start, Move(1, 1), puzzle.occupancy(start))


def test_move_for_checks_orientation() -> None:
    puzzle = small().puzzle
    assert puzzle.move_for(0, Direction.RIGHT) == Move(0, 1)
    assert puzzle.move_for(1, Direction.UP) == Move(1, -1)
    assert puzzle.move_for(0, Direction.UP) is None
    assert puzzle.move_for(1, Direction.LEFT) is None
    assert puzzle.move_for(5, Direction.LEFT) is None


def test_apply_changes_one_car_only() -> None:
    assert Puzzle.apply((1, 2, 3), Move(1, -1)) == (1, 1, 3)


def test_is_solved() -> None:
    level = small()
    assert not level.puzzle.is_solved(level.start)
    assert level.puzzle.is_solved((4, 0, 3))


def test_check_accepts_start_and_rejects_bad_states() -> None:
    level = traffic()
    level.puzzle.check(level.start)
    with pytest.raises(BoardError, match="offsets"):
        level.puzzle.check(level.start[:-1])
    with pytest.raises(BoardError, match="outside"):
        level.puzzle.check((5,) + level.start[1:])
    with pytest.raises(BoardError, match="overlaps"):
        level.puzzle.check((3,) + level.start[1:])


@pytest.mark.parametrize(
    ("width", "height", "cars", "message"),
    [
        (1, 3, (Car(True, 2, 0),), "too small"),
        (6, 6, (), "1 to 26"),
        (6, 6, (Car(True, 2, 0),) * (MAX_CARS + 1), "1 to 26"),
        (6, 6, (Car(False, 2, 0),), "horizontal"),
        (6, 6, (Car(True, 1, 0),), "does not fit"),
        (6, 6, (Car(True, 7, 0),), "does not fit"),
        (6, 6, (Car(True, 2, 0), Car(False, 2, 6)), "car B does not fit"),
    ],
)
def test_invalid_puzzles(
    width: int, height: int, cars: tuple[Car, ...], message: str
) -> None:
    with pytest.raises(BoardError, match=message):
        Puzzle(width, height, cars)


@pytest.mark.parametrize("seed", range(40))
def test_moves_match_a_cell_by_cell_reference(seed: int) -> None:
    rng = random.Random(seed)
    puzzle, state = random_parking(rng)
    for position, _ in random_walk(rng, puzzle, state, 60):
        assert set(puzzle.moves(position)) == reference_moves(puzzle, position)


@pytest.mark.parametrize("seed", range(40))
def test_random_walks_never_overlap_and_are_reversible(seed: int) -> None:
    rng = random.Random(seed)
    puzzle, state = random_parking(rng, width=6, height=6, cars=9)
    for position, move in random_walk(rng, puzzle, state, 80):
        child = puzzle.apply(position, move)
        puzzle.check(child)
        back = Move(move.car, -move.step)
        assert puzzle.can_move(child, back)
        assert puzzle.apply(child, back) == position
