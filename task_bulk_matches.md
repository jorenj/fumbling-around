# Task: Bulk Bot Matches & UI Summary

## Objective
Add the ability to run high-volume simulated tournaments (e.g., 100 to 1,000 games) between AI bots. The system must run these matches efficiently and present a summarized statistical view in the frontend, rather than attempting to render a massive event log.

## Architecture & Implementation Strategy

### 1. Backend (`backend/src/api.py`)
The current API supports a `num_games` parameter, but it builds the `game_log` in memory for every single game. For 10,000 games, this will result in a massive JSON payload and likely cause memory exhaustion.

*   **Memory Optimization inside `backend/src/cribbage/engine.py`:**
    *   Add a `verbose: bool = True` parameter to `GameEngine.__init__`.
    *   In the `GameEngine.log_event` method, wrap the appending to `self.game_log` with an `if self.verbose:` check. This prevents the engine from generating massive log arrays in memory during bulk matches.
*   **API Adjustments inside `backend/src/api.py`:**
    *   In the `_run()` function inside the `start_tournament` endpoint, if `req.num_games > 1`, instantiate the `GameEngine` with `verbose=False`.
    *   For bulk matches, do not append the result of `play_game()` to the `all_logs` array. Only track the macroscopic statistics: `wins` dict, `skunks` dict, and `final_scores` dict per player.
    *   Ensure the JSON payload returned strictly sets the `games` and `log` keys to empty lists (`[]`) when `req.num_games > 1`.

### 2. Frontend (`frontend/src/App.jsx`)
The UI needs to expose this feature and handle the specialized response structure.

*   **Controls Update:**
    *   In the `<section className="controls">`, add an HTML `<input type="number" min="1" max="1000" />` field bound to a new `numGames` state variable (default 1).
    *   Validation: If the user selects "Human" for either player, the `numGames` input must be disabled and forced to 1. Bulk matches are strictly for Bot vs Bot.
    *   Update the `fetch` payload body to send `num_games: parseInt(numGames)`.
*   **Results Rendering (Single vs Bulk Mode):**
    *   Check if `result.log.length > 0`. If true (Single mode), render the existing `.log-section` and `.game-log`.
    *   If `result.log.length === 0` and `numGames > 1` (Bulk mode), DO NOT render the `.log-section`.
    *   Instead, render a new `<section className="glass-panel summary-section">` that displays a **Tournament Summary Dashboard**.
    *   The Summary Dashboard should visualize the data clearly (e.g., use simple flexbox/CSS percentage bars to show the Win Rate for Player 1 vs Player 2, and list the total Skunks).

## Acceptance Criteria
- [x] The user can specify between 1 and 1,000 games in the UI.
- [x] The backend runs 1,000 games without crashing or returning a multi-megabyte JSON payload.
- [x] The UI displays a clear statistical summary (Win %, Skunks) for bulk matches.
- [x] Human players are explicitly blocked from participating in bulk matches.

## Implementation Summary
- **Backend Optimization**: Modified `GameEngine` to accept a `verbose` flag that determines whether game events are appended to the in-memory log list. Updated `api.py` to instantiate engines with `verbose=False` when `num_games > 1` and omitted logs from the response payload, ensuring memory-safe and network-efficient bulk simulations.
- **Frontend Dashboard**: Added a "Games" input field constrained to `[1, 1000]`, disabled when a Human player is selected. Handled the new API response shape by conditionally bypassing the massive log renderer for bulk matches, opting instead for a new "Tournament Summary Dashboard" component. Designed the dashboard with dynamic, side-by-side win/skunk statistics and a color-coded flexbox progress bar visualizing the overall Win Rate percentage.
