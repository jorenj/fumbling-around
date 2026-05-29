from .random_bot import RandomBot
from .greedy_bot import GreedyBot
from .remote_bot import RemoteBot
from .gemini_flash_simple_bot import GeminiFlashSimpleBot
from .scaredy_bot import ScaredyBot
from .joren_bot_v0 import JorenBotV0

BOT_REGISTRY = {
    "random": {"class": RandomBot, "label": "RandomBot"},
    "greedy": {"class": GreedyBot, "label": "GreedyBot"},
    "gemini_flash": {"class": GeminiFlashSimpleBot, "label": "FlashBot"},
    "scaredy": {"class": ScaredyBot, "label": "ScaredyBot"},
    "joren_v0": {"class": JorenBotV0, "label": "JorenBot_v0"},
}

__all__ = ["RandomBot", "GreedyBot", "RemoteBot", "GeminiFlashSimpleBot", "ScaredyBot", "JorenBotV0", "BOT_REGISTRY"]