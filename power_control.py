
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

      def calc_intens_profile(self):
        self.intensProfile=self.calc_intens_profile_sun()+self.calc_intens_profile_moon()
       
class powerChannel(object):

    def __init__(self,name,gpio,number,**kwargs):
        self.name=name
        self.gpio=gpio
        self.number=number
        self.on=1
        
    def set_on(self):
        '''
        function that sets a single power channel on
        '''
       self.on=1
    def set_off(self):
        '''
        function that sets a single power channel off
        '''
        self.on=0
        
class powerModule(object):
    
    def __init__(self,channel,readTank=21,readSump=20):
        self.channel=channel
        if type(channel)==list:
            self.numChannel=len(self.channel)+1
        else:
            self.numChannel=1
            self.channel=[channel]
        self.readTank=readTank
        self.on=False#relict not sure if needed
        self.readSump=readSump
        self.power=-1.#relict not sure if needed

class RunPower(threading.Thread):

    def __init__(self, event,powerModule,lock,data):
        threading.Thread.__init__(self)
        self.stopped=event
        self.powerModule=powerModule
        self.lock=lock
        self.data=data

    def run(self):
        logging.debug('power control initializing')
        counter=0n
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

            

#time.sleep(10)
#stopFlag.set()

