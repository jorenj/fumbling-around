import asyncio
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .tournament import run_tournament
from .engine import GameEngine
from .bots import BOT_REGISTRY
from .bots.remote_bot import RemoteBot

app = FastAPI(title="Cribbage Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store of active remote bots
active_bots = {}

@app.get("/api/bots")
async def get_bots():
    return {"bots": [{"value": k, "label": v["label"]} for k, v in BOT_REGISTRY.items()]}

@app.websocket("/ws/bot/{bot_id}")
async def websocket_bot_endpoint(websocket: WebSocket, bot_id: str):
    await websocket.accept()
    
    timeout = None if bot_id == "human" else 30
    bot_instance = RemoteBot(bot_id, timeout=timeout)
    active_bots[bot_id] = bot_instance
    
    try:
        while True:
            req = await asyncio.to_thread(bot_instance.request_queue.get)
            if bot_id != "human" and req.get("action") in ["discard", "peg"]:
                await asyncio.sleep(1.0)
            await websocket.send_json(req)
            res = await websocket.receive_json()
            bot_instance.response_queue.put(res)
    except WebSocketDisconnect:
        bot_instance.response_queue.put(None)
        if bot_id in active_bots:
            del active_bots[bot_id]

@app.websocket("/ws/human/{p2_type}")
async def websocket_human_endpoint(websocket: WebSocket, p2_type: str):
    await websocket.accept()
    bot = RemoteBot("Player 1", timeout=None)
    
    try:
        p2_bot = _get_bot(p2_type, "Player 2")
    except ValueError as e:
        await websocket.close(code=1003, reason=str(e))
        return
    
    def handle_event(e):
        bot.send_event(e)
        
    engine = None
    
    def _run_engine():
        nonlocal engine
        original_peg = p2_bot.peg
        original_discard = p2_bot.discard
        
        def delayed_peg(*args, **kwargs):
            import time
            time.sleep(1.0)
            return original_peg(*args, **kwargs)
            
        def delayed_discard(*args, **kwargs):
            import time
            time.sleep(1.0)
            return original_discard(*args, **kwargs)
            
        p2_bot.peg = delayed_peg
        p2_bot.discard = delayed_discard

        engine = GameEngine(bot, p2_bot, on_event=handle_event, manual_count=True)
        winner, _ = engine.play_game()
        bot.request_queue.put({"action": "game_over", "winner": winner, "reason": engine.end_reason})
        
    game_thread = threading.Thread(target=_run_engine, daemon=True)
    game_thread.start()
    
    try:
        while True:
            req = await asyncio.to_thread(bot.request_queue.get)
            await websocket.send_json(req)
            
            if req.get("action") == "game_over":
                break
            
            if req.get("action") in ["discard", "peg"]:
                res = await websocket.receive_json()
                if res.get("action") == "resume_count":
                    if engine: engine.count_resume_event.set()
                else:
                    bot.response_queue.put(res)
            elif req.get("action") == "state_update":
                if req.get("event", {}).get("type") == "count_hand_request":
                    res = await websocket.receive_json()
                    if res.get("action") == "resume_count":
                        if engine: engine.count_resume_event.set()
    except WebSocketDisconnect:
        bot.response_queue.put(None)
        if engine:
            engine.count_resume_event.set()

class TournamentRequest(BaseModel):
    p1_type: str 
    p2_type: str
    p1_id: str = "Player 1"
    p2_id: str = "Player 2"
    num_games: int = Field(1, ge=1)

def _get_bot(bot_type: str, bot_id: str):
    if bot_type == "human":
        raise ValueError("Human player cannot be used as an automated bot.")
    if bot_type in BOT_REGISTRY:
        return BOT_REGISTRY[bot_type]["class"](bot_id)
    if bot_type == "remote":
        if bot_id not in active_bots:
            raise ValueError(f"Remote bot {bot_id} is not connected via WebSocket")
        return active_bots[bot_id]
    raise ValueError(f"Unknown bot type {bot_type}")

@app.websocket("/ws/tournament")
async def websocket_tournament_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        p1_type = data.get("p1_type")
        p2_type = data.get("p2_type")
        p1_id = data.get("p1_id", "Player 1")
        p2_id = data.get("p2_id", "Player 2")
        num_games = int(data.get("num_games", 10))

        p1 = _get_bot(p1_type, p1_id)
        p2 = _get_bot(p2_type, p2_id)
        
        wins = {p1_id: 0, p2_id: 0}
        skunks = {p1_id: 0, p2_id: 0}
        total_scores = {p1_id: 0, p2_id: 0}
        
        last_engine = None
        for i in range(num_games):
            first, second = (p1, p2) if i % 2 == 0 else (p2, p1)
            last_engine = GameEngine(first, second, verbose=False)
            winner, _ = await asyncio.to_thread(last_engine.play_game)
            
            wins[winner] += 1
            if last_engine.skunk:
                skunks[winner] += 1
            for pid, pts in last_engine.state.scores.items():
                total_scores[pid] += pts
                
            await websocket.send_json({
                "action": "progress",
                "game": i + 1,
                "total_games": num_games,
                "winner": winner,
                "wins": wins,
                "skunks": skunks,
                "total_score": total_scores
            })
            
        if last_engine:
            await websocket.send_json({
                "action": "complete",
                "winner": max(wins, key=wins.get),
                "wins": wins,
                "skunks": skunks,
                "total_score": total_scores,
                "final_score": last_engine.state.scores
            })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass

@app.post("/api/tournament")
async def start_tournament(req: TournamentRequest):
    try:
        p1 = _get_bot(req.p1_type, req.p1_id)
        p2 = _get_bot(req.p2_type, req.p2_id)
    except ValueError as e:
        return {"error": str(e)}
        
    def _run():
        all_logs = []
        wins = {req.p1_id: 0, req.p2_id: 0}
        skunks = {req.p1_id: 0, req.p2_id: 0}
        final_scores = {req.p1_id: 0, req.p2_id: 0}
        last_score = {}
        last_skunk = False

        for i in range(req.num_games):
            first, second = (p1, p2) if i % 2 == 0 else (p2, p1)
            engine = GameEngine(first, second, verbose=(req.num_games == 1))
            winner, log = engine.play_game()
            wins[winner] = wins.get(winner, 0) + 1
            last_skunk = engine.skunk
            if engine.skunk:
                skunks[winner] = skunks.get(winner, 0) + 1
            for pid, pts in engine.state.scores.items():
                final_scores[pid] = final_scores.get(pid, 0) + pts
            last_score = engine.state.scores
            
            if req.num_games == 1:
                all_logs.append({"game": i + 1, "winner": winner, "log": log})

        return {
            "winner": max(wins, key=wins.get),
            "wins": wins,
            "skunks": skunks,
            "skunk": last_skunk if req.num_games == 1 else False,
            "final_score": last_score,
            "total_score": final_scores,
            "games": all_logs,
            "log": all_logs[0]["log"] if all_logs else [],
        }
        
    result = await asyncio.to_thread(_run)
    return result
