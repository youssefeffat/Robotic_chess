from stockfish import Stockfish  # Import the Stockfish engine
from core.interfaces import IStockfishEngine
from typing import Optional
import os
from dotenv import load_dotenv

class StockfishEngine(IStockfishEngine):
    
    def __init__(self):
        """
        Initialize the StockfishEngine with the path to the Stockfish executable.
        """
        load_dotenv()
        STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")
        if not STOCKFISH_PATH:
            raise EnvironmentError("STOCKFISH_PATH not found in environment variables.")
        
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
    
