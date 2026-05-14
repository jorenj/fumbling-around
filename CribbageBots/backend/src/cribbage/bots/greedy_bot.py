from typing import List, Tuple, Optional
from itertools import combinations
from ..bot import CribbagePlayer
from ..models import Card
from ..rules import get_legal_pegging_moves, score_hand, score_pegging

class GreedyBot(CribbagePlayer):
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        best_score = -1
        best_discard = None
        
        # We need to find 4 cards to keep that maximize points.
        # We don't know the cut card, so we'll just score the 4 kept cards with a dummy cut card that can't possibly help
        # Actually, scoring without a cut card is technically not allowed by our function (requires a cut card).
        # We'll evaluate average score over all possible cut cards for each combination.
        deck_cards = [Card(rank=r, suit=s) for r in type(hand[0].rank) for s in type(hand[0].suit)]
        possible_cuts = [c for c in deck_cards if c not in hand]
        
        for keep in combinations(hand, 4):
            # Calculate what we throw away
            throw = tuple(c for c in hand if c not in keep)
            
            # Estimate expected value of the kept hand
            total_expected_pts = 0
            for cut in possible_cuts:
                pts, _ = score_hand(list(keep), cut, is_crib=False)
                total_expected_pts += pts
                
            if total_expected_pts > best_score:
                best_score = total_expected_pts
                best_discard = throw
                
        return best_discard

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        legal_moves = get_legal_pegging_moves(hand, current_count)
        if not legal_moves:
            return None
            
        best_card = None
        best_pts = -1
        
        for card in legal_moves:
            # Simulate playing the card
            pts, _ = score_pegging(peg_history + [card])
            if current_count + card.value == 15 or current_count + card.value == 31:
                pts += 2
                
            if pts > best_pts:
                best_pts = pts
                best_card = card
            elif pts == best_pts:
                # Tie-breaker: play highest value card to get rid of big cards early
                if best_card is None or card.value > best_card.value:
                    best_card = card
                    
        return best_card
