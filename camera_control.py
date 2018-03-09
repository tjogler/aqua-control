#!/usr/bin/python
import numpy as np
import sys,os
import time
import logging
import threading
from picamera import PiCamera
import light_control as lc


def take_image(path="./",number=0):
    camera.start_preview()
    sleep(3)
    fname=path+'image_{:04d}.jpg'.format(number)
    camera.capture(fname)
    camera.stop_preview()

    
def make_bright(channel):
    if type(channel)==list:
        self.numChannel=len(self.channel)+1
    else:
        self.numChannel=1
        self.channel=[channel]

    for c in channel:
        if "white" in c.name:
                
