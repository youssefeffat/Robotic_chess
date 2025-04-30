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
        # self.game = Game()
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

    def get_move_between_fens(self, fen1, fen2):
        board1 = self.fen_to_board(fen1)
        board2 = self.fen_to_board(fen2)
        moving_color = fen1.split()[1].lower()

        sources = []
        destinations = []

        for i in range(8):
            for j in range(8):
                square = f"{chr(97 + j)}{8 - i}"
                if board1[i][j] != '.' and board1[i][j].lower() == moving_color:
                    if board1[i][j] != board2[i][j]:
                        sources.append(square)
                if board2[i][j] != '.' and board2[i][j].lower() == moving_color:
                    if board1[i][j] != board2[i][j]:
                        destinations.append(square)

        if len(sources) == 1 and len(destinations) == 1:
            from_sq, to_sq = sources[0], destinations[0]
            # Promotion check
            if self.fen_to_board(fen1)[8 - int(from_sq[1])][ord(from_sq[0]) - 97].lower() == 'p':
                if (moving_color == 'w' and to_sq[1] == '8') or (moving_color == 'b' and to_sq[1] == '1'):
                    return f"{from_sq}{to_sq}{board2[8 - int(to_sq[1])][ord(to_sq[0]) - 97].upper()}"
            # Castling check
            if self.fen_to_board(fen1)[8 - int(from_sq[1])][ord(from_sq[0]) - 97].lower() == 'k':
                if abs(ord(from_sq[0]) - ord(to_sq[0])) == 2:
                    return "O-O-O" if ord(to_sq[0]) < ord(from_sq[0]) else "O-O"
            # En passant check
            if (self.fen_to_board(fen1)[8 - int(to_sq[1])][ord(to_sq[0]) - 97] == '.' and 
                abs(ord(from_sq[0]) - ord(to_sq[0])) == 1 and
                self.fen_to_board(fen1)[8 - int(from_sq[1])][ord(from_sq[0]) - 97].lower() == 'p'):
                return f"{from_sq}x{to_sq}"
            # Normal move/capture
            if self.fen_to_board(fen1)[8 - int(to_sq[1])][ord(to_sq[0]) - 97] != '.':
                return f"{from_sq}x{to_sq}"
            return f"{from_sq}{to_sq}"
        elif len(sources) == 2 and len(destinations) == 2:
            return "O-O" if sources[0][0] < sources[1][0] else "O-O-O"
        return "Unknown move"
    
    @staticmethod
    def fen_to_board(fen):
        board = []
        for rank in fen.split()[0].split('/'):
            expanded = []
            for c in rank:
                if c.isdigit():
                    expanded.extend(['.'] * int(c))
                else:
                    expanded.append(c)
            board.append(expanded)
        return board

    def handle_bot_move(self) -> str:
        move = self.stockfish.calculate_best_move(self.game.get_fen())
        self.robot.execute_move(move)
        self.verify_robot_move(move)
        self.user_interface.apply_move(move)
        if self.game.is_game_over():
            self.shutdown()
        print(f"Bot moved: {move}")

    # def verify_robot_move(self, move: str):
    #     # expected_fen = self.fen_after_move(self.game.get_fen(), move)
    #     # fen_after_robot = self.camera.get_fen()
    #     # if not self.verify_move(expected_fen, fen_after_robot):
    #     #     raise Exception("Invalid move detected")
    #     # self.game.set_fen(fen_after_robot)
    #     print("Verifying robot move")

    # def verify_move(self, expected_fen: str, actual_fen: str) -> bool:
    #     # return expected_fen == actual_fen   
    #     print("Verifying robot move")

    # def fen_after_move(self, fen: str, move: str) -> str:
    #     # return self.stockfish.get_fen_after_move(fen, move)
    #     print("Getting fen after move")

    def shutdown(self):
        self.user_interface.shutdown()
        # self.game.close_game()
        print("Game engine shut down.")