"""
LeifV4.5 Bot — Optimized EV discard with tuned positional play.
No Hail Mary mode.
"""

from typing import List, Tuple, Optional
from itertools import combinations
from ..models import Card, Rank, Suit
from .leifv3_bot import LeifV3Bot, _KEEP_PRIOR
from .leifv2_bot import _SUIT_INT, _get_crib_ev, _crib_key

class LeifV4_5Bot(LeifV3Bot):
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        self._reset_round_state()
        self._my_dealt = set(hand)

        thrown = self._discard_v4_5(hand, is_dealer)
        thrown_set = set(thrown)
        self._my_kept = self._my_dealt - thrown_set

        # Seed P(opp_has(c)) using LeifV3 logic
        full_deck = [Card(r, s) for r in Rank for s in Suit]
        unseen = [c for c in full_deck if c not in self._my_dealt]
        weights = {c: _KEEP_PRIOR[c.rank] for c in unseen}
        total = sum(weights.values())
        if total > 0:
            scale = 4.0 / total
            self._p_opp = {c: min(w * scale, 1.0) for c, w in weights.items()}
        else:
            self._p_opp = {c: 4.0 / len(unseen) for c in unseen}

        return thrown

    def _discard_v4_5(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        crib_ev = _get_crib_ev()
        
        # Determine score delta and modes
        my_score = getattr(self, "scores", {}).get(self.player_id, 0)
        opp_scores = [v for k, v in getattr(self, "scores", {}).items() if k != self.player_id]
        opp_score = opp_scores[0] if opp_scores else 0
        delta = my_score - opp_score

        opp_crib_w = 1.0
        our_crib_w = 1.0
        
        # Tuned thresholds and weights
        if delta > 10:
            # Defensive (far ahead): penalize giving opponent a good crib, value hand safety slightly more
            opp_crib_w = 1.2
            our_crib_w = 0.9
        elif delta < -10:
            # Aggressive (far behind): prioritize high crib EV for ourselves, care less about opponent's crib
            opp_crib_w = 0.8
            our_crib_w = 1.1

        n = len(hand)
        h_val = [c.value for c in hand]
        h_nrk = [c.numeric_rank for c in hand]
        h_sut = [_SUIT_INT[c.suit] for c in hand]
        h_jck = [c.rank == Rank.JACK for c in hand]

        full_deck = [Card(r, s) for r in Rank for s in Suit]
        hand_set = set(hand)
        unseen = [c for c in full_deck if c not in hand_set]

        # Precompute counts in unseen for fast iterations
        unseen_suit_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        unseen_rank_counts = {}
        for c in unseen:
            s_int = _SUIT_INT[c.suit]
            unseen_suit_counts[s_int] += 1
            
            r_nrk = c.numeric_rank
            if r_nrk not in unseen_rank_counts:
                unseen_rank_counts[r_nrk] = (c.value, 0)
            unseen_rank_counts[r_nrk] = (c.value, unseen_rank_counts[r_nrk][1] + 1)

        best_score = float("-inf")
        best_throw: Optional[Tuple[Card, Card]] = None

        for keep_idx in combinations(range(n), 4):
            i0, i1, i2, i3 = keep_idx
            kv0, kv1, kv2, kv3 = h_val[i0], h_val[i1], h_val[i2], h_val[i3]
            kn0, kn1, kn2, kn3 = h_nrk[i0], h_nrk[i1], h_nrk[i2], h_nrk[i3]
            ks0, ks1, ks2, ks3 = h_sut[i0], h_sut[i1], h_sut[i2], h_sut[i3]
            kj0, kj1, kj2, kj3 = h_jck[i0], h_jck[i1], h_jck[i2], h_jck[i3]

            # Keep-only 15s subset DP
            dp = [0] * 16
            dp[0] = 1
            for v in (kv0, kv1, kv2, kv3):
                for s in range(15, v - 1, -1):
                    dp[s] += dp[s - v]
            keep_15s = dp[15] * 2

            # Keep-only pairs
            keep_pair_pts = 0
            if kn0 == kn1: keep_pair_pts += 2
            if kn0 == kn2: keep_pair_pts += 2
            if kn0 == kn3: keep_pair_pts += 2
            if kn1 == kn2: keep_pair_pts += 2
            if kn1 == kn3: keep_pair_pts += 2
            if kn2 == kn3: keep_pair_pts += 2

            keep_4flush = (ks0 == ks1 == ks2 == ks3)
            keep_flush_suit = ks0 if keep_4flush else -1

            jack_suits = []
            if kj0: jack_suits.append(ks0)
            if kj1: jack_suits.append(ks1)
            if kj2: jack_suits.append(ks2)
            if kj3: jack_suits.append(ks3)

            sorted4 = sorted((kn0, kn1, kn2, kn3))

            total = 0
            for cn, (cv, cnt) in unseen_rank_counts.items():
                score = keep_15s
                if cv <= 15:
                    score += dp[15 - cv] * 2

                score += keep_pair_pts
                if cn == kn0: score += 2
                if cn == kn1: score += 2
                if cn == kn2: score += 2
                if cn == kn3: score += 2

                # Insertion of cn into sorted4
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

                distinct = [s5[0]]
                counts = [1]
                for k in range(1, 5):
                    if s5[k] == distinct[-1]:
                        counts[-1] += 1
                    else:
                        distinct.append(s5[k])
                        counts.append(1)

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

                total += score * cnt

            # Add flush points
            if keep_4flush:
                flush_suit_cnt = unseen_suit_counts[keep_flush_suit]
                total += 5 * flush_suit_cnt + 4 * (46 - flush_suit_cnt)

            # Add nobs points
            if jack_suits:
                for js in jack_suits:
                    total += unseen_suit_counts[js]

            hand_ev = total / 46.0

            keep_set = {i0, i1, i2, i3}
            throw_idx = [i for i in range(n) if i not in keep_set]
            t0, t1 = hand[throw_idx[0]], hand[throw_idx[1]]
            c_ev = crib_ev[_crib_key(t0.rank, t1.rank)]

            if is_dealer:
                total_ev = hand_ev + c_ev * our_crib_w
            else:
                total_ev = hand_ev - c_ev * opp_crib_w

            if total_ev > best_score:
                best_score = total_ev
                best_throw = (t0, t1)

        return best_throw
