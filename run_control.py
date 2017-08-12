#!/usr/bin/env python

import logging
import random
import threading
import time
import numpy as np

import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib import pyplot as plt

import utilities as ut
import light_control as lc


data=[]
lockPi=threading.Lock()
res=1
stopFlag=threading.Event()
cwhite=lc.lightChannel(name="white",resolution=res,address=[0,5],sset="21:00",srise='9:00',maxIM=0.0,maxintens=0.75)
cblue1=lc.lightChannel(name='blue_1',resolution=res,address=1,sset='21:00',srise='9:00',maxIM=0.,maxintens=0.75)
cblue2=lc.lightChannel(name='blue_2',resolution=res,address=2,sset='21:00',srise='9:00',maxIM=0.05,mrise='21:30',mset='8:30',maxintens=0.75)
cred=lc.lightChannel(name="red",resolution=res,address=4,sset="21:00",srise='9:00',maxIM=0.0,maxintens=0.20)
cgreen=lc.lightChannel(name="green",resolution=res,address=3,sset="21:00",srise='9:00',maxIM=0.0,maxintens=0.20)
led=lc.lamp([cwhite,cblue1,cblue2,cred,cgreen])

led=lc.lamp([cwhite,cblue1,cblue2,cred,cgreen])
t=lc.RunLamp(stopFlag,led,lockPi,data=data)
t.daemon=True
t.start()
plt.figure()
plt.axis([0, 180, 0, 1.15])
ln, = plt.plot([])
plt.ion()
plt.show()
timer=0
run=True
while run:
    plt.pause(1.5)
    lockPi.acquire()
    print range(len(data)),data
    ln.set_xdata(range(len(data)))
    ln.set_ydata(data)
    plt.draw()
    lockPi.release()
    ''' timer+=1
    if timer>100:
        run=False
        stopFlag.set()
    '''
t.join()
