from flask import Flask, request
from flask_cors import CORS
from PIL import Image
from io import BytesIO, StringIO
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
import json
import urllib.request
import os
import subprocess

KEY = 'd09e05217d2e40b98e07f105b90de804'
ENDPOINT = 'https://westcentralus.api.cognitive.microsoft.com/'

DATASET_PATH = "[prepared dataset path]"
IMAGE_DATA_PATH = "data"
IMAGE_FILE = "sample.jpg"

app = Flask(__name__)
CORS(app)

@app.route('/model', methods=['POST'])
def run_model():
  imageData = request.form["image"]

  # save image into temp file to pass stream to face api
  tempImagePath = os.path.join(IMAGE_DATA_PATH, IMAGE_FILE)
  urllib.request.urlretrieve(imageData, tempImagePath)
  image = open(tempImagePath, 'rb')

  # call Azure Face API
  face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))
  detected_faces = face_client.face.detect_with_stream(
    image,
    return_face_id=False,
    return_face_landmarks=True,
    return_face_attributes=None,
    recognition_model='recognition_01',
    return_recognition_model=False,
    detection_model='detection_01'
  )

  if not detected_faces:
    raise Exception('No face detected from image')

  # TODO: to account for multiple images coming
  # need to loop around whole code for calling azure
  # need to call face api for each image, jsons will be top of loop
  # CHOOSE: send one image to model at a time, or multiple (groups of 5 or 10)
  #         Depends on how long the model takes
  face = detected_faces[0]

  # Save face dimensions in face rectangle and face landmarks
  appleFace = {'H': [], 'W': [], 'X': [], 'Y': [], 'IsValid': []}
  appleLeftEye = {'H': [], 'W': [], 'X': [], 'Y': [], 'IsValid': []}
  appleRightEye = {'H': [], 'W': [], 'X': [], 'Y': [], 'IsValid': []}

  addFaceValues(appleFace, face, True, False)
  addFaceValues(appleLeftEye, face, False, True)
  addFaceValues(appleRightEye, face, False, False)

  # Save into json files for prepareDataset to crop image
  facePath = os.path.join(IMAGE_DATA_PATH, 'appleFace.json')
  with open(facePath, 'w') as outfile:
    json.dump(appleFace, outfile)

  leftEyePath = os.path.join(IMAGE_DATA_PATH, 'appleLeftEye.json')
  with open(leftEyePath, 'w') as outfile:
    json.dump(appleLeftEye, outfile)

  rightEyePath = os.path.join(IMAGE_DATA_PATH, 'appleRightEye.json')
  with open(rightEyePath, 'w') as outfile:
    json.dump(appleRightEye, outfile)


  # run facegrid matlab script to get facegrid json



  # run prepareDataset to generate cropped images
  #output = subprocess.run(["python3", "../prepareDataset.py",
  #                         "--dataset_path", IMAGE_DATA_PATH,
  #                         "--output_path", DATASET_PATH])


  # run model with file
  #output = subprocess.run(["python3", "../main.py",
  #                         "--data_path", DATASET_PATH, "--sink"], capture_output=True)

  # save coordinates (will likely need to change to properly extract the output from the model)
  #coords = output.stdout

  # debug (delete after)
  coords = json.dumps(appleFace) + "\n\n" + json.dumps(appleLeftEye) + "\n\n" + json.dumps(appleRightEye)

  # delete temp file
  os.remove(tempImagePath)

  ## (can change if want to send both (x,y) or just y coord)
  return coords

def addFaceValues(json, face, isFace, isLeftEye):
  face_rect = face.face_rectangle
  if isFace:
    x, y, w, h = face_rect.left, face_rect.top, \
                 face_rect.width, face_rect.height
  else:
    face_details = face.face_landmarks
    if isLeftEye:
      o, i, t, b = face_details.eye_left_outer, face_details.eye_left_inner, \
                   face_details.eye_left_top, face_details.eye_left_bottom
    else:
      o, i, t, b = face_details.eye_right_outer, face_details.eye_right_inner, \
                   face_details.eye_right_top, face_details.eye_right_bottom
    x, y, w, h = computeEyeData(o, i, t, b, face_rect.left, face_rect.top)
  json['H'].append(h)
  json['W'].append(w)
  json['X'].append(x)
  json['Y'].append(y)
  json['IsValid'].append(1)

def computeEyeData(outer, inner, top, bottom, faceX, faceY):
  minLeft = min(outer.x, min(inner.x, top.x))
  minTop = min(outer.y, min(inner.y, top.y))
  maxTop = max(outer.y, max(inner.y, top.y))
  h = abs(maxTop - minTop) * 2 # likely need to make the eye crop a square
  w = abs(inner.x - outer.x) * 2
  x = minLeft - faceX -  w / 4 # play with this divide
  y = minTop - faceY - h / 4

  return x, y, w, h