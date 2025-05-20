import time
import cv2

class Camera1:

    def __init__(self, index=0, selector=cv2.CAP_ANY) -> None:
        self.index = index
        self.selector = selector
        self.cap = None
        self.width = None
        self.height = None
        self.fps = None
        self.expose = 50
        self.auto_expose = 0
        self.brightness = 0 #-64:64
        self.contrast = 10 #0:100
        self.wb_auto = 0
        self.wb_temp = 8000
        self.backlight = 1

    def open(self):
        self.cap = cv2.VideoCapture(self.index, self.selector)

        if self.width and self.height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if self.fps:
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
        if self.expose:
            self.cap.set(cv2.CAP_PROP_EXPOSURE, self.expose)
            
        if self.auto_expose:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, self.auto_expose)    
            
        if self.brightness:
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness)
            
        if self.contrast:
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.contrast)  
            
        if self.wb_auto:
            self.cap.set(cv2.CAP_PROP_AUTO_WB, self.wb_auto) 

        if self.wb_temp:
            self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, self.wb_temp) 
            
        if self.backlight:
            self.cap.set(cv2.CAP_PROP_BACKLIGHT, self.backlight)
    
    def set_width(self, width):
        self.width = width
    
    def set_height(self, height):
        self.height = height
    
    def set_fps(self, fps):
        self.fps = fps

    def set_expose(self, expose):
        self.expose = expose
        
    def set_auto(self, auto):
        self.auto = auto

    def set_focus(self, val):
        self.cap.set(cv2.CAP_PROP_FOCUS, val)

    def read(self):
        return self.cap.read()

    def reStart(self):
        self.release()
        time.sleep(0.5)
        self.open()

    def release(self):
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()

class Camera2:

    def __init__(self, index=2, selector=cv2.CAP_ANY) -> None:
        self.index = index
        self.selector = selector
        self.cap = None
        self.width = None
        self.height = None
        self.fps = None
        self.expose = 50
        self.auto_expose = 0
        self.brightness = 0 #-64:64
        self.contrast = 10 #0:100
        self.wb_auto = 0
        self.wb_temp = 3000
        self.backlight = 1

    def open(self):
        self.cap = cv2.VideoCapture(self.index, self.selector)

        if self.width and self.height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if self.fps:
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
        if self.expose:
            self.cap.set(cv2.CAP_PROP_EXPOSURE, self.expose)
           
        if self.auto_expose:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, self.auto_expose)
            
        if self.brightness:
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness)            

        if self.contrast:
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.contrast)   

        if self.wb_auto:
            self.cap.set(cv2.CAP_PROP_AUTO_WB, self.wb_auto) 

        if self.wb_temp:
            self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, self.wb_temp) 

        if self.backlight:
            self.cap.set(cv2.CAP_PROP_BACKLIGHT, self.backlight)
    
    def set_width(self, width):
        self.width = width
    
    def set_height(self, height):
        self.height = height
    
    def set_fps(self, fps):
        self.fps = fps
        
    def set_expose(self, expose):
        self.expose = expose

    def set_auto(self, auto):
        self.auto = auto        

    def set_focus(self, val):
        self.cap.set(cv2.CAP_PROP_FOCUS, val)

    def read(self):
        return self.cap.read()

    def reStart(self):
        self.release()
        time.sleep(0.5)
        self.open()

    def release(self):
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()
        
