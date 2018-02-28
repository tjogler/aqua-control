
#!/usr/bin/env python

import logging
import random
import threading
import time
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
        self.switchTime=switchTime  #time between two state switches, dampens oszilations
        self.counter=0 #coutner for debugg and timing of switching, is used by other programs
        self.inverted=invert
        
        GPIO.setup(self.gpio,GPIO.OUT)
        if self.state==1:
            GPIO.output(self.gpio,GPIO.HIGH)
        else:
            GPIO.output(self.gpio,GPIO.LOW)
            
    def set_on(self):
        '''
        function that sets a single power channel on
        '''
        if self.inverted:
            GPIO.output(self.gpio,GPIO.LOW)
        else:
            GPIO.output(self.gpio,GPIO.HIGH)
        self.state=1
        
    def set_off(self):
        '''
        function that sets a single power channel off
        '''
        if self.inverted:
            GPIO.output(self.gpio,GPIO.HIGH)
        else:
            GPIO.output(self.gpio,GPIO.LOW)
        self.state=0

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
        counter=0n
        logging.debug('power state: initialzing')
        
        now=ut.convert_timestr_to_s(time.strftime('%H:%M:%S'))

        logging.debug('starting at intensity array  position: {}'.format(counter))
        start=1
        while not self.stopped.wait(self.frequency):
            self.lock.acquire()
            self.powerModule.status()
            if self.powerModule.statusTank==1:
                logging.debug('{} ALERT! water level in tank to high!'.format(time.strftime('%H:%M:%S')))
            
            if self.powerModule.statusSUMP==1:
                logging.debug('{} ALERT! water level in to low!'.format(time.strftime('%H:%M:%S')))
                            
        logging.debug('{} power control stopped'.format(time.strftime('%H:%M:%S')))

            

#time.sleep(10)
#stopFlag.set()

