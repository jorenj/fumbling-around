"""Catch infinite loop condition by adding iteration counter."""
import time, sys, os, signal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cribbage.models import Card, Rank, Suit
from src.cribbage.rules import get_legal_pegging_moves, score_hand, score_pegging
from src.cribbage.bot import CribbagePlayer
from src.cribbage.engine import GameEngine, IllegalMoveError
from src.cribbage.bots.random_bot import RandomBot
from src.cribbage.bots.greedy_bot import GreedyBot
from typing import Dict, List, Optional, Tuple

class InstrumentedEngine(GameEngine):
    def run_pegging_phase(self, hands: Dict[str, List[Card]], non_dealer: str, dealer: str):
        current_player = non_dealer
        other_player = dealer
        last_to_play = None
        passed = set()
        just_hit_31 = False
        iterations = 0

        while hands[non_dealer] or hands[dealer]:
            iterations += 1
            if iterations > 500:
                print(f"\n*** INFINITE LOOP DETECTED after {iterations} iterations ***")
                print(f"  hands: nd={[str(c) for c in hands[non_dealer]]} d={[str(c) for c in hands[dealer]]}")
                print(f"  current={current_player} other={other_player}")
                print(f"  passed={passed} count={self.state.current_count}")
                print(f"  last_to_play={last_to_play} just_hit_31={just_hit_31}")
                return

            if not hands[non_dealer]:
                passed.add(non_dealer)
            if not hands[dealer]:
                passed.add(dealer)

            if len(passed) == 2:
                if not just_hit_31 and last_to_play is not None:
                    self.award_points(last_to_play, 1, "Go")
                    if self.winner:
                        return
                self.state.current_count = 0
                self.state.peg_history = []
                just_hit_31 = False
                passed.clear()
                current_player = non_dealer if last_to_play == dealer else dealer
                if not hands[current_player]:
                    current_player, other_player = other_player, current_player
                else:
                    other_player = non_dealer if current_player == dealer else dealer
                continue

            if not hands[current_player] or current_player in passed:
                current_player, other_player = other_player, current_player
                continue

            bot = self.players[current_player]
            legal_moves = get_legal_pegging_moves(hands[current_player], self.state.current_count)
            played_card = bot.peg(hands[current_player].copy(), self.state.peg_history.copy(), self.state.current_count)

            if played_card is None:
                if legal_moves:
                    raise IllegalMoveError(current_player, "Passed when legal moves exist")
                passed.add(current_player)
                self.log_event("peg_go", current_player, f"{current_player} says Go.")
            else:
                if played_card not in legal_moves:
                    raise IllegalMoveError(current_player, f"Played illegal card {played_card}")

                hands[current_player].remove(played_card)
                self.state.current_count += played_card.value
                self.state.peg_history.append(played_card)
                last_to_play = current_player
                just_hit_31 = False

                self.log_event("peg_play", current_player, f"{current_player} played {played_card} (Count: {self.state.current_count})", {"card": str(played_card), "count": self.state.current_count})

                pts, bd = score_pegging(self.state.peg_history)
                if pts > 0:
                    self.award_points(current_player, pts, f"Pegging ({bd})")
                    if self.winner:
                        return

                if self.state.current_count == 31:
                    just_hit_31 = True
                    self.state.current_count = 0
                    self.state.peg_history = []
                    passed.clear()
                    current_player, other_player = other_player, current_player
                else:
                    current_player, other_player = other_player, current_player

        if last_to_play and self.state.current_count > 0:
            self.award_points(last_to_play, 1, "Last Card")


import random
random.seed(42)  # Deterministic for reproducibility

found = False
for i in range(200):
    p1 = RandomBot("RandomBot")
    p2 = GreedyBot("GreedyBot")
    engine = InstrumentedEngine(p1 if i % 2 == 0 else p2, p2 if i % 2 == 0 else p1)
    t = time.time()
    engine.play_game()
    elapsed = time.time() - t
    if elapsed > 0.1:
        print(f"Game {i+1}: {elapsed:.2f}s")
    else:
        sys.stdout.write('.')
        sys.stdout.flush()

print(f"\nCompleted 200 games")
