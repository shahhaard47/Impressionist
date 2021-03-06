from speech_to_emotion.emotion_classifier_nn import livePredictions
"""
Application server (Flask)
$ python3 server.py
"""

import os
# make sure it is run from Impressionist/application
if (os.getcwd() != os.path.dirname(os.path.realpath(__file__))):
    print("Application server should be run from application folder.")
    print("cwd:", os.getcwd())
    exit()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import sys
import threading

SAVE_USER_AUDIO = False # FOR NOW
CWD = os.getcwd()
CONTENT_DIR = os.path.join(os.path.dirname(CWD), 'contentData')
FRIENDS_DIR_2_12 = os.path.join(
    CONTENT_DIR, 'tvShows/Friends/02/12-The-One-After-The-Superbowl-Part1')
USER_DIALOGUE_DIR = os.path.join(FRIENDS_DIR_2_12, "userAudio")

sys.path.insert(0, 'signalComparison/')
sys.path.insert(0, 'speech_to_text/')
sys.path.insert(0, 'speech_to_emotion/')
sys.path.insert(0, 'databuilder/')
from compareAudio import performThreeComparisons, sendScoreToBack, _logToFile

PORT = 3000        # Port to listen on (non-privileged ports are > 1023)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

@app.route("/")
def home_screen():
    return "Welcome to the Impressionist Application Server!"

socketio = SocketIO(app)

# load emotion comparison model
emoPredictor = livePredictions(path='speech_to_emotion/Emotion_Voice_Detection_Model.h5', file='speech-to-text/dummy.wav')
emoPredictor.load_model()
_logToFile(["emoPredictor after"])

@socketio.on('connect')
def test_connect():
    _logToFile(["a user connected"])
    print('a user connected')


@socketio.on('disconnect')
def test_disconnect():
    _logToFile(["a user disconnected"])
    print('a user disconnected')

@socketio.on('compareDialogue')
def handle_compareDialogue(message):
    _logToFile(["handle_compareDialogue"])
    loglst = []
    loglst.append("Data received (on compareDialogue)")
    loglst.append("gameID:" + message['gameID'])
    loglst.append("netflixWatchID:" + message['netflixWatchID'])
    loglst.append("dialogueID:" + str(message['dialogueID']))
    _logToFile(loglst)
    # print(message['audioBlob'])
    stream = message['audioBlob']

    userTranscript = message['userTranscript']
    # print(message)

    prefix = "diag"+str(message['dialogueID']+1)
    webmname = prefix + ".webm"
    wavname = prefix + ".wav"

    webmFile = webmname if not SAVE_USER_AUDIO else os.path.join(USER_DIALOGUE_DIR, webmname)
    wavFile = wavname if not SAVE_USER_AUDIO else os.path.join(USER_DIALOGUE_DIR, wavname) # for deleting purposes later

    # FIXME: just writing as raw and then running ffmpeg again inside `compareAudio.py`
    with open(webmFile, 'wb') as aud:
        aud.write(stream)

    resultBYTES, resultJSON, errorLst = performThreeComparisons(message['netflixWatchID'], message['dialogueID'], webmFile, message['gameID'], message['userTranscript'], emoPredictor, profile=True, logErrors=True)

    _logToFile(["Done comparing", "resultJSON from func"+resultJSON])

    if not SAVE_USER_AUDIO: os.remove(wavFile)
    os.remove(webmFile)

    _logToFile(["about to use threading to talk to back userDB"])
    # print("send to db", resultBYTES)
    # FIXME: don't wanna wait until back responds 
    # SOLUTION: async process
    thr = threading.Thread(target=sendScoreToBack, args=(resultBYTES, True))
    thr.start()

    # thr = socketio.start_background_task(sendScoreToBack, resultBYTES, True)
    # print(thr)

    # response = sendScoreToBack(resultBYTES)
    # print("response:", response)

    
    print(resultJSON)
    _logToFile(["Returning JSON back to front!"])

    return resultJSON


# interface to send dialogue 2D array
@socketio.on('getDialogue')
def handle_getDialogue(message):
    print(message)

# get unique characters
@socketio.on('getUniqueCharacters')
def handle_getUniqueCharacters(message):
    print(message)

# calibrate vtt file with netflix subtitles
# NOT NEEDED atm (3/29/19) because manualling entering offset when adding to appending to contentDB
# @socketio.on('calibrate')
# def handle_calibrate(message):
#     print(message)

def initializeUserAudioDir():
    if not os.path.isdir(USER_DIALOGUE_DIR):
        os.makedirs(USER_DIALOGUE_DIR)
        print("created:", os.path.isdir(USER_DIALOGUE_DIR),USER_DIALOGUE_DIR )

if __name__ == '__main__':
    _logToFile(["Application Server about to run"])
    print("Application Server is listening in port " + str(PORT))
    if SAVE_USER_AUDIO: initializeUserAudioDir()
    app.debug=False
    socketio.run(app, host='0.0.0.0', port=PORT)
