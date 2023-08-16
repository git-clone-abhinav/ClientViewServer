def log(message):
    with open("log.txt", "a") as f:
        f.write(str(message) + "\n")


try:
    import time
    import os
    import pyautogui
    import json 
    import socketio
except Exception as e:
    print("Error importing modules:", e)
    log(e)
    input()



# load the timeout from a config file clientConfig.json
with open('clientConfig.json') as f:
    config = json.load(f)
    location = config['location']
    timeout = config['timeout']
    screenshot_folder = config['screenshot_folder']
    screenshot_file = config['screenshot_file']
    server = config['server']['host']
    port = config['server']['port']
    thumbnail_mode = config['thumbnail_mode']
    screenshot_limit = config['screenshot_limit']

print()
print()
print("###########################################")
print("Client started successfully")
print("Location : " + location)
print("Timeout: " + str(timeout) + " seconds")
print("Screenshot folder: " + screenshot_folder)
# print("Screenshot file: " + screenshot_file)
print("Server: " + server + ":" + str(port))
print("Thumbnail mode: " + str(thumbnail_mode))
print("Screenshot limit: " + str(screenshot_limit))
print("===========================================")
print()
print()

# if the screenshot_folder folder doesn't exist, create it
if not os.path.exists(screenshot_folder):
    os.mkdir(screenshot_folder)

if not os.path.exists(os.path.join(screenshot_folder,location)):
    os.mkdir(os.path.join(screenshot_folder,location))

if not os.path.exists(os.path.join(screenshot_folder,location,os.getlogin())):
    os.mkdir(os.path.join(screenshot_folder,location,os.getlogin()))

print("Connecting to Socket Server")

# Connect to the Flask-SocketIO server
sio = socketio.Client()
# while the connection is not established, try to connect
while not sio.connected:
    try:
        sio.connect(f"http://{server}:{port}")
        print("Syncing client details from server")
        sio.emit('client-connect', {'username': os.getlogin(), 'location': location, 'thumbnail_mode': thumbnail_mode, 'timeout': timeout})
    except Exception as e:
        log(e)
        print("Error connecting to Socket Server:", e)
        print("Sleeping for 5 seconds and retrying ...")
        time.sleep(5)
        continue

@sio.event
def connect():
    sio.emit('client-connect', {'username': os.getlogin(), 'location': location, 'thumbnail_mode': thumbnail_mode, 'timeout': timeout})
    print("Connected to Socket Server")
    
@sio.event
def disconnect():
    print("Disconnected from Socket Server")

@sio.event
def update_config(data):
    print("Updating config to ",data)
    global config, timeout, thumbnail_mode
    try:
        if data['timeout'] != timeout:
            timeout = data['timeout']
            print("Timeout updated to:", timeout)
            # write the updated timeout to the config file
            with open('clientConfig.json', 'w') as f:
                config['timeout'] = timeout
                json.dump(config, f, indent=4)
    except Exception as e:
        log(e)
        pass
    try:
        if data['thumbnail_mode'] != thumbnail_mode:
            thumbnail_mode = data['thumbnail_mode']
            print("Thumbnail mode updated to:", thumbnail_mode)
            # write the updated thumbnail_mode to the config file
            with open('clientConfig.json', 'w') as f:
                config['thumbnail_mode'] = thumbnail_mode
                json.dump(config, f, indent=4)
    except Exception as e:
        log(e)

# get the pc username
username = os.getlogin()

try :
    while True:

        ctime = time.strftime('%Y-%m-%d_%H-%M-%S')
        try:
            # take a screenshot
            screenshot = pyautogui.screenshot()
        except Exception as e:
            log(e)
            print("Error taking screenshot:", e, "Sleeping ...")
            time.sleep(timeout)
            continue
        
        if thumbnail_mode:
            # make the thumbnail of the screenshot
            screenshot.thumbnail((screenshot.size[0] / 4, screenshot.size[1] / 4))
        else:
            screenshot.thumbnail((screenshot.size[0] / 2, screenshot.size[1] / 2))

        # remove the oldest screenshot if the screenshot_limit is reached
        if len(os.listdir(os.path.join(screenshot_folder, location, username))) >= screenshot_limit:
            # get the oldest screenshot
            oldest_screenshot = min(os.listdir(os.path.join(screenshot_folder, location, username)))
            # delete the oldest screenshot
            os.remove(os.path.join(screenshot_folder, location, username, oldest_screenshot))

        # save the screenshot in the screenshot_folder folder
        screenshot_file_name = os.path.join(screenshot_folder,location,os.getlogin(), ctime + ".png")
        screenshot.save(screenshot_file_name)
        relative_path = screenshot_folder.split("/")[-1] + "/" + location + "/" + username + "/" + ctime + ".png"
        # create a dictionary with username, time and screenshot
        data = {'username': username, 'time': ctime, "location": location, "file": relative_path}
        # check if socket is connected
        if sio.connected:
            sio.emit('screenshot-save', data)
            print("Screenshot saved successfully")
            time.sleep(timeout)
        else:
            print("Socket not connected, sleeping ...")
            time.sleep(timeout)

except KeyboardInterrupt:
    print("Keyboard Interrupt detected, exiting ...")
    exit()