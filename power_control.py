#!/usr/bin/env python

import logging
import threading
import time
import datetime
import numpy as np
import utilities as ut
import RPi.GPIO as GPIO
from Adafruit_PWM_Servo_Driver import PWM

#logging.basicConfig(level=logging.DEBUG,
 #                   format='(%(threadName)-10s) %(message)s',
                    #                   )
GPIO.setmode(GPIO.BCM)

class powerChannel(object):

    def __init__(self,name,gpio,number,state,inverted,switchTime,location,offtimes=[],timeoff=30):
        self.name=name
        self.gpio=gpio
        self.number=number
        self.state=state #default is on if not oserwise configured
        self.switchTime=datetime.timedelta(seconds=switchTime)  #time between two state switches, dampens oszilations, muste be a datetime.timedelta(seconds=xxx) object
        self.counter=0 #coutner for debugg and timing of switching, is used by other programs
        self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
        self.inverted=inverted
        self.errors=[]
        self.location=location #currently only SUMP is relevant
        logging.debug('Setting GPIO {} as OUTPUT'.format(self.gpio))
        GPIO.setup(self.gpio,GPIO.OUT)
        #switches channel off druing certain time intervals and swithces it back on after 30 miutes
        self.timeoff=timeoff
        self.offtimes=[]
        for off in offtimes:
            off=datetime.datetime.strptime(off,'%H:%M').time()
            if off.minute+self.timeoff > 59:
                minute=off.minute-self.timeoff
                hour=off.hour+1
                on=datetime.time(hour=hour,minute=minute)
            else:
                on=datetime.time(hour=off.hour,minute=off.minute+30)
            self.offtimes.append([off,on])
            logging.debug('Adding feeding time {} to RFP schedule'.format([off,on]))
        if self.state==1:
            self.set_on(atonce=True)
        else:
            self.set_off(atonce=True)
        
            
    def set_on(self,atonce=False):
        '''
        function that sets a single power channel on
        '''
        now=datetime.datetime.now().replace(microsecond=0)
        if atonce:
            if self.inverted:
                GPIO.output(self.gpio,GPIO.LOW)
            else:
                GPIO.output(self.gpio,GPIO.HIGH)
            self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
            self.state=1
        elif self.switchTime<(now-self.timeSwitched):
            if self.inverted:
                GPIO.output(self.gpio,GPIO.LOW)
            else:
                GPIO.output(self.gpio,GPIO.HIGH)
            self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
            self.state=1
        else:
            print 'WARNING: Switching time to short, no switching occured'
            self.errors.append(-1)
            
    def set_off(self,atonce=False): 
        '''
        function that sets a single power channel off
        '''
        now=datetime.datetime.now().replace(microsecond=0)
        if atonce:
            if self.inverted:
                GPIO.output(self.gpio,GPIO.HIGH)
            else:
                GPIO.output(self.gpio,GPIO.LOW)
            self.state=0
            self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
        elif self.switchTime<(now-self.timeSwitched):
            if self.inverted:
                GPIO.output(self.gpio,GPIO.HIGH)
            else:
                GPIO.output(self.gpio,GPIO.LOW)
            self.state=0
            self.timeSwitched=datetime.datetime.now().replace(microsecond=0)
        else:
            print 'WARNING: Switching time to short, no switching occured'
            self.errors=(-1)
            
    def toggle(self,atonce=False):
        '''
        functions that toggles the state of the channel
        '''
        if self.state==1:
            self.state=0
            self.set_off(atonce)
        else:
            self.state=1
            self.set_on(atonce)            
        
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
        
    def statusRead(self,verbose=True):
        self.statusTank=GPIO.input(self.readTank)
        self.statusSump=GPIO.input(self.readSump)
        if verbose:
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
        self.powerModule.status()
        self.counterAlarmTank=0
        now=datetime.datetime.now().replace(microsecond=0)
        self.counterAlarmTankTime=now
        self.counterAlarmSumpTime=now
        self.counterAlarmSump=0
        self.counterAlarmMax=3 # maximum number of alarms allowed within an hour
        self.counterAlarmResetTime=3600 #time in seconds after which the counterAlarms are reset to 0
        self.channelDeactivationListSump=[]
        
    def run(self):
        logging.debug('power control initializing at {}'.format(time.strftime('%Y %m %d %H:%M:%S')))
        counter=0
        logging.debug('power state: initialzing')
        
        #now=ut.convert_timestr_to_s(time.strftime('%H:%M:%S'))
        for c in self.powerModule.channel:
            if c.name=='RFP':
                rfp=c
                logging.debug('power initializing: RFP channel found')
                break
            
                
        while not self.stopped.wait(1):#self.frequency):
            self.lock.acquire()
            try:
                if counter<self.frequency:
                    self.powerModule.statusRead(verbose=False)
                    counter+=1
                else:
                    counter=0
                    self.powerModule.status()
                    #check if alarm counters should be reset
                    now=datetime.datetime.now().replace(microsecond=0)
                    logging.debug('time: {}'.format(now.time()))
                    for o in rfp.offtimes:
                        if o[0]<now.time() and o[1]>now.time():
                            if rfp.state==1:
                                rfp.set_off()
                                logging.debug('{} FEEDING power channel {} at gpio {} in state {} switched off!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                        if o[1]<now.time(): 
                            if rfp.state==0 and self.counterAlarmTank<self.counterAlarmMax:
                                 logging.debug('{} FEEDING STOPPED: power channel {} at gpio {} in state {} switched on again!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                                 rfp.set_on()
                    
                    if (now-self.counterAlarmTankTime).seconds>self.counterAlarmResetTime:
                        if self.counterAlarmTank==self.counterAlarmMax:
                           # rfp=self.powerModule.channel[self.powerModule.channel.name.index('RFP')]
                            rfp.set_on()
                        self.counterAlarmTank=0
                        self.counterAlarmTankTime=now
                        
                        
                    if (now-self.counterAlarmSumpTime).seconds>self.counterAlarmResetTime:
                        if self.counterAlarmSump==self.counterAlarmMax:
                            for c in self.channelDeactivationListSump:
                                try:
                                    c.set_on()
                                    self.channelDeactivationListSump.remove(c)
                                except:
                                    logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                                
                        self.counterAlarmSump=0
                        self.counterAlarmSumpTime=now
                    counter=0
                self.lock.release()
            except:
                self.lock.release()

            # Check water level Tank
            if self.powerModule.statusTank==0:
                logging.debug('{} ALERT! water level in tank to high!'.format(time.strftime('%Y %m %d %H:%M:%S')))
                self.counterAlarmTank+=1
                for c in self.powerModule.channel:
                    if 'RFP' in c.name:
                        self.lock.acquire()
                        try:
                            c.set_off()
                            logging.debug('{} RFP at gpio {} (state={} now) switched off!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.gpio,c.state))
                            time.sleep(c.switchTime.seconds+1) #prevents rapid switching due to water movement does only use switchTimes of less than a day
                            
                            if self.counterAlarmTank<= self.counterAlarmMax: #If problem with drain of tank persists, switch off RFP permanently 
                                c.set_on()
                            else:
                                logging.debug('{} RFP at gpio {} (state={} now) switched off for {} seconds due to reccuring water level ALERT in Tank!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.gpio,c.state,self.counterAlarmResetTime)) 
                            self.lock.release()
                        except:
                            logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched off!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                            self.lock.release()
                    if 'UeberlaufEntlueftung' in c.name:
                        self.lock.acquire()
                        try:
                            c.set_on()
                            logging.debug('{} Ueberlauf Entlueftung at gpio {} (state={} now) switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.gpio,c.state))
                            time.sleep(c.switchTime.seconds+1)
                            c.set_off()
                            logging.debug('{} Ueberlauf Entlueftung at gpio {} (state={} now) switched off!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.gpio,c.state))
                            if self.counterAlarmTank<= self.counterAlarmMax: #If problem with drain of tank persists, switch off RFP permanently 
                                rfp=self.powerModule.channel[self.powerModule.channel.name.index('RFP')]
                                rfp.set_on()
                                logging.debug('{} RFP at gpio {} (state={} now) switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.gpio,c.state))
                            else:
                               logging.debug('{} RFP at gpio {} (state={} now) switched off permanently due to reccuring water level ALERT in Tank!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.gpio,c.state)) 
                            self.lock.release()
                        except:
                             logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                             
                             self.lock.release()

            # Check water level Sump                 
            if self.powerModule.statusSump==1:
                logging.debug('{} ALERT! water level in sump to low!'.format(time.strftime('%Y %m %d %H:%M:%S')))
                switchTimeList=[]
                
                self.counterAlarmSump+=1
                for c in self.powerModule.channel:
                    if c.loaction=='SUMP':
                        self.lock.acquire()
                        try:
                            if c.status==1:
                                c.set_off()
                                switchTimeList.append(c.switchTime.seconds)
                                self.channelDeactivationListSump.append(c)
                                self.lock.release()
                        except:
                            logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                            self.lock.release()
                        self.lock.release()
                if switchTimeList!=[] and self.counterAlarmSump<=self.counterAlarmMax:
                    time.sleep(max(switchTimeList))
                    for c in self.channelDeactivationListSump:
                        if c.loaction=='SUMP':
                            self.lock.acquire()
                            try:
                                c.set_on()#turns only channels on that were turned off by this instance of this Alert
                                self.channelDeactivationListSump.remove(c)
                                self.lock.release()
                            except:
                                logging.debug('{} ERROR power channel {} at gpio {} in state {} can not be switched on!'.format(time.strftime('%Y %m %d %H:%M:%S'),c.name,c.gpio,c.state))
                            self.lock.release()
                        time.sleep(1) # do not switch to rapidly because of possible power surges
                else:
                    logging.debug('{} the following channels are deactivated {} due to reccuring {} water level alarm in SUMP they can be reactivated in {} seconds'.format(time.strftime('%Y %m %d %H:%M:%S'),self.channelDeactivationListSump,self.counterAlarmSump,self.counterAlarmResetTime))
                                
        logging.debug('{} power control stopped'.format(time.strftime('%Y %m %d %H:%M:%S')))

            

