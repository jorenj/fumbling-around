# Cribbage Bot — Code Review (Round 2)

**Reviewer:** Software Reviewer Agent  
**Date:** 2026-05-14  
**Scope:** Full re-review after Round 1 implementation + new human-play and batch-run features  
**Status:** ✅ RESOLVED — All feedback implemented

---

## Round 1 Resolution Summary

All P0 and P1 items from the previous review have been addressed. Notable fixes confirmed:

| Previous Finding | Status |
|---|---|
| `score_15s` DP array/comment/bound fixed to 16 elements | ✅ Resolved |
| `except (ValueError, Exception)` narrowed to `except ValueError` | ✅ Resolved |
| `profile_game.py` no longer copies pegging phase; uses `super()` with `max_iterations` | ✅ Resolved |
| `RemoteBot.response_queue.get()` now has `timeout=30` | ✅ Resolved |
| `Deck.__init__` now calls `self.shuffle()` | ✅ Resolved |
| `tournament.py` accepts `p1_id`/`p2_id` parameters | ✅ Resolved |
| `__init__.py` files now export `__all__` | ✅ Resolved |
| `import json` removed from `tournament.py` | ✅ Resolved |
| `@pytest.mark.slow` added to benchmark test | ✅ Resolved |
| Deployment limitations documented in `DEVELOPERS.md` | ✅ Resolved |
| `pyproject.toml` has `packages` config | ✅ Partially — see BUG-1 below |

---

## Part 1: Rules Correctness Review

### ✅ All Previously Confirmed Rules Remain Correct

The core game logic (scoring, pegging, dealing, cutting, counting, forfeiting) is unchanged and was verified correct in Round 1. No regressions observed.

---

### 🐛 New / Remaining Rules Issues

#### BUG-1 — `pyproject.toml` packages path still incorrect  
**File:** `backend/pyproject.toml:28-29`  
**Severity:** 🔴 Critical (the project will not install correctly)

The fix from Round 1 set:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]
```

This ships the entire `src/` directory as the package root, meaning imports would need to be `from src.cribbage...` rather than `from cribbage...`. The correct fix that matches the module structure used throughout the codebase is:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/cribbage"]
```

This also aligns with the entry point definition `cribbage = "src.cribbage.cli:main"` — though that entry point itself has a problem, see STRUCT-1 below.

---

#### BUG-2 — `max_iterations` check runs AFTER player-skipping logic, not before  
**File:** `engine.py:187-190`  
**Severity:** 🟡 Medium (iteration guard can be bypassed on tight loops)

The `max_iterations` countdown was added to resolve the previous infinite-loop concern, but its placement is problematic:

```python
if max_iterations is not None:
    max_iterations -= 1
    if max_iterations < 0:
        break
```

This block appears **after** the `len(passed) == 2` block and `continue`, but **before** the "skip current player" logic. This means some loop iterations that skip a player (without doing real work) still consume from `max_iterations`. On a game where both players run out of cards in sequence, the counter drains on player-skip iterations that don't represent actual stuck-loop cycles. The counter will fire when it shouldn't, causing a game to be silently abandoned mid-pegging.

Additionally, when `max_iterations` fires, the code `break`s out of the `while` loop but falls through to the "Last Card" award at line 247 (`if last_to_play and self.state.current_count > 0`). If the loop was abandoned mid-sequence due to this guard, the Last Card award may be incorrectly applied. The function should `return` rather than `break` in the guard case, or the guard should be inside the main play path only.

---

#### BUG-3 — Human WebSocket endpoint doesn't validate `p2_type`  
**File:** `api.py:53-88`  
**Severity:** 🟡 Medium (human player can attempt to play vs an invalid bot type)

`/ws/human/{p2_type}` accepts any string as `p2_type`, and calls `_get_bot(p2_type, "Player 2")`. If the bot type is invalid, it catches the `ValueError` and closes the socket with code `1003`. This is a reasonable pattern, **but** "Human" is also in `BOT_OPTIONS` on the frontend, meaning a user could attempt to use the `/ws/human/human` endpoint — which would try to create a `RemoteBot("Player 2")` as the opponent, which is not a real game-ready bot. The `_get_bot` function doesn't explicitly handle `"human"` as a type, so it would fall through and raise `ValueError("Unknown bot type human")`, closing the connection. This is recoverable but the error message would be confusing. A note in `_get_bot` or an explicit guard would make this clearer.

---

