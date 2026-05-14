import asyncio
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .cribbage.tournament import run_tournament
from .cribbage.engine import GameEngine
from .cribbage.bots.remote_bot import RemoteBot
from .cribbage.bots.random_bot import RandomBot
from .cribbage.bots.greedy_bot import GreedyBot

app = FastAPI(title="Cribbage Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store of active remote bots
active_bots = {}

@app.websocket("/ws/bot/{bot_id}")
async def websocket_bot_endpoint(websocket: WebSocket, bot_id: str):
    await websocket.accept()
    
    bot_instance = RemoteBot(bot_id)
    active_bots[bot_id] = bot_instance
    
    try:
        # Loop to bridge the WebSocket (async) with the RemoteBot queues (sync)
        while True:
            # 1. Wait for a request from the engine (via the bot instance)
            # We use asyncio.to_thread because Queue.get() is blocking
            req = await asyncio.to_thread(bot_instance.request_queue.get)
            
            # 2. Send the request to the connected client
            await websocket.send_json(req)
            
            # 3. Wait for the client's response
            res = await websocket.receive_json()
            
            # 4. Put the response back for the engine to consume
            bot_instance.response_queue.put(res)
            
    except WebSocketDisconnect:
        # If they disconnect, feed None to the engine to trigger a forfeit
        bot_instance.response_queue.put(None)
        del active_bots[bot_id]

class TournamentRequest(BaseModel):
    p1_type: str # "random", "greedy", "remote"
    p2_type: str
    p1_id: str = "Player 1"
    p2_id: str = "Player 2"
    num_games: int = 1

def _get_bot(bot_type: str, bot_id: str):
    if bot_type == "random": return RandomBot(bot_id)
    if bot_type == "greedy": return GreedyBot(bot_id)
    if bot_type == "remote":
        if bot_id not in active_bots:
            raise ValueError(f"Remote bot {bot_id} is not connected via WebSocket")
        return active_bots[bot_id]
    raise ValueError(f"Unknown bot type {bot_type}")

@app.post("/api/tournament")
async def start_tournament(req: TournamentRequest):
    try:
        p1 = _get_bot(req.p1_type, req.p1_id)
        p2 = _get_bot(req.p2_type, req.p2_id)
    except ValueError as e:
        return {"error": str(e)}
        
    # Run the tournament in a separate thread so it doesn't block the event loop
    # (Especially important since it will block waiting on Queues for RemoteBots)
    
    def _run():
        engine = GameEngine(p1, p2)
        winner, log = engine.play_game() # For simplicity, API just runs 1 game right now
        return {
            "winner": winner,
            "skunk": engine.skunk,
            "final_score": engine.state.scores,
            "log": log
        }
        
    result = await asyncio.to_thread(_run)
    return result
