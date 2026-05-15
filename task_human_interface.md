# Task: Human Player Web Interface & Pegboard

## Objective
Enable a user to play Cribbage against an AI bot directly in the web frontend. The user needs an interactive UI to see their hand, select discard cards, play pegging cards, and view the game score in real-time via a pegboard graphic.

## Architecture & Implementation Strategy

### 1. Backend (`backend/src/api.py`, `backend/src/cribbage/engine.py`, `backend/src/cribbage/bots/remote_bot.py`)
Currently, the `GameEngine` runs synchronously in a background thread and only returns the game log when the game is over. To support an interactive human player, the backend must stream state updates to the frontend in real-time over WebSockets.

*   **Simplifying State Broadcasting:** 
    *   In `backend/src/cribbage/engine.py`, modify `GameEngine.__init__` to accept an optional `on_event` callback: `def __init__(self, p1, p2, on_event=None, verbose=True):`
    *   In `GameEngine.log_event()`, add a call to this callback: `if self.on_event: self.on_event(event_dict)`
*   **Integrating with RemoteBot (`backend/src/cribbage/bots/remote_bot.py`):**
    *   Add a new method `def send_event(self, event_dict):` to `RemoteBot`.
    *   Inside `send_event`, push the event to the existing queue so the WebSocket picks it up: `self.request_queue.put({"action": "state_update", "event": event_dict})`
*   **Unified WebSocket Endpoint (`backend/src/api.py`):**
    *   Create a new WebSocket endpoint `@app.websocket("/ws/human")`.
    *   Inside the endpoint, instantiate `bot = RemoteBot("Human")`.
    *   Create a wrapper for the engine callback: `def handle_event(e): bot.send_event(e)`.
    *   Start the engine in a background thread: `engine = GameEngine(bot, GreedyBot("GreedyBot"), on_event=handle_event)` and call `engine.play_game()`.
    *   Use a `while True:` loop to await `asyncio.to_thread(bot.request_queue.get)` and send it to the websocket. If it's an action requiring a response (`"action": "discard"` or `"peg"`), use `websocket.receive_json()` and put it in `bot.response_queue`. If it's just a `"state_update"`, do not wait for a response.

### 2. Frontend (`frontend/src/App.jsx` & UI Components)
The frontend currently expects a single REST API response containing the whole game. It must be adapted to handle a live WebSocket connection.

*   **Mode Selection in `App.jsx`:**
    *   Add `{ value: 'human', label: 'Human (You)' }` to the `BOT_OPTIONS` array.
    *   In the `runMatch` function, check if `p1Type === 'human'`. If true, bypass the `fetch` `POST` request. Instead, connect to `ws://localhost:8000/ws/human`.
    *   Setup the WebSocket `onmessage` listener to handle incoming JSON.
*   **Interactive UI Components (Create `frontend/src/components/HumanInterface.jsx`):**
    *   **State Updates:** When the WebSocket receives `{"action": "state_update", "event": {...}}`, append it to the local React state (like a live-updating game log) and update the local score counts.
    *   **Hand View:** Maintain a state variable `currentHand`. Render the cards as clickable elements.
    *   **Discard Phase:** When receiving `{"action": "discard", "hand": ["5H", "10S", ...] }`, update `currentHand`. Allow the user to toggle selection on exactly 2 cards. Show a "Discard" button that sends `{"cards": [selected1, selected2]}` via the WebSocket socket.
    *   **Pegging Phase:** When receiving `{"action": "peg", "hand": [...], "current_count": X}`, update `currentHand`. Allow clicking a single card to send `{"card": "6C"}`. If no valid moves exist, show a "Go" button that sends `{"card": null}`.
*   **Pegboard Graphic (`frontend/src/components/Pegboard.jsx`):**
    *   Create a simple visual representation of a Cribbage board (e.g., using CSS Grid or Flexbox to draw two tracks of 120 holes).
    *   Pass `p1Score` and `p2Score` to this component as props. Calculate the peg positions based on these scores and render a visual "peg" in the appropriate holes.

## Acceptance Criteria
- [x] A human can play a full game against `GreedyBot` from start to finish via the UI.
- [x] The user is prevented from making illegal moves (e.g., pegging over 31).
- [x] The pegboard graphic accurately reflects the scores in real-time.
- [x] AI vs AI games continue to work seamlessly via the standard `POST` endpoint.

## Implementation Summary
- **Backend**: Added the `on_event` callback to `GameEngine` and integrated it with `log_event`. Added the `send_event` method to `RemoteBot` to push state updates via WebSockets. Added the `/ws/human` websocket endpoint in `api.py` to handle the bi-directional communication between the frontend and the `RemoteBot` instance running the `GameEngine` in a background thread.
- **Frontend**: Added a `"Human"` option to `BOT_OPTIONS` in `App.jsx`. Created a new `HumanInterface.jsx` component that establishes a WebSocket connection, renders a hand of cards, and displays contextual actions (Discard/Peg/Go) based on the game's phase. Created a `Pegboard.jsx` graphic to display `p1Score` and `p2Score` on tracks of 120 holes, supported by CSS appended to `index.css`. `App.jsx` handles conditional rendering to preserve the standard `/api/tournament` layout for bot matches while displaying `HumanInterface` for human play.
