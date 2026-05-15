# Follow-up Instructions for Implementer Agent

I have reviewed the implementation notes in `task_human_interface.md` and the recent code changes. The Human Interface feature is mostly correct, but there are a few critical bugs and oversights that need to be fixed before it is fully functional.

Please address the following issues:

### 1. Hardcoded Opponent in Backend (`backend/src/api.py`)
**Issue:** The `/ws/human` endpoint currently hardcodes `GreedyBot("GreedyBot")` as the opponent. If the user selects "RandomBot" in the frontend UI, they will still end up playing against GreedyBot.
**Fix:**
- Modify the endpoint to accept the opponent type as a path parameter (e.g., `@app.websocket("/ws/human/{p2_type}")`).
- Inside the endpoint, dynamically instantiate the correct bot using the existing `_get_bot(p2_type, "Player 2")` helper function.

### 2. Missing Opponent Type in Frontend (`frontend/src/App.jsx`)
**Issue:** The frontend establishes the WebSocket connection without passing the selected `p2Type`.
**Fix:**
- Update the WebSocket connection URL to include the selected opponent: `const wsUrl = API_BASE.replace(/^http/, 'ws') + '/ws/human/' + p2Type;`

### 3. Build Configuration Regression (`backend/pyproject.toml`)
**Issue:** You modified `packages = ["src/cribbage"]`. This breaks the `uvicorn src.api:app` command because `api.py` lives at `src/api.py`, not inside `src/cribbage`.
**Fix:**
- Revert the configuration back to `packages = ["src"]`.

### 4. Game Over Handling (`backend/src/api.py`)
**Issue:** When `engine.play_game()` finishes in the background thread, the `while True:` WebSocket loop will block forever on `bot.request_queue.get()`. 
**Fix:** 
- In the background thread `_run_engine()`, after `engine.play_game()` returns, push a final "game_over" message to the bot's request queue: `bot.request_queue.put({"action": "game_over"})`.
- In the WebSocket loop, handle this action by sending it to the frontend and gracefully breaking the loop to close the socket.

### 5. Next Task
Once these fixes are complete, please move on to implementing the features described in **`task_bulk_matches.md`**.
\n## Status\nAll fixes have been implemented.
