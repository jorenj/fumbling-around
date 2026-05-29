"""JorenBotV3 — Feature-flagged cribbage bot with disruptive strategies."""

import sys
import random
import inspect
from typing import List, Optional, Tuple
from itertools import combinations

from ..bot import CribbagePlayer
from ..models import Card, Rank, Suit
from ..rules import get_legal_pegging_moves, score_hand, score_pegging, score_15s, score_pairs, score_runs

FULL_DECK = [Card(rank=r, suit=s) for r in Rank for s in Suit]

def get_current_scores() -> Optional[dict]:
    """Find the GameEngine in the call stack and return the current scores."""
    try:
        frame = sys._getframe(1)
        while frame:
            obj = frame.f_locals.get('self')
            if obj and obj.__class__.__name__ == 'GameEngine':
                return obj.state.scores
            frame = frame.f_back
    except Exception:
        pass
    return None

def estimate_crib_value(discard_cards: List[Card]) -> float:
    """Statistical crib value estimator for the 2 discarded cards."""
    if len(discard_cards) != 2:
        return 0.0
        
    c1, c2 = discard_cards
    val = 1.5 # Base expected value
    
    # Pairs in discard
    if c1.rank == c2.rank:
        val += 4.0
        
    # Fifteens in discard
    if c1.value + c2.value == 15:
        val += 3.0
        
    # Consecutive ranks (runs potential)
    diff = abs(c1.numeric_rank - c2.numeric_rank)
    if diff == 1:
        val += 2.5
    elif diff == 2:
        val += 1.5
        
    # 5s in discard
    for c in discard_cards:
        if c.rank == Rank.FIVE:
            val += 3.0
            
    # Jacks in discard (Nobs potential)
    for c in discard_cards:
        if c.rank == Rank.JACK:
            val += 1.0
            
    return val

def minimax(
    our_hand: List[Card],
    opp_hand_size: int,
    peg_history: List[Card],
    current_count: int,
    is_our_turn: bool,
    depth: int,
    unknown_deck: List[Card],
    passed: set,
    last_player: Optional[str]
) -> float:
    # Terminal conditions
    if depth == 0 or (not our_hand and opp_hand_size == 0):
        return 0.0

    if depth == 1:
        if is_our_turn:
            legal_moves = [c for c in our_hand if current_count + c.value <= 31]
            if not legal_moves or "us" in passed:
                return 0.0
            best_val = -float('inf')
            for card in legal_moves:
                pts, _ = score_pegging(peg_history + [card])
                best_val = max(best_val, float(pts))
            return best_val
        else:
            rank_counts = {}
            rep_cards = {}
            for c in unknown_deck:
                r = c.rank
                if r in rank_counts:
                    rank_counts[r] += 1
                else:
                    rank_counts[r] = 1
                    rep_cards[r] = c
            legal_reps = [rep_cards[r] for r in rep_cards if current_count + rep_cards[r].value <= 31]
            if not legal_reps or opp_hand_size == 0 or "them" in passed:
                return 0.0
            total_val = 0.0
            total_weight = 0
            for card in legal_reps:
                weight = rank_counts[card.rank]
                pts, _ = score_pegging(peg_history + [card])
                total_val += -pts * weight
                total_weight += weight
            return total_val / total_weight if total_weight > 0 else 0.0

    # If both have passed or are out of cards, reset count
    if len(passed) == 2:
        go_points = 0
        if current_count != 31 and last_player is not None:
            go_points = 1 if last_player == "us" else -1
            
        next_turn = (last_player == "them")
        return go_points + minimax(
            our_hand=our_hand,
            opp_hand_size=opp_hand_size,
            peg_history=[],
            current_count=0,
            is_our_turn=next_turn,
            depth=depth,
            unknown_deck=unknown_deck,
            passed=set(),
            last_player=None
        )

    if is_our_turn:
        legal_moves = [c for c in our_hand if current_count + c.value <= 31]
        if not legal_moves or "us" in passed:
            new_passed = passed.copy()
            new_passed.add("us")
            return minimax(
                our_hand=our_hand,
                opp_hand_size=opp_hand_size,
                peg_history=peg_history,
                current_count=current_count,
                is_our_turn=False,
                depth=depth - 1,
                unknown_deck=unknown_deck,
                passed=new_passed,
                last_player=last_player
            )
            
        best_val = -float('inf')
        for card in legal_moves:
            pts, _ = score_pegging(peg_history + [card])
            new_history = peg_history + [card]
            new_count = current_count + card.value
            new_hand = [c for c in our_hand if c != card]
            new_passed = passed.copy()
            if not new_hand:
                new_passed.add("us")
                
            if new_count == 31:
                val = pts + minimax(
                    our_hand=new_hand,
                    opp_hand_size=opp_hand_size,
                    peg_history=[],
                    current_count=0,
                    is_our_turn=False,
                    depth=depth - 1,
                    unknown_deck=unknown_deck,
                    passed=set(),
                    last_player="us"
                )
            else:
                val = pts + minimax(
                    our_hand=new_hand,
                    opp_hand_size=opp_hand_size,
                    peg_history=new_history,
                    current_count=new_count,
                    is_our_turn=False,
                    depth=depth - 1,
                    unknown_deck=unknown_deck,
                    passed=new_passed,
                    last_player="us"
                )
            best_val = max(best_val, val)
        return best_val
    else:
        # Group unknown deck by rank to drastically reduce branching factor
        rank_counts = {}
        rep_cards = {}
        for c in unknown_deck:
            r = c.rank
            if r in rank_counts:
                rank_counts[r] += 1
            else:
                rank_counts[r] = 1
                rep_cards[r] = c
                
        legal_reps = [rep_cards[r] for r in rep_cards if current_count + rep_cards[r].value <= 31]
        
        if not legal_reps or opp_hand_size == 0 or "them" in passed:
            new_passed = passed.copy()
            new_passed.add("them")
            return minimax(
                our_hand=our_hand,
                opp_hand_size=opp_hand_size,
                peg_history=peg_history,
                current_count=current_count,
                is_our_turn=True,
                depth=depth - 1,
                unknown_deck=unknown_deck,
                passed=new_passed,
                last_player=last_player
            )
            
        total_val = 0.0
        total_weight = 0
        for card in legal_reps:
            weight = rank_counts[card.rank]
            pts, _ = score_pegging(peg_history + [card])
            new_history = peg_history + [card]
            new_count = current_count + card.value
            new_opp_size = opp_hand_size - 1
            new_passed = passed.copy()
            if new_opp_size == 0:
                new_passed.add("them")
                
            new_unknown = [c for c in unknown_deck if c != card]
            
            if new_count == 31:
                val = -pts + minimax(
                    our_hand=our_hand,
                    opp_hand_size=new_opp_size,
                    peg_history=[],
                    current_count=0,
                    is_our_turn=True,
                    depth=depth - 1,
                    unknown_deck=new_unknown,
                    passed=set(),
                    last_player="them"
                )
            else:
                val = -pts + minimax(
                    our_hand=our_hand,
                    opp_hand_size=new_opp_size,
                    peg_history=new_history,
                    current_count=new_count,
                    is_our_turn=True,
                    depth=depth - 1,
                    unknown_deck=new_unknown,
                    passed=new_passed,
                    last_player="them"
                )
            total_val += val * weight
            total_weight += weight
            
        return total_val / total_weight if total_weight > 0 else 0.0


