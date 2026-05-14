import json
from queue import Queue
from typing import List, Tuple, Optional
from ..bot import CribbagePlayer
from ..models import Card
from ..rules import get_legal_pegging_moves

class RemoteBot(CribbagePlayer):
    def __init__(self, player_id: str):
        super().__init__(player_id)
        # Queue for sending requests TO the websocket
        self.request_queue = Queue()
        # Queue for receiving responses FROM the websocket
        self.response_queue = Queue()
        
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        req = {
            "action": "discard",
            "hand": [str(c) for c in hand],
            "is_dealer": is_dealer
        }
        self.request_queue.put(req)
        
        # Block until websocket provides a response
        res = self.response_queue.get()
        if not res or "cards" not in res or len(res["cards"]) != 2:
            # If the remote bot disconnects or returns garbage, we just throw an exception 
            # which will cause them to forfeit
            raise ValueError(f"Invalid remote response: {res}")
            
        c1_str, c2_str = res["cards"][0], res["cards"][1]
        
        # Find matching cards in hand
        c1 = next((c for c in hand if str(c) == c1_str), None)
        c2 = next((c for c in hand if str(c) == c2_str), None)
        
        if not c1 or not c2:
            raise ValueError("Remote bot tried to discard cards not in hand")
            
        return c1, c2

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        req = {
            "action": "peg",
            "hand": [str(c) for c in hand],
            "peg_history": [str(c) for c in peg_history],
            "current_count": current_count
        }
        self.request_queue.put(req)
        
        res = self.response_queue.get()
        if not res or "card" not in res:
            raise ValueError(f"Invalid remote response: {res}")
            
        card_str = res.get("card")
        if card_str is None:
            return None # "Go"
            
        c = next((card for card in hand if str(card) == card_str), None)
        if not c:
            raise ValueError("Remote bot tried to play card not in hand")
            
        return c
