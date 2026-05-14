from typing import List, Tuple, Optional
from ..bot import CribbagePlayer
from ..models import Card
from ..rules import get_legal_pegging_moves

class HumanPlayer(CribbagePlayer):
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        while True:
            print(f"\n--- {self.player_id}'s Turn to Discard ---")
            print(f"You are the {'Dealer' if is_dealer else 'Non-Dealer'}")
            print("Your hand:")
            for i, card in enumerate(hand):
                print(f"{i}: {card}")
                
            try:
                indices = input("Enter 2 indices to discard (e.g., '0 2'): ").split()
                if len(indices) != 2:
                    print("Please enter exactly two indices.")
                    continue
                i1, i2 = int(indices[0]), int(indices[1])
                if i1 == i2:
                    print("Cannot discard the same card twice.")
                    continue
                return hand[i1], hand[i2]
            except (ValueError, IndexError):
                print("Invalid indices. Try again.")

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        legal_moves = get_legal_pegging_moves(hand, current_count)
        
        print(f"\n--- {self.player_id}'s Turn to Peg ---")
        print(f"Current Count: {current_count}")
        print(f"Peg History: {peg_history}")
        print("Your hand:")
        for i, card in enumerate(hand):
            is_legal = " " if card in legal_moves else " (ILLEGAL)"
            print(f"{i}: {card}{is_legal}")
            
        if not legal_moves:
            print("You have no legal moves. You must say 'Go'.")
            input("Press Enter to say 'Go'...")
            return None
            
        while True:
            try:
                idx_str = input("Enter index of card to play (or 'G' for Go if no moves): ")
                if idx_str.upper() == 'G':
                    if legal_moves:
                        print("You have legal moves! You cannot say Go.")
                        continue
                    return None
                    
                idx = int(idx_str)
                card = hand[idx]
                if card not in legal_moves:
                    print("That card brings the count over 31! Try again.")
                    continue
                return card
            except (ValueError, IndexError):
                print("Invalid input. Try again.")
