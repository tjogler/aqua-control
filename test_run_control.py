#!/usr/bin/env python

from PyQt5.uic import loadUiType
import pyqtgraph as pg
import sys
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5 import QtGui, QtCore
from PyQt5 import  QtWidgets
import numpy as np

import logging
import random
import threading
import time
import utilities as ut
import light_control as lc

 

Ui_MainWindow, QMainWindow = loadUiType('AquaControl/mainwindow.ui')

WindowTemplate, TemplateBaseClass = pg.Qt.loadUiType('AquaControl/mainwindow.ui')
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class MainWindow(TemplateBaseClass):  
    def __init__(self):
        TemplateBaseClass.__init__(self)
        self.setWindowTitle('AquaControl')
        
        # Create the main window
        self.ui = WindowTemplate()
        self.ui.setupUi(self)
        self.ui.startBtn.clicked.connect(self.start)
        self.ui.stopBtn.clicked.connect(self.stop)
        self.stop=False
        
        self.show()
        self.ui.tabWidget.plotWidget.setXRange(0,250)
        self.ui.tabWidget.plotWidget.setYRange(0,1)
        
        
    def plot(self,x,y):
        self.ui.tabWidget.plotWidget.plot(x,y,pen='b')
        #self.plot.setData(x,y,clear=True)
        pg.QtGui.QApplication.processEvents()

    def start(self):
        self.stop=False
        
    def stop(self):
        self.stop=True
        

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.bthl.startBtn.clicked.connect(self.plot)
        self.show()

    def plot(self,data):
        self.plotW.plot(len(data),data,clear=True)

        
if __name__ == '__main__':
    

    #--------------------------------------
    #global variable definition
    intensityLamp=[]
    lockPi=threading.Lock()

    stopFlagLamp=threading.Event()

    cwhite=lc.lightChannel(name="white",resolution=1,sset="16:45")
    led=lc.lamp(cwhite)
    t=lc.RunLamp(stopFlagLamp,led,lockPi,data=intensityLamp)
    t.daemon=True
    t.start()
    timer=0
    run=True

    #plotIntens=pg.PlotWidget()
    
    app = QtWidgets.QApplication(sys.argv)

    main = MainWindow()
    #main.show()
    '''
    timer = QtCore.QTimer()
    def update():
        lockPi.acquire()
        main.plot(intensityLamp)
        lockPi.release()
    timer.timeout.connect(update)
    timer.start(0)
    if len(intensityLamp) >50:
        stopFlagLamp.set()
    '''
    counter=0
    while (main.stop==False):
        time.sleep(1)
        lockPi.acquire()
        #print intensityLamp[len(intensityLamp)-1],len(intensityLamp),intensityLamp
        xa=np.linspace(0,counter,len(intensityLamp))
        main.plot(xa,intensityLamp)
        #pg.QtGui.QApplication.processEvents()
        #print intensityLamp[len(intensityLamp)-1],len(intensityLamp),intensityLamp
        lockPi.release()
        counter+=1
    else:
        stopFlagLamp.set()    
    
    t.join() 
   
    sys.exit(app.exec_())
    
  
