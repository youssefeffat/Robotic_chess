import os
from dotenv import load_dotenv
from core.interfaces import IUserInterface
from core.enums import LichessParams

load_dotenv()  # Load environment variables from .env


class UserInterface(IUserInterface):

    def __init__(self):
        self.lichess = LichessAPI()

    def create_game(self) -> str:
        return self.lichess.create_game()

    def apply_move(self, move: str) -> None:
        self.lichess.make_move(move)

    def is_game_over(self, game_id: str) -> bool:
        return self.lichess.is_game_over(game_id)
    
    def shutdown(self) -> None:
        """
        Clean up resources (e.g., close connections).
        """
        self.lichess.shutdown()


class LichessAPI(IUserInterface):
    BASE_URL = "https://lichess.org"
    BOT1_USERNAME = os.getenv("LICHESS_BOT1_USERNAME", "bot_polytech")
    BOT2_USERNAME = os.getenv("LICHESS_BOT2_USERNAME", "youssefeffat")
    CLOCK_LIMIT = 600

    def __init__(self) -> None:
        if not self.BOT1_USERNAME or not self.BOT2_USERNAME:
            raise EnvironmentError("LICHESS_BOT1_USERNAME OR LICHESS_BOT2_USERNAME not found in environment variables.")
        self.headers = {
            "Authorization": f"Bearer {os.getenv('LICHESS_API_TOKEN_BOT1')}",
            "Accept": "application/x-ndjson"
        }

    def create_game(self) -> str:
        """
        Create a game on Lichess and return the game URL.
        """
        # Placeholder implementation
        return f"{self.BASE_URL}/game/{self.BOT1_USERNAME}_vs_{self.BOT2_USERNAME}"

    def make_move(self, uci_move: str) -> None:
        """
        Submit a move to Lichess for the bot's turn.
        """
        # Placeholder implementation
        print(f"Move {uci_move} submitted.")
    
    def apply_move(self, move: str) -> None:
        """Apply the given move to the game session."""
        pass

    def is_game_over(self, game_id: str) -> bool:
        """
        Check if the game is over.
        """
        # Placeholder implementation
        return False

    def shutdown(self) -> None:
        """
        Clean up resources (e.g., close connections).
        """
        print("Lichess API session closed.")
    
    def create_game(self) -> str:
        """
        Create a game on Lichess and return the game URL.
        :return: Game URL if successful / Exception if failed.
        """
        return 

    def make_move(self, uci_move: str) -> None:
        """
        Submit a move to Lichess for the bot's turn.
        :param game_id: ID of the game.
        :param uci_move: UCI move string (e.g., "e2e4").
        """
        
    def is_game_over(self) -> bool:
        """
        Check if the game is over.
        :return: True if game is over, False otherwise.
        """
        return True
    

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







