from typing import List, Tuple, Optional
from itertools import combinations
from ..bot import CribbagePlayer
from ..models import Card, Rank
from ..rules import get_legal_pegging_moves


# Static per-rank "keep value" — favors 5s (pair any face for 15) and mid cards
# that combine into 15s. Index by Card.value (1..10).
_RANK_KEEP_BONUS = (
    0.0,  # unused (value 0)
    0.3,  # A
    0.2,  # 2
    0.2,  # 3
    0.5,  # 4 (combos with face for 14, 5+4 for 9, etc.)
    1.5,  # 5 (most valuable mid card)
    0.5,  # 6
    0.2,  # 7
    0.2,  # 8
    0.3,  # 9
    0.2,  # 10/J/Q/K
)


class LeifV1Bot(CribbagePlayer):
    """
    A faster greedy bot. Same greedy philosophy as GreedyBot but inlines all
    keep scoring into a single pass over 4 cards (no Counter allocations,
    no DP arrays, no combinations() inside the scorer). Peg evaluation likewise
    inlines pair/run/15/31 detection from the existing peg_history without
    materializing a new list for each candidate.
    """

    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        # Precompute per-card numeric values once (attribute access is slow in CPython).
        cards = list(hand)
        values = [c.value for c in cards]
        nranks = [c.numeric_rank for c in cards]
        suits = [c.suit for c in cards]
        ranks = [c.rank for c in cards]

        n = len(cards)
        best_score = -1.0
        best_discard: Optional[Tuple[Card, Card]] = None

        # Iterate over indices of 4 cards to keep.
        for keep_idx in combinations(range(n), 4):
            kv = (values[keep_idx[0]], values[keep_idx[1]],
                  values[keep_idx[2]], values[keep_idx[3]])
            kn = (nranks[keep_idx[0]], nranks[keep_idx[1]],
                  nranks[keep_idx[2]], nranks[keep_idx[3]])
            ks = (suits[keep_idx[0]], suits[keep_idx[1]],
                  suits[keep_idx[2]], suits[keep_idx[3]])
            kr = (ranks[keep_idx[0]], ranks[keep_idx[1]],
                  ranks[keep_idx[2]], ranks[keep_idx[3]])

            score = 0.0

            # --- 15s on the 4-card keep (subset-sum over 4 values) ---
            # Unrolled: 4 singles, 6 pairs, 4 triples, 1 quad. Only sums hitting 15.
            v0, v1, v2, v3 = kv
            fifteens = 0
            # pairs
            if v0 + v1 == 15: fifteens += 1
            if v0 + v2 == 15: fifteens += 1
            if v0 + v3 == 15: fifteens += 1
            if v1 + v2 == 15: fifteens += 1
            if v1 + v3 == 15: fifteens += 1
            if v2 + v3 == 15: fifteens += 1
            # triples
            if v0 + v1 + v2 == 15: fifteens += 1
            if v0 + v1 + v3 == 15: fifteens += 1
            if v0 + v2 + v3 == 15: fifteens += 1
            if v1 + v2 + v3 == 15: fifteens += 1
            # quad
            if v0 + v1 + v2 + v3 == 15: fifteens += 1
            score += fifteens * 2

            # --- Pairs on the 4-card keep ---
            r0, r1, r2, r3 = kr
            pairs = 0
            if r0 == r1: pairs += 1
            if r0 == r2: pairs += 1
            if r0 == r3: pairs += 1
            if r1 == r2: pairs += 1
            if r1 == r3: pairs += 1
            if r2 == r3: pairs += 1
            score += pairs * 2

            # --- Runs on the 4-card keep (sorted unique-or-not) ---
            sn = sorted(kn)
            # Detect longest consecutive distinct run via simple scan.
            # Multiplier handles dup ranks like [3,3,4,5] = two runs of 3.
            run_len = 1
            run_mult = 1
            cur_len = 1
            cur_mult = 1
            best_len = 0
            best_mult_sum = 0
            i = 1
            prev = sn[0]
            dup_count = 1
            # Walk sorted list, tracking consecutive distinct values and dup multiplier.
            distinct = [prev]
            dup_counts = [1]
            while i < 4:
                if sn[i] == prev:
                    dup_counts[-1] += 1
                else:
                    distinct.append(sn[i])
                    dup_counts.append(1)
                    prev = sn[i]
                i += 1

            # Now find longest consecutive sequence in `distinct`, multiplying dup counts.
            j = 1
            cur_len = 1
            cur_mult = dup_counts[0]
            while j < len(distinct):
                if distinct[j] == distinct[j - 1] + 1:
                    cur_len += 1
                    cur_mult *= dup_counts[j]
                else:
                    if cur_len >= 3 and cur_len > best_len:
                        best_len = cur_len
                        best_mult_sum = cur_mult
                    elif cur_len >= 3 and cur_len == best_len:
                        best_mult_sum += cur_mult
                    cur_len = 1
                    cur_mult = dup_counts[j]
                j += 1
            if cur_len >= 3 and cur_len > best_len:
                best_len = cur_len
                best_mult_sum = cur_mult
            elif cur_len >= 3 and cur_len == best_len:
                best_mult_sum += cur_mult
            if best_len >= 3:
                score += best_len * best_mult_sum

            # --- Per-card keep bonuses (5s, mid cards, jacks, flush) ---
            score += (_RANK_KEEP_BONUS[v0] + _RANK_KEEP_BONUS[v1]
                      + _RANK_KEEP_BONUS[v2] + _RANK_KEEP_BONUS[v3])

            # Jacks: small bonus for nobs potential.
            jack = Rank.JACK
            if r0 == jack: score += 0.25
            if r1 == jack: score += 0.25
            if r2 == jack: score += 0.25
            if r3 == jack: score += 0.25

            # Flush: all 4 same suit.
            s0, s1, s2, s3 = ks
            if s0 == s1 == s2 == s3:
                score += 2.0

            if score > best_score:
                best_score = score
                # Keep these indices, discard the others.
                keep_set = set(keep_idx)
                throw = tuple(cards[i] for i in range(n) if i not in keep_set)
                best_discard = throw

        return best_discard

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        """
        Inline peg scoring. Avoids allocating a new history list per candidate
        by computing 15/31, pair-streak, and run-length deltas directly from
        peg_history + the candidate card.
        """
        # Inline legal-move filter (skip the helper's list comprehension overhead is minor,
        # but we already need the list once).
        legal: List[Card] = []
        for c in hand:
            if current_count + c.value <= 31:
                legal.append(c)
        if not legal:
            return None

        # Cache trailing pair-streak from existing history (cards of the same
        # rank counting back from the most recent play).
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

            # 15 / 31
            if new_count == 15:
                pts += 2
            elif new_count == 31:
                pts += 2

            # Pair / triple / quad: extends streak only if same rank as previous.
            if hist_len and card.rank == trailing_rank:
                streak = trailing_streak + 1
                if streak == 2:
                    pts += 2
                elif streak == 3:
                    pts += 6
                elif streak == 4:
                    pts += 12

            # Runs: longest run-length ending at this card.
            # Walk back through history, including this candidate, looking for
            # the longest suffix whose ranks form a consecutive set with no dups.
            # Max length to check is hist_len + 1, capped at 7 (full pegging round).
            max_check = hist_len + 1
            if max_check > 7:
                max_check = 7
            run_score = 0
            for run_len in range(3, max_check + 1):
                # Build the rank set from peg_history[-(run_len-1):] + [card].
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
                    if nr < lo: lo = nr
                    if nr > hi: hi = nr
                if ok and (hi - lo) == run_len - 1:
                    run_score = run_len  # keep the longest valid run
            pts += run_score

            if pts > best_pts:
                best_pts = pts
                best_card = card
            elif pts == best_pts and best_card is not None:
                # Tie-break: shed highest-value card first.
                if card.value > best_card.value:
                    best_card = card

        return best_card

    def count_hand(self, hand: List[Card], cut_card: Card, is_crib: bool) -> bool:
        return True
