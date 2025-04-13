from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

# Enums for Game Mode and Player Color
class GameMode(Enum):
    HUMAN_VS_BOT = "human_vs_bot"
    BOT_VS_BOT = "bot_vs_bot"

class Color(Enum):
    WHITE = "white"
    BLACK = "black"

# Interface for the Game Engine
class IGameEngine(ABC):
    @abstractmethod
    def initialize_game(self, mode: GameMode, color: Color, difficulty: int, fen: str) -> None:
        """Initialize the game with the given parameters."""
        pass

    @abstractmethod
    def start_game(self) -> None:
        """Start the game workflow."""
        pass

    @abstractmethod
    def handle_human_move(self, move: str) -> None:
        """Handle a human player's move."""
        pass

    @abstractmethod
    def handle_bot_move(self) -> str:
        """Calculate and execute the bot's move."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shut down the game engine and clean up resources."""
        pass

# Interface for the Button Module
class IButtonModule(ABC):
    @abstractmethod
    def initialize_button(self) -> None:
        """Initialize the button module."""
        pass

    @abstractmethod
    def human_turn_finished(self) -> None:
        """Block until the human player's turn is finished."""
        pass

# Interface for the Stockfish Engine Module
class IStockfishEngine(ABC):
    @abstractmethod
    def initialize_engine(self, difficulty: int) -> None:
        """Initialize the Stockfish engine with the given difficulty level."""
        pass

    @abstractmethod
    def calculate_best_move(self, fen: str) -> str:
        """Calculate the best move based on the given FEN string."""
        pass

    @abstractmethod
    def check_is_game_over(self, fen: str) -> bool:
        """Check if the game is over."""
        pass


# Interface for the Camera Module
class ICameraModule(ABC):
    @abstractmethod
    def initialize_camera(self) -> None:
        """Initialize the camera module."""
        pass

    @abstractmethod
    def get_fen(self) -> str:
        """Capture the current board state and return it as a FEN string."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shut down the camera module."""
        pass
    
# Interface for the Robotic Arm Module
class IRoboticArmModule(ABC):
    @abstractmethod
    def initialize_robot(self) -> None:
        """Initialize the robotic arm module."""
        pass

    @abstractmethod
    def execute_move(self, move: str) -> None:
        """Execute the given move on the physical chessboard."""
        pass



# Interface for the User Interface (Lichess API Integration)
class IUserInterface(ABC):
    @abstractmethod
    def create_game(self) -> None:
        """Create a new game session (e.g., on Lichess)."""
        pass

    @abstractmethod
    def apply_move(self, move: str) -> None:
        """Apply the given move to the game session."""
        pass

    @abstractmethod
    def is_game_over(self) -> bool:
        """Check if the game is over. True/False"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shut down the user interface / finish the session """
        pass