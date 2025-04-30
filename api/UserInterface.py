import os
from dotenv import load_dotenv
from core.interfaces import IUserInterface
from core.enums import LichessParams
import requests
import time
import chess
import chess.pgn
import io
from IPython.display import display, SVG

load_dotenv()  # Load environment variables from .env


class UserInterface(IUserInterface):

    def __init__(self):
        self.lichess = LichessAPI()

    def create_game(self,fen) -> str:
        return self.lichess.create_game(fen)

    def apply_move(self, move: str) -> None:
        self.lichess.apply_move(move)

    def is_game_over(self, game_id: str) -> bool:
        return self.lichess.is_game_over(game_id)
    
    def shutdown(self) -> None:
        """
        Clean up resources (e.g., close connections).
        """
        self.lichess.shutdown()


class LichessAPI( IUserInterface):
    BASE_URL = "https://lichess.org"
    BOT1_USERNAME = os.getenv("LICHESS_BOT1_USERNAME")
    BOT2_USERNAME = os.getenv("LICHESS_BOT2_USERNAME")
    TOKEN_1 = os.getenv("LICHESS_API_TOKEN_BOT1")
    TOKEN_2 = os.getenv("LICHESS_API_TOKEN_BOT2")
    CLOCK_LIMIT = 600
    #if not BOT1_USERNAME or not BOT2_USERNAME:
       # raise EnvironmentError("LICHESS_BOT1_USERNAME OR LICHESS_BOT2_USERNAME not found in environment variables.")
    HEADERS_1 = {
        "Authorization": f"Bearer {TOKEN_1}",
        "Content-Type": "application/json"
    }

#ChessPlayer2Project
    HEADERS_2 = {
        "Authorization": f"Bearer {TOKEN_2}",
        "Content-Type": "application/json"
    }
    # Implement IUserInterface methods 
    def __init__(self) -> None: 
        self.game_id=None
        self.fen=None
    
    def create_game(self,fen) -> str:
        """
        Create a game on Lichess and return the game URL.
        :return: Game URL if successful / Exception if failed.
        """
        self.fen=fen
        url = f"{self.BASE_URL}/api/challenge/{self.BOT2_USERNAME}"
        print(f"url : {url}")
        data = {
        "level": 3,
        "clock.limit": 300,  
        "clock.increment": 0,
        "color": "black",  
        "fen": fen,
        "rated": False  
        }
        
        response = requests.post(url, headers=self.HEADERS_1, json=data)

        if response.status_code == 200:
            game_data = response.json()
            self.game_id = game_data.get("id")  
            if self.game_id:
                print(f" Game Created! Game ID: {self.game_id}")
                self.__accept_challenge(self.game_id)
                return f"{self.BASE_URL}/{self.game_id}"
            else:
                print(f" Unexpected response: {game_data}")
                return None
        else:
            print(f" Failed to create game: {response.text}")
            return None


    def apply_move(self, uci_move: str) -> None:
        """
        Submit a move to Lichess for the bot's turn.
        :param game_id: ID of the game.
        :param uci_move: UCI move string (e.g., "e2e4").
        """
        current_fen=self.fen
        url = f"{self.BASE_URL}/api/board/game/{self.game_id}/move/{uci_move}"
        player=self.__get_player_turn_from_fen(current_fen)
        if player=="b":
            headers_player=self.HEADERS_1
        else:
            headers_player=self.HEADERS_2
        response = requests.post(url, headers=headers_player)
        if response.status_code == 200:
            print(f" Move '{uci_move}' played successfully!")
            self.fen=self.__get_fen_chain(uci_move, current_fen)
        else:
            print(f" Failed to make move: {response.text}")
        
    def is_game_over(self) -> bool:
        """
        Check if the game is over.
        :return: True if game is over, False otherwise.
        """

        url = f'{self.BASE_URL}/api/game/{self.game_id}'
        response = requests.get(url, headers=self.HEADERS_1)
        response.raise_for_status()  # Ensure the request was successful
    
        game_data = response.json()
        status = game_data.get('status')
    
        if status == 'started':
            return False
        else:
            return True
    
    def shutdown(self) -> None:
        """
        Clean up resources (e.g., close connections).
        """
        self.game_id=None
        self.fen=None 
        return

    def __accept_challenge(self,game_id):
        url = f"https://lichess.org/api/challenge/{game_id}/accept"
        time.sleep(5)
        response = requests.post(url, headers=self.HEADERS_2)
        if response.status_code==200:
            print(f"challenge accepted!")
            return True
        else:
            print(f"challenge not accepted!")
            return False
        

    def __get_player_turn_from_fen(self,fen):
        fen_parts=fen.split()
        player_turn = fen_parts[1]
        return player_turn
    
    def __get_fen_chain(self,move_str, initial_fen):
        
        board = chess.Board(initial_fen)
        fen_chain = [board.fen()]  
    
        move = chess.Move.from_uci(move_str)
        board.push(move)
        fen_chain.append(board.fen())
    
        return fen_chain[1]

