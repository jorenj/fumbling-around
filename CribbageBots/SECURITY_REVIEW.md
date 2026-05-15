# Cribbage Bot — Security Review

**Reviewer:** Software Reviewer Agent  
**Date:** 2026-05-15  
**Scope:** Remote bot cheating vectors, information leakage, engine integrity, and API abuse  
**Status:** ⚠️ OPEN — Findings below require action before competitive/public use

---

## Threat Model

The adversary is a **remote bot operator** who connects their bot via WebSocket and wants to gain an unfair advantage. They can:
- Control every byte their bot sends to the server
- Observe every byte the server sends to their bot
- Reconnect, time out, or crash deliberately
- Run the connection in parallel with out-of-band coordination
- Attempt to corrupt the engine state or steer game outcomes

The adversary **cannot** (under current architecture):
- Directly call Python functions on the server
- Observe internal engine memory without receiving it over the wire

---

## Part 1: Information Leakage — Opponent's Cards

### 🔴 SEC-1 — Engine event log broadcasts opponent's hand during counting phase

**File:** `engine.py:145-177` (the `count_hand_request` events)  
**Severity:** 🔴 Critical — direct cheating vector

When `manual_count=True`, the engine emits `count_hand_request` events via `log_event`, which includes the **full hand of each player** and the **full crib** in the `data` field:

```python
data={"hand": [str(c) for c in hands[non_dealer]], "is_crib": False, "points": pts_nd, "breakdown": bd_nd}
```

The `on_event` callback passes these events to `RemoteBot.send_event`, which puts them directly into `request_queue` with `action: "state_update"`. The remote bot receives the **opponent's complete hand** and **the crib contents** as plaintext JSON over the WebSocket. This is the most valuable information in the game — knowing the opponent's hand and crib cards before the next deal would allow a bot to make perfectly informed discard decisions.

**In the current human-play WebSocket endpoint**, all `state_update` events (which include all log events, including `count_hand_request` with opponent hand data) are forwarded to the human player's browser. A remote bot operator connecting as `p2_bot` in a human vs bot game wouldn't receive this — but a remote bot operator participating in a bot vs bot match where both sides are RemoteBots would receive both hands. 

