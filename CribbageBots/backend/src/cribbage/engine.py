import inspect
import queue
import random
import threading
import time
from typing import Dict, List, Tuple
from .models import Card, Deck, GameState, Phase, Rank
from .rules import get_legal_pegging_moves, score_hand, score_pegging
from .bot import CribbagePlayer
from .exceptions import IllegalMoveError, TimeoutError


PER_BOT_CPU_BUDGET_SECONDS = 0.050


# ── Introspection hardening ──────────────────────────────────────────
# Strip GameEngine frames from inspect.stack() so that even if a bot
# circumvents thread isolation, it cannot read engine locals.

_introspection_hardened = False

def _harden_introspection():
    global _introspection_hardened
    if _introspection_hardened:
        return

    _original_stack = inspect.stack

    def _hardened_stack(*args, **kwargs):
        frames = _original_stack(*args, **kwargs)
        return [
            fi for fi in frames
            if not (
                "self" in fi.frame.f_locals
                and fi.frame.f_locals["self"].__class__.__name__ == "GameEngine"
            )
            and "hands" not in fi.frame.f_locals
        ]

    inspect.stack = _hardened_stack
    _introspection_hardened = True


class GameEngine:
    def __init__(self, p1: CribbagePlayer, p2: CribbagePlayer, verbose: bool = True, on_event=None, manual_count: bool = False, enforce_time_limit: bool = True):
        self.players = {p1.player_id: p1, p2.player_id: p2}
        self.player_ids = list(self.players.keys())
        self.deck = Deck()
        
        # Randomly assign the first dealer/crib
        if random.choice([True, False]):
            dealer_id = p1.player_id
            non_dealer_id = p2.player_id
        else:
            dealer_id = p2.player_id
            non_dealer_id = p1.player_id
            
        self.state = GameState(dealer_id=dealer_id, non_dealer_id=non_dealer_id)
        self.verbose = verbose
        self.on_event = on_event
        self.manual_count = manual_count
        self.count_resume_event = threading.Event()
        self.winner = None
        self.end_reason = "Natural" # Default reason
        self.skunk = False
        self.game_log = []
        self.event_counter = 0
        self.enforce_time_limit = enforce_time_limit
        self.cpu_remaining = {p1.player_id: PER_BOT_CPU_BUDGET_SECONDS, p2.player_id: PER_BOT_CPU_BUDGET_SECONDS}
        _harden_introspection()

        # Start persistent worker threads for each player to reuse them across turns
        self.bot_queues = {}
        self.bot_threads = {}
        for pid in self.player_ids:
            q_in = queue.Queue()
            q_out = queue.Queue()
            self.bot_queues[pid] = (q_in, q_out)
            
            def _worker(pid_local=pid, qi=q_in, qo=q_out):
                while True:
                    task = qi.get()
                    if task is None:
                        break
                    method_name, args, kwargs = task
                    bot = self.players[pid_local]
                    method = getattr(bot, method_name)
                    t0 = time.thread_time()
                    try:
                        res = method(*args, **kwargs)
                        elapsed = time.thread_time() - t0
                        qo.put((res, None, elapsed))
                    except Exception as e:
                        elapsed = time.thread_time() - t0
                        qo.put((None, e, elapsed))
            
            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            self.bot_threads[pid] = t

    def _call_bot(self, player_id: str, method_name: str, *args, **kwargs):
        """Invoke a bot method in an isolated thread to prevent stack inspection.

        Bot code running inside the thread cannot walk the call stack to reach
        engine frames (hands, deck, scores, etc.) because those frames live on
        a different thread's stack.

        CPU time is measured per-thread via time.thread_time() for accuracy.
        """
        bot = self.players[player_id]
        if hasattr(self, "state") and hasattr(self.state, "scores"):
            bot.scores = dict(self.state.scores)
            
        is_remote = type(bot).__name__ == "RemoteBot"

        q_in, q_out = self.bot_queues[player_id]
        q_in.put((method_name, args, kwargs))

        try:
            res, err, elapsed = q_out.get(timeout=30.0 if is_remote else 5.0)
        except queue.Empty:
            raise TimeoutError(player_id, "Bot timed out (wall-clock limit)")

        if err is not None:
            raise err

        if self.enforce_time_limit and not is_remote:
            self.cpu_remaining[player_id] -= elapsed
            if self.cpu_remaining[player_id] < 0:
                used = PER_BOT_CPU_BUDGET_SECONDS - self.cpu_remaining[player_id]
                raise TimeoutError(
                    player_id,
                    f"Exceeded {PER_BOT_CPU_BUDGET_SECONDS*1000:.0f}ms CPU budget "
                    f"(used {used*1000:.1f}ms cumulative)"
                )
        return res, elapsed

    def log_event(self, event_type: str, player_id: str = None, message: str = "", data: dict = None):
        self.event_counter += 1
        if not self.verbose and not self.on_event:
            return
            
        event = {
            "id": self.event_counter - 1,
            "type": event_type,
            "player_id": player_id,
            "message": message,
            "data": data or {},
            "p1_score": self.state.scores.get(self.player_ids[0], 0),
            "p2_score": self.state.scores.get(self.player_ids[1], 0),
            "cut_card": str(self.state.cut_card) if self.state.cut_card else None,
            "current_count": self.state.current_count,
            "pegged_cards": [{"player_id": p["player_id"], "card": str(p["card"])} for p in self.state.pegged_cards]
        }
        if self.verbose:
            self.game_log.append(event)
        if self.on_event:
            self.on_event(event)

    def award_points(self, player_id: str, points: int, reason: str):
        if points > 0:
            self.state.add_score(player_id, points)
            score = self.state.scores[player_id]
            self.log_event("score", player_id, f"Scored {points} for {reason}", {"points": points, "reason": reason})
            if self.state.scores[player_id] >= 121 and not self.winner:
                self.winner = player_id
                self.end_reason = "reached 121 points"

    def cleanup(self):
        """Terminate the persistent bot worker threads."""
        if hasattr(self, "bot_queues"):
            for pid in list(self.bot_queues.keys()):
                q_in, q_out = self.bot_queues[pid]
                q_in.put(None)

    def play_game(self) -> Tuple[str, List[dict]]:
        try:
            p1_id, p2_id = self.player_ids
            self.state.scores = {p1_id: 0, p2_id: 0}

            for player in self.players.values():
                player.reset()

            self.log_event("game_start", message=f"Game started between {p1_id} and {p2_id}")

            while not self.winner:
                try:
                    self.play_round()
                except (IllegalMoveError, TimeoutError) as e:
                    # Correctly identify the offender and award the win to the opponent
                    offender = e.player_id
                    self.winner = p1_id if offender == p2_id else p2_id
                    self.end_reason = f"Forfeit: {e.message}"
                    self.log_event("forfeit", offender, f"{offender} forfeited: {e.message}")
                    break
                except Exception as e:
                    # Catch-all for unexpected internal engine errors
                    # We do NOT award a win on system errors to prevent bots from winning via crashes
                    self.winner = None
                    self.end_reason = f"System Error: {str(e)}"
                    self.log_event("forfeit", None, f"Unexpected internal error: {e}")
                    return None, self.game_log

                # Switch dealer
                self.state.dealer_id, self.state.non_dealer_id = self.state.non_dealer_id, self.state.dealer_id

            # Determine if it was a skunk
            loser_id = p1_id if self.winner == p2_id else p2_id
            if self.state.scores.get(loser_id, 0) <= 90:
                self.skunk = True

            self.log_event("game_over", self.winner, f"{self.winner} wins!", {"skunk": self.skunk})
            return self.winner, self.game_log
        finally:
            self.cleanup()

    def play_round(self):
        self.deck.reset()
        self.state.crib = []
        self.state.peg_history = []
        self.state.pegged_cards = []
        self.state.current_count = 0
        self.state.cut_card = None

        dealer = self.state.dealer_id
        non_dealer = self.state.non_dealer_id

        # 1. Deal
        self.state.phase = Phase.DEAL
        hands = {non_dealer: [], dealer: []}
        for _ in range(6):
            hands[non_dealer].extend(self.deck.deal(1))
            hands[dealer].extend(self.deck.deal(1))

        self.log_event("deal", None, "Dealt 6 cards to each player")

        # 2. Discard to crib
        self.state.phase = Phase.DISCARD
        for pid in [non_dealer, dealer]:
            # Pass a copy of the hand to prevent bots from mutating engine state
            discards, elapsed = self._call_bot(pid, "discard", list(hands[pid]), is_dealer=(pid == dealer))

            if not all(any(c is h for h in hands[pid]) for c in discards) or len(discards) != 2 or len(set(discards)) != 2:
                raise IllegalMoveError(pid, f"Invalid discard: {discards}")

            self.state.crib.extend(discards)
            for card in discards:
                hands[pid].remove(card)
            self.log_event(
                "discard", pid,
                f"{pid} discarded 2 cards. ({elapsed*1000:.2f}ms, {self.cpu_remaining[pid]*1000:.2f}ms remaining)",
                {"elapsed_ms": elapsed * 1000, "cpu_remaining_ms": self.cpu_remaining[pid] * 1000},
            )

        # 3. Cut
        self.state.phase = Phase.CUT
        self.state.cut_card = self.deck.deal(1)[0]
        self.log_event("cut", message=f"Cut card is {self.state.cut_card}", data={"card": str(self.state.cut_card)})

        if self.state.cut_card.rank == Rank.JACK:
            self.award_points(dealer, 2, "His Heels")
            if self.winner:
                return

        # 4. Pegging
        self.state.phase = Phase.PEGGING
        pegging_hands = {k: v.copy() for k, v in hands.items()}
        self.run_pegging_phase(pegging_hands, non_dealer, dealer)
        if self.winner:
            return

        # 5. Counting
        self.state.phase = Phase.COUNTING

        # Non-dealer hand first
        pts_nd, bd_nd = score_hand(hands[non_dealer], self.state.cut_card, is_crib=False)
        if self.manual_count:
            self.log_event("count_hand_request", non_dealer, 
                           message=f"Count {non_dealer}'s hand",
                           data={"hand": [str(c) for c in hands[non_dealer]], "is_crib": False, "points": pts_nd, "breakdown": bd_nd})
            self.count_resume_event.wait()
            self.count_resume_event.clear()

        self.award_points(non_dealer, pts_nd, f"Hand ({bd_nd})")
        if self.winner:
            return

        # Dealer hand second
        pts_d, bd_d = score_hand(hands[dealer], self.state.cut_card, is_crib=False)
        if self.manual_count:
            self.log_event("count_hand_request", dealer, 
                           message=f"Count {dealer}'s hand",
                           data={"hand": [str(c) for c in hands[dealer]], "is_crib": False, "points": pts_d, "breakdown": bd_d})
            self.count_resume_event.wait()
            self.count_resume_event.clear()

        self.award_points(dealer, pts_d, f"Hand ({bd_d})")
        if self.winner:
            return

        # Crib last (dealer scores)
        pts_c, bd_c = score_hand(self.state.crib, self.state.cut_card, is_crib=True)
        if self.manual_count:
            self.log_event("count_hand_request", dealer, 
                           message=f"Count the crib",
                           data={"hand": [str(c) for c in self.state.crib], "is_crib": True, "points": pts_c, "breakdown": bd_c})
            self.count_resume_event.wait()
            self.count_resume_event.clear()

        self.award_points(dealer, pts_c, f"Crib ({bd_c})")

    def run_pegging_phase(self, hands: Dict[str, List[Card]], non_dealer: str, dealer: str, max_iterations: int = None):
        def other(pid: str) -> str:
            """Always return the correct opponent — no stale variable issues."""
            return dealer if pid == non_dealer else non_dealer

        current_player = non_dealer
        last_to_play = None
        passed = set()
        just_hit_31 = False

        while hands[non_dealer] or hands[dealer]:
            # Mark empty-handed players as automatically passed for this sequence
            if not hands[non_dealer]:
                passed.add(non_dealer)
            if not hands[dealer]:
                passed.add(dealer)

            if len(passed) == 2:
                # Both passed: award "Go" if we didn't just hit an exact 31
                if not just_hit_31 and last_to_play is not None:
                    self.award_points(last_to_play, 1, "Go")
                    if self.winner:
                        return
                # Reset the pegging sequence
                self.state.current_count = 0
                self.state.peg_history = []
                just_hit_31 = False
                passed.clear()
                # The player who did NOT play last starts the new sequence
                # Fallback if last_to_play is None (e.g. both pass immediately): use non_dealer
                next_player = other(last_to_play) if last_to_play is not None else non_dealer
                # If that player has no cards either, the other one must go
                if not hands[next_player]:
                    next_player = other(next_player)
                current_player = next_player
                continue

            # Skip current player if they already passed or are out of cards
            if not hands[current_player] or current_player in passed:
                current_player = other(current_player)
                continue

            if max_iterations is not None:
                max_iterations -= 1
                if max_iterations < 0:
                    return

            legal_moves = get_legal_pegging_moves(hands[current_player], self.state.current_count)

            played_card, elapsed = self._call_bot(
                current_player,
                "peg",
                hands[current_player].copy(),
                self.state.peg_history.copy(),
                self.state.current_count,
            )
            timing_suffix = f"({elapsed*1000:.2f}ms, {self.cpu_remaining[current_player]*1000:.2f}ms remaining)"
            timing_data = {"elapsed_ms": elapsed * 1000, "cpu_remaining_ms": self.cpu_remaining[current_player] * 1000}

            if played_card is None:
                if legal_moves:
                    raise IllegalMoveError(current_player, "Passed when legal moves exist")
                passed.add(current_player)
                self.log_event("peg_go", current_player, f"{current_player} says Go. {timing_suffix}", timing_data)
                current_player = other(current_player)
            else:
                if not any(played_card is m for m in legal_moves):
                    raise IllegalMoveError(
                        current_player,
                        f"Played {played_card} (count {self.state.current_count} + {played_card.value} = {self.state.current_count + played_card.value} > 31)"
                    )

                hands[current_player].remove(played_card)
                self.state.current_count += played_card.value
                self.state.peg_history.append(played_card)
                self.state.pegged_cards.append({"player_id": current_player, "card": played_card})
                last_to_play = current_player
                just_hit_31 = False

                self.log_event(
                    "peg_play", current_player,
                    f"{current_player} played {played_card} (Count: {self.state.current_count}) {timing_suffix}",
                    {"card": str(played_card), "count": self.state.current_count, **timing_data}
                )

                pts, bd = score_pegging(self.state.peg_history)
                if pts > 0:
                    self.award_points(current_player, pts, f"Pegging ({bd})")
                    if self.winner:
                        return

                if self.state.current_count == 31:
                    just_hit_31 = True
                    self.state.current_count = 0
                    self.state.peg_history = []
                    passed.clear()
                    current_player = other(current_player)
                else:
                    current_player = other(current_player)

        # Award "Last Card" (1 pt) only if the final count wasn't exactly 31
        if last_to_play and self.state.current_count > 0:
            self.award_points(last_to_play, 1, "Last Card")

