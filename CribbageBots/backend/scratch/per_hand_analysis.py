import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from cribbage.engine import GameEngine
from cribbage.bots.gemini_flash_simple_bot import GeminiFlashSimpleBot
from cribbage.bots.scaredy_bot import ScaredyBot

def get_pegging_pts(log, player_id):
    return sum(ev["data"].get("points", 0) for ev in log 
               if ev["type"] == "score" and ev["player_id"] == player_id 
               and ("Pegging" in ev["data"].get("reason", "") or "Go" in ev["data"].get("reason", "") or "Last Card" in ev["data"].get("reason", "")))

def count_hands(log):
    # Each round has exactly one 'deal' event
    return sum(1 for ev in log if ev["type"] == "deal")

def run_per_hand_analysis(p1_class, p2_class, num_games=100):
    p1 = p1_class("P1")
    p2 = p2_class("P2")
    
    total_p1_pts = 0
    total_p2_pts = 0
    total_hands = 0
    
    for i in range(num_games):
        if i % 2 == 0:
            engine = GameEngine(p1, p2, verbose=True)
            _, log = engine.play_game()
            total_p1_pts += get_pegging_pts(log, "P1")
            total_p2_pts += get_pegging_pts(log, "P2")
        else:
            engine = GameEngine(p2, p1, verbose=True)
            _, log = engine.play_game()
            total_p1_pts += get_pegging_pts(log, "P1")
            total_p2_pts += get_pegging_pts(log, "P2")
        
        total_hands += count_hands(log)
            
    return total_p1_pts / total_hands, total_p2_pts / total_hands, total_hands / num_games

def main():
    num_games = 100
    print(f"Running Per-Hand Comparison ({num_games} games each)...")
    
    # 1. ScaredyBot vs GeminiFlash
    print("Testing ScaredyBot vs GeminiFlash...")
    sc_pts_per_hand, gf_vs_sc_pts_per_hand, avg_hands_sc = run_per_hand_analysis(ScaredyBot, GeminiFlashSimpleBot, num_games)
    
    # 2. GeminiFlash vs GeminiFlash
    print("Testing GeminiFlash vs GeminiFlash...")
    gf_self_p1_per_hand, gf_self_p2_per_hand, avg_hands_self = run_per_hand_analysis(GeminiFlashSimpleBot, GeminiFlashSimpleBot, num_games)
    gf_self_avg_per_hand = (gf_self_p1_per_hand + gf_self_p2_per_hand) / 2
    
    print(f"\n{'='*60}")
    print(f"PER-HAND PEGGING COMPARISON")
    print(f"{'='*60}")
    print(f"Avg Hands/Game (Self):    {avg_hands_self:.2f}")
    print(f"Avg Hands/Game (Scaredy): {avg_hands_sc:.2f}")
    print(f"\nGeminiFlash vs Self (Per Hand):    {gf_self_avg_per_hand:.3f} pts")
    print(f"GeminiFlash vs Scaredy (Per Hand):  {gf_vs_sc_pts_per_hand:.3f} pts")
    
    reduction = (gf_self_avg_per_hand - gf_vs_sc_pts_per_hand) / gf_self_avg_per_hand * 100
    
    print(f"\nDefensive Effectiveness: {reduction:.1f}% reduction in opponent pegging per hand.")
    print(f"ScaredyBot's own avg pegging per hand: {sc_pts_per_hand:.3f} pts")

if __name__ == "__main__":
    main()
