import torch.utils.data as data
import scipy.io as sio
import os.path
import torchvision.transforms as transforms
import torch
import numpy as np
from PIL import Image

DIR_PATH = './'

class FormatData(data.Dataset):
    def __init__(self, dataPath, split = 'train', imSize=(224,224), gridSize=(25, 25)):
        self.dataPath = dataPath
        self.imSize = imSize
        self.gridSize = gridSize

        metaFile = os.path.join(dataPath, 'metadata.mat')
        if metaFile is None or not os.path.isfile(metaFile):
            raise RuntimeError('File %s not found. Provide a valid dataset path.' % metaFile)
        self.metadata = self.loadMATFile(metaFile)
        if self.metadata is None:
            raise RuntimeError('Could not read metadata file %s. Provide a valid dataset path.' % metaFile)

        self.faceMean = self.loadMATFile(os.path.join(DIR_PATH, 'mean_face_224.mat'))['image_mean']
        self.eyeLeftMean = self.loadMATFile(os.path.join(DIR_PATH, 'mean_left_224.mat'))['image_mean']
        self.eyeRightMean = self.loadMATFile(os.path.join(DIR_PATH, 'mean_right_224.mat'))['image_mean']
        
        self.transformFace = transforms.Compose([
            transforms.Resize(self.imSize),
            transforms.ToTensor(),
            SubtractMean(meanImg=self.faceMean),
        ])

        self.transformEyeL = transforms.Compose([
            transforms.Resize(self.imSize),
            transforms.ToTensor(),
            SubtractMean(meanImg=self.eyeLeftMean),
        ])

        self.transformEyeR = transforms.Compose([
            transforms.Resize(self.imSize),
            transforms.ToTensor(),
            SubtractMean(meanImg=self.eyeRightMean),
        ])

        if split == 'test':
            mask = self.metadata['labelTest']
        elif split == 'val':
            mask = self.metadata['labelVal']
        else:
            mask = self.metadata['labelTrain']

        self.indices = np.argwhere(mask)[:,0]

    def __getitem__(self, index):
        index = self.indices[index]
        print(index)
        suffix = (self.metadata['labelRecNum'][index], self.metadata['frameIndex'][index])

        imFacePath = os.path.join(self.dataPath, '%05d/appleFace/%05d.jpg' % suffix)
        imEyeLPath = os.path.join(self.dataPath, '%05d/appleLeftEye/%05d.jpg' % suffix)
        imEyeRPath = os.path.join(self.dataPath, '%05d/appleRightEye/%05d.jpg' % suffix)

        imFace = self.transformFace(self.loadImage(imFacePath))
        imEyeL = self.transformEyeL(self.loadImage(imEyeLPath))
        imEyeR = self.transformEyeR(self.loadImage(imEyeRPath))

        row = torch.LongTensor([int(index)])

        faceGrid = self.createGrid(self.metadata['labelFaceGrid'][index,:])
        faceGrid = torch.FloatTensor(faceGrid)

        gaze = np.array([self.metadata['labelDotXCam'][index], self.metadata['labelDotYCam'][index]], np.float32)
        gaze = torch.FloatTensor(gaze)

        return row, imFace, imEyeL, imEyeR, faceGrid, gaze
        
    def __len__(self):
        return len(self.indices)

    def loadImage(self, path):
        try:
            im = Image.open(path).convert('RGB')
        except OSError:
            raise RuntimeError('Could not read image: ' + path)
        return im

    def loadMATFile(self, filename):
        try:
            metadata = sio.loadmat(filename, squeeze_me=True, struct_as_record=False)
        except:
            print('\tFailed to load meta file "%s"' % filename)
            return None
        return metadata

    def createGrid(self, params):
        gridLen = self.gridSize[0] * self.gridSize[1]
        grid = np.zeros(gridLen, np.float32)
        
        for i in range(self.gridSize[0]):
            for j in range(self.gridSize[1]):
                if i >= params[1] and i < params[1] + params[3] and \
                    j >= params[0] and j < params[0] + params[2]:
                    grid[i * self.gridSize[0] + j] = 1

        return grid

class SubtractMean(object):
    def __init__(self, meanImg):
        self.meanImg = transforms.ToTensor()(meanImg / 255)

    def __call__(self, tensor):    
        return tensor.sub(self.meanImg)