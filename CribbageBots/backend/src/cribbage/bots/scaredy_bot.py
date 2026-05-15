from typing import List, Tuple, Optional
from itertools import combinations
from ..bot import CribbagePlayer
from ..models import Card, Rank
from ..rules import get_legal_pegging_moves, score_15s, score_pairs, score_runs, score_pegging

class ScaredyBot(CribbagePlayer):
    """
    An extremely defensive Cribbage bot.
    - When opponent deals: Throws the safest cards to the crib.
    - When it deals: Maximizes hand + crib points (ignoring cut).
    - Pegging: Plays the safest card to avoid giving points to the opponent.
    """

    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        if is_dealer:
            return self._discard_as_dealer(hand)
        else:
            return self._discard_as_non_dealer(hand)

    def _discard_as_dealer(self, hand: List[Card]) -> Tuple[Card, Card]:
        """Maximize hand points + crib points (from the 2 cards thrown)."""
        best_score = -1.0
        best_discard = None

        for keep in combinations(hand, 4):
            keep_list = list(keep)
            throw = [c for c in hand if c not in keep_list]
            
            # Score guaranteed points in hand
            h_score = score_15s(keep_list) + score_pairs(keep_list) + score_runs(keep_list)
            # Score guaranteed points in crib (just these 2 cards)
            c_score = score_15s(throw) + score_pairs(throw) + score_runs(throw)
            
            total = h_score + c_score
            if total > best_score:
                best_score = total
                best_discard = tuple(throw)
            elif total == best_score:
                # Tie-breaker: prefer keeping lower ranks for flexibility in pegging
                if best_discard is None or sum(c.numeric_rank for c in keep_list) < sum(c.numeric_rank for c in [x for x in hand if x not in best_discard]):
                    best_discard = tuple(throw)

        return best_discard

    def _discard_as_non_dealer(self, hand: List[Card]) -> Tuple[Card, Card]:
        """Minimize danger score for cards thrown to opponent's crib."""
        best_danger = 1000.0
        best_discard = None

        for keep in combinations(hand, 4):
            keep_list = list(keep)
            throw = [c for c in hand if c not in keep_list]
            
            danger = self._calculate_danger(throw)
            
            # Also consider what we keep. If we keep a great hand, it might be worth a bit of danger.
            # But ScaredyBot is EXTREMELY defensive.
            # We'll subtract a small fraction of the keep's score to break ties.
            h_score = score_15s(keep_list) + score_pairs(keep_list) + score_runs(keep_list)
            effective_danger = danger - (h_score * 0.1)

            if effective_danger < best_danger:
                best_danger = effective_danger
                best_discard = tuple(throw)

        return best_discard

    def _calculate_danger(self, throw: List[Card]) -> float:
        """Heuristic for how dangerous these 2 cards are in an opponent's crib."""
        danger = 0.0
        c1, c2 = throw
        
        # 1. Guaranteed points
        if c1.rank == c2.rank:
            danger += 8.0 # Pair
        if c1.value + c2.value == 15:
            danger += 8.0 # 15
            
        # 2. Potential for runs
        rank_diff = abs(c1.numeric_rank - c2.numeric_rank)
        if rank_diff == 1:
            danger += 5.0 # Consecutive
        elif rank_diff == 2:
            danger += 3.0 # One gap
            
        # 3. 5s are very dangerous
        for c in throw:
            if c.rank == Rank.FIVE:
                danger += 10.0
            elif c.value == 5: # Should be only 5, but covering bases
                danger += 10.0
                
        # 4. Jacks (Nobs)
        for c in throw:
            if c.rank == Rank.JACK:
                danger += 2.0
                
        # 5. 10-value cards (very common, easy to make 15s)
        for c in throw:
            if c.value == 10:
                danger += 1.0
                
        return danger

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        legal_moves = get_legal_pegging_moves(hand, current_count)
        if not legal_moves:
            return None

        best_score = -1000.0
        best_card = None

        for card in legal_moves:
            # 1. Immediate points for me
            pts, _ = score_pegging(peg_history + [card])
            
            # 2. Risk for opponent points next
            danger = 0.0
            new_count = current_count + card.value
            
            if new_count == 5 or new_count == 21:
                danger += 4.0 # High risk of opponent having a 10
            elif new_count < 15 and (15 - new_count) == 10:
                danger += 2.0
                
            if peg_history:
                # Pair risk
                if card.rank == peg_history[-1].rank:
                    danger += 3.0 # Opponent might have a 3rd card of same rank
                # Run risk
                if abs(card.numeric_rank - peg_history[-1].numeric_rank) == 1:
                    danger += 2.0
            else:
                # Leading
                if card.rank == Rank.FIVE:
                    danger += 4.0
                elif card.value == 10:
                    danger += 1.0
                elif card.numeric_rank == 4:
                    danger -= 1.0 # Safe lead
            
            # ScaredyBot formula: MyPoints - Danger
            # We also add a tiny bonus for playing higher value cards to get them out of hand
            # but only if safety is equal.
            move_score = pts - danger + (card.value * 0.01)
            
            if move_score > best_score:
                best_score = move_score
                best_card = card
        
        return best_card
