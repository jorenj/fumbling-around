from enum import Enum
from typing import List, Optional, Dict
from dataclasses import dataclass, field
import random

class Suit(str, Enum):
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    SPADES = "S"

class Rank(str, Enum):
    ACE = "A"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"

@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    @property
    def value(self) -> int:
        """Returns the pegging value of the card (Face cards = 10)"""
        if self.rank in (Rank.JACK, Rank.QUEEN, Rank.KING):
            return 10
        if self.rank == Rank.ACE:
            return 1
        return int(self.rank.value)
    
    @property
    def numeric_rank(self) -> int:
        """Returns the numeric rank for calculating runs (A=1, 2=2... J=11, Q=12, K=13)"""
        if self.rank == Rank.ACE: return 1
        if self.rank == Rank.JACK: return 11
        if self.rank == Rank.QUEEN: return 12
        if self.rank == Rank.KING: return 13
        return int(self.rank.value)

    def __str__(self):
        return f"{self.rank.value}{self.suit.value}"

# Pre-create all 52 unique Card instances to avoid recreating them in every round
ALL_52_CARDS = [Card(rank=r, suit=s) for r in Rank for s in Suit]

class Deck:
    def __init__(self):
        self._rng = random.SystemRandom()
        self.cards: List[Card] = []
        self.reset()
        
    def shuffle(self):
        self._rng.shuffle(self.cards)
        
    def deal(self, n: int) -> List[Card]:
        if n > len(self.cards):
            raise ValueError("Not enough cards in deck")
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt

    def reset(self):
        self.cards = list(ALL_52_CARDS)
        self.shuffle()

# Enums for Game State tracking
class Phase(str, Enum):
    DEAL = "deal"
    DISCARD = "discard"
    CUT = "cut"
    PEGGING = "pegging"
    COUNTING = "counting"
    GAME_OVER = "game_over"

@dataclass
class GameState:
    dealer_id: str
    non_dealer_id: str
    phase: Phase = Phase.DEAL
    scores: Dict[str, int] = field(default_factory=dict)
    
    # Pegging state
    current_count: int = 0
    peg_history: List[Card] = field(default_factory=list)
    pegged_cards: List[dict] = field(default_factory=list) # List of {"player_id": str, "card": Card}
    
    # Hand/Crib state (only visible to engine, bots get their own hands)
    crib: List[Card] = field(default_factory=list)
    cut_card: Optional[Card] = None
    
    def add_score(self, player_id: str, points: int):
        if player_id not in self.scores:
            self.scores[player_id] = 0
        self.scores[player_id] += points

