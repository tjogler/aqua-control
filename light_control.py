#!/usr/bin/env python

import logging
import random
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
        
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

data=[]
lockPi=threading.Lock()

def convert_timestr_to_s(time):
        '''converts HH:MM:SS string to s in int'''
        factor=3600
        res=0
        for t in time.split(':'):
            res+=int(t)*factor
            factor/=60
        return res

class lightProfile(object):

    def __init__(self,profile_type='simple',resolution=60,maxI=1.,maxIM=0.05,srise='8:00:00',sset='20:00:00',mrise='22:00:00',mset='4:00:00'):
        self.name=profile_type
        self.resolution=resolution
        if maxI <=1: #prevent impossible max intensity
            self.maxI=maxI
        else:
            self.maxI=1.
        self.maxIM=maxIM
        if self.maxIM>0.1*self.maxI: #prevent to bright moonlight by false settings
            self.maxIM=0.1*self.maxI
        self.sunRise=self._convert_timestr_to_s(srise)
        self.sunSet=self._convert_timestr_to_s(sset)
        self.moonRise=self._convert_timestr_to_s(mrise)
        self.moonSet=self._convert_timestr_to_s(mset)
        self.calc_intens_profile()

        
    def _convert_timestr_to_s(self,time):
        '''converts HH:MM:SS string to s in int'''
        factor=3600
        res=0
        for t in time.split(':'):
            res+=int(t)*factor
            factor/=60
        return res

    def calc_intens_profile_sun(self):
        if self.name=='simple':
            intP=np.ones(int(86400/self.resolution))*self.maxI
            sRiseIndex=int(self.sunRise/self.resolution)
            sSetIndex=int(self.sunSet/self.resolution)
            intP[:sRiseIndex]=0
            intP[sSetIndex:]=0
            duration=int(30*60/self.resolution)
            intP[sRiseIndex:sRiseIndex+duration]=np.linspace(0,self.maxI,duration)
            intP[sSetIndex-duration:sSetIndex]=np.linspace(self.maxI,0,duration)
            
        else:
            intP=np.zeroes(int(86400/self.resolution))
        print intP
        return intP

    def calc_intens_profile_moon(self):
        if self.name=='simple':
            intP=np.ones(int(86400/self.resolution))*self.maxIM
            sRiseIndex=int(self.moonRise/self.resolution)
            sSetIndex=int(self.moonSet/self.resolution)
            duration=int(30*60/self.resolution)
            if sSetIndex<sRiseIndex:
                intP[sSetIndex:sRiseIndex]=0

            else:
                intP[:sRiseIndex]=0
                intP[sSetIndex:]=0
               
            intP[sRiseIndex:sRiseIndex+duration]=np.linspace(0,self.maxIM,duration)
            intP[sSetIndex-duration:sSetIndex]=np.linspace(self.maxIM,0,duration)
            
        else:
            intP=np.zeroes(int(86400/self.resolution))
        print intP
        return intP

    def calc_intens_profile(self):
        self.intensProfile=self.calc_intens_profile_sun()+self.calc_intens_profile_moon()
    
        
class lightChannel(object):

    def __init__(self,name,address=None,maxintens=1.,**kwargs):
        self.name=name
        self.address=address
        self.maxI=maxintens
        self.profileI=lightProfile(maxI=self.maxI,**kwargs)


    def set_intens(self,intens):
        '''
        function that sets a single channels light intensity
        '''
        if intens>self.maxI: #protect coral from too high intensity
            intens=self.maxI
            
            
class lamp(object):
    
    def __init__(self,channel):
        self.channel=channel
        if type(channel)==list:
            self.numChannel=len(self.channel)+1
        else:
            self.numChannel=1
            self.channel=[channel]
        self.temp=-1.
        self.fans=False
        self.on=False
        self.power=-1.

class RunLamp(threading.Thread):

    def __init__(self, event,lamp,lock):
        threading.Thread.__init__(self)
        self.stopped=event
        self.lamp=lamp
        self.lock=lock

    def run(self):
        logging.debug('light intensity profile started')
        counter=0
        res=self.lamp.channel[0].profileI.resolution
        logging.debug('intensity resolution: {}'.format(res))
        
        
        #calculate index to start light intensity from
        now=convert_timestr_to_s(time.strftime('%H:%M:%S'))
        counter=int(now/res)+1
        if counter >=len(self.lamp.channel[0].profileI.intensProfile):
                counter=0
        logging.debug('starting at intensity array  position: {}'.format(counter))
        while not self.stopped.wait(res):
            self.lock.acquire()
            print 'intensity: {}'.format(self.lamp.channel[0].profileI.intensProfile[counter])
            data.append(self.lamp.channel[0].profileI.intensProfile[counter])
            self.lock.release()
            counter+=1
            if counter >=len(self.lamp.channel[0].profileI.intensProfile):
                counter=0
        logging.debug('light intensity profile stopped')

            
stopFlag=threading.Event()

cwhite=lightChannel(name="white",resolution=1)
led=lamp(cwhite)
t=RunLamp(stopFlag,led,lockPi)
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
#time.sleep(10)
#stopFlag.set()