More critically: the `count_hand_request` data field is also included in regular `log_event` calls made during verbose mode, which populates `game_log`. The full `game_log` (with both players' hands) is returned to the REST API caller. A remote bot that won a match and examines the returned log gets the opponent's hand for every round.

**Recommendation:**
- **This fix does not break core bot functionality.** Bots receive their own hand explicitly in `discard` and `peg` request payloads — they do not depend on `count_hand_request` events to play. Filtering opponent hand data from `state_update` events only removes information bots were never supposed to have; their move-making ability is entirely unaffected.
- Strip `hand` and `is_crib` from `count_hand_request` events before they are forwarded to the non-owning player's `state_update` channel. A bot should only receive a `count_hand_request` event for its own hand (to display scores to its operator), not for the opponent's.
- In the `on_event` callback path, implement a player-aware filter that accepts a `recipient_id` and removes sensitive fields before forwarding to that player's queue.
- The `game_log` returned to REST API callers should similarly scrub opponent hand data from `data` fields in `count_hand_request` events, or maintain separate bot-specific and observer-specific log streams.

---

### 🔴 SEC-2 — `log_event` broadcasts cut card before bots have discarded in async tournament flow

**File:** `engine.py:127` + `api.py:238`  
**Severity:** 🔴 Critical — timing-based cheating vector in async tournament mode

The game sequence is: Deal → Discard → Cut → Peg → Count. The cut card is revealed **after** discards. However, in the WebSocket tournament endpoint (`/ws/tournament`), `play_game()` is called via `asyncio.to_thread` but the `on_event` callback is called synchronously inside the engine thread. In a future multi-game or streaming scenario where event updates are sent to observers during play, the cut card is emitted to the game log while both bots are potentially still connected.

More importantly: in a **bot vs remote_bot** scenario, the `peg` request sent to the remote bot includes `peg_history` and `current_count` — these are correct. **But** the `cut` event (`log_event("cut", ...)`) is sent via the `on_event` callback, which in the WebSocket tournament path currently goes nowhere (no `on_event` is set for tournament games). This is safe today, but if `on_event` were ever wired into the tournament WebSocket stream, the remote bot would receive the cut card information before peg requests. The cut card is already visible during pegging since `current_count` is derived from pegged cards, but explicit broadcast of it pre-pegging has no game-rules justification.

**Recommendation:** Document clearly that `on_event` in tournament mode must never be wired to a player-facing channel without per-player filtering. This is a latent risk.

---

### ✅ SEC-3 — `peg_history` is intentionally public; sophisticated bots should use it

**File:** `remote_bot.py:81`, `engine.py:232-234`  
**Severity:** ✅ No issue — by design

The peg request includes `peg_history` (the current uninterrupted sequence of played cards). Pegging is a fully public phase of cribbage — both players observe every card played. A sophisticated bot that records peg history across the game to infer opponent tendencies, deduce unplayed cards, or optimize future pegging decisions is playing **within the rules**. This is an intended feature of the protocol, not a vulnerability.

**No action required.** Document in DEVELOPERS.md that bots are explicitly permitted and encouraged to use peg history for strategic inference.

---

## Part 2: Information Leakage — Opponent's Score & Game State

### 🟡 SEC-4 — Every log event includes both players' scores

**File:** `engine.py:31-32`  
**Severity:** 🟡 Low / Expected behavior

Every `log_event` call includes `p1_score` and `p2_score`. This is intentional and correct — in real cribbage, scores are public. Remote bots receive their opponent's score via the `state_update` events and peg request payloads. This is not a vulnerability but should be confirmed as intentional in documentation.

---

## Part 3: Deliberate Forfeit / Denial-of-Service by a Remote Bot

### 🟡 SEC-5 — Deliberate disconnect can be used to inflate a second bot's win record

**File:** `api.py:246-269`  
**Severity:** 🟡 Low — accepted policy risk; heavy punishment is intentional deterrent

In the WebSocket tournament endpoint, when a bot disconnects mid-tournament, the code awards **all remaining games** to the opponent:

```python
remaining = num_games - i
wins[winner] += remaining
```

A malicious operator controlling two bots could have bot A deliberately disconnect early in a tournament against bot B, causing bot B to be credited with all remaining wins. If the same operator controls bot B, this inflates its win record artificially.

**Policy decision: This behavior is intentional and is kept as a deterrent.** The heavy forfeiture penalty strongly discourages real bots from disconnecting (whether accidentally or deliberately) and encourages reliable, well-behaved implementations. The dual-bot inflation attack is an accepted risk — a bot inflated this way will eventually face legitimately strong opponents and its record will normalize. The cost of disrupting real matches through disconnection should be severe.

**Recommended monitoring action only:**
- Track per-bot forfeit and disconnect rates in tournament results. Flag or quarantine bots with a disconnect rate above a threshold (e.g., >5% of games).
- Display forfeit history alongside win records so the community can identify bad actors.

---

### 🟡 SEC-6 — Infinite stall via intentional `timeout=None` on human RemoteBot

**File:** `api.py:121`  
**Severity:** 🟡 Medium (engine thread stall)

The human player's `RemoteBot` is created with `timeout=None`:

```python
bot = RemoteBot("Player 1", timeout=None)
```

This means `response_queue.get()` blocks **indefinitely**. If the human player (or a malicious actor pretending to be a human player) connects the WebSocket but never sends a response to a `discard` or `peg` request, the engine thread stalls permanently. Since engine games run in daemon threads, this doesn't crash the server, but the thread is leaked and the game never completes. Accumulated leaked threads over many connections would exhaust the server's thread pool.

**Recommendation:** Use a finite timeout for the human player as well (e.g., `timeout=300` for a 5-minute think time). If the human times out, end the game gracefully with a forfeit rather than stalling forever.

---

### 🟢 SEC-7 — Bot ID squatting / namespace pollution

**File:** `api.py:59-78`  
**Severity:** 🟢 Low (nuisance)

Any actor can register any `bot_id` string by connecting to `/ws/bot/{bot_id}` without a token. If a legitimate bot (`"AwesomeBot"`) has never connected before, a malicious actor can connect first with that ID (without a token) and effectively impersonate the name. When the real `"AwesomeBot"` connects, the token check fires:

```python
if existing["token"] and existing["token"] != token:
```

Since the squatter registered **without** a token (`token=None`), `existing["token"]` is `None`, and `None and None != token` evaluates to `False` — the check **does not fire**. The real bot connects and overwrites the instance. This is ultimately harmless (the squatter gets kicked), but it means bot IDs are not truly owned.

**Recommendation:** If competitive use is intended, require tokens at registration. If `token` is not provided on first connection, generate and return one. Subsequent connections must supply it.

---

## Part 4: Engine Integrity & Manipulation

### 🔴 SEC-8 — `security.py` file-hash check can be trivially bypassed and provides false assurance

**File:** `security.py`, `api.py:221-234, 324-346`  
**Severity:** 🔴 Critical (the integrity system does not protect what it claims to protect)

`get_engine_signature()` hashes `engine.py`, `rules.py`, and `models.py` on disk and compares the hash between a baseline taken at tournament start and periodic mid-tournament checks. The intent is to detect if the code was modified during a tournament.

**The current disk-hash approach has the following limitations:**

1. **Python code is already loaded into memory at startup.** Modifying `engine.py` on disk during a running tournament has no effect on the running process — Python doesn't re-import modules from disk during execution. The hash comparison would detect a disk change, but that disk change has no effect on actual game behavior.

2. **The check does not verify what code is actually executing.** A malicious actor with server access could patch the in-memory module objects (`engine.GameEngine.__dict__`, etc.) or monkey-patch individual functions. The disk hash would remain unchanged. There is no way to hash "the code that is actually running" in CPython without a specialized runtime.

3. **The `except Exception` fallback in `get_engine_signature` returns `"error:{str(e)}"`.** If an attacker causes the file read to fail consistently (e.g., by removing file permissions), both the baseline and mid-tournament calls return the same error string, leaving `integrity_violated = False` and silently disabling the check.

4. **The check runs every 10 games, not every game.** An attacker modifying the running process between check intervals would not be detected until the next check cycle.

**`integrity_violated` as a flag-only signal is an accepted design.** Flagging the result for human review (rather than halting the tournament automatically) allows spurious failures to be investigated and discarded. This is the right tradeoff.

**Recommendation — Runtime Integrity Options:**

The following approaches are ordered from lowest to highest implementation complexity. Choose the one that fits the deployment context:

**Option A — Cryptographically signed tournament results (low complexity, recommended first step)**  
Generate an RSA or Ed25519 key pair at server startup (or load from a secrets store). After each tournament completes, sign the result payload with the private key and include the signature in the response. Any result can then be independently verified against the server's public key. A tampered result (whether from a compromised server process or a spoofed response) will have an invalid signature. This does not prevent tampering — it detects it and makes tampering non-deniable.

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import json, base64

# At startup:
SIGNING_KEY = Ed25519PrivateKey.generate()
VERIFY_KEY_BYTES = base64.b64encode(
    SIGNING_KEY.public_key().public_bytes_raw()
).decode()

# After tournament:
result_bytes = json.dumps(result, sort_keys=True).encode()
signature = base64.b64encode(SIGNING_KEY.sign(result_bytes)).decode()
result["signature"] = signature
result["verify_key"] = VERIFY_KEY_BYTES
```

**Option B — Bytecode hash of loaded modules (medium complexity)**  
Instead of hashing source files, hash the `__code__` objects of the engine's key functions at startup, capturing what is actually executing:

```python
import hashlib, marshal
from . import engine, rules, models

def get_runtime_signature():
    hasher = hashlib.sha256()
    for module in [engine, rules, models]:
        for name, obj in vars(module).items():
            if callable(obj) and hasattr(obj, '__code__'):
                hasher.update(marshal.dumps(obj.__code__))
    return hasher.hexdigest()
```

This detects monkey-patching of functions (the patched function has a different `__code__`) but not patching of class instance methods after object creation. It is significantly harder to bypass than the disk-hash approach.

**Option C — Read-only filesystem / container isolation (high complexity, strongest guarantee)**  
Run the engine inside a Docker container with the source directory mounted read-only (`-v /path/to/engine:/app:ro`). No process inside the container can modify the source files. Combine with `--read-only` on the container root filesystem and explicit tmpfs mounts for writable paths. This prevents both disk and memory tampering by external actors with partial server access, as they cannot modify the image layer the process was started from.

---

### 🟡 SEC-9 — `BotDisconnectedError` caught in the same `except` clause as all `Exception`s in REST tournament

**File:** `api.py:365`  
**Severity:** 🟡 Medium (offender attribution is wrong for engine errors)

```python
except (BotDisconnectedError, Exception) as e:
    offender_id = getattr(e, "player_id", None)
    winner = req.p2_id if offender_id == req.p1_id else req.p1_id
```

`(BotDisconnectedError, Exception)` is redundant — `Exception` catches everything including `BotDisconnectedError`. More importantly, if a genuine internal engine error occurs (not caused by either bot), `offender_id` will be `None`, and the code falls back to awarding the win to `req.p1_id`. This means a server-side bug always punishes Player 2 with a forfeit loss, regardless of who was at fault. In a competitive context, this creates an asymmetry that favors the first-registered player.

**Recommendation:** Split the catches: handle `BotDisconnectedError` and `(IllegalMoveError, TimeoutError)` separately from bare `Exception`. For uncaught engine exceptions, do **not** award a forfeit — record a void game or abort the tournament and report the error.

---

### 🟡 SEC-10 — `hands[pid]` passed directly to `bot.discard` as a mutable list before the defensive copy

**File:** `engine.py:114`  
**Severity:** 🟡 Medium (in-process bots only — not remotely exploitable, but relevant for local bots)

```python
discards = self.players[pid].discard(list(hands[pid]), is_dealer=(pid == dealer))
```

`list(hands[pid])` creates a **shallow copy** of the list, meaning the `Card` objects inside are shared. Since `Card` is a frozen dataclass, this is safe — bots cannot mutate cards. However, the engine then does:

```python
if not all(c in hands[pid] for c in discards) or ...
```

It checks membership in the **original** list. If a bot returned a card object that is equal-but-not-identical to a card in the hand (e.g., a newly constructed `Card(Rank.ACE, Suit.SPADES)` that wasn't dealt), the `in` check uses `__eq__`, which for frozen dataclasses is true when rank and suit match. A bot could thus "discard" a card that wasn't in their dealt hand, as long as they knew its rank and suit from some other source.

**Example attack (local bot only):** A locally-running malicious bot could construct `Card(Rank.ACE, Suit.SPADES)` and return it as a discard even if that card was in the opponent's hand (i.e., was never dealt to this bot). The engine's membership check uses `==` (value equality), so it would pass.

For **remote bots**, this is not exploitable because `RemoteBot.discard` receives `hand` as a list of Card objects from the engine, sends string representations to the client, and the client's response is matched back against the original hand using string comparison — `next((c for c in hand if str(c) == c1_str), None)`. This correctly bounds the response to cards actually dealt.

**Recommendation:** For completeness and future-proofing, change the engine's discard validation to use identity checking (`is`) rather than equality (`==`), or validate against the engine's internal deck ledger (cards dealt = cards that exist). For remote bots, the current string-matching is safe.

---

### 🟡 SEC-11 — No rate limiting on WebSocket connections or bot registration

**File:** `api.py:52-116`  
**Severity:** 🟡 Medium (resource exhaustion / bot flooding)

Any number of WebSocket connections can be opened to `/ws/bot/{bot_id}`. Each connection creates a `RemoteBot` instance (with two bounded `Queue(maxsize=1000)` objects). There is no limit on:
- How many distinct bot IDs can be registered simultaneously
- How many connection attempts per second are allowed
- How large `active_bots` can grow

A malicious actor could open thousands of connections, filling `active_bots` with dummy bots and consuming server memory/threads. The `cleanup_inactive_bots` task only removes bots that have been **inactive for 24 hours** — it provides no near-term protection against a flood.

**Recommendation:**
- Add a hard cap on `len(active_bots)` (e.g., 100 concurrent bots).
- Implement a per-IP connection rate limit using FastAPI middleware or a reverse proxy (nginx/Caddy).
- Reduce the cleanup interval or the inactivity threshold for bots that never entered a game.

---

### 🟢 SEC-12 — Token is passed as a query parameter, not in headers

**File:** `api.py:53`  
**Severity:** 🟢 Low (operational security)

```python
async def websocket_bot_endpoint(websocket: WebSocket, bot_id: str, token: str = None):
```

FastAPI reads `token` from the WebSocket URL query string (`ws://server/ws/bot/my_bot?token=secret`). Query parameters appear in server access logs, browser history, and reverse proxy logs. For a competitive tournament, this means bot tokens can leak via log files.

**Recommendation:** Require bots to send their token as the **first message** after connecting, before any game data is exchanged. Close the connection immediately if the first message is not a valid `{"action": "auth", "token": "..."}` frame.

---

## Part 5: Response Payload Abuse

### 🟡 SEC-13 — JSON response payload is parsed without schema validation

**File:** `api.py:98-103`  
**Severity:** 🟡 Medium (unexpected key injection into engine state)

```python
text = await websocket.receive_text()
if len(text) > 65536:  # 64KB limit
    await websocket.close(...)
res = json.loads(text)
...
bot_instance.response_queue.put(res)
```

The 64KB size limit is good. However, `res` is a raw dict placed directly into `response_queue`. `RemoteBot.discard` and `RemoteBot.peg` then index into this dict (`res["cards"]`, `res["card"]`). Extra keys in `res` are silently ignored.

The concern is that `res` is a plain Python dict with no type enforcement. If `res["cards"]` is a list of 10,000 items instead of 2, `RemoteBot.discard` reads:

```python
if not res or "cards" not in res or len(res["cards"]) != 2:
    raise IllegalMoveError(...)
```

The `len(...) != 2` check catches this correctly. Similarly `res["cards"][0]` and `res["cards"][1]` are validated by the string lookup in the hand. **This path is currently safe.** However, there is no guard against `res["cards"][0]` being a non-string (e.g., a dict or int), which would cause `str(card) == c1_str` to be `False` for all cards, raising `IllegalMoveError` — which forfeits the bot. That's the right outcome. 

**Recommendation:** Add explicit type assertions before use to make the failure mode clear and prevent confusing tracebacks:
```python
if not isinstance(res.get("cards"), list) or not all(isinstance(c, str) for c in res["cards"]):
    raise IllegalMoveError(...)
```

---

### ✅ SEC-14 — Remote bot saying "Go" with legal moves causes immediate forfeit — accepted risk

**File:** `remote_bot.py:97-99`, `engine.py:237-239`  
**Severity:** ✅ No action required — engine handles this correctly

When `card_str` is `None` in the peg response, `RemoteBot.peg` returns `None` (Go). The engine correctly checks:

```python
if played_card is None:
    if legal_moves:
        raise IllegalMoveError(current_player, "Passed when legal moves exist")
```

A bot that says Go with legal moves immediately forfeits the game — it cannot gain an advantage by doing so. The theoretical dual-bot inflation concern (using this to trigger a forfeit to inflate a second bot's record) is accepted risk per the SEC-5 policy decision. **No action required.**

---

### 🟡 SEC-15 — `num_games` is validated client-side only; the WebSocket tournament endpoint has no server-side validation

**File:** `api.py:210`  
**Severity:** 🟡 Medium (resource exhaustion)

The REST endpoint uses `Field(1, ge=1)` on `TournamentRequest.num_games` — correctly validated by Pydantic. But the WebSocket tournament endpoint reads `num_games` from raw JSON:

```python
num_games = int(data.get("num_games", 10))
```

There is no maximum cap. A client can request `num_games=1_000_000`, causing the server thread to run a million games (which would take hours or days).

**Recommendation:** Add `min`/`max` bounds: `num_games = max(1, min(int(data.get("num_games", 10)), 5000))`.

---

## Part 6: Randomness & Deck Integrity

### ✅ SEC-16 — `random.SystemRandom` used for shuffling

**File:** `models.py:55`  
**Severity:** ✅ No issue — this is good practice

```python
self._rng = random.SystemRandom()
```

`SystemRandom` uses the OS's cryptographic PRNG (`/dev/urandom` on Unix), which is not seeded predictably and cannot be influenced by a bot that observes prior outputs. This is the correct choice for a game engine. No action required.

---

### ✅ SEC-17 — Cards dealt from a server-side deck; bots cannot influence dealing

**File:** `engine.py:103-106`  
**Severity:** ✅ No issue

Cards are dealt from a server-controlled, server-shuffled deck. Bots have no input into the deal, cut, or shuffle. A remote bot cannot request specific cards or predict the deal.

---

## Prioritized Recommendations

### P0 — Fix Before Any Competitive Use

| ID | Action |
|---|---|
| **SEC-1** | Filter `count_hand_request` events per-player: strip opponent hand and crib contents before forwarding to a bot's state_update channel. **Does not affect core bot move-making functionality.** |
| **SEC-8** | Implement runtime integrity (recommend Option A: signed results; Option B: bytecode hash). Relabel the current disk-hash as a development-only file-change detector. |

### P1 — Fix Soon

| ID | Action |
|---|---|
| **SEC-6** | Set a finite timeout (e.g., 300s) for the human player's `RemoteBot` to prevent permanent engine thread stalls. |
| **SEC-9** | Split the catch block in the REST tournament to handle engine errors separately from bot forfeits; never award a win on an internal server error. |
| **SEC-11** | Add a hard cap on `active_bots` size and a per-IP rate limit on WebSocket connections. |
| **SEC-15** | Add `min`/`max` bounds: `num_games = max(1, min(int(data.get("num_games", 10)), 5000))` in the WebSocket tournament endpoint. |

### P2 — Improve

| ID | Action |
|---|---|
| **SEC-12** | Move token authentication from query string to first WebSocket message. |
| **SEC-7** | Require tokens at registration (generate and return one if not supplied); bots cannot be registered without a secret. |
| **SEC-13** | Add explicit `isinstance` checks on response payload fields before use in `RemoteBot`. |
| **SEC-2** | Document that `on_event` must never be wired to a player-facing channel without per-player filtering. |
| **SEC-5** | Track per-bot disconnect rates; flag bots exceeding a threshold (e.g., >5% of games) for review. |

### P3 — Monitor / Accepted

| ID | Action |
|---|---|
| **SEC-3** | By design — document in DEVELOPERS.md that bots are encouraged to use peg history strategically. |
| **SEC-4** | By design — scores are public in cribbage. No action required. |
| **SEC-10** | Consider identity-based (`is`) card validation in the engine as defense-in-depth against future local bot implementations. |
| **SEC-14** | Accepted risk — deliberate self-forfeit causes immediate loss; not a meaningful attack vector. |

---

## Change Log

| Date | Author | Change |
|---|---|---|
| 2026-05-15 | Reviewer Agent | Initial security review created |
| 2026-05-15 | Reviewer Agent | Revised per user comments: SEC-3/SEC-14 closed as accepted/by-design; SEC-5 policy updated to keep heavy punishment as deterrent; SEC-8 expanded with three runtime integrity implementation options; SEC-15 cap updated to 5000; SEC-1 clarified that filtering does not affect bot move-making functionality |
