import cv2
from camera import Camera1
from camera import Camera2
from utils import *
from datetime import datetime
import time
import threading
import sys
import Jetson.GPIO as GPIO
from threading import Thread, Lock

# Global variables:
fps = 15
focus = 0
output_path = "/home/user/Pictures/"
imagetime = ' '
restart_times = 0
selector = None
SnapTime = 2   # photos are snapped at this interval, seconds
width  = 1920
height = 1080

Cam1PhotoTime = 0.0     # Time of last photo from camera1, for watchdog
Cam2PhotoTime = 0.0     # Time of last photo from camera2, for watchdog
WatchDogPollTime = 10   # How often watch dog times are checked, seconds

# Thread synchronization using condition variables
condition1 = threading.Condition()   # Cam1Thread
condition2 = threading.Condition()   # Cam2Thread
PrintMutex = Lock()                  # Used to clean up screen printing


# nameCurrTime
# Compute name for photos
def nameCurrTime():
    now = datetime.now()
    return now.strftime("%Y%m%d_%H%M%S")
# End of nameCurrTime


# WatchDogThread
# Send a signal through GPIO to an external MCU.
# If the External MCU does not received this signal
# over a period of time, the reset pin will be toggled
# on the NVIDIA Jetson.
def WatchDogThread():
    print("WatchDogThread: starting")

    # Wait for camera threads to initialize and snap photos.
    time.sleep(WatchDogPollTime)

    while True:
        CurrentTime = time.time()
        Cam1DiffTime = CurrentTime - Cam1PhotoTime
        Cam2DiffTime = CurrentTime - Cam2PhotoTime

        if (Cam1DiffTime < WatchDogPollTime) and (Cam2DiffTime < WatchDogPollTime):
            # Pet the watch dog by sending a heartbeat signal
            # to the watchdog MCU.
            GPIO.output(12, GPIO.HIGH)
            time.sleep(0.5)  # Adjust as needed
            GPIO.output(12, GPIO.LOW)
            time.sleep(0.5)  # Adjust as needed
            PrintMutex.acquire()
            print("WatchDogThread: sending heartbeat")
            PrintMutex.release()
        else:
            PrintMutex.acquire()
            print("WatchDogThread: missed heartbeat")
            PrintMutex.release()
        # End of Else
        time.sleep(WatchDogPollTime)
    # End of While

    # Should never get here.
    PrintMutex.acquire()
    print("WatchDogThread: finished")
    PrintMutex.release()
# End of WatchDogThread


# Cam1Thread
# Capture images from Camera1
def Cam1Thread():
    global Cam1PhotoTime

    PrintMutex.acquire()
    print("Cam1Thread: starting")
    PrintMutex.release()

    cap = Camera1(0, selector)
    cap.set_width(width)
    cap.set_height(height)
    cap.set_fps(fps)
    cap.open()

    while not cap.isOpened():
        PrintMutex.acquire()
        print("Cam1Thread: Can't open camera1, retry after 1 second")
        PrintMutex.release()
        time.sleep(1)
        cap = Camera1(0, selector)
        cap.set_width(width)
        cap.set_height(height)
        cap.set_fps(fps)
        cap.open()
    # End of While

    while True:
        with condition1:
            condition1.wait()

            ret, frame = cap.read()
            if not ret:
                if restart_times != 0:
                    PrintMutex.acquire()
                    print("Cam1Thread: Unable to read video frame")
                    PrintMutex.release()
                    success = False
                    for i in range(1, restart_times + 1):
                        PrintMutex.acquire()
                        print(f"Cam1Thread: reopen {i} times")
                        PrintMutex.release()
                        try:
                            cap.reStart()
                            success = True
                            break
                        except:
                            continue
                    # End of For

                    if success:
                        continue
                    else:
                        PrintMutex.acquire()
                        print("Cam1Thread: reopen failed")
                        PrintMutex.release()
                # End of If - restart_times
            # End of If - ret

            cv2.imwrite(output_path + imagetime + "L.png", frame)
            Cam1PhotoTime = time.time()
            PrintMutex.acquire()
            print("Cam1Thread: Captured " + imagetime)
            PrintMutex.release()
                
            key = cv2.waitKey(1)                                            
            if key == ord("q"):
                break

        # End of With
    # End of While

    cap.release()
    PrintMutex.acquire()
    print("Cam1Thread: finished")
    PrintMutex.release()
