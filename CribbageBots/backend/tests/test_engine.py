"""
Performance and correctness tests for the Cribbage engine and bots.

Run with:
    python3 -m pytest tests/test_engine.py -v
or for the benchmark specifically:
    python3 tests/test_engine.py
"""
import time
import sys
import os

try:
    import pytest
    slow_marker = pytest.mark.slow
except ImportError:
    # Dummy decorator if pytest is not available
    def slow_marker(func): return func

from cribbage.models import Card, Rank, Suit
from cribbage.rules import (
    get_legal_pegging_moves, score_15s, score_pairs, score_runs,
    score_flush, score_nobs, score_hand, score_pegging
)
from cribbage.engine import GameEngine, PER_BOT_CPU_BUDGET_SECONDS
from cribbage.bots.random_bot import RandomBot
from cribbage.bots.greedy_bot import GreedyBot
from cribbage.bots.slow_bot import SlowBot


# ---------------------------------------------------------------------------
# Scoring unit tests
# ---------------------------------------------------------------------------

def test_score_15s_basic():
    hand = [
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.THREE, Suit.DIAMONDS),
        Card(Rank.KING, Suit.HEARTS),
    ]
    # 5+10 = 15, 5+K = 15, 2+3+10 = 15, 2+3+K = 15 → 8 pts
    assert score_15s(hand) == 8, f"Expected 8, got {score_15s(hand)}"


def test_score_pairs():
    hand = [
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS),
    ]
    # Three 5s = 3 pairs = 6 pts
    assert score_pairs(hand) == 6, f"Expected 6, got {score_pairs(hand)}"


def test_score_runs_basic():
    hand = [
        Card(Rank.THREE, Suit.HEARTS),
        Card(Rank.FOUR, Suit.SPADES),
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.SIX, Suit.DIAMONDS),
        Card(Rank.TWO, Suit.HEARTS),
    ]
    assert score_runs(hand) == 5, f"Expected 5 (run of 5), got {score_runs(hand)}"


def test_score_hand_perfect_29():
    """The highest possible Cribbage hand: J + 5,5,5 with a 5 cut of same suit as J."""
    hand = [
        Card(Rank.JACK, Suit.SPADES),
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.FIVE, Suit.CLUBS),
        Card(Rank.FIVE, Suit.DIAMONDS),
    ]
    cut = Card(Rank.FIVE, Suit.SPADES)
    pts, breakdown = score_hand(hand, cut)
    assert pts == 29, f"Expected 29, got {pts} ({breakdown})"


def test_score_hand_flush_4():
    hand = [
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.FOUR, Suit.HEARTS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.HEARTS),
    ]
    cut = Card(Rank.TEN, Suit.SPADES)
    pts, _ = score_hand(hand, cut)
    assert pts == 4, f"Expected 4 (flush only), got {pts}"


def test_score_hand_flush_5():
    hand = [
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.FOUR, Suit.HEARTS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.HEARTS),
    ]
    cut = Card(Rank.TEN, Suit.HEARTS)
    pts, _ = score_hand(hand, cut)
    assert pts == 5, f"Expected 5 (5-flush), got {pts}"


def test_crib_no_4flush():
    """A 4-flush is NOT valid in the crib — must be 5."""
    hand = [
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.FOUR, Suit.HEARTS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.HEARTS),
    ]
    cut = Card(Rank.TEN, Suit.SPADES)
    pts, _ = score_hand(hand, cut, is_crib=True)
    assert pts == 0, f"Expected 0 (no 4-flush in crib), got {pts}"


def test_pegging_15():
    history = [
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
    ]
    pts, bd = score_pegging(history)
    assert pts == 2, f"Expected 2 (15), got {pts} ({bd})"


def test_pegging_31():
    history = [
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.TEN, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS),
    ]
    pts, bd = score_pegging(history)
    assert pts == 2, f"Expected 2 (31), got {pts} ({bd})"


def test_pegging_pair():
    history = [
        Card(Rank.SEVEN, Suit.HEARTS),
        Card(Rank.SEVEN, Suit.SPADES),
    ]
    pts, bd = score_pegging(history)
    assert pts == 2, f"Expected 2 (pair), got {pts} ({bd})"


def test_pegging_run_of_3():
    history = [
        Card(Rank.THREE, Suit.HEARTS),
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.TWO, Suit.CLUBS),
    ]
    pts, bd = score_pegging(history)
    assert pts == 3, f"Expected 3 (run of 3), got {pts} ({bd})"


