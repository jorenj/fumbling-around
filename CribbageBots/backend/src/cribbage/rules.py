from typing import List, Tuple
from itertools import combinations
from collections import Counter

from .models import Card, Rank

def get_legal_pegging_moves(hand: List[Card], current_count: int) -> List[Card]:
    """Returns a list of cards from the hand that keep the count <= 31."""
    return [card for card in hand if current_count + card.value <= 31]

def score_15s(cards: List[Card]) -> int:
    """
    Scores 2 points for every combination of cards that sums to 15.

    Uses a compact subset-sum DP over card values instead of iterating
    all combinations explicitly, which is ~10x faster for 5-card hands.
    """
    # dp[s] = number of subsets whose values sum to s.
    dp = [0] * 16  # indices 0–15; we only care about subsets summing to exactly 15
    dp[0] = 1
    for card in cards:
        v = card.value
        # Iterate backwards to avoid using the same card twice
        for s in range(15, v - 1, -1):
            dp[s] += dp[s - v]
    return dp[15] * 2

def score_pairs(cards: List[Card]) -> int:
    """Scores 2 points for every pair."""
    score = 0
    for combo in combinations(cards, 2):
        if combo[0].rank == combo[1].rank:
            score += 2
    return score

def score_runs(cards: List[Card]) -> int:
    """Scores points for runs of 3 or more."""
    ranks = [c.numeric_rank for c in cards]
    counts = Counter(ranks)
    distinct_ranks = sorted(list(counts.keys()))
    
    max_run_length = 0
    # multiplier logic: we multiply by the count of each rank 
    # to account for duplicated runs (e.g. [3,3,4,5] is two runs of 3-4-5)
    run_combinations = 1
    
    # Find longest run
    current_run_length = 1
    current_combinations = counts[distinct_ranks[0]] if distinct_ranks else 0
    
    longest_runs = [] # Keep track of (length, multiplier)
    
    for i in range(1, len(distinct_ranks)):
        if distinct_ranks[i] == distinct_ranks[i-1] + 1:
            current_run_length += 1
            current_combinations *= counts[distinct_ranks[i]]
        else:
            if current_run_length >= 3:
                longest_runs.append((current_run_length, current_combinations))
            current_run_length = 1
            current_combinations = counts[distinct_ranks[i]]
            
    if current_run_length >= 3:
        longest_runs.append((current_run_length, current_combinations))
        
    if not longest_runs:
        return 0
        
    # The rules of cribbage dictate we only score the longest runs
    max_len = max(run[0] for run in longest_runs)
    total_score = 0
    for r_len, r_mult in longest_runs:
        if r_len == max_len:
            total_score += (r_len * r_mult)
            
    return total_score

def score_flush(hand: List[Card], cut_card: Card, is_crib: bool) -> int:
    """Scores flushes (4 or 5 points)."""
    suits = [c.suit for c in hand]
    if len(set(suits)) == 1:
        # Hand has a 4-flush
        if hand[0].suit == cut_card.suit:
            return 5 # 5-flush
        elif not is_crib:
            return 4 # 4-flush (only allowed in hand, not crib)
    return 0

def score_nobs(hand: List[Card], cut_card: Card) -> int:
    """Scores 1 point for having the Jack of the same suit as the cut card."""
    for card in hand:
        if card.rank == Rank.JACK and card.suit == cut_card.suit:
            return 1
    return 0

def score_hand(hand: List[Card], cut_card: Card, is_crib: bool = False, return_breakdown: bool = True) -> Tuple[int, str]:
    """
    Scores a 4-card hand plus the cut card.
    Returns (total_score, breakdown_string).
    """
    all_cards = hand + [cut_card]
    
    p15 = score_15s(all_cards)
    pairs = score_pairs(all_cards)
    runs = score_runs(all_cards)
    flush = score_flush(hand, cut_card, is_crib)
    nobs = score_nobs(hand, cut_card)
    
    total = p15 + pairs + runs + flush + nobs
    if not return_breakdown:
        return total, ""
        
    breakdown = []
    if p15 > 0: breakdown.append(f"15s: {p15}")
    if pairs > 0: breakdown.append(f"Pairs: {pairs}")
    if runs > 0: breakdown.append(f"Runs: {runs}")
    if flush > 0: breakdown.append(f"Flush: {flush}")
    if nobs > 0: breakdown.append(f"Nobs: {nobs}")
    
    bd_str = ", ".join(breakdown) if breakdown else "0"
    return total, bd_str

def score_pegging(play_history: List[Card]) -> Tuple[int, str]:
    """
    Given the recent history of uninterrupted pegging (no 'Go' resets),
    returns the points scored by the MOST RECENT card played.
    """
    if not play_history:
        return 0, ""
        
    score = 0
    breakdowns = []
    
    # Note: A single card can simultaneously score multiple point types.
    # For example, playing a 5 onto a count of 26 makes the count 31,
    # which can also form a pair if the previous card was a 5.
    # The structure below ensures 15 and 31 are mutually exclusive (via elif),
    # but pairs and runs are checked independently so their scores accumulate.
    
    # 15 or 31
    current_count = sum(c.value for c in play_history)
    if current_count == 15:
        score += 2
        breakdowns.append("15 for 2")
    elif current_count == 31:
        score += 2
        breakdowns.append("31 for 2")
        
    # Pairs
    pair_count = 1
    for i in range(len(play_history) - 2, -1, -1):
        if play_history[i].rank == play_history[-1].rank:
            pair_count += 1
        else:
            break
            
    if pair_count == 2:
        score += 2
        breakdowns.append("Pair for 2")
    elif pair_count == 3:
        score += 6
        breakdowns.append("Triple for 6")
    elif pair_count == 4:
        score += 12
        breakdowns.append("Quad for 12")
        
    # Runs (must be consecutive ranks, but can be played in any order)
    # Start looking backwards from length 3 up to the entire play history
    max_run_score = 0
    run_len_to_score = 0
    
    for run_len in range(3, len(play_history) + 1):
        subset = play_history[-run_len:]
        ranks = [c.numeric_rank for c in subset]
        
        # Are these ranks a consecutive sequence without duplicates?
        if len(set(ranks)) == run_len: # No duplicates
            if max(ranks) - min(ranks) == run_len - 1: # Consecutive
                max_run_score = run_len
                run_len_to_score = run_len
                
    if max_run_score > 0:
        score += max_run_score
        breakdowns.append(f"Run of {run_len_to_score} for {max_run_score}")
        
    return score, ", ".join(breakdowns)
