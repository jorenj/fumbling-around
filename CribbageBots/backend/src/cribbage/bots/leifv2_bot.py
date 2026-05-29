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
_SUIT_INT = {s: i for i, s in enumerate(Suit)}


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


# Built at import time. ~1–2 s in CPython. Done once per process, before
# any GameEngine starts charging CPU against the bot's per-game budget.
_CRIB_EV: Dict[Tuple[Rank, Rank], float] = _build_crib_ev_table()


def _get_crib_ev() -> Dict[Tuple[Rank, Rank], float]:
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

        # Extract primitives for the 6 dealt cards once. CPython property
        # access on Enum members is the dominant cost in score_hand.
        n = len(hand)
        h_val = [c.value for c in hand]
        h_nrk = [c.numeric_rank for c in hand]
        h_sut = [_SUIT_INT[c.suit] for c in hand]
        h_jck = [c.rank == Rank.JACK for c in hand]

        # Precompute primitives for the 46 unseen cards once.
        full_deck = [Card(r, s) for r in Rank for s in Suit]
        hand_set = set(hand)
        unseen = [c for c in full_deck if c not in hand_set]
        unseen_v = tuple(c.value for c in unseen)
        unseen_n = tuple(c.numeric_rank for c in unseen)
        unseen_s = tuple(_SUIT_INT[c.suit] for c in unseen)

        best_score = float("-inf")
        best_throw: Optional[Tuple[Card, Card]] = None

        for keep_idx in combinations(range(n), 4):
            i0, i1, i2, i3 = keep_idx
            kv0, kv1, kv2, kv3 = h_val[i0], h_val[i1], h_val[i2], h_val[i3]
            kn0, kn1, kn2, kn3 = h_nrk[i0], h_nrk[i1], h_nrk[i2], h_nrk[i3]
            ks0, ks1, ks2, ks3 = h_sut[i0], h_sut[i1], h_sut[i2], h_sut[i3]
            kj0, kj1, kj2, kj3 = h_jck[i0], h_jck[i1], h_jck[i2], h_jck[i3]

            # Keep-only 15s subset-sum DP. dp[s] = # subsets summing to s.
            # We care about dp[s] for every s in 0..15 because, with the cut,
            # subsets summing to (15 - cut_v) become 15s.
            dp = [0] * 16
            dp[0] = 1
            for v in (kv0, kv1, kv2, kv3):
                for s in range(15, v - 1, -1):
                    dp[s] += dp[s - v]
            keep_15s = dp[15] * 2  # subsets entirely within keep

            # Keep-only pairs: count rank-equal among the 4 keep cards.
            # Compare via numeric_rank (1:1 with rank for our purposes, no
            # face-card ambiguity since J/Q/K all have distinct numeric_ranks).
            keep_pair_pts = 0
            if kn0 == kn1: keep_pair_pts += 2
            if kn0 == kn2: keep_pair_pts += 2
            if kn0 == kn3: keep_pair_pts += 2
            if kn1 == kn2: keep_pair_pts += 2
            if kn1 == kn3: keep_pair_pts += 2
            if kn2 == kn3: keep_pair_pts += 2

            # Keep is a 4-flush only if all 4 suits match.
            keep_4flush = (ks0 == ks1 == ks2 == ks3)
            keep_flush_suit = ks0 if keep_4flush else -1

            # Jack suits in keep — used for nobs.
            jack_suits = []
            if kj0: jack_suits.append(ks0)
            if kj1: jack_suits.append(ks1)
            if kj2: jack_suits.append(ks2)
            if kj3: jack_suits.append(ks3)

            # Sorted numeric ranks of the 4 keep cards (used for 5-card runs).
            sorted4 = sorted((kn0, kn1, kn2, kn3))

            total = 0
            for cut_i in range(46):
                cv = unseen_v[cut_i]
                cn = unseen_n[cut_i]
                cs = unseen_s[cut_i]

                # 15s: keep-only + subsets-of-keep-summing-to-(15-cv) joined with cut
                score = keep_15s
                if cv <= 15:
                    score += dp[15 - cv] * 2

                # Pairs: keep-internal + (cut, each_keep) pairs
                score += keep_pair_pts
                if cn == kn0: score += 2
                if cn == kn1: score += 2
                if cn == kn2: score += 2
                if cn == kn3: score += 2

                # Runs on 5 cards: sort once, then collapse duplicates,
                # then walk for longest consecutive sequence with multiplier.
                # Insertion of cn into sorted4 (length-4) into a length-5 sorted list.
                if cn <= sorted4[0]:
                    s5 = (cn, sorted4[0], sorted4[1], sorted4[2], sorted4[3])
                elif cn <= sorted4[1]:
                    s5 = (sorted4[0], cn, sorted4[1], sorted4[2], sorted4[3])
                elif cn <= sorted4[2]:
                    s5 = (sorted4[0], sorted4[1], cn, sorted4[2], sorted4[3])
                elif cn <= sorted4[3]:
                    s5 = (sorted4[0], sorted4[1], sorted4[2], cn, sorted4[3])
                else:
                    s5 = (sorted4[0], sorted4[1], sorted4[2], sorted4[3], cn)

                # Collapse duplicates → distinct[], counts[].
                distinct = [s5[0]]
                counts = [1]
                for k in range(1, 5):
                    if s5[k] == distinct[-1]:
                        counts[-1] += 1
                    else:
                        distinct.append(s5[k])
                        counts.append(1)

                # Longest consecutive sequence in distinct, multiplying counts.
                best_len = 0
                best_mult_sum = 0
                cur_len = 1
                cur_mult = counts[0]
                for k in range(1, len(distinct)):
                    if distinct[k] == distinct[k - 1] + 1:
                        cur_len += 1
                        cur_mult *= counts[k]
                    else:
                        if cur_len >= 3:
                            if cur_len > best_len:
                                best_len = cur_len
                                best_mult_sum = cur_mult
                            elif cur_len == best_len:
                                best_mult_sum += cur_mult
                        cur_len = 1
                        cur_mult = counts[k]
                if cur_len >= 3:
                    if cur_len > best_len:
                        best_len = cur_len
                        best_mult_sum = cur_mult
                    elif cur_len == best_len:
                        best_mult_sum += cur_mult
                if best_len >= 3:
                    score += best_len * best_mult_sum

                # Flush: 5-flush if cut suit matches keep suit, else 4-flush
                # (allowed in non-crib hands).
                if keep_4flush:
                    if cs == keep_flush_suit:
                        score += 5
                    else:
                        score += 4

                # Nobs: a Jack in keep with the same suit as cut.
                if jack_suits:
                    for js in jack_suits:
                        if js == cs:
                            score += 1
                            break

                total += score

            hand_ev = total / 46.0

            # Throw is the 2 cards not in keep.
            keep_set = {i0, i1, i2, i3}
            throw_idx = [i for i in range(n) if i not in keep_set]
            t0, t1 = hand[throw_idx[0]], hand[throw_idx[1]]
            c_ev = crib_ev[_crib_key(t0.rank, t1.rank)]
            total_ev = hand_ev + sign * c_ev

            if total_ev > best_score:
                best_score = total_ev
                best_throw = (t0, t1)

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
