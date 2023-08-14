from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY']="secret!"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client connected', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected', request.sid)

@socketio.on('message')
def handle_message(message):
    print('##################### received message: ' + message)

if __name__ == '__main__':
    socketio.run(app, host='192.168.1.72', port=4000,debug=True)