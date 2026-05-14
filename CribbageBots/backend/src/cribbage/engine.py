from typing import Dict, List, Tuple
from .models import Card, Deck, GameState, Phase, Rank
from .rules import get_legal_pegging_moves, score_hand, score_pegging
from .bot import CribbagePlayer


class IllegalMoveError(Exception):
    def __init__(self, player_id: str, message: str):
        self.player_id = player_id
        super().__init__(f"{player_id}: {message}")


class GameEngine:
    def __init__(self, p1: CribbagePlayer, p2: CribbagePlayer):
        self.players = {p1.player_id: p1, p2.player_id: p2}
        self.state = GameState(dealer_id=p1.player_id, non_dealer_id=p2.player_id)
        self.deck = Deck()
        self.game_log = []
        self.winner = None
        self.skunk = False

    def log_event(self, event_type: str, player_id: str = None, message: str = "", data: dict = None):
        event = {
            "type": event_type,
            "player_id": player_id,
            "message": message,
            "data": data or {},
            "p1_score": self.state.scores.get(list(self.players.keys())[0], 0),
            "p2_score": self.state.scores.get(list(self.players.keys())[1], 0)
        }
        self.game_log.append(event)

    def award_points(self, player_id: str, points: int, reason: str):
        if points > 0:
            self.state.add_score(player_id, points)
            self.log_event("score", player_id, f"Scored {points} for {reason}", {"points": points, "reason": reason})
            if self.state.scores[player_id] >= 121 and not self.winner:
                self.winner = player_id

    def play_game(self) -> Tuple[str, List[dict]]:
        p1_id, p2_id = list(self.players.keys())
        self.state.scores = {p1_id: 0, p2_id: 0}

        self.log_event("game_start", message=f"Game started between {p1_id} and {p2_id}")

        while not self.winner:
            try:
                self.play_round()
            except IllegalMoveError as e:
                # Use the structured player_id from the exception directly — no hacky string splitting
                offender = e.player_id
                self.winner = p1_id if offender == p2_id else p2_id
                self.log_event("forfeit", offender, f"{offender} forfeited: {e}")
                break
            except (ValueError, Exception) as e:
                # Catch unhandled errors from RemoteBots (ValueError) and others,
                # treat as a forfeit by the last active player (fallback to p1 wins).
                self.winner = p1_id
                self.log_event("forfeit", None, f"Unexpected error during game: {e}")
                break

            # Switch dealer
            self.state.dealer_id, self.state.non_dealer_id = self.state.non_dealer_id, self.state.dealer_id

        # Determine if it was a skunk
        loser_id = p1_id if self.winner == p2_id else p2_id
        if self.state.scores.get(loser_id, 0) <= 90:
            self.skunk = True

        self.log_event("game_over", self.winner, f"{self.winner} wins!", {"skunk": self.skunk})
        return self.winner, self.game_log

    def play_round(self):
        self.deck.reset()
        self.state.crib = []
        self.state.peg_history = []
        self.state.current_count = 0

        dealer = self.state.dealer_id
        non_dealer = self.state.non_dealer_id

        # 1. Deal
        self.state.phase = Phase.DEAL
        hands = {
            non_dealer: self.deck.deal(6),
            dealer: self.deck.deal(6)
        }
        self.log_event("deal", message=f"Dealt 6 cards each. {dealer} is dealer.")

        # 2. Discard
        self.state.phase = Phase.DISCARD
        for pid in [non_dealer, dealer]:
            bot = self.players[pid]
            discards = bot.discard(hands[pid].copy(), is_dealer=(pid == dealer))

            # Validate discards — must be exactly 2 distinct cards from the hand
            if (len(discards) != 2
                    or discards[0] not in hands[pid]
                    or discards[1] not in hands[pid]
                    or discards[0] == discards[1]):
                raise IllegalMoveError(pid, f"Invalid discard {discards}")

            hands[pid].remove(discards[0])
            hands[pid].remove(discards[1])
            self.state.crib.extend(discards)
            self.log_event("discard", pid, f"{pid} discarded 2 cards.")

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
        pts, breakdown = score_hand(hands[non_dealer], self.state.cut_card, is_crib=False)
        self.award_points(non_dealer, pts, f"Hand ({breakdown})")
        if self.winner:
            return

        # Dealer hand
        pts, breakdown = score_hand(hands[dealer], self.state.cut_card, is_crib=False)
        self.award_points(dealer, pts, f"Hand ({breakdown})")
        if self.winner:
            return

        # Crib (always goes to dealer)
        pts, breakdown = score_hand(self.state.crib, self.state.cut_card, is_crib=True)
        self.award_points(dealer, pts, f"Crib ({breakdown})")

    def run_pegging_phase(self, hands: Dict[str, List[Card]], non_dealer: str, dealer: str):
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
                next_player = other(last_to_play) if last_to_play else non_dealer
                # If that player has no cards either, the other one must go
                if not hands[next_player]:
                    next_player = other(next_player)
                current_player = next_player
                continue

            # Skip current player if they already passed or are out of cards
            if not hands[current_player] or current_player in passed:
                current_player = other(current_player)
                continue

            bot = self.players[current_player]
            legal_moves = get_legal_pegging_moves(hands[current_player], self.state.current_count)

            played_card = bot.peg(
                hands[current_player].copy(),
                self.state.peg_history.copy(),
                self.state.current_count
            )

            if played_card is None:
                if legal_moves:
                    raise IllegalMoveError(current_player, "Passed when legal moves exist")
                passed.add(current_player)
                self.log_event("peg_go", current_player, f"{current_player} says Go.")
                current_player = other(current_player)
            else:
                if played_card not in legal_moves:
                    raise IllegalMoveError(
                        current_player,
                        f"Played {played_card} (count {self.state.current_count} + {played_card.value} = {self.state.current_count + played_card.value} > 31)"
                    )

                hands[current_player].remove(played_card)
                self.state.current_count += played_card.value
                self.state.peg_history.append(played_card)
                last_to_play = current_player
                just_hit_31 = False

                self.log_event(
                    "peg_play", current_player,
                    f"{current_player} played {played_card} (Count: {self.state.current_count})",
                    {"card": str(played_card), "count": self.state.current_count}
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

