from enum import Enum

class GameMode(Enum):
    HUMAN_VS_BOT = "human_vs_bot"
    BOT_VS_BOT = "bot_vs_bot"

class Color(Enum):
    WHITE = "white"
    BLACK = "black"