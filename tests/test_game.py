from collections.abc import Iterator

import pytest

from helpers import small, traffic
from rushhour.board import Direction
from rushhour.game import Game, Outcome, play
from rushhour.level import Level
from rushhour.solver import solve

SOLUTION_KEYS = ["c", "RIGHT", "B", "UP", "a", "RIGHT", "RIGHT", "RIGHT", "RIGHT"]


def keys(sequence: list[str]) -> Iterator[str]:
    yield from sequence
    raise AssertionError("the game asked for more keys than expected")


def run(game: Game, sequence: list[str]) -> tuple[Outcome, list[str]]:
    screens: list[str] = []
    source = keys(sequence)
    outcome = play(game, lambda: next(source), lambda g: screens.append(g.screen()))
    return outcome, screens


def test_new_game_starts_at_level_start() -> None:
    game = Game(small())
    assert game.state == small().start and game.moves == 0 and game.outcome is None


def test_game_from_another_position_is_checked() -> None:
    with pytest.raises(ValueError, match="overlaps"):
        Game(small(), state=(1, 1, 2))


def test_move_counts_only_legal_moves() -> None:
    game = Game(small())
    assert not game.move(0, Direction.RIGHT)  # blocked by B
    assert not game.move(0, Direction.UP)  # wrong orientation
    assert game.move(2, Direction.RIGHT)
    assert game.moves == 1


def test_win_with_the_shortest_solution() -> None:
    outcome, screens = run(Game(small()), SOLUTION_KEYS)
    assert outcome is Outcome.WON
    assert len(screens) == len(SOLUTION_KEYS) + 1
    assert "solved in 6 moves" in screens[-1]


def test_continuous_moves_and_reselection() -> None:
    game = Game(small())
    sequence = ["C", "RIGHT", "RIGHT", "LEFT", "b", "b", "UP", "A"] + ["RIGHT"] * 4
    outcome, _ = run(game, sequence)
    assert outcome is Outcome.WON and game.moves == 8


def test_lost_when_moves_run_out() -> None:
    level = small()
    game = Game(Level(level.puzzle, level.start, 4, "short"))
    outcome, screens = run(game, ["c", "RIGHT", "LEFT", "RIGHT", "LEFT"])
    assert outcome is Outcome.LOST and game.moves == 4
    assert "no moves left" in screens[-1]


def test_win_on_the_last_allowed_move_is_a_win() -> None:
    level = small()
    game = Game(Level(level.puzzle, level.start, 6))
    assert run(game, SOLUTION_KEYS)[0] is Outcome.WON


def test_escape_abandons() -> None:
    game = Game(small())
    outcome, screens = run(game, ["c", "RIGHT", "ESCAPE"])
    assert outcome is Outcome.ABANDONED and game.moves == 1
    assert "abandoned" in screens[-1]


@pytest.mark.parametrize(
    ("sequence", "message"),
    [
        (["UP"], "choose a car first"),
        (["z"], "there is no car Z"),
        (["a", "UP"], "car A only moves left or right"),
        (["b", "LEFT"], "car B only moves up or down"),
        (["a", "RIGHT"], "car A is blocked"),
        (["a", "LEFT"], "car A is blocked"),
        (["1"], "unknown key '1'"),
        (["é"], "unknown key 'é'"),
        (["ENTER"], "unknown key 'ENTER'"),
        (["b"], "car B selected"),
    ],
)
def test_messages(sequence: list[str], message: str) -> None:
    game = Game(small())
    for key in sequence:
        assert game.press(key) is None
    assert message in game.message and game.moves == 0


def test_message_is_cleared_by_the_next_key() -> None:
    game = Game(small())
    game.press("z")
    game.press("c")
    assert game.message == "car C selected"


def test_hint_gives_the_first_move_without_counting_it() -> None:
    game = Game(small())
    assert game.press("?") is None
    assert game.message == "hint: C→ (6 moves to the exit)"
    assert game.moves == 0


def test_hint_follows_the_current_position() -> None:
    game = Game(traffic())
    solution = solve(game.puzzle, game.state)
    assert solution is not None
    game.press("?")
    assert f"({len(solution)} moves to the exit)" in game.message


def test_hint_when_unsolvable() -> None:
    from rushhour.board import Car, Puzzle

    puzzle = Puzzle(6, 2, (Car(True, 2, 0), Car(False, 2, 5), Car(True, 2, 0)))
    game = Game(Level(puzzle, (0, 0, 2), 10))
    game.press("?")
    assert game.message == "no solution from this position"


def test_screen_shows_board_counters_and_selection() -> None:
    game = Game(small())
    game.press("b")
    screen = game.screen(color=False)
    assert "[B]" in screen and "moves: 0 / 12" in screen and "car B selected" in screen
    assert "\x1b[" not in screen
    assert "\x1b[47m" in game.screen(color=True)


def test_play_returns_at_once_if_already_over() -> None:
    level = small()
    game = Game(level, state=(4, 0, 3))
    outcome, screens = run(game, [])
    assert outcome is Outcome.WON and len(screens) == 1
