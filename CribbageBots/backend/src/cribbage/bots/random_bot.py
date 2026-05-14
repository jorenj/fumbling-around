import random
from typing import List, Tuple, Optional
from ..bot import CribbagePlayer
from ..models import Card
from ..rules import get_legal_pegging_moves

class RandomBot(CribbagePlayer):
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        return tuple(random.sample(hand, 2))

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        legal_moves = get_legal_pegging_moves(hand, current_count)
        if not legal_moves:
            return None
        return random.choice(legal_moves)
