from core.interfaces import IGameEngine
from api.UserInterface import UserInterface
from api.stockfish_api import StockfishEngine
from hardware.camera import Camera
from hardware.robotic_arm import RoboticArm
from hardware.button import Button
from core.enums import GameMode, Color

from game.game import Game

# GameEngine class is responsible for managing the game state and orchestrating the interactions between the different components of the system.
# It implements the IGameEngine interface, which defines the methods that need to be implemented by a game engine.
# The GameEngine class uses the UserInterface, StockfishEngine, Camera, RoboticArm, Button, and Game classes to interact with the user interface, chess engine, camera, robotic arm, button, and game logic, respectively.
# The initialize_game method initializes the game engine with the specified mode, color, difficulty, and FEN string.
# The start_game method starts the game by creating the game interface and calling the start_game method of the Game class.
# The handle_human_move method handles the human player's move by waiting for the human player to make a move and then applying the move to the game state.
# The wait_for_human_move method blocks until the human player makes a move by pressing the button.
# The apply_human_move method applies the human player's move to the game state and updates the user interface.
# The handle_bot_move method handles the bot player's move by calculating the best move using the Stockfish engine, executing the move with the robotic arm, and updating the user interface.
# The verify_robot_move method verifies that the move executed by the robotic arm is valid by comparing the expected FEN string with the actual FEN string captured by the camera.
# The verify_move method compares two FEN strings to determine if they are equal.
# The fen_after_move method calculates the FEN string after a move is applied to the current FEN string.
# The shutdown method shuts down the game engine by closing the user interface and the game.

#TODO: managing the clock orchestration 

class GameEngine(IGameEngine):
    def __init__(self, user_interface: UserInterface):
        self.user_interface = user_interface
        self.stockfish = StockfishEngine()
        self.camera = Camera()
        self.robot = RoboticArm()
        self.game = Game()
        self.button = Button(self.robot)  

    def initialize_game(self, mode: GameMode, color: Color, difficulty: int):
        print("Initializing game engine... mode:", mode, "color:", color, "difficulty:", difficulty)
        self.stockfish.initialize_engine(difficulty)
        self.camera.initialize_camera()
        self.robot.initialize_robot()
        self.button.initialize_button()  
        self.game.initialize_game(self, mode, color, difficulty, self.camera.get_fen())

    def start_game(self):
        # self.user_interface.create_game(self.camera.get_fen())
        self.game.start_game()

    def handle_human_move(self, move: str):
        self.wait_for_human_move()
        self.apply_human_move(move)

    def wait_for_human_move(self):
        ## TODO : try and catch to be added
        if self.button:
            self.button.human_turn_finished()  # Block until the button is pressed

    def apply_human_move(self, move: str):
        self.game.set_fen(self.camera.get_fen())
        self.user_interface.apply_move(move)
        if self.game.is_game_over():
            self.shutdown()
        print(f"Human moved: {move}")
        print(f"Current game status: {self.game.get_game_state()}")

    def handle_bot_move(self) -> str:
        move = self.stockfish.calculate_best_move(self.game.get_fen())
        self.robot.execute_move(move)
        self.verify_robot_move(move)
        self.user_interface.apply_move(move)
        if self.game.is_game_over():
            self.shutdown()
        print(f"Bot moved: {move}")

    def verify_robot_move(self, move: str):
        expected_fen = self.fen_after_move(self.game.get_fen(), move)
        fen_after_robot = self.camera.get_fen()
        if not self.verify_move(expected_fen, fen_after_robot):
            raise Exception("Invalid move detected")
        self.game.set_fen(fen_after_robot)

    def verify_move(self, expected_fen: str, actual_fen: str) -> bool:
        return expected_fen == actual_fen

    def fen_after_move(self, fen: str, move: str) -> str:
        return self.stockfish.get_fen_after_move(fen, move)

    def shutdown(self):
        self.user_interface.shutdown()
        self.game.close_game()
        print("Game engine shut down.")