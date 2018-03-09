#!/usr/bin/env python
import time
import numpy as np
import utilities as ut
from Adafruit_PWM_Servo_Driver import PWM


pwm=PWM(0x41)
pwm.setPWMFreq(500)


for k in range(5):
    
    for i in range(5):
        pwm.setPWM(k,0,256)
        print "channel {} intensity 256".format(k)
        time.sleep(5)
        pwm.setPWM(k,0,4095)
        print 'channel {} intensity 4095'.format(k)
        time.sleep(5)

    pwm.setPWM(k,0,0)
           
