from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome to the Robotic Chess Player!"

if __name__ == "__main__":
    app.run(debug=True)