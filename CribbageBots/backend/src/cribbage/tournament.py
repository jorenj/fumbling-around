from typing import Type
from .engine import GameEngine
from .bot import CribbagePlayer

def run_tournament(p1_class: Type[CribbagePlayer], p2_class: Type[CribbagePlayer], num_games: int = 10, verbose: bool = False, p1_id: str = "Player 1", p2_id: str = "Player 2", enforce_time_limit: bool = True):
    p1 = p1_class(p1_id)
    p2 = p2_class(p2_id)

    stats = {
        p1_id: {"wins": 0, "skunks": 0, "total_pts": 0, "forfeits": 0},
        p2_id: {"wins": 0, "skunks": 0, "total_pts": 0, "forfeits": 0}
    }

    p1_deals_first = True

    for i in range(num_games):
        if verbose:
            print(f"\n{'='*20} GAME {i+1} {'='*20}")

        # Alternate dealers
        if p1_deals_first:
            engine = GameEngine(p1, p2, enforce_time_limit=enforce_time_limit)
        else:
            engine = GameEngine(p2, p1, enforce_time_limit=enforce_time_limit)
            
        winner, log = engine.play_game()
        
        # Update stats
        stats[winner]["wins"] += 1
        if engine.skunk:
            stats[winner]["skunks"] += 1

        if engine.end_reason.startswith("Forfeit:"):
            loser = p1_id if winner == p2_id else p2_id
            stats[loser]["forfeits"] += 1

        for pid in [p1_id, p2_id]:
            stats[pid]["total_pts"] += engine.state.scores.get(pid, 0)
            
        if verbose:
            for event in log:
                print(f"[{event['type'].upper()}] {event['player_id'] or ''} - {event['message']}")
            print(f"Game {i+1} Winner: {winner} (Skunk: {engine.skunk})")
            print(f"Final Score: P1 {engine.state.scores.get(p1_id, 0)} - P2 {engine.state.scores.get(p2_id, 0)}")
            
        p1_deals_first = not p1_deals_first

    # Print Summary
    print("\n" + "="*40)
    print(f"TOURNAMENT SUMMARY ({num_games} Games)")
    print("="*40)
    for pid in [p1_id, p2_id]:
        avg_pts = stats[pid]["total_pts"] / num_games
        forfeits = stats[pid]["forfeits"]
        forfeit_str = f", {forfeits} Forfeits" if forfeits else ""
        print(f"{pid}: {stats[pid]['wins']} Wins, {stats[pid]['skunks']} Skunks{forfeit_str} (Avg Pts: {avg_pts:.1f})")

if __name__ == "__main__":
    from .bots.random_bot import RandomBot
    from .bots.greedy_bot import GreedyBot
    run_tournament(RandomBot, GreedyBot, num_games=10, verbose=False)