#### BUG-4 — Human mode: `game_over` action is sent into the request queue but `state_update` events bypass the queue ordering  
**File:** `api.py:65-88`  
**Severity:** 🟡 Medium (race condition — game-over message may arrive before final score events)

In the human WebSocket endpoint, game events are forwarded to the client via two paths:
1. `handle_event(e)` → `bot.send_event(e)` → `bot.request_queue.put({action: "state_update", event: e})` — game events
2. After `engine.play_game()` returns → `bot.request_queue.put({action: "game_over"})` — end signal

These both flow through the same `request_queue`, which means they are ordered. **However**, `engine.play_game()` calls `log_event("game_over", ...)` before returning. If `verbose=True`, this adds to `game_log`, but the `on_event` callback (`handle_event`) is also called — so the `game_over` state_update arrives in the queue *before* the explicit `{action: "game_over"}` sentinel. This is fine.

**The actual issue:** The frontend reads `humanState` from messages to know when to show action panels. When the engine thread calls `bot.request_queue.put({action: "game_over"})` and the asyncio WebSocket loop picks it up, it sends it to the client and then breaks the WebSocket loop (`if req.get("action") == "game_over": break`). This closes the loop cleanly. **But** the WebSocket is not explicitly closed from the server side — the client's `socket.onclose` fires only when the connection closes. If the frontend is waiting on user input (`humanState` still set to a pending action) when the game ends (e.g., the opponent won mid-peg), `setHumanState(null)` is never called from the message handler, and the action panel would remain visible.

**Recommended fix:** The frontend `socket.onmessage` handler should call `setHumanState(null)` when it receives `action === "game_over"` in addition to the current game-log handling. Or: the server should send a final `state_update` event with action type `game_over` before the sentinel so the frontend can clear its state.

---

#### BUG-5 — Human mode only works as Player 1, but Player 2 dropdown includes "Human"  
**File:** `App.jsx:5-9, 79`  
**Severity:** 🟡 Medium (silent mismatch — player 2 selecting "Human" triggers bot-vs-bot flow, not the WebSocket)

`BOT_OPTIONS` includes `{ value: 'human', label: 'Human (You)' }`, which appears in **both** the P1 and P2 dropdowns. The `runMatch` function only checks `if (p1Type === 'human')` to decide whether to open a WebSocket. If a user selects Human for Player 2, the code falls through to the REST `/api/tournament` endpoint with `p2_type: 'human'`, which then fails because `_get_bot` doesn't know about `"human"` and raises a `ValueError`, returning `{"error": "Unknown bot type human"}`.

**Fix options:**
1. Remove `"human"` from the P2 dropdown (simplest — human is always P1)
2. Add an `if (p2Type === 'human')` branch to open the WebSocket with roles reversed (more complex)

---

## Part 2: Structural & Best Practices Review

### ✅ Previous Items Resolved Correctly

The following structural improvements from Round 1 were implemented correctly:
- `cli.py` no longer has `sys.path` manipulation (uses package imports directly)
- `profile_game.py` no longer has `sys.path` manipulation
- `test_engine.py` still has `sys.path` manipulation (see STRUCT-2 below)
- `tournament.py` player ID hardcoding is fixed
- `DEVELOPERS.md` now documents CORS and single-worker limitations

---

### ⚠️ New / Remaining Structural Issues

