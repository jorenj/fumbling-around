import json
from queue import Queue, Empty
from typing import List, Tuple, Optional
from ..bot import CribbagePlayer
from ..models import Card
from ..rules import get_legal_pegging_moves
from ..exceptions import TimeoutError, IllegalMoveError

class RemoteBot(CribbagePlayer):
    def __init__(self, player_id: str, timeout: Optional[float] = 30):
        super().__init__(player_id)
        self.timeout = timeout
        # Queue for sending requests TO the websocket
        self.request_queue = Queue()
        # Queue for receiving responses FROM the websocket
        self.response_queue = Queue()
        
    def send_event(self, event_dict):
        self.request_queue.put({"action": "state_update", "event": event_dict})
        
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        req = {
            "action": "discard",
            "hand": [str(c) for c in hand],
            "is_dealer": is_dealer
        }
        self.request_queue.put(req)
        
        # Block until websocket provides a response
        try:
            res = self.response_queue.get(timeout=self.timeout)
        except Empty:
            raise TimeoutError(self.player_id, "Timed out waiting for discard response")
            
        if not res or "cards" not in res or len(res["cards"]) != 2:
            raise IllegalMoveError(self.player_id, f"Invalid remote discard response: {res}")
            
        c1_str, c2_str = res["cards"][0], res["cards"][1]
        
        # Find matching cards in hand
        c1 = next((c for c in hand if str(c) == c1_str), None)
        c2 = next((c for c in hand if str(c) == c2_str), None)
        
        if not c1 or not c2:
            raise IllegalMoveError(self.player_id, "Tried to discard cards not in hand")
            
        return c1, c2

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        req = {
            "action": "peg",
            "hand": [str(c) for c in hand],
            "peg_history": [str(c) for c in peg_history],
            "current_count": current_count
        }
        self.request_queue.put(req)
        
        try:
            res = self.response_queue.get(timeout=self.timeout)
        except Empty:
            raise TimeoutError(self.player_id, "Timed out waiting for peg response")
            
        if not res or "card" not in res:
            raise IllegalMoveError(self.player_id, f"Invalid remote peg response: {res}")
            
        card_str = res.get("card")
        if card_str is None:
            return None # "Go"
            
        c = next((card for card in hand if str(card) == card_str), None)
        if not c:
            raise IllegalMoveError(self.player_id, "Tried to play card not in hand")
            
        return c
