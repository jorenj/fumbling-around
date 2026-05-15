import asyncio
import json
import logging
import argparse
from typing import List, Tuple, Optional
from itertools import combinations

try:
    # Try relative imports for package usage
    from ..bot import CribbagePlayer
    from ..models import Card, Rank, Suit
    from ..rules import score_hand, score_pegging, get_legal_pegging_moves
except (ImportError, ValueError):
    # Fallback to absolute imports for standalone script execution
    from cribbage.bot import CribbagePlayer
    from cribbage.models import Card, Rank, Suit
    from cribbage.rules import score_hand, score_pegging, get_legal_pegging_moves

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("FlashBot")

def parse_card(card_str: str) -> Card:
    """Parses a string like '10H' or 'AS' into a Card object."""
    if card_str.startswith("10"):
        rank_str = "10"
        suit_str = card_str[2:]
    else:
        rank_str = card_str[0]
        suit_str = card_str[1:]
    
    return Card(rank=Rank(rank_str), suit=Suit(suit_str))

def _estimate_crib_ev(discard: List[Card]) -> float:
    """
    Heuristic to estimate the average points two cards contribute to a crib.
    Uses an improved valuation model based on common cribbage statistics.
    """
    score = 0.0
    r1, r2 = sorted([c.numeric_rank for c in discard])
    v1, v2 = sorted([c.value for c in discard])
    
    # 1. Pairs
    if r1 == r2:
        if r1 == 5: score += 6.5 # 5-5 is the best discard (avg ~8-9 pts)
        elif r1 in [2, 3, 7, 8]: score += 4.0 # Very flexible pairs
        elif r1 in [1, 4, 6, 9]: score += 3.0
        else: score += 2.5 # Face card pairs
    
    # 2. 15s
    if v1 + v2 == 15:
        score += 2.0
        if r1 in [7, 8]: score += 0.5 # 7-8 is slightly better than 10-5
        
    # 3. Runs / Consecutive
    if r2 == r1 + 1:
        if r1 in [4, 5, 6, 7]: score += 3.5 # Middle runs are powerful
        else: score += 2.0
    elif r2 == r1 + 2:
        score += 1.2 # Gapped run potential
        
    # 4. 5s bonus (extremely flexible for 15s)
    if v1 == 5 or v2 == 5:
        if not (v1 == 5 and v2 == 5): # Already handled by pairs
            score += 2.0
            
    # 5. Suit potential (Flush)
    if discard[0].suit == discard[1].suit:
        score += 0.5
        
    # 6. Jacks (Nobs)
    for c in discard:
        if c.rank == Rank.JACK:
            score += 0.4
            
    # 7. Low card safety (Low cards in crib often help dealer more than high cards)
    if v2 <= 5: score += 0.5
    if v1 >= 10 and v2 >= 10: score -= 0.5 # 10-10, 10-J etc are "safe" to throw to opponent
        
    return score

class GeminiFlashSimpleBot(CribbagePlayer):
    """
    A high-performance Cribbage bot that uses exact Hand EV calculations 
    and heuristic-based crib/pegging strategy.
    """
    
    def discard(self, hand: List[Card], is_dealer: bool) -> Tuple[Card, Card]:
        """
        Choose the best 2 cards to discard by calculating the exact EV of the hand
        across all possible cut cards, plus a crib value estimate.
        """
        all_cards = [Card(r, s) for r in Rank for s in Suit]
        remaining_deck = [c for c in all_cards if c not in hand]
        
        best_total_ev = -100.0
        best_discard = None

        # There are 15 ways to choose 4 cards to keep from 6
        for keep in combinations(hand, 4):
            keep_list = list(keep)
            discarded = [c for c in hand if c not in keep_list]
            
            # 1. Exact Hand EV (Score the 4-card keep against all 46 possible cuts)
            hand_total_score = 0
            for cut in remaining_deck:
                score, _ = score_hand(keep_list, cut, is_crib=False)
                hand_total_score += score
            hand_ev = hand_total_score / len(remaining_deck)
            
            # 2. Crib EV Heuristic
            crib_ev = _estimate_crib_ev(discarded)
            
            # 3. Total EV
            # If we are the dealer, the crib points are ours (+).
            # If we are not, they are the opponent's (-).
            total_ev = hand_ev + (crib_ev if is_dealer else -crib_ev)
            
            if total_ev > best_total_ev:
                best_total_ev = total_ev
                best_discard = tuple(discarded)
                
        return best_discard

    def peg(self, hand: List[Card], peg_history: List[Card], current_count: int) -> Optional[Card]:
        """
        Pegging strategy: Prioritize immediate points and use defensive lookahead 
        to avoid giving the opponent easy counter-scores.
        """
        legal_moves = get_legal_pegging_moves(hand, current_count)
        if not legal_moves:
            return None

        best_move = None
        best_score = -100.0

        for card in legal_moves:
            # 1. Immediate points
            pts, _ = score_pegging(peg_history + [card])
            move_score = float(pts)
            
            new_count = current_count + card.value
            
            # 2. Defensive Heuristics (Avoid setting up the opponent)
            opponent_risk = 0.0
            
            # 15 and 31 risk
            if new_count == 5 or new_count == 21:
                opponent_risk += 1.5 # Very dangerous (opponent likely has 10/face)
            elif new_count < 15 and new_count > 10:
                opponent_risk += 0.5 # Risk of 15
            elif new_count > 25:
                opponent_risk += 0.3 # Risk of 31
                
            # Pair risk and Baiting
            # If I have a pair of this card in my hand, I WANT the opponent to pair it
            # so I can play my second one for a Triple (6 pts).
            same_rank_in_hand = [c for c in hand if c.rank == card.rank and c != card]
            if same_rank_in_hand:
                move_score += 0.8 # Encourage "baiting" with pairs
            else:
                # If I don't have another, being paired just gives opponent 2 pts.
                # We assume a baseline risk that opponent might have any rank.
                pass 
                
            # Run risk
            # If playing this card creates a 2-card sequence, opponent might complete the run.
            if len(peg_history) >= 1:
                r1 = peg_history[-1].numeric_rank
                r2 = card.numeric_rank
                if abs(r1 - r2) == 1:
                    opponent_risk += 1.0 # High risk of opponent completing a run
            
            move_score -= opponent_risk
            
            # 3. Leading Strategy
            if not peg_history:
                if card.value == 4:
                    move_score += 0.6 # 4 is the safest lead
                elif card.value == 10 or card.value == 5:
                    move_score -= 1.0 # Bad leads
            
            # 4. Tie-breaker: prefer lower value cards to stay flexible
            move_score -= (card.value / 100.0)

            if move_score > best_score:
                best_score = move_score
                best_move = card

        return best_move

