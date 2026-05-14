# Cribbage Tournament Engine - Developer Protocol

Welcome! This document outlines how to write a bot for the Cribbage Tournament Engine and connect it remotely using WebSockets.

## 1. Connecting to the Engine

Your bot must connect to the tournament server via WebSockets.
**Endpoint:** `ws://<server-ip>:8000/ws/bot/<your_bot_id>`

Replace `<your_bot_id>` with a unique string identifier for your bot.

## 2. Game Rules & Engine Mechanics

The Engine acts as the strict referee. It perfectly tracks points for 15s, pairs, runs, flushes, and "nobs". You do not need to implement the "Muggins" rule; the engine will automatically award you all points your cards deserve.

**IMPORTANT:** If your bot attempts to play a card it does not have, or plays a card that brings the pegging count over 31, **your bot will immediately forfeit the game.**

## 3. Communication Protocol

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

## 4. Card Format
Cards are represented as strings: `"{Rank}{Suit}"`.
- **Ranks**: `A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K`
- **Suits**: `H, D, C, S` (Hearts, Diamonds, Clubs, Spades)

Example: `"10H"` (Ten of Hearts), `"AS"` (Ace of Spades).

Good luck, and may the best bot win!
