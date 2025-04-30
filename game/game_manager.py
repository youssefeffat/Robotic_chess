from engine.game_engine import GameEngine  # Import GameEngine from the appropriate module
from game.game import Game
from api.UserInterface import UserInterface
from core.enums import GameMode, Color
import chess

class GameManager:
    def __init__(self, user_interface: UserInterface):
        self.engine = GameEngine(user_interface)
        self.game = Game()

    def initialize_game(self, mode: GameMode, color: Color , difficulty: int ):
        self.game.initialize_game(mode, color, difficulty, self.engine.camera.get_fen())
        self.engine.initialize_game(mode,color, difficulty)

    def start_game(self):
        # self.user_interface.create_game(self.camera.get_fen())
        print("Starting game...", "mode:", self.game.mode, "color:", self.game.color, "difficulty:", self.game.difficulty)
        if self.game.mode == GameMode.HUMAN_VS_BOT.value:
            self.start_human_vs_bot_game()
        elif self.game.mode == GameMode.BOT_VS_BOT.value:
            self.start_bot_vs_bot_game()
        else:
            raise ValueError("Invalid game mode")

    def start_human_vs_bot_game(self):
        if self.game.color == Color.WHITE.value:
            # TODO : potential issue 
            while not self.is_game_over():
                self.handle_human_move("e2e4")
                if self.is_game_over():
                    break
                self.handle_bot_move()
        elif self.game.color == Color.BLACK.value:
            while not self.is_game_over():
                self.handle_bot_move()
                if self.is_game_over():
                    break
                self.handle_human_move()
        else:
            raise ValueError("Invalid player color")

    def start_bot_vs_bot_game(self):
        while not self.is_game_over():
            self.handle_bot_move()

    def handle_human_move(self, move: str):
        self.wait_for_human_move()
        self.apply_human_move(move)

    def wait_for_human_move(self):
        ## TODO : try and catch to be added
        if self.engine.button:
            self.engine.button.human_turn_finished()  # Block until the button is pressed

    def apply_human_move(self, move: str):
        self.game.set_fen(self.engine.camera.get_fen())
        self.engine.user_interface.apply_move(move)
        if self.is_game_over():
            self.shutdown() # self.engine.shutdown() ??
        print(f"Human moved: {move}")
        print(f"Current game status: {self.get_game_state()}")

    def handle_bot_move(self) -> str:
        move = self.engine.stockfish.calculate_best_move(self.game.get_fen())
        self.engine.robot.execute_move(move)
        self.verify_robot_move(move)
        #TODO : case if the humain move is not valid (for camera)
        #TODO : case if the humain move is not valid
        self.engine.user_interface.apply_move(move)
        if self.is_game_over():
            self.shutdown() # self.engine.shutdown() ??
        print(f"Bot moved: {move}")

    def verify_robot_move(self, move: str):
        expected_fen = self.fen_after_move(self.game.get_fen(), move)
        fen_after_robot = self.engine.camera.get_fen()
        if not self.verify_move(expected_fen, fen_after_robot):
            raise Exception("Invalid move detected")
        self.game.set_fen(fen_after_robot)

    def verify_move(self, expected_fen: str, actual_fen: str) -> bool:
        return expected_fen == actual_fen

    def fen_after_move(self, fen: str, move: str) -> str:
        return self.engine.stockfish.get_fen_after_move(fen, move)
    
    def Get_move_between_fens(self, fen1, fen2) -> str:
        board1= chess.Board(fen1)
        board2= chess.Board(fen2)
        for move in board1.legal_moves:
            temp_board=board1.copy()
            temp_board.push(move)
            temp_fen = temp_board.fen()[:-10]
            print(f"temp_board fen : {temp_fen}")
            if temp_fen== board2.fen()[:-10]:
                print(f"Move: {board1.uci(move)}")
                return move.uci()
        fen3=fen1+" b"
        fen4=fen2+" w"
        board1= chess.Board(fen3)
        board2= chess.Board(fen4)
        for move in board1.legal_moves:
            temp_board=board1.copy()
            temp_board.push(move)
            temp_fen = temp_board.fen()[:-8]
            print(f"temp_board fen : {temp_fen}")
            if temp_fen== board2.fen()[:-8]:
                print(f"Move: {board1.uci(move)}")
                return move.uci()
        
        print(f"Illegal move")
        return None# Liste des FEN pour chaque étape de la partie
        
    def is_game_over(self) -> bool:
        # Example implementation (replace with actual logic)
        # return self.engine.is_game_over()
        return False

    def get_game_state(self) -> str:
        # Example implementation (replace with actual logic)
        # return self.engine.get_game_state()
        return "Game is ongoing"
    
    

    def shutdown(self):
        self.engine.shutdown()
        self.game.close_game()
        print("Game engine shut down.")