def test_legal_moves_excludes_over_31():
    hand = [
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.ACE, Suit.SPADES),
    ]
    # Count is 25: TEN (10) would bring it to 35 (illegal), ACE (1) to 26 (legal)
    legal = get_legal_pegging_moves(hand, 25)
    assert Card(Rank.ACE, Suit.SPADES) in legal
    assert Card(Rank.TEN, Suit.HEARTS) not in legal


# ---------------------------------------------------------------------------
# Integration: single game doesn't crash
# ---------------------------------------------------------------------------

def test_single_game_completes():
    p1 = RandomBot("RandomBot")
    p2 = GreedyBot("GreedyBot")
    engine = GameEngine(p1, p2, verbose=True)
    winner, log = engine.play_game()
    assert winner in ("RandomBot", "GreedyBot"), f"Unexpected winner: {winner}"
    assert len(log) > 0


def test_winner_has_121_or_forfeit():
    p1 = RandomBot("RandomBot")
    p2 = GreedyBot("GreedyBot")
    engine = GameEngine(p1, p2, verbose=True)
    winner, log = engine.play_game()
    winner_score = engine.state.scores.get(winner, 0)
    final_event = log[-1]
    # Winner either hit 121+ or the game ended in a forfeit
    assert winner_score >= 121 or final_event["type"] == "forfeit"


# ---------------------------------------------------------------------------
# Per-bot CPU budget enforcement
# ---------------------------------------------------------------------------

def test_slow_bot_forfeits_against_fast_bot():
    """SlowBot burns ~30ms per discard; cumulative budget (50ms) is exhausted on
    the second discard, so SlowBot forfeits and the opponent wins."""
    slow = SlowBot("SlowBot")
    fast = RandomBot("FastBot")
    engine = GameEngine(slow, fast, verbose=True)
    winner, log = engine.play_game()
    assert winner == "FastBot", f"Expected FastBot to win by forfeit, got {winner}"
    assert engine.end_reason.startswith("Forfeit:"), f"Expected forfeit, got {engine.end_reason}"
    assert "CPU budget" in engine.end_reason, f"Expected CPU budget message, got {engine.end_reason}"
    forfeit_events = [e for e in log if e["type"] == "forfeit"]
    assert len(forfeit_events) == 1
    assert forfeit_events[0]["player_id"] == "SlowBot"


def test_slow_bot_does_not_forfeit_when_enforcement_off():
    """Disabling enforcement lets SlowBot finish a game normally."""
    slow = SlowBot("SlowBot")
    fast = RandomBot("FastBot")
    engine = GameEngine(slow, fast, verbose=False, enforce_time_limit=False)
    winner, _ = engine.play_game()
    assert winner in ("SlowBot", "FastBot"), f"Unexpected winner: {winner}"
    assert not engine.end_reason.startswith("Forfeit:"), (
        f"Should not forfeit with enforcement off, got {engine.end_reason}"
    )


def test_log_messages_include_timing():
    """Every discard / peg_play / peg_go log entry includes elapsed_ms and
    cpu_remaining_ms in event data and a (Xms, Yms remaining) suffix in message."""
    p1 = RandomBot("RandomBot")
    p2 = GreedyBot("GreedyBot")
    engine = GameEngine(p1, p2, verbose=True)
    _, log = engine.play_game()
    timed_events = [e for e in log if e["type"] in ("discard", "peg_play", "peg_go")]
    assert timed_events, "Expected discard/peg events in log"
    for ev in timed_events:
        assert "elapsed_ms" in ev["data"], f"Missing elapsed_ms in {ev}"
        assert "cpu_remaining_ms" in ev["data"], f"Missing cpu_remaining_ms in {ev}"
        assert "ms remaining)" in ev["message"], f"Missing timing suffix in: {ev['message']}"
        assert ev["data"]["elapsed_ms"] >= 0
        assert ev["data"]["cpu_remaining_ms"] <= PER_BOT_CPU_BUDGET_SECONDS * 1000


def test_budget_resets_per_game():
    """A fresh GameEngine starts each player at the full budget; the budget
    is per-game, not per-process."""
    p1 = RandomBot("R1")
    p2 = RandomBot("R2")
    engine_a = GameEngine(p1, p2, verbose=False)
    assert engine_a.cpu_remaining["R1"] == PER_BOT_CPU_BUDGET_SECONDS
    engine_a.play_game()
    # After play, budget should be lower.
    assert engine_a.cpu_remaining["R1"] < PER_BOT_CPU_BUDGET_SECONDS
    # New engine = fresh budget.
    engine_b = GameEngine(p1, p2, verbose=False)
    assert engine_b.cpu_remaining["R1"] == PER_BOT_CPU_BUDGET_SECONDS