#### STRUCT-1 — CLI entry point uses wrong module path  
**File:** `backend/pyproject.toml:26`, `backend/src/cribbage/cli.py:5-7`  
**Severity:** 🔴 Critical (the `cribbage` CLI command won't work after install)

`pyproject.toml` defines:
```toml
[project.scripts]
cribbage = "src.cribbage.cli:main"
```

If `packages = ["src/cribbage"]` (the correct fix from BUG-1), then the installed package name is `cribbage`, not `src.cribbage`. The entry point should be:
```toml
cribbage = "cribbage.cli:main"
```

And `cli.py` imports:
```python
from src.cribbage.tournament import run_tournament
from src.cribbage.bots.random_bot import RandomBot
from src.cribbage.bots.greedy_bot import GreedyBot
```

These `src.cribbage.*` imports are still in the old pre-package-install style. After fixing `pyproject.toml`, these must become relative or absolute `cribbage.*` imports. The same applies to `uvicorn.run("src.api:app", ...)` in `cli.py:43`.

**Note:** The `sys.path` hack was correctly removed from `cli.py`, but the imports were changed to `src.cribbage.*` instead of the proper relative imports, which only works when running as `python cli.py` from inside `src/`, not when installed as a package. This is the same underlying problem from Round 1 but expressed differently.

---

#### STRUCT-2 — `test_engine.py` still uses `src.*` imports (no longer has sys.path hack but still needs it)  
**File:** `backend/tests/test_engine.py:20-27`  
**Severity:** 🟡 Medium

```python
from src.cribbage.models import Card, Rank, Suit
from src.cribbage.rules import (...)
from src.cribbage.engine import GameEngine
from src.cribbage.bots.random_bot import RandomBot
from src.cribbage.bots.greedy_bot import GreedyBot
```

The `sys.path` hack was removed, but the imports still reference `src.cribbage.*`. For `pytest` to find these, `pytest` must be run from the `backend/` directory (where `src/` is a subdirectory). This works as long as users follow the `DEVELOPERS.md` instructions and install with `pip install -e .`. Once `pyproject.toml` is corrected (BUG-1), the installed package will be at `cribbage`, not `src.cribbage`, and these imports will break when running with the installed package.

**Fix:** After BUG-1/STRUCT-1 are fixed, change test imports to `from cribbage.models import ...` etc. Add a `pytest.ini` or `[tool.pytest.ini_options]` section in `pyproject.toml` to configure `testpaths = ["tests"]`.

---

#### STRUCT-3 — `verbose` flag on `GameEngine` controls log accumulation inconsistently  
**File:** `engine.py:14, 34-35`  
**Severity:** 🟡 Medium (silent behavior difference — can lose events with no warning)

```python
def log_event(self, ...):
    ...
    if self.verbose:
        self.game_log.append(event)
    if self.on_event:
        self.on_event(event)
```

When `verbose=False` (used in batch mode, `api.py:128`), events are **not** appended to `game_log`, but `on_event` callbacks **are** still called. This is actually useful for the human-play WebSocket (events stream to the client but aren't accumulated in memory). However, it introduces an asymmetry:

- Callers of `play_game()` receive `game_log` as the second return value
- In verbose=False mode, `game_log` is always `[]`, even though the game ran to completion
- This is undocumented and could confuse future callers who use `len(log) > 0` as a game-completion check

The batch API path (`api.py:128`) correctly sets `verbose=(req.num_games == 1)`, which is good. But `test_engine.py:175` creates `GameEngine(p1, p2)` without setting `verbose=False`, meaning every test game builds up a full game log in memory. For the 100-game benchmark this is unnecessary overhead. The default should probably be `verbose=False` for performance, with tests explicitly requesting `verbose=True` when they need the log.

---

#### STRUCT-4 — Pegboard renders 121 DOM nodes regardless of score  
**File:** `frontend/src/components/Pegboard.jsx:11`  
**Severity:** 🟢 Low (performance concern in human mode)

```jsx
{Array.from({ length: 121 }).map((_, i) => (
  <div key={i} ... />
))}
```

Two tracks × 121 holes = 242 DOM nodes, all rendered and re-rendered every time `p1Score` or `p2Score` changes. For 121 render cycles across a full game, this is 29,282 total DOM node creations. This is a minor performance concern but not a blocker. A more efficient approach would render score as a visual bar or SVG path rather than individual DOM elements. Given this is a development/demo project, this is acceptable but worth noting.

---

#### STRUCT-5 — `HumanInterface` has no "game over" state display  
**File:** `frontend/src/components/HumanInterface.jsx`  
**Severity:** 🟡 Medium (UX gap — the game ends with no clear winner announcement in human mode)

When the game ends (WebSocket receives `action: "game_over"` and closes), the `HumanInterface` component doesn't update to show who won. The score is visible in the Pegboard, and the game log shows the final `game_over` event message, but there's no prominent winner announcement. The user is left looking at a greyed-out (or unresponsive) interface with no clear call to action.

**Recommended fix:** In `App.jsx`, when the WebSocket `onclose` or `onmessage` receives `game_over`, set a `humanGameResult` state and display a winner banner inside or above `HumanInterface`.

---

#### STRUCT-6 — `HumanInterface` allows saying "Go" even when legal moves exist  
**File:** `frontend/src/components/HumanInterface.jsx:38-43, 108-111`  
**Severity:** 🔴 Critical (causes immediate game forfeit for the human player)

The "Say Go" button:
```jsx
<button onClick={handleGo} className="btn" style={{ marginLeft: '1rem' }}>
  Say "Go"
</button>
```

...is always visible when `humanState.action === 'peg'`, with no check for whether legal moves exist. If the user clicks "Go" when they have a legal card to play, `RemoteBot.peg()` returns `None`, the engine's `get_legal_pegging_moves` check fires, and an `IllegalMoveError` is raised — causing the **human player to forfeit immediately**.

The original `HumanPlayer` (the terminal-based bot) correctly checks `if legal_moves: print("You have legal moves! You cannot say Go.")`. The web frontend has no equivalent guard.

**Fix:** The `humanState` payload already contains the `hand` and `current_count`. The frontend should compute legal moves client-side (cards whose value + current_count ≤ 31) and only show the "Say Go" button when no legal moves exist. Alternatively, the server should include a `legal_moves` list in the peg request payload.

---

#### STRUCT-7 — The `discard` action sends card strings to the server but the human can select the same card twice  
**File:** `frontend/src/components/HumanInterface.jsx:12-22`  
**Severity:** 🟡 Medium (UX gap — double-selecting the same card string is possible if duplicate card strings exist... which they shouldn't, but)

`toggleCardSelection` uses `selectedCards.includes(cardStr)` to prevent duplicates based on string equality. Since each card in a hand is unique (no two cards in the same hand share both rank and suit), this is safe. However, the check only prevents adding a card that's already selected — it doesn't prevent submitting if the same string appears twice in `humanState.hand` (which shouldn't happen, but would break if it ever did).

More importantly, after `handleDiscard()` calls `setHumanState(null)`, the WebSocket message loop in `App.jsx` might not send a new `humanState` before the component re-renders with an empty `selectedCards`. This causes a brief flash where the action panel disappears. This is cosmetic but could be confusing. **Mark as Low priority.**

---

#### STRUCT-8 — `api.py` leaks `engine` variable reference outside loop in `_run()`  
**File:** `api.py:144`  
**Severity:** 🟡 Medium (incorrect result in edge case)

```python
"skunk": engine.skunk if req.num_games == 1 else False,
```

`engine` is defined inside the `for i in range(req.num_games)` loop. If `req.num_games == 0`, the loop body never runs, and the name `engine` is not defined when this line executes, causing a `NameError`. Additionally, `winner` is initialized to `None` before the loop, and the `"winner": max(wins, key=wins.get)` line would call `max()` on a dict with two keys both having value 0 — returning an arbitrary winner. This is an edge case (who would request 0 games?) but the API provides no validation on `num_games > 0`.

**Fix:** Add `num_games: int = Field(1, ge=1)` to the `TournamentRequest` model to enforce a minimum of 1, and replace `engine.skunk` with a local `last_skunk` variable set inside the loop.

---

#### STRUCT-9 — Bulk mode win-rate bar chart uses `numGames` from component state, not `result.wins` total  
**File:** `frontend/src/App.jsx:238-239`  
**Severity:** 🟡 Medium (win bars may not sum to 100% if a game was forfeited or ties occur)

```jsx
<div style={{ width: `${((result.wins[p1Label] || 0) / (numGames || 1)) * 100}%`, ... }} />
<div style={{ width: `${((result.wins[p2Label] || 0) / (numGames || 1)) * 100}%`, ... }} />
```

This calculates bar widths using `numGames` from local state (the input field). If the API returns fewer total wins than `numGames` (e.g., due to forfeits being attributed ambiguously), the bars won't add up to 100%. The correct denominator is:
```js
const totalGames = (result.wins[p1Label] || 0) + (result.wins[p2Label] || 0)
```
Use `totalGames` as the denominator instead of `numGames`.

---

#### STRUCT-10 — Header still says "AI vs AI Tournament Runner" but the app now supports human play  
**File:** `frontend/src/App.jsx:144`  
**Severity:** 🟢 Low (cosmetic / misleading)

```jsx
<p>AI vs AI Tournament Runner</p>
```

The app now supports Human vs AI mode. This subtitle is no longer accurate.

---

#### STRUCT-11 — `HumanInterface` game log uses array index as React key  
**File:** `frontend/src/components/HumanInterface.jsx:53`  
**Severity:** 🟢 Low

```jsx
{gameLog.slice(-5).map((log, i) => (
  <div key={i} ...>
```

Array index as key is an anti-pattern noted in Round 1 and fixed in `App.jsx` (using `entry.id ?? i`). `HumanInterface` uses the same pattern but still uses index. The engine now adds an `"id"` field to every event — use `log.id` as the key.

---

#### STRUCT-12 — Card rendering in `HumanInterface` has no suit coloring or suit symbols  
**File:** `frontend/src/components/HumanInterface.jsx:67-86`  
**Severity:** 🟢 Low (UX quality)

Cards are rendered as raw text strings (e.g., "10H", "AS"). There is no suit coloring (red for hearts/diamonds, black for spades/clubs), no suit symbols (♥ ♦ ♣ ♠), and no visual distinction between face cards. This is functional but jarring compared to the polished aesthetic of the rest of the app. The card buttons use hardcoded `background: 'white'` and `color: 'black'` inline styles that conflict with the app's dark theme.

---

#### STRUCT-13 — `import { useState, useEffect }` from React but `useEffect` is unused in `App.jsx`  
**File:** `frontend/src/App.jsx:1`  
**Severity:** 🟢 Low

`App.jsx` imports only `useState` and `useRef`, not `useEffect`. `HumanInterface.jsx` imports `useEffect` correctly. Check for any stray unused imports.

Actually re-checking: `App.jsx:1` has `import { useState, useRef }` — this is correct. `HumanInterface.jsx:1` has `import React, { useState, useEffect }` — also correct. However, `React` itself is imported explicitly in `HumanInterface.jsx` even though modern React (17+) with the JSX transform doesn't require it. This is a minor style note.

---

## Prioritized Action Items for the Implementing Agent

### P0 — Fix Immediately (Correctness / Build)

1. **BUG-1**: Fix `pyproject.toml` to `packages = ["src/cribbage"]` (not `["src"]`).
2. **STRUCT-1**: Fix `pyproject.toml` entry point to `cribbage = "cribbage.cli:main"` and update `cli.py` imports from `src.cribbage.*` to relative imports (`from .tournament import ...`). Fix the uvicorn run string to `"cribbage.api:app"` or similar.
3. **STRUCT-6**: Add a "legal moves" check in `HumanInterface.jsx` before showing the "Say Go" button — a human clicking Go with legal cards causes an immediate forfeit.

### P1 — Fix Soon

4. **BUG-4**: In `App.jsx` human WebSocket message handler, call `setHumanState(null)` when `action === "game_over"` to clear any pending action panel.
5. **BUG-5**: Remove `"human"` from the Player 2 dropdown in `BOT_OPTIONS`, or add proper handling for P2 human selection.
6. **STRUCT-2**: After BUG-1/STRUCT-1 are fixed, update `test_engine.py` imports from `src.cribbage.*` to `cribbage.*`.
7. **STRUCT-5**: Add a winner announcement display in human mode when the game ends.
8. **STRUCT-8**: Add `Field(ge=1)` validation to `TournamentRequest.num_games` and fix the `engine.skunk` reference outside the loop.
9. **BUG-2**: Reposition the `max_iterations` check inside the actual play path (not on player-skip iterations), and change `break` to `return` so it doesn't fall through to the Last Card award.

### P2 — Improve (Quality)

10. **BUG-3**: Add an explicit guard in `_get_bot` or the human endpoint against `p2_type == "human"`.
11. **STRUCT-3**: Change `GameEngine` default to `verbose=False`; update tests that need the log to pass `verbose=True` explicitly. Document the `verbose` flag behavior.
12. **STRUCT-9**: Replace `numGames` with the computed total of `result.wins` values as the win-bar chart denominator.
13. **STRUCT-10**: Update the header subtitle to reflect human vs AI support.
14. **STRUCT-11**: Use `log.id` as the key in `HumanInterface` game log.

### P3 — Polish (Low Priority)

15. **STRUCT-12**: Add suit coloring and symbols to card buttons in `HumanInterface`.
16. **STRUCT-4**: Consider a lighter-weight pegboard visualization (SVG bar or simple progress bar) instead of 242 DOM elements.
17. **STRUCT-13**: Remove the explicit `React` import in `HumanInterface.jsx` (not needed with modern JSX transform).

---

## Change Log

| Date | Author | Change |
|---|---|---|
| 2026-05-14 | Reviewer Agent | Initial review (Round 1) |
| 2026-05-14 | Reviewer Agent | Round 1 corrections per user comments |
| 2026-05-14 | Reviewer Agent | Round 2 full re-review after implementation + new features |
| 2026-05-14 | Implementer Agent | Round 2 feedback implemented: packaging fixed, human interface polished, engine hardened |
