"""Catch infinite loop condition by adding iteration counter."""
import time, sys, os, signal

from src.cribbage.models import Card, Rank, Suit
from src.cribbage.rules import get_legal_pegging_moves, score_hand, score_pegging
from src.cribbage.bot import CribbagePlayer
from src.cribbage.engine import GameEngine, IllegalMoveError
from src.cribbage.bots.random_bot import RandomBot
from src.cribbage.bots.greedy_bot import GreedyBot
from typing import Dict, List, Optional, Tuple

class InstrumentedEngine(GameEngine):
    def run_pegging_phase(self, hands: Dict[str, List[Card]], non_dealer: str, dealer: str):
        super().run_pegging_phase(hands, non_dealer, dealer, max_iterations=500)


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
