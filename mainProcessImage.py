import math, shutil, os, time, argparse
import numpy as np
import scipy.io as sio

import torch
import torch.nn as nn
import torch.nn.parallel
import torch.backends.cudnn as cudnn
import torch.optim
import torch.utils.data
import torchvision.transforms as transforms
import torchvision.datasets as datasets
import torchvision.models as models

from .ITrackerData import ITrackerData
from .models.ITrackerModelOriginal import ITrackerModel

'''
Train/test code for iTracker.

Author: Petr Kellnhofer ( pkel_lnho (at) gmai_l.com // remove underscores and spaces), 2018.

Website: http://gazecapture.csail.mit.edu/

Cite:

Eye Tracking for Everyone
K.Krafka*, A. Khosla*, P. Kellnhofer, H. Kannan, S. Bhandarkar, W. Matusik and A. Torralba
IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016

@inproceedings{cvpr2016_gazecapture,
Author = {Kyle Krafka and Aditya Khosla and Petr Kellnhofer and Harini Kannan and Suchendra Bhandarkar and Wojciech Matusik and Antonio Torralba},
Title = {Eye Tracking for Everyone},
Year = {2016},
Booktitle = {IEEE Conference on Computer Vision and Pattern Recognition (CVPR)}
}

'''

# So we can kill runmodel.sh:
print("Parent Process ID:", os.getppid())
print("Process ID:", os.getpid())

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

workers = 16
epochs = 25
batch_size = torch.cuda.device_count()*100 # Change if out of cuda memory

def runModel(output_path):
    model = ITrackerModel()
    model = torch.nn.DataParallel(model)
    model.cuda()

    imSize=(20,20)
    cudnn.benchmark = True

    saved = load_checkpoint()
    if saved:
        print('Loading checkpoint for epoch %05d with loss %.5f (which is the mean squared error not the actual linear error)...' % (saved['epoch'], saved['best_prec1']))
        state = saved['state_dict']
        try:
            model.module.load_state_dict(state)
        except:
            model.load_state_dict(state)
    else:
        print('Warning: Could not read checkpoint!')

    dataVal = ITrackerData(dataPath = output_path, split='test', imSize = imSize)
    val_loader = torch.utils.data.DataLoader(
        dataVal,
        batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=True)

    # Quick test
    return validate(val_loader, model)

def validate(val_loader, model):
    for i, (row, imFace, imEyeL, imEyeR, faceGrid, gaze) in enumerate(val_loader):
        # measure data loading time
        imFace = imFace.cuda(non_blocking=True)
        imEyeL = imEyeL.cuda(non_blocking=True)
        imEyeR = imEyeR.cuda(non_blocking=True)
        faceGrid = faceGrid.cuda(non_blocking=True)

        imFace = torch.autograd.Variable(imFace, requires_grad = False)
        imEyeL = torch.autograd.Variable(imEyeL, requires_grad = False)
        imEyeR = torch.autograd.Variable(imEyeR, requires_grad = False)
        faceGrid = torch.autograd.Variable(faceGrid, requires_grad = False)

        # compute output
        with torch.no_grad():
            output = model(imFace, imEyeL, imEyeR, faceGrid)

        return output

    return None

CHECKPOINTS_PATH = '/home/wtang06/gazecapture/gazecapture-cse455/checkpoints'

def load_checkpoint(filename='original.checkpoint.pth.tar'):
    filename = os.path.join(CHECKPOINTS_PATH, filename)
    print(filename)
    if not os.path.isfile(filename):
        return None
    state = torch.load(filename)
    return state