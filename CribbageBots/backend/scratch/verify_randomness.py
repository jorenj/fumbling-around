import random
from collections import Counter
from cribbage.models import Deck, Card, Rank, Suit

def check_randomness(num_trials=10000):
    print(f"Running {num_trials} trials to verify randomness...")
    
    # Track which card ends up in which position (0-51)
    position_counts = [Counter() for _ in range(52)]
    
    for _ in range(num_trials):
        deck = Deck() # Init calls shuffle()
        for i, card in enumerate(deck.cards):
            position_counts[i][str(card)] += 1
            
    # Check a few sample cards to see if they are roughly uniformly distributed
    sample_cards = ["AH", "KS", "5D", "JH"]
    
    print("\nDistribution checks (Expected approx. {} per position):".format(num_trials // 52))
    for card_str in sample_cards:
        counts = [pos[card_str] for pos in position_counts]
        avg = sum(counts) / 52
        std_dev = (sum((x - avg)**2 for x in counts) / 52)**0.5
        print(f"Card {card_str}: Avg={avg:.1f}, StdDev={std_dev:.1f}, Min={min(counts)}, Max={max(counts)}")

if __name__ == "__main__":
    check_randomness()
