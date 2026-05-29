from .random_bot import RandomBot
from .greedy_bot import GreedyBot
from .remote_bot import RemoteBot
from .gemini_flash_simple_bot import GeminiFlashSimpleBot
from .scaredy_bot import ScaredyBot
from .joren_bot_v0 import JorenBotV0
from .leifv1_bot import LeifV1Bot
from .leifv2_bot import LeifV2Bot

BOT_REGISTRY = {
    "random": {"class": RandomBot, "label": "RandomBot"},
    "greedy": {"class": GreedyBot, "label": "GreedyBot"},
    "gemini_flash": {"class": GeminiFlashSimpleBot, "label": "FlashBot"},
    "scaredy": {"class": ScaredyBot, "label": "ScaredyBot"},
    "joren_v0": {"class": JorenBotV0, "label": "JorenBot_v0"},
    "leifv1": {"class": LeifV1Bot, "label": "LeifV1Bot"},
    "leifv2": {"class": LeifV2Bot, "label": "LeifV2Bot"},
}

__all__ = ["RandomBot", "GreedyBot", "RemoteBot", "GeminiFlashSimpleBot", "ScaredyBot", "JorenBotV0", "LeifV1Bot", "LeifV2Bot", "BOT_REGISTRY"]
