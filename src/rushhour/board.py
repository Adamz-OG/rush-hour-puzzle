"""Parking model: cars, positions, legal moves and the winning condition.

A puzzle is split in two parts:

* :class:`Puzzle` holds what never changes during a game: the size of the
  parking and, for every car, its orientation, its length and the line it
  lives on (its row if it is horizontal, its column if it is vertical);
* a :data:`State` holds what changes: the offset of every car along its
  line, as a tuple of integers.

A state is immutable and hashable, so the solver can store millions of them
in a set. The cells of the parking are numbered ``y * width + x`` and every
set of cells is an integer bit mask, so a collision test is a single ``&``.
Car 0 (letter ``A``) is the car that must reach the exit on the right edge.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple

State = tuple[int, ...]
"""Offset of every car along its line: ``x`` if horizontal, ``y`` if vertical."""

MAX_CARS = 26


class BoardError(ValueError):
    """Raised for an impossible parking or an impossible position."""


class Direction(Enum):
    """The four arrow keys, with their unit vector (``y`` points down)."""

    _value_: tuple[int, int]

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def horizontal(self) -> bool:
        """Whether the direction moves along a row."""
        return self.value[1] == 0

    @property
    def step(self) -> int:
        """``+1`` towards the right or the bottom, ``-1`` otherwise."""
        dx, dy = self.value
        return dx + dy


@dataclass(frozen=True)
class Car:
    """The fixed part of a car.

    ``line`` is the row of a horizontal car or the column of a vertical one.
    """

    horizontal: bool
    length: int
    line: int

    def cells(self, offset: int) -> list[tuple[int, int]]:
        """Cells ``(x, y)`` covered by the car at ``offset``, top-left first."""
        if self.horizontal:
            return [(offset + i, self.line) for i in range(self.length)]
        return [(self.line, offset + i) for i in range(self.length)]

    def origin(self, offset: int) -> tuple[int, int]:
        """Top-left cell ``(x, y)`` of the car at ``offset``."""
        return (offset, self.line) if self.horizontal else (self.line, offset)

    def direction(self, step: int) -> Direction:
        """Arrow key that moves the car by ``step`` (``-1`` or ``+1``)."""
        if self.horizontal:
            return Direction.RIGHT if step > 0 else Direction.LEFT
        return Direction.DOWN if step > 0 else Direction.UP


class Move(NamedTuple):
    """One car moved by one cell: ``step`` is ``-1`` or ``+1``."""

    car: int
    step: int


def car_name(index: int) -> str:
    """Letter of a car: ``A`` for index 0, ``B`` for index 1, and so on."""
    return chr(ord("A") + index)


@dataclass(frozen=True)
class Puzzle:
    """Size of the parking and the fixed part of its cars."""

    width: int
    height: int
    cars: tuple[Car, ...]
    _masks: tuple[tuple[int, ...], ...] = field(init=False, repr=False, compare=False)
    _back: tuple[tuple[int, ...], ...] = field(init=False, repr=False, compare=False)
    _front: tuple[tuple[int, ...], ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Check the cars and precompute the bit masks of every position."""
        self._check()
        masks, back, front = [], [], []
        for car in self.cars:
            last = self.limit(car)
            masks.append(tuple(self._mask(car.cells(o)) for o in range(last + 1)))
            back.append(tuple(self._cell_mask(car, o - 1) for o in range(last + 1)))
            front.append(
                tuple(self._cell_mask(car, o + car.length) for o in range(last + 1))
            )
        object.__setattr__(self, "_masks", tuple(masks))
        object.__setattr__(self, "_back", tuple(back))
        object.__setattr__(self, "_front", tuple(front))

    # ------------------------------------------------------------ geometry
    def limit(self, car: Car) -> int:
        """Largest offset of ``car`` that keeps it inside the parking."""
        size = self.width if car.horizontal else self.height
        return size - car.length

    @property
    def exit_row(self) -> int:
        """Row of the exit, which is the row of car ``A``."""
        return self.cars[0].line

    def occupancy(self, state: State) -> int:
        """Bit mask of the cells covered by the cars in ``state``."""
        mask = 0
        for car_masks, offset in zip(self._masks, state, strict=True):
            mask |= car_masks[offset]
        return mask

    def grid(self, state: State) -> list[list[int | None]]:
        """Car index in every cell (``None`` if empty), row by row."""
        rows: list[list[int | None]] = [[None] * self.width for _ in range(self.height)]
        for index, (car, offset) in enumerate(zip(self.cars, state, strict=True)):
            for x, y in car.cells(offset):
                rows[y][x] = index
        return rows

    # --------------------------------------------------------------- moves
    def check(self, state: State) -> None:
        """Raise :class:`BoardError` if ``state`` is not a valid position."""
        if len(state) != len(self.cars):
            raise BoardError(f"expected {len(self.cars)} offsets, got {len(state)}")
        seen = 0
        for index, (car, offset) in enumerate(zip(self.cars, state, strict=True)):
            if not 0 <= offset <= self.limit(car):
                raise BoardError(f"car {car_name(index)} is outside the parking")
            mask = self._masks[index][offset]
            if seen & mask:
                raise BoardError(f"car {car_name(index)} overlaps another car")
            seen |= mask

    def can_move(self, state: State, move: Move, occupied: int | None = None) -> bool:
        """Whether ``move`` is legal in ``state``.

        ``occupied`` is the occupancy of ``state``; it is computed when omitted.
        """
        car, step = move
        if not 0 <= car < len(self.cars) or step not in (-1, 1):
            return False
        offset = state[car]
        if step < 0:
            entering = self._back[car][offset]
        else:
            entering = self._front[car][offset]
        if not entering:
            return False
        if occupied is None:
            occupied = self.occupancy(state)
        return not occupied & entering

    def moves(self, state: State, occupied: int | None = None) -> Iterator[Move]:
        """Every legal move in ``state``, car by car, backwards first."""
        if occupied is None:
            occupied = self.occupancy(state)
        for car, offset in enumerate(state):
            back = self._back[car][offset]
            if back and not occupied & back:
                yield Move(car, -1)
            front = self._front[car][offset]
            if front and not occupied & front:
                yield Move(car, 1)

    def move_for(self, car: int, direction: Direction) -> Move | None:
        """Move of ``car`` towards ``direction``, or ``None`` if it cannot go there.

        A horizontal car only goes left or right, a vertical car up or down.
        """
        if not 0 <= car < len(self.cars):
            return None
        if self.cars[car].horizontal != direction.horizontal:
            return None
        return Move(car, direction.step)

    @staticmethod
    def apply(state: State, move: Move) -> State:
        """State after ``move``; the move is assumed to be legal."""
        car, step = move
        return state[:car] + (state[car] + step,) + state[car + 1 :]

    def is_solved(self, state: State) -> bool:
        """Whether car ``A`` touches the exit on the right edge."""
        return state[0] == self.limit(self.cars[0])

    # ------------------------------------------------------------- helpers
    def _check(self) -> None:
        if self.width < 2 or self.height < 1:
            raise BoardError(f"parking too small: {self.width}x{self.height}")
        if not 1 <= len(self.cars) <= MAX_CARS:
            raise BoardError(f"a parking holds 1 to {MAX_CARS} cars")
        if not self.cars[0].horizontal:
            raise BoardError("car A must be horizontal")
        for index, car in enumerate(self.cars):
            size = self.height if car.horizontal else self.width
            if car.length < 2 or self.limit(car) < 0 or not 0 <= car.line < size:
                raise BoardError(f"car {car_name(index)} does not fit the parking")

    def _mask(self, cells: Sequence[tuple[int, int]]) -> int:
        mask = 0
        for x, y in cells:
            mask |= 1 << (y * self.width + x)
        return mask

    def _cell_mask(self, car: Car, offset: int) -> int:
        """Mask of the single cell at ``offset`` on the car's line, 0 if outside."""
        size = self.width if car.horizontal else self.height
        if not 0 <= offset < size:
            return 0
        x, y = car.origin(offset)
        return 1 << (y * self.width + x)
