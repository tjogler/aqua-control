#!/usr/bin/env python

import logging
import random
import threading
import time
import numpy as np
import utilities as ut
from Adafruit_PWM_Servo_Driver import PWM

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )



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
        self.sunRise=ut.convert_timestr_to_s(srise)
        self.sunSet=ut.convert_timestr_to_s(sset)
        self.moonRise=ut.convert_timestr_to_s(mrise)
        self.moonSet=ut.convert_timestr_to_s(mset)
        self.calc_intens_profile()


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

    def __init__(self,name,address=None,pwmAddr=0x41,pwmFreq=1000,maxintens=1.,**kwargs):
        self.name=name
        self.address=address
        self.maxI=maxintens
        self.profileI=lightProfile(maxI=self.maxI,**kwargs)
        self.pwm = PWM(pwmAddr)
        self.pwm.setPWMFreq(pwmFreq)
        
    def set_intens(self,intens):
        '''
        function that sets a single channels light intensity
        '''
        if intens>self.maxI: #protect coral from too high intensity
            intens=self.maxI
        if type(self.address)==list:    
            for a in self.address:
                self.pwm.setPWM(a,0,int(intens*4095))
        else:
            self.pwm.setPWM(self.address,0,int(intens*4095)) 
            
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

    def __init__(self, event,lamp,lock,data):
        threading.Thread.__init__(self)
        self.stopped=event
        self.lamp=lamp
        self.lock=lock
        self.data=data

    def run(self):
        logging.debug('light intensity profile started')
        counter=0
        res=self.lamp.channel[0].profileI.resolution
        logging.debug('intensity resolution: {}'.format(res))
        
        
        #calculate index to start light intensity from
        now=ut.convert_timestr_to_s(time.strftime('%H:%M:%S'))
        counter=int(now/res)+1
        if counter >=len(self.lamp.channel[0].profileI.intensProfile):
                counter=0
        logging.debug('starting at intensity array  position: {}'.format(counter))
        start=1
        while not self.stopped.wait(res):
            self.lock.acquire()
            for c in self.lamp.channel:
                print 'intensity {}: {}'.format(c.name,c.profileI.intensProfile[counter])
                if counter==0:
                    if c.profileI.intensProfile[len(c.profileI.intensProfile)-1]!=c.profileI.intensProfile[counter]:
                         c.set_intens(c.profileI.intensProfile[counter])
                    self.data.append(c.profileI.intensProfile[counter])
                elif c.profileI.intensProfile[counter-1]!=c.profileI.intensProfile[counter] or start==1:
                    print 'setting intensity channel {} to {}'.format(c.name,c.profileI.intensProfile[counter])
                    c.set_intens(c.profileI.intensProfile[counter])
                    self.data.append(c.profileI.intensProfile[counter])
            if start==1:
                start=0
            self.lock.release()
            counter+=1
            if counter >=len(self.lamp.channel[0].profileI.intensProfile):
                counter=0
        logging.debug('light intensity profile stopped')
