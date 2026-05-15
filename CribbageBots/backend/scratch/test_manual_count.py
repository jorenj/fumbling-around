import threading
import time
from cribbage.engine import GameEngine
from cribbage.bots.random_bot import RandomBot
from cribbage.models import Card, Rank, Suit

def test_manual_count_sync():
    p1 = RandomBot("P1")
    p2 = RandomBot("P2")
    
    events = []
    def on_event(e):
        events.append(e)
        
    engine = GameEngine(p1, p2, on_event=on_event, manual_count=True)
    
    # Run engine in a thread
    def run():
        engine.play_game()
        
    t = threading.Thread(target=run)
    t.start()
    
    # Wait for counting phase to be reached
    # We'll poll the events for 'count_hand_request'
    found = False
    for _ in range(50):
        if any(e['type'] == 'count_hand_request' for e in events):
            found = True
            print("Found count_hand_request!")
            break
        time.sleep(0.1)
        
    assert found, "Engine did not hit counting phase"
    
    # Verify engine is paused (no new events for a bit)
    count_before = len(events)
    time.sleep(0.5)
    assert len(events) == count_before, "Engine did not pause during counting phase"
    
    # Signal resume
    print("Signaling resume...")
    engine.count_resume_event.set()
    
    # Wait for it to finish or hit next request
    time.sleep(0.5)
    assert len(events) > count_before, "Engine did not resume after signal"
    
    # Cleanup
    # We won't wait for full game but we'll signal again if needed
    while t.is_alive():
        engine.count_resume_event.set()
        time.sleep(0.1)
        
    print("Test Passed!")

if __name__ == "__main__":
    # We need to add src to path
    import sys
    import os
    sys.path.append(os.path.join(os.getcwd(), "src"))
    test_manual_count_sync()
