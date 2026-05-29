"""
LeifV2Bot — EV-based discard, leifv1-style pegging.

Discard objective:
    total_ev(keep, throw, is_dealer) =
          E[score_hand(keep, cut)]    averaged over the 46 unseen cuts
        + sign * E[score_hand(crib, cut, is_crib=True)]
                                     averaged over opponent's 2 throws and cut
where sign = +1 as dealer, -1 as non-dealer.

The crib-EV term is sampled once at first use (rank-pair indexed, cached
at module level). It assumes opponent throws a uniformly random 2 cards
from the 50 remaining; this is a known approximation but well within
the noise of typical discard decisions.

Pegging is the same inlined greedy used in LeifV1Bot.
"""

import random
from itertools import combinations, combinations_with_replacement
from typing import Dict, List, Optional, Tuple

from ..bot import CribbagePlayer
from ..models import Card, Rank, Suit
from ..rules import get_legal_pegging_moves, score_hand


_RANK_ORDER = list(Rank)
_RANK_INDEX = {r: i for i, r in enumerate(_RANK_ORDER)}


def _crib_key(r1: Rank, r2: Rank) -> Tuple[Rank, Rank]:
    """Canonical (lower-rank, higher-rank) key for a multiset of 2 ranks."""
    if _RANK_INDEX[r1] <= _RANK_INDEX[r2]:
        return (r1, r2)
    return (r2, r1)


def _build_crib_ev_table(num_samples: int = 1000, seed: int = 12345) -> Dict[Tuple[Rank, Rank], float]:
    """
    Estimate E[crib_score | thrown rank-pair] by sampling opponent's 2-card
    discard and the cut. Our 2 throw cards always use different suits, which
    makes a 5-card crib flush impossible — a small bias, but the alternative
    (modelling crib flushes correctly) requires per-hand suit reasoning we
    don't have at discard time anyway.
    """
    rng = random.Random(seed)
    full_deck = [Card(r, s) for r in Rank for s in Suit]
    table: Dict[Tuple[Rank, Rank], float] = {}

    for r1, r2 in combinations_with_replacement(Rank, 2):
        throw = [Card(r1, Suit.SPADES), Card(r2, Suit.HEARTS)]
        throw_set = set(throw)
        remaining = [c for c in full_deck if c not in throw_set]

        total = 0
        for _ in range(num_samples):
            opp = rng.sample(remaining, 2)
            opp_set = set(opp)
            # 48 cards remain after our throw + opp's throw
            rest = [c for c in remaining if c not in opp_set]
            cut = rng.choice(rest)
            crib = [throw[0], throw[1], opp[0], opp[1]]
            pts, _ = score_hand(crib, cut, is_crib=True)
            total += pts

        table[_crib_key(r1, r2)] = total / num_samples

    return table


# Lazy-built once on first discard. Building is ~1–2 s in CPython; we don't
# pay that at import time, only when a tournament actually starts.
_CRIB_EV: Optional[Dict[Tuple[Rank, Rank], float]] = None


def _get_crib_ev() -> Dict[Tuple[Rank, Rank], float]:
    global _CRIB_EV
    if _CRIB_EV is None:
        _CRIB_EV = _build_crib_ev_table()
    return _CRIB_EV


# leifv1's static per-rank "keep value" — copied so peg() works without
# importing LeifV1Bot internals.
_RANK_KEEP_BONUS = (
    0.0,  # unused
    0.3,  # A
    0.2,  # 2
    0.2,  # 3
    0.5,  # 4
    1.5,  # 5
    0.5,  # 6
    0.2,  # 7
    0.2,  # 8
    0.3,  # 9
    0.2,  # 10/J/Q/K
)


class LeifV2Bot(CribbagePlayer):
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        crib_ev = _get_crib_ev()
        sign = 1.0 if is_dealer else -1.0

        full_deck = [Card(r, s) for r in Rank for s in Suit]
        hand_set = set(hand)
        unseen = [c for c in full_deck if c not in hand_set]
        # Cribbage always deals 6, so this should be 46.
        assert len(unseen) == 46

        best_score = float("-inf")
        best_throw: Optional[Tuple[Card, Card]] = None

        for keep in combinations(hand, 4):
            keep_list = list(keep)
            keep_set = set(keep)
            throw = tuple(c for c in hand if c not in keep_set)

            total = 0
            for cut in unseen:
                pts, _ = score_hand(keep_list, cut, is_crib=False)
                total += pts
            hand_ev = total / 46.0

            c_ev = crib_ev[_crib_key(throw[0].rank, throw[1].rank)]
            total_ev = hand_ev + sign * c_ev

            if total_ev > best_score:
                best_score = total_ev
                best_throw = throw

        return best_throw

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        # Inlined greedy peg — same as LeifV1Bot.
        legal: List[Card] = []
        for c in hand:
            if current_count + c.value <= 31:
                legal.append(c)
        if not legal:
            return None

        hist_len = len(peg_history)
        trailing_rank = peg_history[-1].rank if hist_len else None
        trailing_streak = 0
        if hist_len:
            trailing_streak = 1
            i = hist_len - 2
            while i >= 0 and peg_history[i].rank == trailing_rank:
                trailing_streak += 1
                i -= 1

        best_pts = -1
        best_card: Optional[Card] = None

        for card in legal:
            new_count = current_count + card.value
            pts = 0

            if new_count == 15:
                pts += 2
            elif new_count == 31:
                pts += 2

            if hist_len and card.rank == trailing_rank:
                streak = trailing_streak + 1
                if streak == 2:
                    pts += 2
                elif streak == 3:
                    pts += 6
                elif streak == 4:
                    pts += 12

            max_check = hist_len + 1
            if max_check > 7:
                max_check = 7
            run_score = 0
            for run_len in range(3, max_check + 1):
                ranks_seen = {card.numeric_rank}
                start = hist_len - (run_len - 1)
                lo = card.numeric_rank
                hi = card.numeric_rank
                ok = True
                for k in range(start, hist_len):
                    nr = peg_history[k].numeric_rank
                    if nr in ranks_seen:
                        ok = False
                        break
                    ranks_seen.add(nr)
                    if nr < lo:
                        lo = nr
                    if nr > hi:
                        hi = nr
                if ok and (hi - lo) == run_len - 1:
                    run_score = run_len
            pts += run_score

            if pts > best_pts:
                best_pts = pts
                best_card = card
            elif pts == best_pts and best_card is not None:
                if card.value > best_card.value:
                    best_card = card

        return best_card

    def count_hand(self, hand: List[Card], cut_card: Card, is_crib: bool) -> bool:
        return True
