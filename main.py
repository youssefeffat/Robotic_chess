from flask import Flask, request, render_template, jsonify
from engine.game_engine import GameEngine
from dotenv import load_dotenv
import os
import threading

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='frontend/templates')

# STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")
# if not STOCKFISH_PATH:
#     raise EnvironmentError("STOCKFISH_PATH not found in environment variables.")

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

    game_engine = GameEngine()
    game_engine.initialize_game(mode=mode, color=color, difficulty=difficulty)

    threading.Thread(target=game_engine.start_game).start()

    return jsonify({"message": "Game started successfully!"})

if __name__ == "__main__":
    app.run(debug=True)