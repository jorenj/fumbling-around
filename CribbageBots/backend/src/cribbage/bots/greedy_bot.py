import random
from typing import List, Tuple, Optional
from itertools import combinations
from ..bot import CribbagePlayer
from ..models import Card, Rank, Suit
from ..rules import get_legal_pegging_moves, score_15s, score_pairs, score_runs, score_pegging


def _score_keep_heuristic(keep: List[Card]) -> float:
    """
    Fast heuristic to evaluate a 4-card keep without knowing the cut card.
    Scores guaranteed points (15s, pairs, runs) in the 4-card hand and adds
    a bonus for cards that are likely to combine well with a cut card.

    This replaces the expensive Monte Carlo approach (240 score_hand calls per
    discard decision) with O(1) operations, enabling 100 games in ~1-2 minutes.
    """
    score = 0.0

    # Score guaranteed points in the 4-card hand
    score += score_15s(keep)
    score += score_pairs(keep)
    score += score_runs(keep)

    # Bonus for cards close to 5 (most likely to make 15s with face cards)
    for card in keep:
        if card.rank == Rank.FIVE:
            score += 1.5  # 5s are extremely valuable (pair with any face card = 15)
        elif card.value in (4, 6):
            score += 0.5  # 4s and 6s combine with 9s/Aces for 15s

    # Bonus for flush potential (all same suit)
    suits = [c.suit for c in keep]
    if len(set(suits)) == 1:
        score += 2.0  # Already a 4-flush, good chance of 5-flush with cut

    # Bonus for "nobs" potential (having a Jack = 1 guaranteed if cut matches)
    for card in keep:
        if card.rank == Rank.JACK:
            score += 0.25  # 1/4 chance the cut matches the Jack's suit

    return score


class GreedyBot(CribbagePlayer):
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        """
        Choose the 2 cards to discard by evaluating all 15 possible 4-card keeps
        using a fast heuristic (no cut card required). O(1) per discard.
        """
        best_score = -1.0
        best_discard = None

        for keep in combinations(hand, 4):
            keep_list = list(keep)
            throw = tuple(c for c in hand if c not in keep_list)

            score = _score_keep_heuristic(keep_list)

            if score > best_score:
                best_score = score
                best_discard = throw

        return best_discard

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        """
        Play the card that scores the most immediate pegging points.
        Tie-break by playing the highest-value card to shed big cards early.
        score_pegging handles 15s, 31s, pairs, and runs — no double-counting.
        """
        legal_moves = get_legal_pegging_moves(hand, current_count)
        if not legal_moves:
            return None

        best_card = None
        best_pts = -1

        for card in legal_moves:
            pts, _ = score_pegging(peg_history + [card])

            if pts > best_pts:
                best_pts = pts
                best_card = card
            elif pts == best_pts:
                # Tie-breaker: shed highest value card first
                if best_card is None or card.value > best_card.value:
                    best_card = card

        return best_card
        
    def count_hand(self, hand: List[Card], cut_card: Card, is_crib: bool) -> bool:
        return True
