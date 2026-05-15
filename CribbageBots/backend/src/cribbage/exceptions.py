class CribbageError(Exception):
    def __init__(self, player_id: str, message: str):
        self.player_id = player_id
        self.message = message
        super().__init__(f"{player_id}: {message}")

class IllegalMoveError(CribbageError):
    pass

class TimeoutError(CribbageError):
    pass