if __name__ == "__main__":
    lichess = LichessAPI()
    lichess.create_game("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq")
    lichess.apply_move("e2e4")
    print(lichess.is_game_over())
    lichess.shutdown()

# def get_game_outcome(game_id, api_token=None):
#     headers = {'Authorization': f'Bearer {api_token}'} if api_token else {}
    
    
# class LichessAPI():
#     
#     API_TOKEN_BOT1 = os.getenv("LICHESS_API_TOKEN_BOT1")
#     API_TOKEN_BOT2 = os.getenv("LICHESS_API_TOKEN_BOT2")
#     if not API_TOKEN_BOT1 or not API_TOKEN_BOT2:
#         raise EnvironmentError("LICHESS_API_TOKEN_BOT1 OR LICHESS_API_TOKEN_BOT2 not found in environment variables.")

#     def __init__(self):
#         return

#     # Implement IUserInterface methods
#     def create_game(self) -> str:
#         """
#         return: Game url if successful.
#         """
#         self.headers = {
#             "Authorization": f"Bearer {self.API_TOKEN_BOT1}",
#             "Accept": "application/x-ndjson"
#         }

#         # challenge_id = self._create_challenge(LichessParams.BOT2_USERNAME, LichessParams.CLOCK_LIMIT)
#         challenge_id = self._create_challenge("youssefeffat",600)


#         self.headers = {
#             "Authorization": f"Bearer {self.API_TOKEN_BOT2}",
#             "Accept": "application/x-ndjson"
#         }

#         game_url = self.BASE_URL+' '+self._accept_challenge(challenge_id)

#         return game_url


#     def _create_challenge(self, fen, color) -> str:
#         """Create a challenge to start a game with a user."""
#         endpoint = f"{self.BASE_URL}/api/challenge/{opponent_username}"
#         data = {
#             "clock.limit": clock_limit,  
#             "clock.increment": 0,
#             "color": color,  
#             "fen": fen,
#             "rated": False  
#         }
#         response = requests.post(endpoint, headers=self.headers, json=data)
#         if response.status_code == 200:
#             return response.json()["id"]
#         else:
#             raise Exception(f"Failed to create challenge: {response.text}")
        
#     def _accept_challenge(self, challenge_id: str) -> str:
        
#         # Accept the challenge
#         endpoint = f"{self.BASE_URL}/api/challenge/{challenge_id}/accept"
#         response = requests.post(endpoint, headers=self.headers)
#         if response.status_code != 200:
#             raise Exception(f"Failed to accept challenge: {response.text}")

#         # Listen to the Event Stream for the gameStart event
#         for event in self._stream_events():
#             if event["type"] == "gameStart":
#                 return event["game"]["id"]
    
#     def _stream_events(self):
#         """
#         Stream real-time events (e.g., incoming challenges, game starts).
#         Yields event data as dictionaries.
#         """
#         endpoint = f"{self.BASE_URL}/api/stream/event"
#         response = requests.get(endpoint, headers=self.headers, stream=True)
#         if response.status_code == 200:
#             for line in response.iter_lines():
#                 if line:
#                     try:
#                         event = json.loads(line.decode("utf-8"))
#                         yield event
#                     except json.JSONDecodeError:
#                         print(f"Failed to decode event: {line}")
#         else:
#             raise Exception(f"Failed to stream events: {response.text}")
    
#     def get_game_state(self, game_id: str) -> dict:
#         """
#         Get real-time game state via streaming endpoint.
#         :param game_id: ID of the game.
#         :return: Game state data.
#         """
#         endpoint = f"{self.BASE_URL}/api/bot/game/stream/{game_id}"
#         response = requests.get(endpoint, headers=self.headers, stream=True)
#         if response.status_code == 200:
#             for line in response.iter_lines():
#                 if line:
#                     yield json.loads(line)  # Stream game updates
#         else:
#             raise Exception(f"Failed to get game state: {response.text}")

#     def make_move(self, game_id: str, uci_move: str) -> None:
#         """
#         Submit a move to Lichess for the bot's turn.
#         :param game_id: ID of the game.
#         :param uci_move: UCI move string (e.g., "e2e4").
#         """
#         endpoint = f"{self.BASE_URL}/api/bot/game/{game_id}/move/{uci_move}"
#         response = requests.post(endpoint, headers=self.headers)
#         if response.status_code != 200:
#             raise Exception(f"Failed to make move: {response.text}")

#     def shutdown(self) -> None:
#         """
#         Clean up resources (e.g., close connections).
#         """
#         print("Lichess API session closed.")







