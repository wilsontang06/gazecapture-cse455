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
import numpy as np
from .prepareInput import prepareInput
from .mainProcessImage import runModel
from shutil import copytree, rmtree

KEY = 'd09e05217d2e40b98e07f105b90de804'
ENDPOINT = 'https://westcentralus.api.cognitive.microsoft.com/'

DATASET_PATH = "data"
DATASET_OUTPUT_PATH = "data_processed"
SUBJECT_DATA_PATH = DATASET_PATH + "/00000"
IMAGE_FILE = "00000.jpg"

# Measurements of the device that will be taking the photos
# Currently these are values for the iPhone 6s from https://github.com/CSAILVision/GazeCapture/blob/master/code/apple_device_data.csv
deviceCameraToScreenXMm = 18.61
deviceCameraToScreenyMm = 8.04
deviceScreenWidthMm = 58.49
deviceScreenHeightMm = 104.05

app = Flask(__name__)
CORS(app)

@app.route('/model', methods=['POST'])
def run_model():
  imageData = request.form["image"]

  # save image into temp file to pass stream to face api
  tempImagePath = os.path.join(SUBJECT_DATA_PATH + "/frames", IMAGE_FILE)
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
  facePath = os.path.join(SUBJECT_DATA_PATH, 'appleFace.json')
  with open(facePath, 'w') as outfile:
    json.dump(appleFace, outfile)

  leftEyePath = os.path.join(SUBJECT_DATA_PATH, 'appleLeftEye.json')
  with open(leftEyePath, 'w') as outfile:
    json.dump(appleLeftEye, outfile)

  rightEyePath = os.path.join(SUBJECT_DATA_PATH, 'appleRightEye.json')
  with open(rightEyePath, 'w') as outfile:
    json.dump(appleRightEye, outfile)


  # run facegrid matlab script to get facegrid json
  frameW, frameH = Image.open(tempImagePath).size
  gridW = 25
  gridH = 25
  labelFaceGrid = faceGridFromFaceRect(
    frameW, frameH, gridW, gridH,
    appleFace['X'], appleFace['Y'], appleFace['W'], appleFace['H']
  )

  faceGrid = {
    'H': [labelFaceGrid[0][3]],
    'W': [labelFaceGrid[0][2]],
    'X': [labelFaceGrid[0][0]],
    'Y': [labelFaceGrid[0][1]],
    'IsValid': [1]
  }
  faceGridPath = os.path.join(SUBJECT_DATA_PATH, 'faceGrid.json')
  with open(faceGridPath, 'w') as outfile:
    json.dump(faceGrid, outfile)

  # generate frames.json
  frames = [IMAGE_FILE]
  framesPath = os.path.join(SUBJECT_DATA_PATH, 'frames.json')
  with open(framesPath, 'w') as outfile:
    json.dump(frames, outfile)

  # theres a bug where numpy can turn a 1x1 array into a single number, so i just copy this subject and pretend there are 2
  if os.path.exists(DATASET_PATH + "/00001"):
    rmtree(DATASET_PATH + "/00001")
  copytree(DATASET_PATH + "/00000", DATASET_PATH + "/00001")

  # run prepareDataset to generate cropped images
  prepareInput(DATASET_PATH, DATASET_OUTPUT_PATH)

  # run model with new cropped images
  tensor = runModel(DATASET_OUTPUT_PATH)[0]

  # coordinates are distance from camera in cm
  cam_x_cm, cam_y_cm = (tensor[0].item(), tensor[1].item())

  # convert the camera coordinates to screen coordinates in cm
  #
  # orientation:
  #   1 = portrait
  #   2 = portrait upside down
  #   3 = landscape w/ home button on the right
  #   4 = landscape w/ home button on the left
  orientation = 1
  screen_x_cm, screen_y_cm = cam2screen(cam_x_cm, cam_y_cm, orientation)

  # delete temp file
  os.remove(tempImagePath)

  # for now, send back the (x, y) they're looking on the screen in cm
  return (screen_x_cm, screen_y_cm)

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
  w = abs(inner.x - outer.x) * 3
  #h = abs(maxTop - minTop) * 2 # likely need to make the eye crop a square
  h = w
  x = minLeft - faceX -  w / 4 # play with this divide
  y = minTop - faceY - h / 4

  return x, y, w, h

# (parameterized = 1) translation of faceGridFromFaceRect.m into Python
# outputs a (numSamples X 4) numpy array A, where A[i] is the [X, Y, W, H] of the ith index in faceGrid
# TODO: might need parameterized version
def faceGridFromFaceRect(frameW, frameH, gridW, gridH, labelFaceX, labelFaceY, labelFaceW, labelFaceH):
  scaleX = gridW / frameW
  scaleY = gridH / frameH
  numSamples = len(labelFaceX)
  labelFaceGrid = np.zeros((numSamples, 4))

  for i in range(numSamples):
    grid = np.zeros((gridH, gridW))

    # Use one-based image coordinates.
    labelFaceGrid[i][0] = np.round(labelFaceX[i] * scaleX) + 1
    labelFaceGrid[i][1] = np.round(labelFaceY[i] * scaleY) + 1
    labelFaceGrid[i][2] = np.round(labelFaceW[i] * scaleX)
    labelFaceGrid[i][3] = np.round(labelFaceH[i] * scaleY)

  return labelFaceGrid.astype(int).tolist()

# (useCm = 1, single coordinate, single device) translation of cam2screen.m into Python
# https://github.com/CSAILVision/GazeCapture/blob/master/code/cam2screen.m
def cam2screen(xCam, yCam, orientation):
  xScreen = float("nan")
  yScreen = float("nan")

  # Convert input to mm to be compatible with apple_device_data.csv
  xCam *= 10
  yCam *= 10

  # Process device
  xCurr = xCam
  yCurr = yCam

  # Transform so that measurements are relative to the device's origin
  # (depending on its orientation).
  dX = deviceCameraToScreenXMm
  dY = deviceCameraToScreenyMm
  dW = deviceScreenWidthMm
  dH = deviceScreenHeightMm

  if orientation == 1:
    xCurr += dX
    yCurr = -yCurr - dY
  elif orientation == 2:
    xCurr = xCurr - dX + dW
    yCurr = -yCurr + dY + dH
  elif orientation == 3:
    xCurr -= dY
    yCurr = -yCurr - dX + dW
  elif orientation == 4:
    xCurr += dY + dH
    yCurr = -yCurr + dX

  # Convert from mm to cm
  xScreen /= 10
  yScreen /= 10

  return xScreen, yScreen
