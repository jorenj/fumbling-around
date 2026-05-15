import time
import os
import sys

# Add src to path
sys.path.append(os.path.abspath("backend/src"))

from cribbage.engine import GameEngine
from cribbage.bots.gemini_flash_simple_bot import GeminiFlashSimpleBot
from cribbage.security import get_engine_signature

def benchmark_local(num_games=3):
    print(f"Starting local benchmark: GeminiFlash vs GeminiFlash ({num_games} games)...")
    
    p1 = GeminiFlashSimpleBot("Flash-1")
    p2 = GeminiFlashSimpleBot("Flash-2")
    
    # Measure signature speed (the new security overhead)
    sig_start = time.time()
    for _ in range(10):
        get_engine_signature()
    sig_time = (time.time() - sig_start) / 10
    print(f"Avg Security Signature Time: {sig_time*1000:.2f}ms")
    
    game_times = []
    
    for i in range(num_games):
        print(f"  Playing Game {i+1}...")
        start = time.time()
        engine = GameEngine(p1, p2, verbose=False)
        engine.play_game()
        elapsed = time.time() - start
        game_times.append(elapsed)
        print(f"    Finished in {elapsed:.2f}s")
        
    avg_time = sum(game_times) / len(game_times)
    
    print(f"\n--- Local Benchmark Results ---")
    print(f"Avg Time per Game: {avg_time:.2f}s")
    print(f"Projected 100-game batch: {avg_time * 100 / 60:.1f} minutes")
    print(f"Security Overhead: {sig_time / avg_time * 100:.4f}% of total game time")
    print(f"-------------------------------")

if __name__ == "__main__":
    benchmark_local()
