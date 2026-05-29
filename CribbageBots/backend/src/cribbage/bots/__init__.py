from .random_bot import RandomBot
from .greedy_bot import GreedyBot
from .remote_bot import RemoteBot
from .gemini_flash_simple_bot import GeminiFlashSimpleBot
from .scaredy_bot import ScaredyBot
from .leifv1_bot import LeifV1Bot

BOT_REGISTRY = {
    "random": {"class": RandomBot, "label": "RandomBot"},
    "greedy": {"class": GreedyBot, "label": "GreedyBot"},
    "gemini_flash": {"class": GeminiFlashSimpleBot, "label": "FlashBot"},
    "scaredy": {"class": ScaredyBot, "label": "ScaredyBot"},
    "leifv1": {"class": LeifV1Bot, "label": "LeifV1Bot"},
}

__all__ = ["RandomBot", "GreedyBot", "RemoteBot", "GeminiFlashSimpleBot", "ScaredyBot", "LeifV1Bot", "BOT_REGISTRY"]