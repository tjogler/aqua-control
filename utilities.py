import time
import numpy as np

def convert_timestr_to_s(time):
        '''converts HH:MM:SS string to s in int'''
        factor=3600
        res=0
        for t in time.split(':'):
            res+=int(t)*factor
            factor/=60
        return res
