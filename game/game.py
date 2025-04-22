from core.enums import GameMode, Color
# from engine.game_engine import GameEngine  # Import GameEngine from the appropriate module

class Game:
    default_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    default_difficulty = 10
    default_mode = GameMode.HUMAN_VS_BOT.value
    default_color = Color.WHITE.value

    def __init__(self):
        self.engine = None
        self.mode = None
        self.color = None
        self.difficulty = None
        self.fen = None

    def initialize_game(self, engine, mode: GameMode = default_mode, color: Color = default_color, difficulty: int = default_difficulty, fen: str = default_fen):
        print("Initializing game... mode:", mode, "color:", color, "difficulty:", difficulty)
        self.engine = engine
        self.mode = mode
        self.color = color
        self.difficulty = difficulty
        self.fen = fen

    def set_fen(self, fen: str):
        self.fen = fen

    def get_fen(self) -> str:
        return self.fen

    def start_game(self):
        print("Starting game...", "mode:", self.mode, "color:", self.color, "difficulty:", self.difficulty)
        if self.mode == GameMode.HUMAN_VS_BOT.value:
            self.start_human_vs_bot_game()
        elif self.mode == GameMode.BOT_VS_BOT.value:
            self.start_bot_vs_bot_game()
        else:
            raise ValueError("Invalid game mode")

    def start_human_vs_bot_game(self):
        if self.color == Color.WHITE.value:
            # TODO : potential issue 
            while not self.is_game_over():
                self.engine.handle_human_move("e2e4")
                if self.is_game_over():
                    break
                self.engine.handle_bot_move()
        elif self.color == Color.BLACK.value:
            while not self.is_game_over():
                self.engine.handle_bot_move()
                if self.is_game_over():
                    break
                self.engine.handle_human_move()
        else:
            raise ValueError("Invalid player color")

    def start_bot_vs_bot_game(self):
        while not self.is_game_over():
            self.engine.handle_bot_move()

    def is_game_over(self) -> bool:
        # Example implementation (replace with actual logic)
        # return self.engine.is_game_over()
        return False

    def get_game_state(self) -> str:
        # Example implementation (replace with actual logic)
        # return self.engine.get_game_state()
        return "Game is ongoing"
    
    def close_game(self):
        # Example implementation (replace with actual logic)
        pass
    
if __name__ == "__main__":
    game = Game()
    game.initialize_game()
    game.start_game()