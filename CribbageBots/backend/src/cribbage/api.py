import asyncio
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uuid

from .tournament import run_tournament
from .engine import GameEngine
from .bots import BOT_REGISTRY
from .bots.remote_bot import RemoteBot, BotDisconnectedError
from .security import get_runtime_signature, filter_event_for_player, scrub_log_for_observer

app = FastAPI(title="Cribbage Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
import datetime
import json

# In-memory store of active remote bots
# { bot_id: {"instance": RemoteBot, "token": str, "active": bool, "last_activity": float, "busy": bool} }
active_bots = {}
MAX_ACTIVE_BOTS = 100

async def cleanup_inactive_bots():
    """Background task to remove bots inactive for more than 24 hours."""
    while True:
        await asyncio.sleep(3600) # Check every hour
        now = time.time()
        to_delete = []
        for bot_id, data in active_bots.items():
            # If not active (disconnected) and last seen > 24 hours ago
            if not data["active"] and (now - data["last_activity"]) > 86400:
                to_delete.append(bot_id)
        
        for bot_id in to_delete:
            del active_bots[bot_id]

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_inactive_bots())

@app.get("/api/bots")
async def get_bots():
    return {"bots": [{"value": k, "label": v["label"]} for k, v in BOT_REGISTRY.items()]}

@app.websocket("/ws/bot/{bot_id}")
async def websocket_bot_endpoint(websocket: WebSocket, bot_id: str):
    # Security: Validate bot_id and handle registration
    if bot_id == "human":
        await websocket.close(code=1008, reason="Reserved ID")
        return
    
    await websocket.accept()
    
    try:
        # SEC-12: Wait for auth message as the first frame
        auth_msg = await websocket.receive_text()
        if len(auth_msg) > 1024:
             await websocket.close(code=1009, reason="Auth message too large")
             return
             
        auth_data = json.loads(auth_msg)
        if auth_data.get("action") != "auth":
            await websocket.close(code=1008, reason="First message must be 'auth' action")
            return
            
        token = auth_data.get("token")
        
        if bot_id in active_bots:
            existing = active_bots[bot_id]
            # SEC-7: Ensure tokens are required if they were set at registration
            if existing["token"] and existing["token"] != token:
                await asyncio.sleep(1.0) # Throttling brute force attempts
                await websocket.close(code=1008, reason="Invalid token for this bot ID")
                return
            
            if existing["busy"]:
                await websocket.close(code=1008, reason="Bot is currently busy in a tournament")
                return
        else:
            # New registration
            if len(active_bots) >= MAX_ACTIVE_BOTS:
                await websocket.close(code=1008, reason="Server full")
                return
                
            # SEC-7: If no token provided, generate one to ensure ownership
            if not token:
                token = str(uuid.uuid4())
            
            active_bots[bot_id] = {
                "instance": RemoteBot(bot_id, timeout=30),
                "token": token,
                "active": True,
                "last_activity": time.time(),
                "busy": False
            }

        # Send auth success with the token (in case we generated it)
        await websocket.send_json({"action": "auth_success", "token": token})
        
        bot_instance = active_bots[bot_id]["instance"]
        active_bots[bot_id]["active"] = True
        active_bots[bot_id]["last_activity"] = time.time()
        
        while True:
            # Wait for a request from the engine
            req = await asyncio.to_thread(bot_instance.request_queue.get)
            active_bots[bot_id]["last_activity"] = time.time()
            
            # Artificial delay to make bot play feel more natural
            if req.get("action") in ["discard", "peg"]:
                await asyncio.sleep(1.0)
                
            await websocket.send_json(req)
            
            # Block until bot responds via websocket (with size safety)
            text = await websocket.receive_text()
            if len(text) > 65536: # 64KB limit
                await websocket.close(code=1009, reason="Payload too large")
                break
            
            res = json.loads(text)
            active_bots[bot_id]["last_activity"] = time.time()
            bot_instance.response_queue.put(res)
    except WebSocketDisconnect:
        # Don't delete from active_bots so they can reconnect with the same token
        active_bots[bot_id]["active"] = False
        active_bots[bot_id]["last_activity"] = time.time()
        bot_instance.response_queue.put(None) # Unblock engine if waiting
    except Exception as e:
        print(f"Error in bot websocket: {e}")
        if bot_id in active_bots:
            active_bots[bot_id]["active"] = False
            active_bots[bot_id]["last_activity"] = time.time()
        bot_instance.response_queue.put(None)