class JorenBotV3(CribbagePlayer):
    def __init__(
        self, 
        player_id: str, 
        enable_pair_trap: bool = False, 
        enable_run_trap: bool = False, 
        enable_pacing: bool = False
    ):
        super().__init__(player_id)
        self.enable_pair_trap = enable_pair_trap
        self.enable_run_trap = enable_run_trap
        self.enable_pacing = enable_pacing
        self.stats = {"pair_traps": 0, "run_traps": 0, "pacing_actions": 0}
        self.round_our_plays = []
        self.round_opponent_plays = set()

    def reset(self):
        super().reset()
        self.stats = {"pair_traps": 0, "run_traps": 0, "pacing_actions": 0}
        self.round_our_plays = []
        self.round_opponent_plays = set()

    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        # 1. Determine remaining deck cards (52 minus hand)
        hand_set = set(hand)
        remaining_deck = [c for c in FULL_DECK if c not in hand_set]
        
        # 2. Get positional scaling based on scores
        scores = get_current_scores()
        score_delta = 0
        if scores:
            p_ids = list(scores.keys())
            if len(p_ids) == 2:
                my_score = scores.get(self.player_id, 0)
                opp_id = p_ids[1] if p_ids[0] == self.player_id else p_ids[0]
                opp_score = scores.get(opp_id, 0)
                score_delta = my_score - opp_score

        # Multiplier adjustments for positional play
        opp_crib_penalty_weight = 1.0
        our_crib_bonus_weight = 1.0
        
        if score_delta > 15:
            # We are leading -> play defensive
            opp_crib_penalty_weight = 1.5
            our_crib_bonus_weight = 0.8
        elif score_delta < -15:
            # We are trailing -> play aggressive
            opp_crib_penalty_weight = 0.5
            our_crib_bonus_weight = 1.2
            
        best_ev = -float('inf')
        best_discard = None
        
        # Pre-count remaining ranks and suits for analytical expected value
        from collections import Counter
        rank_counts = Counter(c.rank for c in remaining_deck)
        suit_counts = Counter(c.suit for c in remaining_deck)
        
        # Pre-map rank to a representative card to avoid linear search in loop
        rank_to_card = {}
        for c in remaining_deck:
            if c.rank not in rank_to_card:
                rank_to_card[c.rank] = c
                
        for keep in combinations(hand, 4):
            keep_list = list(keep)
            discarded = [c for c in hand if c not in keep_list]
            
            # Analytical Flush EV
            suits_in_keep = [c.suit for c in keep_list]
            if len(set(suits_in_keep)) == 1:
                flush_suit = suits_in_keep[0]
                matching_suits = suit_counts[flush_suit]
                flush_ev = 4.0 + (matching_suits / 46.0)
            else:
                flush_ev = 0.0
                
            # Analytical Nobs EV
            nobs_ev = 0.0
            for card in keep_list:
                if card.rank == Rank.JACK:
                    matching_suits = suit_counts[card.suit]
                    nobs_ev += matching_suits / 46.0
            
            # Rank-based EV (15s, pairs, runs) evaluated over unique ranks
            total_rank_pts = 0
            for rank, r_count in rank_counts.items():
                cut_card = rank_to_card[rank]
                combo = keep_list + [cut_card]
                pts = score_15s(combo) + score_pairs(combo) + score_runs(combo)
                total_rank_pts += pts * r_count
            
            keep_ev = (total_rank_pts / 46.0) + flush_ev + nobs_ev
            
            # Crib EV
            crib_ev = estimate_crib_value(discarded)
            
            if is_dealer:
                total_ev = keep_ev + (crib_ev * our_crib_bonus_weight)
            else:
                total_ev = keep_ev - (crib_ev * opp_crib_penalty_weight)
                
            if total_ev > best_ev:
                best_ev = total_ev
                best_discard = tuple(discarded)
                
        return best_discard

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        # Detect start of round
        if len(hand) == 4 and not peg_history:
            self.round_our_plays = []
            self.round_opponent_plays = set()
            
        # Record opponent plays from the current history
        for card in peg_history:
            if not any(card is our_c for our_c in self.round_our_plays):
                self.round_opponent_plays.add(card)

        legal_moves = get_legal_pegging_moves(hand, current_count)
        if not legal_moves:
            return None
            
        # Combine all played cards
        played_cards = set(self.round_our_plays) | self.round_opponent_plays
        unknown_deck = [c for c in FULL_DECK if c not in set(hand + peg_history) and c not in played_cards]
        
        opp_hand_size = max(0, 4 - len(self.round_opponent_plays))
            
        best_val = -float('inf')
        best_card = None
        
        for card in legal_moves:
            pts, _ = score_pegging(peg_history + [card])
            
            # Apply disruptive strategy heuristics/bonuses
            bonus = 0.0
            
            # 1. Pair Trap (Lead rank R if we hold multiple cards of rank R)
            if self.enable_pair_trap and not peg_history:
                same_rank_count = sum(1 for c in hand if c.rank == card.rank)
                if same_rank_count >= 2:
                    bonus += 1.5
                    self.stats["pair_traps"] += 1
            
            # 2. Run Trap (Connects with another card in hand to invite runs)
            if self.enable_run_trap:
                has_connection = any(
                    c != card and abs(c.numeric_rank - card.numeric_rank) in (1, 2)
                    for c in hand
                )
                if has_connection:
                    bonus += 1.0
                    self.stats["run_traps"] += 1
                    
            # 3. Pacing & Blockades
            if self.enable_pacing:
                new_count = current_count + card.value
                
                # A. Hold low cards (Aces/Twos) early
                if new_count < 15 and card.value <= 2:
                    has_higher_move = any(c.value > 2 for c in legal_moves)
                    if has_higher_move:
                        bonus -= 0.8
                        self.stats["pacing_actions"] += 1
                        
                # B. Avoid making count 21 unless we hold a 10-value card to defend
                if new_count == 21:
                    new_hand = [c for c in hand if c != card]
                    has_ten = any(c.value == 10 for c in new_hand)
                    if not has_ten:
                        bonus -= 1.2
                        self.stats["pacing_actions"] += 1
            
            new_history = peg_history + [card]
            new_count = current_count + card.value
            new_hand = [c for c in hand if c != card]
            
            passed = set()
            if not new_hand:
                passed.add("us")
            if opp_hand_size == 0:
                passed.add("them")
                
            new_unknown = [c for c in unknown_deck if c != card]
            
            if new_count == 31:
                val = pts + bonus + minimax(
                    our_hand=new_hand,
                    opp_hand_size=opp_hand_size,
                    peg_history=[],
                    current_count=0,
                    is_our_turn=False,
                    depth=2,
                    unknown_deck=new_unknown,
                    passed=set(),
                    last_player="us"
                )
            else:
                val = pts + bonus + minimax(
                    our_hand=new_hand,
                    opp_hand_size=opp_hand_size,
                    peg_history=new_history,
                    current_count=new_count,
                    is_our_turn=False,
                    depth=2,
                    unknown_deck=new_unknown,
                    passed=passed,
                    last_player="us"
                )
                
            if val > best_val:
                best_val = val
                best_card = card
            elif val == best_val:
                if best_card is None or card.value > best_card.value:
                    best_card = card
                    
        if best_card is not None:
            self.round_our_plays.append(best_card)
        return best_card

    def count_hand(self, hand: List[Card], cut_card: Card, is_crib: bool) -> bool:
        return True