async def run_remote_bot(bot_id: str, server_url: str):
    """Bridge between the WebSocket protocol and the GeminiFlashSimpleBot logic."""
    import websockets
    
    bot = GeminiFlashSimpleBot(bot_id)
    url = f"{server_url}/ws/bot/{bot_id}"
    
    logger.info(f"Connecting to {url}...")
    async with websockets.connect(url) as ws:
        logger.info(f"Connected as {bot_id}")
        
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                action = data.get("action")
                
                if action == "discard":
                    hand = [parse_card(c) for c in data["hand"]]
                    is_dealer = data["is_dealer"]
                    logger.info(f"Discarding from hand: {data['hand']} (is_dealer={is_dealer})")
                    
                    # Logic
                    discarded = bot.discard(hand, is_dealer)
                    
                    # Response
                    await ws.send(json.dumps({
                        "cards": [str(c) for c in discarded]
                    }))
                    logger.info(f"Discarded: {[str(c) for c in discarded]}")
                    
                elif action == "peg":
                    hand = [parse_card(c) for c in data["hand"]]
                    history = [parse_card(c) for c in data["peg_history"]]
                    count = data["current_count"]
                    logger.info(f"Pegging: hand={data['hand']}, count={count}")
                    
                    # Logic
                    card = bot.peg(hand, history, count)
                    
                    # Response
                    await ws.send(json.dumps({
                        "card": str(card) if card else None
                    }))
                    logger.info(f"Played: {str(card) if card else 'Go'}")
                    
                elif action == "game_over":
                    winner = data.get("winner")
                    logger.info(f"Game Over! Winner: {winner}")
                    # Don't break, wait for next game if tournament
                    
            except websockets.ConnectionClosed:
                logger.info("Connection closed.")
                break
            except Exception as e:
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                break

async def self_test():
    """Verifies bot logic locally without a server."""
    logger.info("Running self-test...")
    bot = GeminiFlashSimpleBot("TestBot")
    
    # Test hand
    hand = [
        Card(Rank.FIVE, Suit.HEARTS),
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.TEN, Suit.CLUBS),
        Card(Rank.JACK, Suit.DIAMONDS),
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.THREE, Suit.SPADES)
    ]
    
    logger.info(f"Testing discard with hand: {[str(c) for c in hand]}")
    discarded = bot.discard(hand, is_dealer=True)
    logger.info(f"Discarded (Dealer): {[str(c) for c in discarded]}")
    
    discarded_nd = bot.discard(hand, is_dealer=False)
    logger.info(f"Discarded (Non-Dealer): {[str(c) for c in discarded_nd]}")
    
    # Test pegging
    history = [Card(Rank.TEN, Suit.HEARTS)]
    logger.info(f"Testing pegging with history: {[str(c) for c in history]}, count=10")
    peg_hand = [Card(Rank.FIVE, Suit.CLUBS), Card(Rank.ACE, Suit.SPADES)]
    move = bot.peg(peg_hand, history, 10)
    logger.info(f"Pegged: {str(move)}")
    
    logger.info("Self-test complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GeminiFlashSimpleBot as a remote client.")
    parser.add_argument("--bot-id", type=str, default="FlashBot", help="Unique ID for this bot instance.")
    parser.add_argument("--server", type=str, default="ws://localhost:8000", help="Engine server WebSocket URL.")
    parser.add_argument("--test", action="store_true", help="Run local self-test and exit.")
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(self_test())
    else:
        try:
            asyncio.run(run_remote_bot(args.bot_id, args.server))
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
