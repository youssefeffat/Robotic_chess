from enum import Enum

class GameMode(Enum):
    HUMAN_VS_BOT = "human_vs_bot"
    BOT_VS_BOT = "bot_vs_bot"

class Color(Enum):
    WHITE = "white"
    BLACK = "black"

class LichessParams(Enum):
    BOT1_USERNAME = "bot_polytech"
    BOT2_USERNAME = "youssefeffat"
    CLOCK_LIMIT = 600
