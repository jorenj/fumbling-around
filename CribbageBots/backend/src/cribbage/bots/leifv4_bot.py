"""
LeifV4Bot — State-tracking bot with positional play and Hail Mary mode.

Inherits from LeifV3Bot to retain belief-driven pegging.
Overrides discard to introduce score tracking and dynamic EV adjustments:
- Defensive: when far ahead, penalize giving opponent a good crib.
- Aggressive: when far behind, focus on our own hand/crib.
- Hail Mary: when almost mathematically eliminated, maximize the maximum possible
  hand score across all cut cards instead of expected value.
"""

from typing import List, Tuple, Optional
from itertools import combinations
from ..models import Card, Rank, Suit
from .leifv3_bot import LeifV3Bot, _KEEP_PRIOR
from .leifv2_bot import _SUIT_INT, _get_crib_ev, _crib_key

class LeifV4Bot(LeifV3Bot):
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        self._reset_round_state()
        self._my_dealt = set(hand)

        # Call our state-aware V4 discard logic
        thrown = self._discard_v4(hand, is_dealer)
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

    def _discard_v4(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        crib_ev = _get_crib_ev()
        
        # Determine score delta and modes
        my_score = getattr(self, "scores", {}).get(self.player_id, 0)
        opp_scores = [v for k, v in getattr(self, "scores", {}).items() if k != self.player_id]
        opp_score = opp_scores[0] if opp_scores else 0
        delta = my_score - opp_score

        hail_mary = False
        if opp_score >= 110:
            # We are in extreme danger. Simulation shows <5% win rate in these conditions.
            if is_dealer and my_score <= 90:
                hail_mary = True
            elif not is_dealer and my_score <= 100:
                hail_mary = True

        opp_crib_w = 1.0
        our_crib_w = 1.0
        if delta > 15:
            # Defensive
            opp_crib_w = 1.5
            our_crib_w = 0.8
        elif delta < -15:
            # Aggressive
            opp_crib_w = 0.5
            our_crib_w = 1.2

        n = len(hand)
        h_val = [c.value for c in hand]
        h_nrk = [c.numeric_rank for c in hand]
        h_sut = [_SUIT_INT[c.suit] for c in hand]
        h_jck = [c.rank == Rank.JACK for c in hand]

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

            dp = [0] * 16
            dp[0] = 1
            for v in (kv0, kv1, kv2, kv3):
                for s in range(15, v - 1, -1):
                    dp[s] += dp[s - v]
            keep_15s = dp[15] * 2

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
            max_score = 0
            for cut_i in range(46):
                cv = unseen_v[cut_i]
                cn = unseen_n[cut_i]
                cs = unseen_s[cut_i]

                score = keep_15s
                if cv <= 15:
                    score += dp[15 - cv] * 2

                score += keep_pair_pts
                if cn == kn0: score += 2
                if cn == kn1: score += 2
                if cn == kn2: score += 2
                if cn == kn3: score += 2

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

                if keep_4flush:
                    if cs == keep_flush_suit:
                        score += 5
                    else:
                        score += 4

                if jack_suits:
                    for js in jack_suits:
                        if js == cs:
                            score += 1
                            break

                total += score
                if score > max_score:
                    max_score = score

            hand_ev = total / 46.0

            keep_set = {i0, i1, i2, i3}
            throw_idx = [i for i in range(n) if i not in keep_set]
            t0, t1 = hand[throw_idx[0]], hand[throw_idx[1]]
            c_ev = crib_ev[_crib_key(t0.rank, t1.rank)]

            if hail_mary:
                # In Hail Mary mode, we solely care about our best-case scenario
                # because an average hand will still lose us the game. We ignore the crib EV.
                total_ev = max_score
            else:
                if is_dealer:
                    total_ev = hand_ev + c_ev * our_crib_w
                else:
                    total_ev = hand_ev - c_ev * opp_crib_w

            if total_ev > best_score:
                best_score = total_ev
                best_throw = (t0, t1)

        return best_throw
