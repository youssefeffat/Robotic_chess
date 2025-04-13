from stockfish import Stockfish  # Import the Stockfish engine
# from core.interfaces import IStockfishEngine
from typing import Optional
import os
from dotenv import load_dotenv

class StockfishEngine():
    
    def __init__(self):
        """
        Initialize the StockfishEngine with the path to the Stockfish executable.
        """
        load_dotenv()
        
        if os.name == 'nt':  # Windows
            STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")
            if not STOCKFISH_PATH:
                raise EnvironmentError("STOCKFISH_PATH not found in environment variables.")
        else:  # Linux or other OS
            STOCKFISH_PATH = "/usr/games/stockfish" # To install : sudo apt-get install stockfish
        
        self.stockfish = Stockfish(STOCKFISH_PATH)
        self.initialized = False

    def initialize_engine(self, difficulty: int) -> None:
        """
        Initialize the Stockfish engine with the given difficulty level.
        :param difficulty: Skill level (1-20).
        """
        if not 1 <= difficulty <= 20:
            raise ValueError("Difficulty must be between 1 and 20.")
        
        self.stockfish.set_skill_level(difficulty)
        self.stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        self.initialized = True

    def calculate_best_move(self, fen: str) -> str:
        """
        Calculate the best move based on the given FEN string.
        :param fen: Current board state in FEN format.
        :return: Best move as a UCI string (e.g., "e2e4").
        """
        if not self.initialized:
            raise RuntimeError("Stockfish engine is not initialized. Call initialize_engine() first.")

        self.stockfish.set_fen_position(fen)
        return self.stockfish.get_best_move()

    def check_is_game_over(self, fen: str) -> bool:
        """
        Check if the game is over based on the given FEN string.
        :param fen: Current board state in FEN format.
        :return: True if the game is over, False otherwise.
        """
        if not self.initialized:
            raise RuntimeError("Stockfish engine is not initialized. Call initialize_engine() first.")

        self.stockfish.set_fen_position(fen)

        # Simulate checking for checkmate or stalemate
        info = self.stockfish.get_evaluation()
        if info.get("type") == "mate" or info.get("value") == 0:
            return True  # Checkmate or stalemate

        return False  # Game is not over
    
if __name__ == "__main__":
    engine = StockfishEngine()
    engine.initialize_engine(difficulty=5)
    
    # Initial board state
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print("Initial board state:")
    print(engine.stockfish.get_board_visual(fen))
    
    # Make a move and display the board
    best_move = engine.calculate_best_move(fen)
    print(f"Best move: {best_move}")
    engine.stockfish.make_moves_from_current_position([best_move])
    print("Board state after best move:")
    print(engine.stockfish.get_board_visual())