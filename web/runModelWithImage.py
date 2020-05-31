from flask import Flask, request
from flask_cors import CORS
from io import BytesIO
import urllib.request
import os
import subprocess

app = Flask(__name__)
CORS(app)

DATA_PATH = ""
IMAGE_FILE = "sample.jpg"

@app.route('/model', methods=['POST'])
def run_model():
    image = request.form["image"]
    urllib.request.urlretrieve(image, IMAGE_FILE)

    # run model with file
    output = subprocess.run(["python3", "main.py", "--data_path", DATA_PATH, "--sink"], capture_output=True)

    # save coordinates (will likely need to change to properly extract the output from the model)
    coords = output.stdout

    # delete file
    os.remove(IMAGE_FILE)

    # (can change if want to send just y coord and also output as text or json)
    return coords