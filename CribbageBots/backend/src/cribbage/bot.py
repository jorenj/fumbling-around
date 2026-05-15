from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from .models import Card

class CribbagePlayer(ABC):
    def __init__(self, player_id: str):
        self.player_id = player_id

    @abstractmethod
    def discard(self, hand: List[Card], is_dealer: bool) -> tuple:
        """
        Choose 2 cards to throw to the crib.
        Must return two Card objects that are currently in `hand`.
        """
        pass

    @abstractmethod
    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        """
        Choose a card to play during pegging, or return None for 'Go'.
        Must return a Card object currently in `hand` that keeps count <= 31.
        """
        pass

    def reset(self):
        """
        Perform any necessary cleanup or state reset before a new game starts.
        Optional for bot implementations.
        """
        pass
