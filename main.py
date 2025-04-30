from flask import Flask, redirect, request, render_template, jsonify
from api.UserInterface import UserInterface
from game.game_manager import GameManager
from dotenv import load_dotenv
import threading

# Installation à faire : 
#     pip install flask
#     pip install dotenv
#     pip install stockfish
#     pip install numpy matplotlib
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

    if mode not in ['human_vs_bot', 'bot_vs_bot'] or color not in ['white', 'black'] or difficulty < 1 or difficulty > 20:
        return jsonify({"error": "Invalid input"}), 400
    
    user_interface = UserInterface()
    game_engine = GameEngine(user_interface)
    
    game_engine.initialize_game(mode=mode, color=color, difficulty=difficulty)
    
    session_url = user_interface.create_game()
    game_engine.start_game()

    # TODO : redirection to the session_url
    

    threading.Thread(target=game_engine.start_game).start()

        # Return session URL to frontend
        return jsonify({
            "message": "Game started successfully!",
            "session_url": session_url  # e.g., "/session/abcd1234"
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/session/<path:session_url>')
def session_page(session_url):
    return render_template('session.html', session_url=session_url)

if __name__ == "__main__":
    app.run(debug=True)