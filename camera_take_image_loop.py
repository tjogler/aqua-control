from picamera import PiCamera
from time import sleep

camera = PiCamera()



for counter in range (30):
    
    camera.start_preview()
    sleep(3)
    camera.exposure_mode = 'auto'
    camera.capture('/home/pi/Desktop/image_auto_{}.jpg'.format(counter))
    camera.stop_preview()
    sleep(86400)

