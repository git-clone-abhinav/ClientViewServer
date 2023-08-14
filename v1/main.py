# RDP Client Monitoring Flask Backend using Flask only that connects with clients and recieves screenshots

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Import the necessary libraries for image processing and saving
from PIL import Image
import io
import os
import json
import base64

# Initialize the Flask app
app = Flask(__name__)
CORS(app)
# Initialize the SocketIO app
socketio = SocketIO(app, cors_allowed_origins="*")

screenshots={}
clients={}

# load the timeout from a config file serverConfig.json
with open('serverConfig.json') as f:
    config = json.load(f)
    timeout = config['timeout']
    screenshot_folder = config['screenshot_folder']
    server = config['server']['host']
    port = config['server']['port']
    screenshot_limit = config['screenshot_limit']
    thumbnail_mode = config['thumbnail_mode']

print()
print()
print("============")
print("Server started successfully")
print("Sending Timeout: " + str(timeout) + " seconds")
print("Screenshot folder: " + screenshot_folder)
print("Server: " + server + ":" + str(port))
print("Screenshot limit: " + str(screenshot_limit))
print("Thumbnail mode: " + str(thumbnail_mode))
print("============")
print()
print()

@socketio.on('server-connect')
def handle_server_connect():
    global clients, screenshots
    print("Server connected to SocketIO Frontend Portal")
    print("Sending all screenshots to Frontend Portal")
    socketio.emit('recieve-first-time-data', {'clients': clients, 'screenshots': screenshots})

@socketio.on('server-disconnect')
def handle_server_disconnect():
    print("Server disconnected from SocketIO Frontend Portal")

@socketio.on('client-connect')
def handle_client_connect(data):
    clients[request.sid] = {'username':data['username'], 'location': data['location'], 'thumbnail_mode': data['thumbnail_mode'], 'timeout': data['timeout']}
    if data['']
    socketio.emit('client-connect-update', {'username': data['username'] })
    print("Client connected to server: ", data['username'])

# SocketIO event handler for client connection
@socketio.on('connect')
def handle_connect():
    print('Client connected')

# SocketIO event handler for client disconnection
@socketio.on('disconnect')
def handle_disconnect():
    global clients
    # Remove the client from the clients dictionary
    socketio.emit('client-disc-update', {'username': clients[request.sid] })
    print(clients[request.sid] + ' disconnected')
    del clients[request.sid]

@socketio.on('message')
def handle_message(message):
    print('##################### received message: ' + message)

# SocketIO event handler for screenshot updates
@socketio.on('screenshot-updated')
def handle_screenshot_updated(data):
    # Broadcast the updated screenshot data to all connected clients
    save_screenshot(data)

def save_screenshot(data):
    global screenshots
    # check if the screenshot_folder folder exists, if not create it
    if not os.path.exists(screenshot_folder):
        os.mkdir(screenshot_folder)

        # check if the username folder exists inside the screenshot folder, if not create it
        if not os.path.exists(os.path.join(screenshot_folder, data['username'])):
            os.mkdir(os.path.join(screenshot_folder, data['username']))
    else:
        # check if the username folder has files, if yes delete them
        if not os.path.exists(os.path.join(screenshot_folder, data['username'])):
            os.mkdir(os.path.join(screenshot_folder, data['username']))
    # create logic to save atleast last 100 screenshots of each user
    # if the number of screenshots is greater than 100, delete the oldest screenshot
    if len(os.listdir(os.path.join(screenshot_folder, data['username']))) >= screenshot_limit:
        # get the oldest screenshot
        oldest_screenshot = min(os.listdir(os.path.join(screenshot_folder, data['username'])))
        # delete the oldest screenshot
        os.remove(os.path.join(screenshot_folder, data['username'], oldest_screenshot))

    # Convert the base64 encoded image to bytes and save it in the username folder
    img = Image.open(io.BytesIO(base64.b64decode(data['screenshot'])))
    img.save(os.path.join(screenshot_folder, data['username'], data['time'] + '.png'))
    screenshots[data['username']] = data['screenshot']
    emit('user-screenshot', {'username': data['username'], 'screenshot': data['screenshot']})
    # make a small thumbnail too and send it over socket to frontend
    img.thumbnail((200, 200))
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    emit('user-screenshot', {'username': data['username'], 'screenshot': img_str.decode('utf-8')})
    print("Screenshot saved for user " + data['username'])



@app.route('/set-timeout/<int:time>',methods=['GET'])
def set_timeout(time):
    global timeout
    timeout = time
    print("Timeout updated to:", timeout)
    # write the updated timeout to the config file
    with open('serverConfig.json', 'w') as f:
        config['timeout'] = timeout
        json.dump(config, f, indent=4)
    socketio.emit('update_config', {"timeout": timeout})
    return "Timeout updated to " + str(timeout) + " seconds"

@app.route('/set-screenshot-limit/<int:limit>',methods=['GET'])
def set_screenshot_limit(limit):
    global screenshot_limit
    screenshot_limit = limit
    print("screenshot_limit updated to:", limit)
    # write the updated timeout to the config file
    with open('serverConfig.json', 'w') as f:
        config['screenshot_limit'] = limit
        json.dump(config, f, indent=4)
    return "screenshot_limit updated to " + str(screenshot_limit) + " seconds"

@app.route('/toggle-thumbnail-mode',methods=['GET'])
def toggle_thumbnail_mode():
    global thumbnail_mode
    thumbnail_mode = not thumbnail_mode
    if thumbnail_mode:
        print("Thumbnail mode turned ON")
    else:
        print("Thumbnail mode turned OFF")
    with open('serverConfig.json', 'w') as f:
        config['thumbnail_mode'] = thumbnail_mode
        json.dump(config, f, indent=4)
    return "Thumbnail mode updated to " + str(thumbnail_mode)



@app.route('/', methods=['GET'])
def index():
    return 'Hello World'

if __name__ == '__main__':
    socketio.run(app,host=server,port=port, debug = True)
