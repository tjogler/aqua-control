#!/usr/bin/python
import numpy as np
import sys,os
import time
import datetime
import logging
import threading
from picamera import PiCamera


class camera(object):

    def __init__(self,path="./"):
        self.path=path
        self.counter=0
        self.lastCaptureTime=datetime.datetime.now().replace(microsecond=0)
        self.camera=PiCamera()
        
    def take_image(self)
        self.camera.start_preview()
        time.sleep(3)
        fname=self.path+'image_{}_{:04d}.jpg'.format(time.strftime('%Y%m%d_%H:%M:%S'),self.counter)
        self.counter+=1
        self.camera.capture(fname)
        self.lastCaptureTime=datetime.datetime.now().replace(microsecond=0)
        self.camera.stop_preview()

    
    def make_bright(self,channel):
        #not yet ready to use, this would require cross thread communication not yet implemented
        if type(channel)==list:
            self.numChannel=len(self.channel)+1
        else:
            self.numChannel=1
            self.channel=[channel]
        
        for c in channel:
            if "white" in c.name:
                c.set_intens(1.0)

class RunCamera(threading.Thread):

    def __init__(self, event,camera,lock,frequency=86400):
        threading.Thread.__init__(self)
        self.stopped=event
        self.frequency=frequency
        self.lock=lock
        self.camera=camera

    def run(self):
        
        logging.debug('camera control initializing at {}'.format(time.strftime('%Y %m %d %H:%M:%S')))
        
        now=datetime.datetime.now().replace(microsecond=0)

        while not self.stopped.wait(300):
            if (now-self.camera.lastCaptureTime)>=self.frequency:
                try:
                    self.lock.acquire()
                    self.camera.take_image()
                    self.lock.release()
                except:
                    self.lock.release()
                     logging.debug('ERROR: camera control could not take image at {}'.format(time.strftime('%Y %m %d %H:%M:%S')))

        logging.debug('{} camera control stopped'.format(time.strftime('%Y %m %d %H:%M:%S')))
