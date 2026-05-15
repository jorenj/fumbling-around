import time
import sys
import os

# Add the src directory to the path so we can import cribbage
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from cribbage.engine import GameEngine
from cribbage.bots.greedy_bot import GreedyBot
from cribbage.bots.gemini_flash_simple_bot import GeminiFlashSimpleBot

def head_to_head(bot1_class, bot2_class, name1, name2, num_games=100):
    print(f"Benchmarking {name1} vs {name2} over {num_games} games...")
    wins1 = 0
    wins2 = 0
    start = time.time()
    for i in range(num_games):
        p1 = bot1_class(name1)
        p2 = bot2_class(name2)
        # Alternate dealer
        if i % 2 == 0:
            engine = GameEngine(p1, p2, verbose=False)
            winner, _ = engine.play_game()
        else:
            engine = GameEngine(p2, p1, verbose=False)
            winner, _ = engine.play_game()
            
        if winner == name1:
            wins1 += 1
        else:
            wins2 += 1
            
    end = time.time()
    total_time = end - start
    print(f"  {name1} wins: {wins1} ({wins1/num_games*100:.1f}%)")
    print(f"  {name2} wins: {wins2} ({wins2/num_games*100:.1f}%)")
    print(f"  Total time: {total_time:.2f}s")
    return wins1 / num_games

if __name__ == "__main__":
    print("Cribbage Head-to-Head Benchmark\n" + "="*30)
    head_to_head(GeminiFlashSimpleBot, GreedyBot, "FlashBot", "GreedyBot", 200)
