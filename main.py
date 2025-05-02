from flask import Flask, request, render_template, jsonify
from api.UserInterface import UserInterface
from game.game_manager import GameManager
from dotenv import load_dotenv
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
    try:
        data = request.json
        mode = data.get('mode', 'human_vs_bot').lower()
        color = data.get('color', 'white').lower()
        difficulty = int(data.get('difficulty', 10))

        # Validate input
        if mode not in ['human_vs_bot', 'bot_vs_bot']:
            return jsonify({"error": "Invalid mode"}), 400
        if color not in ['white', 'black']:
            return jsonify({"error": "Invalid color"}), 400
        if not (1 <= difficulty <= 20):
            return jsonify({"error": "Difficulty must be 1-20"}), 400

        if color == 'white':
            turn = 'w'
        else:
            turn = 'b'
            
        # Initialize game components
        user_interface = UserInterface()
        game_manager = GameManager(user_interface)

        # Generate session URL
        game_manager.initialize_game(mode=mode, color=color, difficulty=difficulty)
        inital_fen = game_manager.engine.camera.get_fen()
        game_manager.game.set_fen(inital_fen)
        session_url = user_interface.create_game(inital_fen+" "+turn)

        # Start game in a background thread
        threading.Thread(target=game_manager.start_game).start()

        # Return session URL to frontend
        return jsonify({
            "message": "Game started successfully!",
            "session_url": session_url  # e.g., "/session/abcd1234"
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)