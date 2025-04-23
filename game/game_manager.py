from engine.game_engine import GameEngine  # Import GameEngine from the appropriate module
from game.game import Game
from api.UserInterface import UserInterface
from core.enums import GameMode, Color

class GameManager:
    def __init__(self, user_interface: UserInterface):
        self.engine = GameEngine(user_interface)
        self.game = Game()

    def initialize_game(self, mode: GameMode, color: Color , difficulty: int ):
        self.game.initialize_game(mode, color, difficulty, self.engine.camera.get_fen())
        self.engine.initialize_game(mode,color, difficulty)

    def start_game(self):
        # self.user_interface.create_game(self.camera.get_fen())
        self.game.start_game()

    def start_human_vs_bot_game(self):
        if self.game.color == Color.WHITE.value:
            # TODO : potential issue 
            while not self.game.is_game_over():
                self.engine.handle_human_move("e2e4")
                if self.game.is_game_over():
                    break
                self.engine.handle_bot_move()
        elif self.game.color == Color.BLACK.value:
            while not self.is_game_over():
                self.engine.handle_bot_move()
                if self.game.is_game_over():
                    break
                self.engine.handle_human_move()
        else:
            raise ValueError("Invalid player color")

    def start_bot_vs_bot_game(self):
        while not self.game.is_game_over():
            self.engine.handle_bot_move()

    def handle_human_move(self, move: str):
        self.wait_for_human_move()
        self.apply_human_move(move)

    def wait_for_human_move(self):
        ## TODO : try and catch to be added
        if self.engine.button:
            self.engine.button.human_turn_finished()  # Block until the button is pressed

    def apply_human_move(self, move: str):
        self.game.set_fen(self.camera.get_fen())
        self.engine.user_interface.apply_move(move)
        if self.game.is_game_over():
            self.shutdown() # self.engine.shutdown() ??
        print(f"Human moved: {move}")
        print(f"Current game status: {self.game.get_game_state()}")

    def handle_bot_move(self) -> str:
        move = self.engine.stockfish.calculate_best_move(self.game.get_fen())
        self.engine.robot.execute_move(move)
        self.verify_robot_move(move)
        #TODO : case if the humain move is not valid (for camera)
        #TODO : case if the humain move is not valid
        self.engine.user_interface.apply_move(move)
        if self.game.is_game_over():
            self.shutdown() # self.engine.shutdown() ??
        print(f"Bot moved: {move}")

    def verify_robot_move(self, move: str):
        expected_fen = self.engine.fen_after_move(self.game.get_fen(), move)
        fen_after_robot = self.engine.camera.get_fen()
        if not self.verify_move(expected_fen, fen_after_robot):
            raise Exception("Invalid move detected")
        self.game.set_fen(fen_after_robot)

    def verify_move(self, expected_fen: str, actual_fen: str) -> bool:
        return expected_fen == actual_fen

    def fen_after_move(self, fen: str, move: str) -> str:
        return self.engine.stockfish.get_fen_after_move(fen, move)
    
    def shutdown(self):
        self.engine.shutdown()
        self.game.close_game()
        print("Game engine shut down.")