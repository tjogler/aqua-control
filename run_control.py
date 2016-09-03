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

stopFlag=threading.Event()

cwhite=lc.lightChannel(name="white",resolution=1,sset="22:30")
led=lc.lamp(cwhite)
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
    timer+=1
    if timer>100:
        run=False
        stopFlag.set()

t.join()
