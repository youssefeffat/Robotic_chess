from flask import Flask, request, render_template, jsonify
from api.UserInterface import UserInterface
from engine.game_engine import GameEngine
from dotenv import load_dotenv
# import os
import threading

# Installation à faire : 
#     pip install flask
#     pip install dotenv
#     sudo apt-get install stockfish
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='frontend/templates')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    mode = data.get('mode', 'human_vs_bot').lower()
    color = data.get('color', 'white').lower()
    difficulty = int(data.get('difficulty',10))

    if mode not in ['human_vs_bot', 'bot_vs_bot'] or color not in ['white', 'black'] or difficulty < 1 or difficulty > 20:
        return jsonify({"error": "Invalid input"}), 400
    
    user_interface = UserInterface()
    game_engine = GameEngine(user_interface)
    
    game_engine.initialize_game(mode=mode, color=color, difficulty=difficulty)
    
    session_url = user_interface.create_game()
    game_engine.start_game()



    threading.Thread(target=game_engine.start_game).start()

    return jsonify({"message": "Game started successfully!"})


if __name__ == "__main__":
    app.run(debug=True)