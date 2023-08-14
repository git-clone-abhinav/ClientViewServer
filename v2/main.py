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

clients={}
servers=[]

import logging
log_flask = logging.getLogger('werkzeug')
log_flask.setLevel(logging.ERROR)

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


# socket connection and disconnection handlers

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    global clients
    if request.sid in clients:
        socketio.emit('client-disc-update', {'client': request.sid})
        print(clients[request.sid]['username'] + ", " + clients[request.sid]['location'] + ' disconnected')
        del clients[request.sid]
    else:
        handle_server_disconnect()

# SocketIO event handler for server connection

@socketio.on('server-connect')
def handle_server_connect():
    global clients, servers
    servers.append(request.sid)
    print("Server connected to SocketIO Frontend Portal")
    print("Sending all client data to Frontend Portal")
    if len(clients)>0:
        socketio.emit('recieve-first-time-data', {'clients': clients})
    else:
        socketio.emit("recieve-first-time-data", 0)

def handle_server_disconnect():
    global servers
    servers.remove(request.sid)
    print("SocketIO Frontend Portal disconnected")

# SocketIO event handler for client connection

@socketio.on('client-connect')
def handle_client_connect(data):
    global config, clients
    clients[request.sid] = {'username':data['username'], 'location': data['location'], 'thumbnail_mode': data['thumbnail_mode'], 'timeout': data['timeout']}
    update = {}
    if data['thumbnail_mode'] != config['thumbnail_mode']:
        update['thumbnail_mode'] = config['thumbnail_mode']
    if data['timeout'] != config['timeout']:
        update['timeout'] = config['timeout']
    if len(update)>0:
        socketio.emit('update_config', update)
        print("Client updateing its config to match server config")
        if 'thumbnail_mode' in update:
            print(" Thumbnail mode "+ str(data['thumbnail_mode']) + " -> " + str(update['thumbnail_mode']))
        if 'timeout' in update:
            print(" Timeout "+ str(data['timeout']) + " -> " + str(update['timeout']))
    socketio.emit('client-connect-update', {"client": request.sid,"data": clients[request.sid]})
    print("Client connected: " + data['username']+", "+data['location']) # SocketIO event handler for client connection


# SocketIO event handler for screenshot updates
@socketio.on('screenshot-updated')
def handle_screenshot_updated(data):
    save_screenshot(data)

def save_screenshot(data):
    global screenshot_folder, screenshot_limit, clients
    # check if the screenshot_folder folder exists, if not create it
    if not os.path.exists(screenshot_folder):
        os.mkdir(screenshot_folder)
        
        # check if the location folder exists, if not create it
        if not os.path.exists(os.path.join(screenshot_folder, data['location'])):
            os.mkdir(os.path.join(screenshot_folder, data['location']))
        # check if the username folder exists inside the screenshot folder, if not create it
        if not os.path.exists(os.path.join(screenshot_folder,data['location'], data['username'])):
            os.mkdir(os.path.join(screenshot_folder,data['location'], data['username']))
    else:
        # check if the location folder exists, if not create it
        if not os.path.exists(os.path.join(screenshot_folder, data['location'])):
            os.mkdir(os.path.join(screenshot_folder, data['location']))

        # check if the username folder exists inside the location folder, if not create it
        if not os.path.exists(os.path.join(screenshot_folder,data['location'], data['username'])):
            os.mkdir(os.path.join(screenshot_folder,data['location'], data['username']))

    # create logic to save atleast last 100 screenshots of each user
    # if the number of screenshots is greater than 100, delete the oldest screenshot
    if len(os.listdir(os.path.join(screenshot_folder,data['location'], data['username']))) >= screenshot_limit:
        # get the oldest screenshot
        oldest_screenshot = min(os.listdir(os.path.join(screenshot_folder, data['location'],data['username'])))
        # delete the oldest screenshot
        os.remove(os.path.join(screenshot_folder, data['location'], data['username'], oldest_screenshot))

    # Convert the base64 encoded image to bytes and save it in the username folder
    img = Image.open(io.BytesIO(base64.b64decode(data['screenshot'])))
    img.save(os.path.join(screenshot_folder,data['location'], data['username'], data['time'] + '.png'))
    clients[request.sid]['screenshot'] = data['screenshot']
    socketio.emit('user-screenshot', {"client":request.sid,"data":clients[request.sid]})
    print("Screenshot saved for " + data['username'] + ", " + data['location'])

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
