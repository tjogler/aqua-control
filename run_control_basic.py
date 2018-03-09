#!/usr/bin/env python

import logging
import random
import threading
import time
import numpy as np

import utilities as ut
import light_control as lc
import temp_control as tc
import power_control as pc

data=[]
lockPi=threading.Lock()

stopFlag=threading.Event()
res=60
cwhite=lc.lightChannel(name="white",resolution=res,address=[0,5],sset="22:00",srise='10:00',maxIM=0.0,maxintens=0.55)
cblue1=lc.lightChannel(name='blue_1',resolution=res,address=1,sset='22:00',srise='10:00',maxIM=0.,maxintens=0.65)
cblue2=lc.lightChannel(name='blue_2',resolution=res,address=2,sset='22:00',srise='10:00',maxIM=0.03,mrise='21:40',mset='23:45',maxintens=0.65)
cred=lc.lightChannel(name="red",resolution=res,address=4,sset="22:00",srise='10:00',maxIM=0.0,maxintens=0.05)
cgreen=lc.lightChannel(name="green",resolution=res,address=3,sset="22:00",srise='10:00',maxIM=0.0,maxintens=0.0)
lightChannels=[cwhite,cblue1,cblue2,cred,cgreen]
led=lc.lamp(lightChannels)

#crfp=pc.powerChannel(name='RFP',gpio=12,number=1,state=1,switchTime=30,location='SUMP',inverted=False)
#cas=pc.powerChannel(name='AS',gpio=13,number=2,state=1,switchTime=30,location='SUMP',inverted=False)
#cheater=pc.powerChannel(name='HEATER',gpio=5,number=3,state=1,switchTime=30,location='SUMP',inverted=False)

power=pc.powerModule(channel=[],readSump=20,readTank=21)

tpower=pc.RunPower(stopFlag,power,lockPi,data=data,frequency=60)
t=lc.RunLamp(stopFlag,led,lockPi,data=data)
t.daemon=True
t.start()
timer=0
ttemp=tc.runTemp(event=False,delay=15,lock=lockPi)
ttemp.daemon=True
ttemp.start()

run=True
"""while run:
    time.sleep(5)
    lockPi.acquire()
    #print range(len(data)),data
    lockPi.release()
    timer+=1

    '''if timer>100:
        run=False
        stopFlag.set()
    '''
"""
t.join()
ttemp.join()
