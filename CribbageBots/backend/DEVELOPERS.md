# Cribbage Tournament Engine - Developer Protocol

Welcome! This document outlines how to add a bot to the Cribbage Tournament Engine. You can either implement a **Native Bot** directly in Python or connect a **Remote Bot** over WebSockets.

## 1. Adding a Native Bot

Native bots run directly within the engine's process. This is the recommended way to add high-performance AI.

### Implementation
1. Create a new file in `backend/src/cribbage/bots/` (e.g., `my_bot.py`).
2. Inherit from `CribbagePlayer` and implement the `discard` and `peg` methods.
3. Register your bot in `backend/src/cribbage/bots/__init__.py`:

```python
from .my_bot import MyBot

BOT_REGISTRY = {
    # ... existing bots ...
    "mybot": {"class": MyBot, "label": "MyAwesomeBot"},
}
```

Once registered, your bot will automatically appear in the `cribbage run` CLI choices and the web interface dropdowns.

## 2. Connecting a Remote Bot

Your bot must connect to the tournament server via WebSockets.
**Endpoint:** `ws://<server-ip>:8000/ws/bot/<your_bot_id>`

Replace `<your_bot_id>` with a unique string identifier for your bot.

## 3. Game Rules & Engine Mechanics

The Engine acts as the strict referee. It perfectly tracks points for 15s, pairs, runs, flushes, and "nobs". You do not need to implement the "Muggins" rule; the engine will automatically award you all points your cards deserve.

**IMPORTANT:** If your bot attempts to play a card it does not have, or plays a card that brings the pegging count over 31, **your bot will immediately forfeit the game.**

## 4. Communication Protocol (Remote Only)

All messages are sent and received as JSON. The engine will send you a payload asking for a decision, and your bot must reply with its decision.

### Action: Discard
At the beginning of a hand, the engine will ask you to discard 2 cards to the crib.

**Engine sends:**
```json
{
  "action": "discard",
  "hand": ["5H", "10S", "AC", "2D", "JS", "6C"],
  "is_dealer": true
}
```

**Your bot must reply:**
```json
{
  "cards": ["5H", "2D"]
}
```

### Action: Peg
During the pegging phase, the engine will ask you to play a card. 

**Engine sends:**
```json
{
  "action": "peg",
  "hand": ["10S", "AC", "JS", "6C"],
  "peg_history": ["4H", "5C", "10D"],
  "current_count": 19
}
```
*Note: `peg_history` represents the uninterrupted sequence of cards played in the current 31-cycle.*

**Your bot must reply:**
```json
{
  "card": "6C"
}
```

If you have no cards in your hand that keep the `current_count + card.value <= 31`, you must say "Go" by sending:
```json
{
  "card": null
}
```

## 5. Card Format
Cards are represented as strings: `"{Rank}{Suit}"`.
- **Ranks**: `A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K`
- **Suits**: `H, D, C, S` (Hearts, Diamonds, Clubs, Spades)

Example: `"10H"` (Ten of Hearts), `"AS"` (Ace of Spades).

## 6. Testing Your Bot

You can test your bot's logic without the web UI using the `cribbage` CLI.

1. **Install the engine locally:**
   ```bash
   cd backend
   pip install -e .
   ```

2. **Run a tournament in the terminal:**
   ```bash
   # Run 100 games between GreedyBot and RandomBot with detailed logs
   cribbage run --p1 greedy --p2 random --games 100 --verbose
   ```

Good luck, and may the best bot win!

## 7. Deployment Limitations

If you intend to deploy the engine publicly, be aware of the following development-oriented configurations:
- **CORS Policy**: The API is currently configured with an open CORS policy (`allow_origins=["*"]`). In a production environment, this should be restricted to your frontend origin.
- **Single Worker Limitation**: The WebSocket connection tracking (`active_bots`) uses an in-memory Python dictionary. If deploying with multiple Uvicorn workers (e.g. `uvicorn --workers 4`), bots connected to one worker will not be visible to requests processed by another worker. For multi-worker deployments, `active_bots` must be replaced with a distributed store like Redis.
