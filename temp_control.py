#!/usr/bin/python
import numpy as np
import sys,os
import time
import logging
import threading

def get_devices(path='/sys/bus/w1/devices/'):
    devList=[]
    folder=os.listdir(path)
    for f in folder:
        if '28-' in f:
            devList.append(path+f+'/w1_slave')
    
    return devList
    

def read_temp(dev=[]):
    counter=0
    for d in dev:
        try:
            fileT=open(d)
            info=fileT.readlines()
        except:
            logging.debug('file could not be opened')
            continue
        
        if 'YES' in info[0]:
            temp=float(info[1].split(' ')[9].split('=')[1])/1000.
            logging.debug('temp{:d}: {:.1f}'.format(counter,temp))
        else:
            logging.debug('temp{:d}: not working properly'.format(counter))
        fileT.close()
        counter+=1

def check_temp(run=True,delay=30,lock=None):
    devList=get_devices()
    while run:
        if lock!=None:
            lock.acquire()
            read_temp(devList)
            lock.release()
            time.sleep(delay)
        else:
            read_temp(devList)
            time.sleep(delay)
            
        
class runTemp(threading.Thread):

    def __init__(self,event,lock=None,log='',data=[],delay=30):
        threading.Thread.__init__(self)
        self.stopped=event
        self.log=log
        self.lock=lock
        self.data=data
        self.delay=delay

    def run(self):
        logging.debug('temp reading started')
        check_temp(not(self.stopped),self.delay,lock=self.lock)
    
        

