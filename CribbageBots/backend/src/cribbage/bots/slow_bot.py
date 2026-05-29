import time
from typing import List, Optional, Tuple

from ..bot import CribbagePlayer
from ..models import Card
from ..rules import get_legal_pegging_moves


def _burn_cpu(seconds: float) -> None:
    end = time.process_time() + seconds
    while time.process_time() < end:
        pass


class SlowBot(CribbagePlayer):
    """A deliberately slow bot used to verify the engine's per-bot CPU budget.

    Burns ~30ms of CPU on every discard, which exceeds the 50ms cumulative
    budget on the second discard of any game and triggers a forfeit.
    """

    DISCARD_BURN_SECONDS = 0.030
    PEG_BURN_SECONDS = 0.001

    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        _burn_cpu(self.DISCARD_BURN_SECONDS)
        return tuple(hand[:2])

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        _burn_cpu(self.PEG_BURN_SECONDS)
        legal = get_legal_pegging_moves(hand, current_count)
        return legal[0] if legal else None
