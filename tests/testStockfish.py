from stockfish_api import StockfishEngine
import os
from dotenv import load_dotenv

load_dotenv()
# Ensure STOCKFISH_PATH is set in environment variables
if "STOCKFISH_PATH" not in os.environ:
    raise EnvironmentError("STOCKFISH_PATH must be set in environment variables.")

# Create an instance of the StockfishEngine
engine = StockfishEngine()

print("Testing StockfishEngine initialization...")
try:
    engine.initialize_engine(difficulty=10)  # Initialize with difficulty level 10
    print("Engine initialized successfully.")
except ValueError as e:
    print(f"Initialization failed: {e}")

print("\nTesting calculate_best_move...")
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
try:
    best_move = engine.calculate_best_move(fen)
    print(f"Best move for FEN '{fen}': {best_move}")
except RuntimeError as e:
    print(f"Error calculating best move: {e}")

print("\nTesting check_is_game_over...")
fen_not_over = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
fen_checkmate = "8/8/8/8/8/8/3K4/3k4 b - - 0 1"

try:
    print(f"Is game over (standard position)? {engine.check_is_game_over(fen_not_over)}")  # Should be False
    print(f"Is game over (checkmate position)? {engine.check_is_game_over(fen_checkmate)}")  # Should be True
except RuntimeError as e:
    print(f"Error checking game-over state: {e}")