import os
import requests
from dotenv import load_dotenv
import json
# from core.interfaces import IUserInterface
# from core.enums import LichessParams
load_dotenv()  # Load environment variables from .env


# class UserInterface(IUserInterface):
class UserInterface():

    def __init__(self):
        self.lichess = LichessAPI()

    def create_game(self) -> str:
        return self.lichess.create_game()

    def apply_move(self, game_id: str, move: str) -> None:
        self.lichess.make_move(game_id, move)

    def get_game_state(self, game_id: str) -> dict:
        return self.lichess.get_game_state(game_id)
    
    def get_seesion_url(self) -> str:
        """
        Get the URL of the game session.
        :param game_id: ID of the game.
        :return: URL of the game session.
        """
        return None

    def get_game_clock_state(self, game_id: str) -> dict:
        """
        Get the clock state of the game.
        :param game_id: ID of the game.
        :return: Clock state of the game.
        """
        endpoint = f"{self.lichess.BASE_URL}/api/bot/game/{game_id}/clock"
        response = requests.get(endpoint, headers=self.lichess.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get game clock state: {response.text}")

    def is_game_over(self, game_id: str) -> bool:
        """
        Check if the game is over.
        :param game_id: ID of the game.
        :return: True if the game is over, False otherwise.
        """
        game_state = self.get_game_state(game_id)
        return game_state.get("status") == "mate" or game_state.get("status") == "resign" or game_state.get("status") == "draw"

    def shutdown(self) -> None:
        """
        Clean up resources (e.g., close connections).
        """
        self.lichess.shutdown()
    # Implement other methods using LichessAPI's functionality

class LichessAPI():
    BASE_URL = "https://lichess.org"
    API_TOKEN_BOT1 = os.getenv("LICHESS_API_TOKEN_BOT1")
    API_TOKEN_BOT2 = os.getenv("LICHESS_API_TOKEN_BOT2")
    if not API_TOKEN_BOT1 or not API_TOKEN_BOT2:
        raise EnvironmentError("LICHESS_API_TOKEN_BOT1 OR LICHESS_API_TOKEN_BOT2 not found in environment variables.")

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {self.API_TOKEN_BOT1}",
            "Accept": "application/x-ndjson"
        }

    # Implement IUserInterface methods
    def create_game(self) -> str:
        """
        return: Game url if successful.
        """
        self.headers = {
            "Authorization": f"Bearer {self.API_TOKEN_BOT1}",
            "Accept": "application/x-ndjson"
        }

        # challenge_id = self._create_challenge(LichessParams.BOT2_USERNAME, LichessParams.CLOCK_LIMIT)
        challenge_id = self._create_challenge("youssefeffat",600)


        self.headers = {
            "Authorization": f"Bearer {self.API_TOKEN_BOT2}",
            "Accept": "application/x-ndjson"
        }

        game_url = self.BASE_URL+' '+self._accept_challenge(challenge_id)

        return game_url


    def _create_challenge(self, opponent_username: str, clock_limit: int) -> str:
        """Create a challenge to start a game with a user."""
        endpoint = f"{self.BASE_URL}/api/challenge/{opponent_username}"
        # params = {
        #     "clock.limit": clock_limit,
        #     "rated": "false"
        # }
        # response = requests.post(endpoint, headers=self.headers, params=params)
        response = requests.post(endpoint, headers=self.headers)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            raise Exception(f"Failed to create challenge: {response.text}")
        
    def _accept_challenge(self, challenge_id: str) -> str:
        
        # Accept the challenge
        endpoint = f"{self.BASE_URL}/api/challenge/{challenge_id}/accept"
        response = requests.post(endpoint, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to accept challenge: {response.text}")

        # Listen to the Event Stream for the gameStart event
        for event in self._stream_events():
            if event["type"] == "gameStart":
                return event["game"]["id"]
    
    def _stream_events(self):
        """
        Stream real-time events (e.g., incoming challenges, game starts).
        Yields event data as dictionaries.
        """
        endpoint = f"{self.BASE_URL}/api/stream/event"
        response = requests.get(endpoint, headers=self.headers, stream=True)
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    try:
                        event = json.loads(line.decode("utf-8"))
                        yield event
                    except json.JSONDecodeError:
                        print(f"Failed to decode event: {line}")
        else:
            raise Exception(f"Failed to stream events: {response.text}")
    
    def get_game_state(self, game_id: str) -> dict:
        """
        Get real-time game state via streaming endpoint.
        :param game_id: ID of the game.
        :return: Game state data.
        """
        endpoint = f"{self.BASE_URL}/api/bot/game/stream/{game_id}"
        response = requests.get(endpoint, headers=self.headers, stream=True)
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)  # Stream game updates
        else:
            raise Exception(f"Failed to get game state: {response.text}")

    def make_move(self, game_id: str, uci_move: str) -> None:
        """
        Submit a move to Lichess for the bot's turn.
        :param game_id: ID of the game.
        :param uci_move: UCI move string (e.g., "e2e4").
        """
        endpoint = f"{self.BASE_URL}/api/bot/game/{game_id}/move/{uci_move}"
        response = requests.post(endpoint, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to make move: {response.text}")

    def shutdown(self) -> None:
        """
        Clean up resources (e.g., close connections).
        """
        print("Lichess API session closed.")


    # Other IUserInterface methods (e.g., get_session_url, get_game_clock_state)
    # can be implemented similarly using Lichess endpoints.











from enum import Enum

class GameMode(Enum):
    HUMAN_VS_BOT = "human_vs_bot"
    BOT_VS_BOT = "bot_vs_bot"

class Color(Enum):
    WHITE = "white"
    BLACK = "black"

class LichessParams(Enum):
    BOT1_USERNAME = "bot_polytech"
    BOT2_USERNAME = "youssefeffat"
    CLOCK_LIMIT = 600
import time

# Create an instance of the UserInterface (which uses LichessAPI internally)
user_interface = UserInterface()

def test_lichess_api():
    try:
        # Step 1: Create a new game
        print("Creating a new game...")
        game_url = user_interface.create_game()
        print(f"Game created! Game URL: {game_url}")

        # Extract the game ID from the URL (assuming it's the last part of the URL)
        game_id = game_url.split("/")[-1]
        print(f"Game ID: {game_id}")

        # Step 2: Make a move
        print("Making a move...")
        move = "e2e4"  # Example UCI move
        user_interface.apply_move(game_id, move)
        print(f"Move '{move}' applied successfully.")

        # Step 3: Get the game state
        print("Fetching the game state...")
        game_state = user_interface.get_game_state(game_id)
        print(f"Game State: {game_state}")

        # Step 4: Check if the game is over
        print("Checking if the game is over...")
        is_over = user_interface.is_game_over(game_id)
        print(f"Is the game over? {is_over}")

        # Step 5: Get the clock state
        print("Fetching the clock state...")
        clock_state = user_interface.get_game_clock_state(game_id)
        print(f"Clock State: {clock_state}")

        # Step 6: Wait for a few seconds and check the game state again
        print("Waiting for 5 seconds before checking the game state again...")
        time.sleep(5)
        updated_game_state = user_interface.get_game_state(game_id)
        print(f"Updated Game State: {updated_game_state}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up resources
        print("Shutting down...")
        user_interface.shutdown()

test_lichess_api()