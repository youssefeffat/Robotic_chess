from engine.game_engine import GameEngine  # Import GameEngine from the appropriate module
from game.game import Game
from api.UserInterface import UserInterface
from core.enums import GameMode, Color
import chess

class GameManager:
    def __init__(self, user_interface: UserInterface):
        self.engine = GameEngine(user_interface)
        self.game = Game()
        self.tomb_squares =[] # z0 -> z15

    def initialize_game(self, mode: GameMode, color: Color , difficulty: int, initial_fen: str):
        self.game.initialize_game(mode, color, difficulty, initial_fen)
        self.engine.initialize_game(mode,color, difficulty)

    def start_game(self):
        
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
                self.handle_human_move()
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

    def handle_human_move(self):
        self.wait_for_human_move()
        self.apply_human_move()

    def wait_for_human_move(self):
        ## TODO : try and catch to be added
        if self.engine.button:
            self.engine.button.human_turn_finished()  # Block until the button is pressed

    def apply_human_move(self):
        fen_before_humain = self.game.get_fen()
        fen_after_human = self.engine.camera.get_fen()
        self.game.set_fen(fen_after_human)
        moves = self.Get_moves_between_fens(fen_before_humain, fen_after_human)
        move = moves[1] if len(moves) > 1 else moves[0]
        self.engine.user_interface.apply_move(move)
        if self.is_game_over():
            self.shutdown() 
        print(f"Human moved: {move}")
        print(f"Current game status: {self.get_game_state()}")

    def handle_bot_move(self) -> str:
        fen_before_bot = self.game.get_fen()
        move = self.engine.stockfish.calculate_best_move(fen_before_bot)
        print (f"Stockfish Bot move: {move}")
        fen_after_bot = self.engine.stockfish.get_fen_after_move(fen_before_bot, move)
        moves = self.Get_moves_between_fens(fen_before_bot, fen_after_bot)
        for m in moves:
            self.engine.robot.execute_move(m)
        self.verify_robot_move(fen_after_bot)
        #TODO : case if the humain move is not valid (for camera)
        #TODO : case if the humain move is not valid
        self.engine.user_interface.apply_move(move)
        self.game.set_fen(fen_after_bot)
        if self.is_game_over():
            self.shutdown() # self.engine.shutdown() ??
        print(f"Bot moved: {move}")

    def verify_robot_move(self, expected_fen: str):
        fen_after_robot = self.engine.camera.get_fen()
        if not self.verify_move(expected_fen, fen_after_robot):
            raise Exception(f"Robot move verification failed! Expected: {expected_fen}, Actual: {fen_after_robot}")

    def verify_move(self, expected_fen: str, actual_fen: str) -> bool:
        return expected_fen == actual_fen

    def fen_after_move(self, fen: str, move: str) -> str:
        return self.engine.stockfish.get_fen_after_move(fen, move)

    def Get_moves_between_fens(self, fen1: str, fen2: str) -> list[str]:
        res = []
        board1 = chess.Board(fen1)
        board2 = chess.Board(fen2)

        # Extract only the piece positions from both FENs
        target_position = fen2.split()[0]  # First part of fen2

        for move in board1.legal_moves:
            temp_board = board1.copy()
            temp_board.push(move)
            current_position = temp_board.fen().split()[0]  # First part of temp_board's FEN
            if current_position == target_position:
                captured_piece = board1.piece_at(move.to_square)
                is_capture = captured_piece is not None

                print(f"Move: {move.uci()} (Capture: {is_capture})")
                final_move = move.uci()
                if is_capture:
                    graveyard_move = final_move[-2:]+ self.next_free_tomb_square()
                    res.append(graveyard_move)
                res.append(final_move)
                return res
                
        return None
    
    def next_free_tomb_square(self) -> str:
        num = len(self.tomb_squares)
        square_name ="i"+str(num)
        self.tomb_squares.append(square_name)
        return square_name

    def is_game_over(self) -> bool:
        return self.engine.is_game_over()

    # def get_game_state(self) -> str:
    #     # Example implementation (replace with actual logic)
    #     # return self.engine.get_game_state()
    #     return "Game is ongoing"
    

    def shutdown(self):
        self.engine.shutdown()
        self.game.close_game()
        print("Game engine shut down.")


if __name__ == "__main__":
    game_manager = GameManager()

    # ----------------------------
    # 1. Standard pawn move: d5
    fen1 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b"
    fen2 = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move[0] == "d7d5", f"Expected 'd7d5', got '{move}'"

    # ----------------------------
    # 2. Pawn capture: exd5
    fen1 = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR "
    fen2 = "rnbqkbnr/ppp1pppp/8/3P4/8/8/PPPP1PPP/RNBQKBNR "
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move[1] == "e4d5", f"Expected 'e5d5', got '{move}'"
    print(move)

    # ----------------------------
    # 3. Knight move: Nf3
    fen1 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKB1R"
    fen2 = "rnbqkb1r/pppppppp/5n2/8/4P3/5N2/PPPP1PPP/RNBQKB1R"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move == "g1f3", f"Expected 'g1f3', got '{move}'"

    # Add other test cases with corrected FENs...

    # ----------------------------
    # 4. Bishop move: Bc4
    fen1 = "rnbqkbnr/pppp1ppp/4p3/8/B3P3/5N2/PPPP1PPP/RNBQKB1R b"
    fen2 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQKB1R w"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move == "f1c4", f"Expected 'f1c4', got '{move}'"

    # ----------------------------
    # 5. Rook move: Rd1
    fen1 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQKB1R w"
    fen2 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQ1BKR w"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move == "h1d1", f"Expected 'h1d1', got '{move}'"

    # ----------------------------
    # 6. Queen move: Qh5
    fen1 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQKB1R w"
    fen2 = "rnb1kb1r/pppp1ppp/4pn2/7q/B3P3/5N2/PPPP1PPP/RNBQKB1R b"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move == "d1h5", f"Expected 'd1h5', got '{move}'"

    # ----------------------------
    # 7. King move: Ke2
    fen1 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQKB1R w"
    fen2 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQ1BKR w"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move == "e1e2", f"Expected 'e1e2', got '{move}'"

    # ----------------------------
    # 8. Queenside castling
    fen1 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 5"
    fen2 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/2BQKB1R w kq - 0 5"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move == "e1c1", f"Expected 'e1c1', got '{move}'"

    # ----------------------------
    # 9. Kingside castling
    fen1 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 5"
    fen2 = "rnbqkb1r/pppp1ppp/4pn2/8/B3P3/5N2/PPPP1PPP/RNBQ1BKR w kq - 0 5"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move == "e1g1", f"Expected 'e1g1', got '{move}'"

    # ----------------------------
    # 10. Promotion without capture: e8=Q
    fen1 = "5rk1/4P3/8/8/8/8/8/5RK1 b - - 0 1"
    fen2 = "5qk1/8/8/8/8/8/8/5RK1 w - - 0 2"
    move = game_manager.Get_moves_between_fens(fen1, fen2)
    assert move == "e8f8q", f"Expected 'e8f8q', got '{move}'"

    print("All tests passed!")