@app.websocket("/ws/human/{p2_type}")
async def websocket_human_endpoint(websocket: WebSocket, p2_type: str):
    await websocket.accept()
    # SEC-6: Use a finite timeout for the human player to prevent leaked threads
    bot = RemoteBot("Player 1", timeout=300)
    
    try:
        p2_bot = _get_bot(p2_type, "Player 2")
    except ValueError as e:
        await websocket.close(code=1003, reason=str(e))
        return
    
    def handle_event(e):
        # SEC-1: Filter events for the human player
        filtered = filter_event_for_player(e, "Player 1")
        bot.send_event(filtered)
        
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
        return active_bots[bot_id]["instance"]
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
        # SEC-15: Bound num_games to prevent resource exhaustion
        num_games = max(1, min(int(data.get("num_games", 10)), 5000))

        p1 = _get_bot(p1_type, p1_id)
        p2 = _get_bot(p2_type, p2_id)
        
        # Lock bots as busy for the duration of the tournament
        for b in [p1, p2]:
            if b.player_id in active_bots:
                active_bots[b.player_id]["busy"] = True
        
        # Capture initial code signature for integrity protection
        initial_sig = get_runtime_signature()
        integrity_violated = False
        
        wins = {p1_id: 0, p2_id: 0}
        skunks = {p1_id: 0, p2_id: 0}
        total_scores = {p1_id: 0, p2_id: 0}
        
        last_engine = None
        for i in range(num_games):
            try:
                # Mid-tournament integrity check
                if i % 10 == 0:
                    if get_runtime_signature() != initial_sig:
                        integrity_violated = True

                first, second = (p1, p2) if i % 2 == 0 else (p2, p1)
                last_engine = GameEngine(first, second, verbose=False)
                winner, _ = await asyncio.to_thread(last_engine.play_game)
                
                # If play_game returned None but no exception (internal system error handled inside engine)
                if winner is None:
                    # Treat as a draw or skip, but for stats we need a winner. 
                    # We'll just continue and not increment wins.
                    continue
                    
            except (BotDisconnectedError, ValueError, Exception) as e:
                # A bot disconnected or a fatal error occurred. 
                # Award all REMAINING games to the opponent and end early but gracefully.
                remaining = num_games - i
                # Determine who the "offender" is
                offender_id = getattr(e, "player_id", None)
                if not offender_id:
                    # If we can't tell, award to whoever didn't crash (arbitrary fallback)
                    winner = p2_id if i % 2 == 0 else p1_id
                else:
                    winner = p2_id if offender_id == p1_id else p1_id
                
                wins[winner] += remaining
                await websocket.send_json({
                    "action": "progress",
                    "game": num_games,
                    "total_games": num_games,
                    "winner": f"{winner} (by batch forfeit)",
                    "wins": wins,
                    "skunks": skunks,
                    "total_score": total_scores,
                    "integrity_violated": integrity_violated
                })
                break
            
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
                "total_score": total_scores,
                "integrity_violated": integrity_violated
            })
            
        if last_engine:
            await websocket.send_json({
                "action": "complete",
                "winner": max(wins, key=wins.get),
                "wins": wins,
                "skunks": skunks,
                "total_score": total_scores,
                "final_score": last_engine.state.scores,
                "integrity_violated": integrity_violated
            })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
            pass
    finally:
        # Unlock bots
        for b_id in [p1_id, p2_id]:
            if b_id in active_bots:
                active_bots[b_id]["busy"] = False
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
        
    # Capture initial code signature for integrity protection
    initial_sig = get_runtime_signature()
    
    # Lock bots
    for b_id in [req.p1_id, req.p2_id]:
        if b_id in active_bots:
            active_bots[b_id]["busy"] = True
        
    def _run():
        all_logs = []
        wins = {req.p1_id: 0, req.p2_id: 0}
        skunks = {req.p1_id: 0, req.p2_id: 0}
        final_scores = {req.p1_id: 0, req.p2_id: 0}
        last_score = {}
        last_skunk = False
        integrity_violated = False

        for i in range(req.num_games):
            try:
                # Mid-tournament integrity check
                if i % 10 == 0:
                    if get_runtime_signature() != initial_sig:
                        integrity_violated = True

                first, second = (p1, p2) if i % 2 == 0 else (p2, p1)
                engine = GameEngine(first, second, verbose=(req.num_games == 1))
                winner, log = engine.play_game()
                
                if winner is None:
                    continue

                wins[winner] = wins.get(winner, 0) + 1
                last_skunk = engine.skunk
                if engine.skunk:
                    skunks[winner] = skunks.get(winner, 0) + 1
                for pid, pts in engine.state.scores.items():
                    final_scores[pid] = final_scores.get(pid, 0) + pts
                last_score = engine.state.scores
                
                if req.num_games == 1:
                    # SEC-1: Strip all hand data for the neutral REST observer.
                    # The caller is unknown (e.g. the dashboard UI), not either player,
                    # so no player's hand should appear in the returned log.
                    scrubbed_log = scrub_log_for_observer(log)
                    all_logs.append({"game": i + 1, "winner": winner, "log": scrubbed_log})
            except (BotDisconnectedError, ValueError) as e:
                # SEC-9: Bot-specific forfeits awarded to opponent
                remaining = req.num_games - i
                offender_id = getattr(e, "player_id", None)
                winner = req.p2_id if offender_id == req.p1_id else req.p1_id
                wins[winner] = wins.get(winner, 0) + remaining
                break
            except Exception as e:
                # SEC-9: Internal engine errors do NOT award wins
                print(f"CRITICAL: Engine error in tournament: {e}")
                break

        return {
            "winner": max(wins, key=wins.get),
            "wins": wins,
            "skunks": skunks,
            "skunk": last_skunk if req.num_games == 1 else False,
            "final_score": last_score,
            "total_score": final_scores,
            "games": all_logs,
            "log": all_logs[0]["log"] if all_logs else [],
            "integrity_violated": integrity_violated
        }
        
    result = await asyncio.to_thread(_run)
    # Unlock bots
    for b_id in [req.p1_id, req.p2_id]:
        if b_id in active_bots:
            active_bots[b_id]["busy"] = False
    return result
