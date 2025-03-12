import cv2
import argparse
from camera import Camera1
from camera import Camera2
from utils import *
from datetime import datetime
import time
import threading
import sys

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

#display_fps.start = time.monotonic()
#display_fps.frame_count = 0

# Thread synchronization using condition variables
condition1 = threading.Condition()   # Cam1Thread
condition2 = threading.Condition()   # Cam2Thread
PrintMutex = Lock()                  # Used to clean up screen printing


def nameCurrTime():
    now = datetime.now()
    return now.strftime("%Y%m%d_%H%M%S")
# End of nameCurrTime


# Cam1Thread
# Capture images from Camera1
def Cam1Thread():
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

        # Wait for next photo snap time
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
   
def main():
    global fps
    global focus
    global height
    global output_path
    global restart_times
    global selector
    global width

#    parser = argparse.ArgumentParser()
#    parser.add_argument('-W', '--width', type=int, required=False, default=0, help='set camera image width')
#    parser.add_argument('-H', '--height', type=int, required=False, default=0, help='set camera image height')
#    parser.add_argument('-d', '--DisplayWindow', type=validate_windows_size, required=False, default="800:600", help='Set the display window size, <width>:<height>')
#    parser.add_argument('-f', '--FrameRate', type=int, required=False, default=0, help='set camera frame rate')
#    parser.add_argument('-F', '--Focus', action='store_true', required=False, help='Add focus control on the display interface')
#    parser.add_argument('-i', '--index', type=int, required=False, default=0, help='set camera index')
#    parser.add_argument('-v', '--VideoCaptureAPI', type=int, required=False, default=0, choices=range(0, len(selector_list)), help=VideoCaptureAPIs)
#    parser.add_argument('-o', '--OutputPath', type=str, required=False, default="test.jpg", help="set save image path")
#    parser.add_argument('-t', '--reStartTimes', type=int, required=False, default=5, help="restart camera times")

#    args = parser.parse_args()
#    width = args.width
#    height = args.height
    # viewview_window_window = [int(i) for i in args.DisplayWindow.split(":")]
    #index = args.index
#    fps = args.FrameRate
#    focus = args.Focus
#    output_path = args.OutputPath
#    restart_times = args.reStartTimes
#    selector = selector_list[args.VideoCaptureAPI]

    # Create threads
    t1 = Thread(target=Cam1Thread,  args=())
    t2 = Thread(target=Cam2Thread,  args=())
    t3 = Thread(target=TimerThread, args=())

    # Start threads
    print("main: starting threads")
    t1.start()   # Start Cam1Thread
    t2.start()   # Start Cam2Thread
    t3.start()   # Start TimeThread

    # Wait for threads to finish
    PrintMutex.acquire()
    print("main: waiting for threads to finish")
    PrintMutex.release()
    t1.join()
    t2.join()
    t3.join()

    print("main: all threads finished")

    # print("main: calling destroyAllWindows()")
    # cv2.destroyAllWindows()
    print("main: exiting")
# End of main

# Execute main()
if __name__ == "__main__":
    sys.exit(main())
    
