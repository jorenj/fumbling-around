import random
from typing import List, Tuple, Optional
from ..bot import CribbagePlayer
from ..models import Card, Rank
from ..rules import get_legal_pegging_moves

class JorenBotV0(CribbagePlayer):
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        # Always keeps Jacks: discard 2 cards randomly from non-Jacks
        non_jacks = [card for card in hand if card.rank != Rank.JACK]
        # In a standard deck, hand of 6 has at most 4 Jacks, so len(non_jacks) is at least 2.
        # Fallback to random sample of the full hand if by any chance non_jacks is fewer than 2.
        if len(non_jacks) >= 2:
            discarded = random.sample(non_jacks, 2)
        else:
            discarded = random.sample(hand, 2)
        return (discarded[0], discarded[1])

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        legal_moves = get_legal_pegging_moves(hand, current_count)
        if not legal_moves:
            return None
        
        # Plays Jacks first
        legal_jacks = [card for card in legal_moves if card.rank == Rank.JACK]
        if legal_jacks:
            return random.choice(legal_jacks)
            
        # Otherwise plays randomly
        return random.choice(legal_moves)
        
    def count_hand(self, hand: List[Card], cut_card: Card, is_crib: bool) -> bool:
        return True