def test_tournament_counts_forfeits(capsys):
    """run_tournament tallies forfeits against the offending bot and prints
    them in the summary line."""
    from cribbage.tournament import run_tournament
    from cribbage.bots.slow_bot import SlowBot
    run_tournament(SlowBot, RandomBot, num_games=3, verbose=False, p1_id="Slow", p2_id="Fast")
    out = capsys.readouterr().out
    assert "Slow: 0 Wins, 0 Skunks, 3 Forfeits" in out, f"Forfeit count missing in:\n{out}"
    # Winner row should not have a Forfeits suffix.
    assert "Fast: 3 Wins" in out and "Forfeits" not in out.split("Fast: 3 Wins")[1].split("\n")[0]


def test_remote_bot_skipped_by_class_name():
    """The engine must not enforce the budget on RemoteBot (WebSocket bots).
    We use a stub class named RemoteBot with a deliberately slow discard
    to confirm enforcement is skipped by class-name check."""
    import time as _time

    class RemoteBot(RandomBot):
        def discard(self, hand, is_dealer):
            # Burn enough CPU to blow the budget if it were enforced.
            end = _time.process_time() + 0.080
            while _time.process_time() < end:
                pass
            return tuple(hand[:2])

    slow_remote = RemoteBot("SlowRemote")
    fast = RandomBot("Fast")
    engine = GameEngine(slow_remote, fast, verbose=False)
    # Single round shouldn't forfeit even though discard burned 80ms (>50ms budget).
    # Use max_iterations-style early exit by playing one full round and checking state.
    # Easiest: just play_game and confirm no Forfeit-by-budget occurred.
    winner, _ = engine.play_game()
    # Either bot can win; the assertion is that we did NOT forfeit on CPU.
    assert "CPU budget" not in (engine.end_reason or ""), (
        f"RemoteBot should be skipped from CPU enforcement, but got: {engine.end_reason}"
    )


# ---------------------------------------------------------------------------
# Performance benchmark: 100 games must complete in <= 120 seconds
# ---------------------------------------------------------------------------

def benchmark_100_games(time_limit_seconds: float = 120.0) -> float:
    """
    Runs 100 games of RandomBot vs GreedyBot and returns elapsed time.
    Raises AssertionError if it exceeds time_limit_seconds.
    """
    start = time.time()
    for i in range(100):
        p1 = RandomBot("RandomBot")
        p2 = GreedyBot("GreedyBot")
        engine = GameEngine(p1 if i % 2 == 0 else p2, p2 if i % 2 == 0 else p1)
        engine.play_game()
    elapsed = time.time() - start
    assert elapsed <= time_limit_seconds, (
        f"100 games took {elapsed:.1f}s — exceeds {time_limit_seconds}s limit"
    )
    return elapsed


@slow_marker
def test_100_games_within_time_limit():
    elapsed = benchmark_100_games(time_limit_seconds=120.0)
    print(f"\n  ✓ 100 games completed in {elapsed:.2f}s")


# ---------------------------------------------------------------------------
# Direct runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_score_15s_basic,
        test_score_pairs,
        test_score_runs_basic,
        test_score_hand_perfect_29,
        test_score_hand_flush_4,
        test_score_hand_flush_5,
        test_crib_no_4flush,
        test_pegging_15,
        test_pegging_31,
        test_pegging_pair,
        test_pegging_run_of_3,
        test_legal_moves_excludes_over_31,
        test_single_game_completes,
        test_winner_has_121_or_forfeit,
        test_slow_bot_forfeits_against_fast_bot,
        test_slow_bot_does_not_forfeit_when_enforcement_off,
        test_log_messages_include_timing,
        test_budget_resets_per_game,
        test_remote_bot_skipped_by_class_name,
    ]

    print("Running unit tests...")
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except AssertionError as e:
            print(f"  ✗ {t.__name__}: {e}")

    print("\nRunning performance benchmark (100 games)...")
    try:
        elapsed = benchmark_100_games(time_limit_seconds=120.0)
        print(f"  ✓ 100 games completed in {elapsed:.2f}s")
    except AssertionError as e:
        print(f"  ✗ {e}")