# End of Cam1Thread


# Cam2Thread
# Capture images from Camera2
def Cam2Thread():
    global Cam2PhotoTime

    PrintMutex.acquire()
    print("Cam2Thread: starting")
    PrintMutex.release()

    cap = Camera2(2, selector)
    cap.set_width(width)
    cap.set_height(height)
    cap.set_fps(fps)
    cap.open()

    while not cap.isOpened():
        PrintMutex.acquire()
        print("Cam2Thread: Can't open camera1, retry after 1 second")
        PrintMutex.release()
        time.sleep(1)
        cap = Camera2(2, selector)
        cap.set_width(width)
        cap.set_height(height)
        cap.set_fps(fps)
        cap.open()
    # End of While

    while True:
        with condition2:
            condition2.wait()

            ret, frame = cap.read()
            if not ret:
                if restart_times != 0:
                    PrintMutex.acquire()
                    print("Cam2Thread: Unable to read video frame")
                    PrintMutex.release()
                    success = False
                    for i in range(1, restart_times + 1):
                        PrintMutex.acquire()
                        print(f"Cam2Thread: reopen {i} times")
                        PrintMutex.release()
                        try:
                            cap.reStart()
                            success = True
                            break
                        except:
                            continue
                    # End of For

                    if success:
                        continue
                    else:
                        PrintMutex.acquire()
                        print("Cam2Thread: reopen failed")
                        PrintMutex.release()
                # End of If - restart_times
            # End of If - ret

            cv2.imwrite(output_path + imagetime + "R.png", frame)
            Cam2PhotoTime = time.time()
            PrintMutex.acquire()
            print("Cam2Thread: Captured "+imagetime)
            PrintMutex.release()
                
            key = cv2.waitKey(1)                                            
            if key == ord("q"):
                break

        # End of With
    # End of While

    cap.release()
    PrintMutex.acquire()
    print("Cam2Thread: finished")
    PrintMutex.release()
# End of Cam2Thread


# TimerThread
def TimerThread():
    global imagetime

    PrintMutex.acquire()
    print("TimerThread: starting")
    PrintMutex.release()

    # Synchronize thread execution.
    NextTime = time.time() + SnapTime   # next photo snap time
    while True:
        imagetime = nameCurrTime()

        # Notify both threads to snap a photo
        with condition1:
            condition1.notify()   # notify Cam1Thread
        # End of With

        with condition2:
            condition2.notify()   # notify Cam2Thread
        # End of With

        # Sync to next photo snap time
        while time.time() < NextTime:
            time.sleep(0.1)
        # End of While

        NextTime = NextTime + SnapTime
    # End of while    

    # Should not get here...
    PrintMutex.acquire()
    print("TimerThread: finished")
    PrintMutex.release()
# End of TimerThread


# main()
# Main calling function.
def main():

    # Setup GPIO to send heartbeat to watchdog MCU
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(12, GPIO.OUT)

    # Create threads
    t0 = Thread(target=WatchDogThread, args=())
    t1 = Thread(target=Cam1Thread,     args=())
    t2 = Thread(target=Cam2Thread,     args=())
    t3 = Thread(target=TimerThread,    args=())

    # Start threads
    print("main: starting threads")
    t0.start()   # Start WatchDogThread
    t1.start()   # Start Cam1Thread
    t2.start()   # Start Cam2Thread
    t3.start()   # Start TimerThread

    # Wait for threads to finish
    PrintMutex.acquire()
    print("main: waiting for threads to finish")
    PrintMutex.release()
    #t0.join()   # WatchDogThread
    t1.join()    # Cam1Thread
    t2.join()    # Cam2Thread
    #t3.join()   # TimerThread

    print("main: exiting")
# End of main


# Execute main()
if __name__ == "__main__":
    sys.exit(main())
    
