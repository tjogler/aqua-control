#!/usr/bin/env python

import logging
import random
import threading
import time
import datetime
import numpy as np
import utilities as ut
import RPi.GPIO as GPIO
from Adafruit_PWM_Servo_Driver import PWM

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )
GPIO.setmode(GPIO.BCM)

class powerChannel(object):

    def __init__(self,name,gpio,number,**kwargs):
        self.name=name
        self.gpio=gpio
        self.number=number
        self.state=state #default is on if not oserwise configured
        self.switchTime=datetime.timedelta(seconds=switchTime)  #time between two state switches, dampens oszilations, muste be a datetime.timedelta(seconds=xxx) object
        self.counter=0 #coutner for debugg and timing of switching, is used by other programs
        self.timeSwitched=None
        self.inverted=invert
        self.errors=[]
        self.location=location #currently only SUMP is relevant
        
        GPIO.setup(self.gpio,GPIO.OUT)
        if self.state==1:
            GPIO.output(self.gpio,GPIO.HIGH)
            self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
        else:
            GPIO.output(self.gpio,GPIO.LOW)
            self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
            
    def set_on(self):
        '''
        function that sets a single power channel on
        '''
        now=datetime.datetime.now().replace(microsecond=0)
        if self.switchTime<(now-self.timeSwitched):
            if self.inverted:
                GPIO.output(self.gpio,GPIO.LOW)
            else:
                GPIO.output(self.gpio,GPIO.HIGH)
            self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
            self.state=1
        else:
            print 'WARNING: Switching time to short, no switching occured'
            self.errors.append(-1)
            
    def set_off(self):
        '''
        function that sets a single power channel off
        '''
        now=datetime.datetime.now().replace(microsecond=0)
        if self.switchTime<(now-self.timeSwitched):
            if self.inverted:
                GPIO.output(self.gpio,GPIO.HIGH)
            else:
                GPIO.output(self.gpio,GPIO.LOW)
            self.state=0
            self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
        else:
            print 'WARNING: Switching time to short, no switching occured'
            self.errors=(-1)
            
    def toggle(self):
        '''
        functions that toggles the state of the channel
        '''
        if self.state==1:
            self.state=0
            self.set_off()
        else:
            self.state=1
            self.set_on()            
        
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
        GPIO.setup(self.readTank,GPIO.IN)
        GPIO.setup(self.readSump,GPIO.IN)
        
    def statusRead(self):
        self.statusTank=GPIO.input(self.readTank)
        self.statusSump=GPIO.input(self.readSump)
        logging.debug('Sump state: {}'.format(self.statusSump))
        logging.debug('Tank state: {}'.format(self.statusTank))
        
    def status(self):
        logging.debug('============================')
        logging.debug('power module status')
        logging.debug('============================')
        for c in self.channel:
            logging.debug('Power channel {} at GPIO[{}], plug number [{}] is set to {}'.format(c.name,c.gpio,c.number,c.state))

        self.statusRead()
        
class RunPower(threading.Thread):

    def __init__(self, event,powerModule,lock,data,frequency=60):
        threading.Thread.__init__(self)
        self.stopped=event
        self.powerModule=powerModule
        self.lock=lock
        self.data=data
        self.frequency=frequency
        
    def run(self):
        logging.debug('power control initializing at {}'.format(time.strftime('%H:%M:%S')))
        counter=0
        logging.debug('power state: initialzing')
        
        now=ut.convert_timestr_to_s(time.strftime('%Y %m %d %H:%M:%S'))
        
        while not self.stopped.wait(self.frequency):
            self.lock.acquire()
            self.powerModule.status()
            if self.powerModule.statusTank==1:
                logging.debug('{} ALERT! water level in tank to high!'.format(time.strftime('%Y %m %d %H:%M:%S')))
                for c in self.powerModule.channel:
                    if 'RFP' in c.name:
                        self.lock.acquire()
                        try:
                            c.set_off()
                            self.lock.release()
                        except:
                            logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched off!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                            self.lock.release()
                    if 'UeberlaufEntlueftung' in c.name:
                        self.lock.acquire()
                        try:
                            c.set_on()
                            time.sleep(30)
                            c.set_off()
                            rfp=self.powerModule.channel[self.powerModule.channel.name.index('RFP')]
                            rfp.set_on()
                            self.lock.release()
                        except:
                             logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                             self.lock.release()
                             
            if self.powerModule.statusSUMP==1:
                logging.debug('{} ALERT! water level in sump to low!'.format(time.strftime('%Y %m %d %H:%M:%S')))
                switchTimeList=[]
                channelDeactivationList=[]
                for c in self.powerModule.channel:
                    if c.loaction='SUMP':
                        self.lock.acquire()
                        try:
                            if c.status==1:
                                c.set_off()
                                switchTimeList.append(c.switchTime)
                                channelDeactivationList.append(c)
                                self.lock.release()
                        except:
                             logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                            self.lock.release()
                if switchTimeList!=[]:
                    time.sleep(max(switchTimeList))
                    for c in channelDeactivationList:
                        if c.loaction='SUMP':
                            self.lock.acquire()
                            try:
                                c.set_on()#turns only channels on that were turned off by this instance of this Alert
                                self.lock.release()
                            except:
                                logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                            self.lock.release()
                            
        logging.debug('{} power control stopped'.format(time.strftime('%Y %m %d %H:%M:%S')))

            

