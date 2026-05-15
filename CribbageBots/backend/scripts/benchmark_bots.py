import time
import sys
import os

# Add the src directory to the path so we can import cribbage
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from cribbage.models import Card, Rank, Suit
from cribbage.engine import GameEngine
from cribbage.bots.random_bot import RandomBot
from cribbage.bots.greedy_bot import GreedyBot
from cribbage.bots.gemini_flash_simple_bot import GeminiFlashSimpleBot

def benchmark(bot_class, name, num_games=50):
    print(f"Benchmarking {name} over {num_games} games...")
    start = time.time()
    for i in range(num_games):
        p1 = bot_class("P1")
        p2 = bot_class("P2")
        # Alternate dealer
        if i % 2 == 0:
            engine = GameEngine(p1, p2, verbose=False)
        else:
            engine = GameEngine(p2, p1, verbose=False)
        engine.play_game()
    end = time.time()
    total_time = end - start
    avg_time = total_time / num_games
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average time per game: {avg_time:.4f}s")
    return avg_time

if __name__ == "__main__":
    print("Starting Cribbage Bot Benchmark\n" + "="*30)
    
    results = {}
    results['RandomBot'] = benchmark(RandomBot, "RandomBot", 100)
    results['GreedyBot'] = benchmark(GreedyBot, "GreedyBot", 100)
    results['GeminiFlashSimpleBot'] = benchmark(GeminiFlashSimpleBot, "GeminiFlashSimpleBot", 20) # Fewer games for slow bot
    
    print("\nSummary Results (Avg time per game):")
    for name, avg in results.items():
        print(f"  {name:25}: {avg:.4f}s")
    
    # Calculate slowdown factor
    greedy_avg = results['GreedyBot']
    flash_avg = results['GeminiFlashSimpleBot']
    print(f"\nFlashBot is {flash_avg/greedy_avg:.1f}x slower than GreedyBot")
