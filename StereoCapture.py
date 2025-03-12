import cv2
from camera import Camera1
from camera import Camera2
from utils import *
import Jetson.GPIO as GPIO
# import RPi.GPIO as GPIO

from datetime import datetime
import time
import threading
import sys
import psutil
import shutil
import calendar
# from pathlib import Path
import os
import configparser
from threading import Thread, Lock

# Global variables:
fps                = 15
focus              = 0
imagetime          = ' '
selector           = None
width              = 1920
height             = 1080

Cam1PhotoTime      = 0.0          # Time of last photo from camera1, for watchdog
Cam2PhotoTime      = 0.0          # Time of last photo from camera2, for watchdog
ConfigPath         = ""           # Config file path
DefaultPhotoPath   = ""           # SD card path to Pictures
FindDriveTimeSec   = 20           # How long to wait for OS to mount USB drive, seconds
LastFileTime       = 0.0          # Epoch time of the last write to ds.conf
PhotoPath          = ""           # Path to still Pictures
restart_times      = 3            # how many retries to read camera frame
SnapTime           = 2            # photos are snapped at this interval, seconds
USBPath            = ""           # path to USB drive, if it exists
WatchDogPollTime   = 10           # How often watch dog times are checked, seconds

# Configuration items - ds.conf
AutoExposure       = 0                       # CAP_PROP_AUTO_EXPOSURE, value varies by OS/camera
Backlight          = 0                       # Ultra Low Light mode = 1, Normal = 0
Exposure           = 0                       # CAP_PROP_EXPOSURE, value varies by OS/camera
MinimumFreeSpace   = 1000000000              # Minimum free space in bytes
MissionStart       = "01/01/1970 00:00:00"   # local date to start mission
MissionStartEpoch  = 0                       # MissionStart converted to epoch seconds
MissionEnd         = "01/01/1970 00:00:00"   # local date to start mission
MissionEndEpoch    = 0                       # MissionEnd converted to epoch seconds

# Thread synchronization using condition variables
condition1 = threading.Condition()   # Cam1Thread
condition2 = threading.Condition()   # Cam2Thread
LogMutex   = Lock()                  # Used to clean up screen printing


# LogWrite
# Write log events to file with a date and time.
# Future enhancement - add log events to a queue that will be written
# to file by a dedicated thread.
def LogWrite(strEvent):
    try:
#         ThreadID = threading.get_ident()   # get_native_id()
#         LogString = datetime.now().strftime("%Y/%m/%d,%H:%M:%S.%f")[:-3] + ',T' + str(ThreadID) +',' + strEvent
        LogString = datetime.now().strftime("%Y/%m/%d,%H:%M:%S.%f")[:-3] + ',' + strEvent
        LogMutex.acquire()
        print(LogString)
        LogMutex.release()
    except Exception as e:
        print("LogWrite: exception caught, strEvent="+ strEvent+", exception: " + str(e))
    except:
        print("LogWrite: exception caught, strEvent=", strEvent)
# End of LogWrite


# nameCurrTime
# Compute name for photos
def nameCurrTime():
    now = datetime.now()
    return now.strftime("%Y%m%d_%H%M%S")
# End of nameCurrTime


# ReadConfEP
# Read date/time value and return Unix Epoch from .conf file
def ReadConfEP(config, ConfigNameStr, FallbackStr):
    try:
        ConfigValStr = config.get('DS', ConfigNameStr, fallback=FallbackStr)

        if len(ConfigValStr) < 2:
            TimeEpoch = 0
            LogWrite('ReadConfEP: ' + ConfigNameStr + ' = 0')
        else:
            DateTimeObj = datetime.strptime(ConfigValStr, '%m/%d/%Y %H:%M:%S')
            TimeEpoch = calendar.timegm(DateTimeObj.timetuple()) + time.altzone
            if TimeEpoch <= 3600*24:
                LogWrite('ReadConfEP:  ' + ConfigNameStr + ' = 0')
                TimeEpoch = 0
            else:
                LogWrite('ReadConfEP: ' + ConfigNameStr + ' = ' + ConfigValStr + ', epoch=' + str(TimeEpoch))
            # End of Else
        # End of Else
        return TimeEpoch

    except Exception as e:
        LogWrite("ReadConfEP: exception caught - check " + ConfigNameStr + " time format, should be MM/DD/YYYY HH:MM:SS, exception: " + str(e))

    except:
        LogWrite("ReadConfEP: exception caught - check " + ConfigNameStr + " time format, should be MM/DD/YYYY HH:MM:SS")

    return 0
# End of ReadConfEP


# ReadConfFloat
# Read and return floating point value from .conf file
def ReadConfFloat(config, ConfigNameStr, FallbackInt):
    try:
        ConfigValStr = config.get('DS', ConfigNameStr, fallback=str(FallbackInt))
        LogWrite('ReadConfFloat: ' + ConfigNameStr + ' = ' + ConfigValStr)
        return float(ConfigValStr)

    except Exception as e:
        LogWrite("ReadConfFloat: exception caught - " + ConfigNameStr + ", exception: " + str(e))

    except:
        LogWrite("ReadConfFloat: exception caught - " + ConfigNameStr)

    return 0.0
# End of ReadConfFloat


# ReadConfInt
# Read and return integer value from .conf file
def ReadConfInt(config, ConfigNameStr, FallbackInt):
    try:
        ConfigValStr = config.get('DS', ConfigNameStr, fallback=str(FallbackInt))
        LogWrite('ReadConfInt: ' + ConfigNameStr + ' = ' + ConfigValStr)
        return int(ConfigValStr)

    except Exception as e:
        LogWrite("ReadConfInt: exception caught - " + ConfigNameStr + ", exception: " + str(e))

    except:
        LogWrite("ReadConfInt: exception caught - " + ConfigNameStr)

    return 0
# End of ReadConfInt


# ReadConf
def ReadConf():
    global AutoExposure
    global Backlight
    global Exposure
    global MinimumFreeSpace
    global MissionStartEpoch
    global MissionEndEpoch

    try:
        LogWrite("ReadConf: Start")
        config = configparser.ConfigParser()
        config.read(ConfigPath)

        AutoExposure      = ReadConfFloat(config, "AutoExposure",     AutoExposure)
        Backlight         = ReadConfInt  (config, "Backlight",        Backlight)
        Exposure          = ReadConfFloat(config, "Exposure",         Exposure)
        MinimumFreeSpace  = ReadConfInt  (config, "MinimumFreeSpace", MinimumFreeSpace)
        MissionStartEpoch = ReadConfEP   (config, "MissionStart",     MissionStart)
        MissionEndEpoch   = ReadConfEP   (config, "MissionEnd",       MissionEnd)

#         # Checks
#         if (AutoExposure < 0) or (AutoExposure > 1):
#             LogWrite('ReadConf: AutoExposure out of range; defaulting to 0 (AutoExposure=On).')
#             AutoExposure = 0
#         # End of If

#         if (Backlight < 0) or (Backlight > 1):
#             LogWrite('ReadConf: Backlight out of range; defaulting to 0 (Mode=Normal).')
#             Backlight = 0
#         # End of If

#         if (Exposure < -13) or (Exposure > 0):
#             LogWrite('ReadConf: Exposure out of range; defaulting to 0 (Exposure=1 second).')
#             Exposure = 0
#         # End of If

        if (MissionStartEpoch==0) and (MissionEndEpoch==0):
            LogWrite('ReadConf: MissionStart & MissionEnd times not set.')
        elif (MissionEndEpoch <= MissionStartEpoch):
            LogWrite('ReadConf: MissionEnd <= MissionStart, MissionEnd will not be used.')
        # End of Elif

    except Exception as e:
        LogWrite('ReadConf: exception caught, exception = ' + str(e))

    except:
        LogWrite('ReadConf: exception caught')

    LogWrite("ReadConf: End")
# End of ReadConf


# WatchDogThread
# Send a signal through GPIO to an external MCU.
# If the External MCU does not received this signal
# over a period of time, the reset pin will be toggled
# on the NVIDIA Jetson.
def WatchDogThread():
    LogWrite("WatchDogThread: starting")

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
            LogWrite("WatchDogThread: sending heartbeat")
        else:
            LogWrite("WatchDogThread: missed heartbeat")
        # End of Else
        time.sleep(WatchDogPollTime)
    # End of While

    # Should never get here.
    LogWrite("WatchDogThread: finished")
# End of WatchDogThread


# Move photo files from SD card to USB drive
def MovePhotos():
    global Cam1PhotoTime
    global Cam2PhotoTime

    # Develop list of photos to move.
    try:
        PhotoList = os.listdir(DefaultPhotoPath)
    except Exception as e:
        LogWrite("MovePhotos: exception caught, os.listdir(" + DefaultPhotoPath + ")," + str(e))
    except:
        LogWrite("MovePhotos: exception caught, os.listdir=(" + DefaultPhotoPath + ")")

    for PhotoFile in PhotoList:
        USBPictures = USBPath + "Pictures/"
        SrcFile  = DefaultPhotoPath + PhotoFile
        DestFile = USBPictures      + PhotoFile
        CopyError = False
        Cam1PhotoTime = time.time()   # Keep watchdog happy
        Cam2PhotoTime = time.time()   # Keep watchdog happy

        try:
            LogWrite("MovePhotos: copying " + SrcFile + " to " + DestFile)
            shutil.copyfile(SrcFile, DestFile)
        except Exception as e:
            CopyError = True
            LogWrite("MovePhotos: exception caught copying '" + SrcFile + "', " + str(e))
        except:
            CopyError = True
            LogWrite("MovePhotos: exception caught copying '" + SrcFile + "'")

        if not CopyError:
            try:
                LogWrite("MovePhotos: removing " + SrcFile)
                os.remove(SrcFile)
            except Exception as e:
                LogWrite("MovePhotos: exception caught removing '" + SrcFile + "', " + str(e))
            except:
                LogWrite("MovePhotos: exception caught removing '" + SrcFile + "'")
        # End of If
    # End of For
# End of MovePhotos


def FindMediaFolder(TimeoutSec):
    EndCheckTime = time.time() + TimeoutSec
    
    while (EndCheckTime > time.time()):
        MediaDirList = os.listdir("/media/")

        for element in MediaDirList:
            HomeMediaDir = str("/media/" + element)
            if os.path.isdir(HomeMediaDir):
                #LogWrite("FindMediaFolder: HomeMediaDir =", HomeMediaDir)
                return(HomeMediaDir)
            # End of If
        # End of For
    # End of While

    LogWrite("FindMediaFolder: no home media folder")
    return ''
# End of Function - FindMediaFolder


# FindDrive
# Find attached USB drive.
def FindDrive(TimeoutSec):
    global Cam1PhotoTime
    global Cam2PhotoTime
    global PhotoPath
    global USBPath

    USBPath   = ""
    PhotoPath = DefaultPhotoPath
    LogRetry = True

    EndCheckTime = time.time() + TimeoutSec
    DriveFound = False
    
    HomeMediaFolder = FindMediaFolder(TimeoutSec)
    if HomeMediaFolder == '':
        LogWrite("No media folder, using SD card instead.")
        return
    # End of If

    LogWrite("FindDrive: HomeMediaFolder = " + HomeMediaFolder)
    
    while (EndCheckTime > time.time()) and not DriveFound:
        MediaDir = os.listdir(HomeMediaFolder)
        
        for element in MediaDir:
            if os.path.isdir(str(HomeMediaFolder + '/' + element)):
                try:
                    USBPath = HomeMediaFolder + '/' + element + '/'
                    LogWrite("FindDrive: potential USB drive found at " + USBPath)

                    USBPictures = USBPath + "Pictures"

                    # Create USB Folders
                    if not os.path.exists(USBPictures):
                        LogWrite("FindDrive: mkdir " + USBPictures)
                        os.mkdir(USBPictures)

                    MovePhotos()
                    
                    PhotoPath  = USBPath + "Pictures/"
                    DriveFound = True
                    break   # break out of for-loop

                except Exception as e:
                    LogWrite("FindDrive: exception caught, " + str(e))

                except:
                    LogWrite("FindDrive: exception caught")
                
                # End try-except

            else:
                LogWrite("FindDrive: " + USBPath + " is not a drive")
            # End of Else
        # End of For

        if not DriveFound:
            time.sleep(1)   # wait a second and try again
            Cam1PhotoTime = time.time()   # keep watchdog happy
            Cam2PhotoTime = time.time()   # keep watchdog happy
            if LogRetry:
                LogWrite("FindDrive: writeable drive not found, retry for 20 seconds...")
                LogRetry = False
            #  End of If
        # End of If
    # End of While

    LogWrite("FindDrive: setting PhotoPath = " + PhotoPath)
# End of FindDrive


# Cam1Thread
# Capture images from Camera1
def Cam1Thread():
    global Cam1PhotoTime

    LogWrite("Cam1Thread: starting")

    cap = Camera1(0, selector)
    cap.set_width(width)
    cap.set_height(height)
    cap.set_fps(fps)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, AutoExposure)
    cap.set(cv2.CAP_PROP_EXPOSURE,      Exposure)
    cap.set(cv2.CAP_PROP_BACKLIGHT,     Backlight)
    cap.open()

    while not cap.isOpened():
        LogWrite("Cam1Thread: Can't open camera1, retry after 1 second")
        time.sleep(1)
        cap = Camera1(0, selector)
        cap.set_width(width)
        cap.set_height(height)
        cap.set_fps(fps)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, AutoExposure)
        cap.set(cv2.CAP_PROP_EXPOSURE,      Exposure)
        cap.set(cv2.CAP_PROP_BACKLIGHT,     Backlight)
        cap.open()
    # End of While

    while True:
        with condition1:
            condition1.wait()

            ret, frame = cap.read()
            if not ret:
                if restart_times != 0:
                    LogWrite("Cam1Thread: Unable to read video frame")
                    success = False
                    for i in range(1, restart_times + 1):
                        LogWrite("Cam1Thread: reopen " + str(i) + " time(s)")
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
                        LogWrite("Cam1Thread: reopen failed")
                # End of If - restart_times
            # End of If - ret

            cv2.imwrite(PhotoPath + imagetime + "L.png", frame)
            Cam1PhotoTime = time.time()   # keep watchdog happy
            LogWrite("Cam1Thread: Captured " + PhotoPath + imagetime + "L.png")

            key = cv2.waitKey(1)                                            
            if key == ord("q"):
                break

        # End of With
    # End of While

    cap.release()
    LogWrite("Cam1Thread: finished")
# End of Cam1Thread


# Cam2Thread
# Capture images from Camera2
def Cam2Thread():
    global Cam2PhotoTime

    LogWrite("Cam2Thread: starting")

    cap = Camera2(2, selector)
    cap.set_width(width)
    cap.set_height(height)
    cap.set_fps(fps)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, AutoExposure)
    cap.set(cv2.CAP_PROP_EXPOSURE,      Exposure)
    cap.set(cv2.CAP_PROP_BACKLIGHT,     Backlight)
    cap.open()

    while not cap.isOpened():
        LogWrite("Cam2Thread: Can't open camera2, retry after 1 second")
        time.sleep(1)
        cap = Camera2(2, selector)
        cap.set_width(width)
        cap.set_height(height)
        cap.set_fps(fps)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, AutoExposure)
        cap.set(cv2.CAP_PROP_EXPOSURE,      Exposure)
        cap.set(cv2.CAP_PROP_BACKLIGHT,     Backlight)
        cap.open()
    # End of While

    while True:
        with condition2:
            condition2.wait()

            ret, frame = cap.read()
            if not ret:
                if restart_times != 0:
                    LogWrite("Cam2Thread: Unable to read video frame")
                    success = False
                    for i in range(1, restart_times + 1):
                        LogWrite("Cam2Thread: reopen " + str(i) + " time(s)")
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
                        LogWrite("Cam2Thread: reopen failed")
                # End of If - restart_times
            # End of If - ret

            cv2.imwrite(PhotoPath + imagetime + "R.png", frame)
            Cam2PhotoTime = time.time()   # keep watchdog happy
            LogWrite("Cam2Thread: Captured " + PhotoPath + imagetime + "R.png")
                
            key = cv2.waitKey(1)                                            
            if key == ord("q"):
                break

        # End of With
    # End of While

    cap.release()
    LogWrite("Cam2Thread: finished")
# End of Cam2Thread


# TimerThread
# Time the execution of the camera threads, and check for
# conditions that will cause photo capture to cease.
def TimerThread():
    global Cam1PhotoTime
    global Cam2PhotoTime
    global imagetime
    global LastFileTime

    LogWrite("TimerThread: starting")

    NextTime = time.time() + SnapTime   # next photo snap time

    # Read configuration
    if os.path.exists(ConfigPath):
        ReadConf()
        LastFileTime = os.path.getmtime(ConfigPath)
    else:
        LogWrite("TimerThread: " + ConfigPath + " does not exist")
        LastFileTime = 0
    # End of Else

    while True:
        CurrentTime = time.time()

        FreeSpace = psutil.disk_usage(PhotoPath).free
        if FreeSpace > MinimumFreeSpace:
            # The drive has sufficient free space
            # Check MissionStart and MissionEnd times
            if CurrentTime > MissionStartEpoch:
                # Current time is past MissionStart time
                if MissionEndEpoch != 0:
                    if MissionEndEpoch > CurrentTime:
                        # Notify both threads to snap a photo
                        imagetime = nameCurrTime()
                        with condition1: condition1.notify()   # notify Cam1Thread
                        with condition2: condition2.notify()   # notify Cam2Thread
                    else:
                        LogWrite("TimerThread: past MissionEnd")
                        Cam1PhotoTime = CurrentTime   # keep watchdog happy
                        Cam2PhotoTime = CurrentTime   # keep watchdog happy
                    # End of Else
                else:
                    # MissionEnd time not specified.
                    # Notify both threads to snap a photo
                    imagetime = nameCurrTime()
                    with condition1: condition1.notify()   # notify Cam1Thread
                    with condition2: condition2.notify()   # notify Cam2Thread
            else:
                LogWrite("TimerThread: awaiting MissionStart")
                Cam1PhotoTime = CurrentTime   # keep watchdog happy
                Cam2PhotoTime = CurrentTime   # keep watchdog happy
            # End of Else

        else:
            Cam1PhotoTime = CurrentTime   # keep watchdog happy
            Cam2PhotoTime = CurrentTime   # keep watchdog happy
            LogWrite("TimerThread: below minimum free space, free space = " + str(FreeSpace))
        # End of Else

        # Check for changes in ds.conf
        if os.path.exists(ConfigPath):
            FileTime = os.path.getmtime(ConfigPath)
            if FileTime != LastFileTime:
                # File change detected - read config file.
                LogWrite("TimerThread: config change detected")
                LastFileTime = FileTime
                ReadConf()
            # End of Else
        # End of If                

        # Sync to next photo snap time
        SleepTime = NextTime - time.time()
        if SleepTime > 0:
            time.sleep(SleepTime)
        # End of While

        NextTime = NextTime + SnapTime
    # End of while    

    # Should not get here...
    LogWrite("TimerThread: finished")
# End of TimerThread


# main()
# Main calling function.
def main():
    global ConfigPath
    global DefaultPhotoPath
    global PhotoPath

    # Setup GPIO to send heartbeat to watchdog MCU
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(12, GPIO.OUT)
    
    t0 = Thread(target=WatchDogThread, args=())
    t0.start()   # Start WatchDogThread

    # Setup default PhotoPath (to SD card)
    HomePath = "/user/home"   # str(Path.home())
    ConfigPath = HomePath + "/ds.conf"   # HomePath + "/Desktop/ds.conf"
    DefaultPhotoPath = HomePath + '/Pictures/'
    PhotoPath = DefaultPhotoPath
    LogWrite("main: ConfigPath = " + ConfigPath)
    LogWrite("main: DefaultPhotoPath = " + PhotoPath)

    # Look for an external USB drive. If a drive is found
    # PhotoPath will be pointed to it.
    #FindDrive(FindDriveTimeSec)
    #LogWrite("main: final PhotoPath = ", PhotoPath)

    # Create threads
    t1 = Thread(target=Cam1Thread,     args=())
    t2 = Thread(target=Cam2Thread,     args=())
    t3 = Thread(target=TimerThread,    args=())

    # Start threads
    LogWrite("main: starting threads")
    t1.start()   # Start Cam1Thread
    t2.start()   # Start Cam2Thread
    t3.start()   # Start TimerThread

    # Wait for threads to finish
    LogWrite("main: waiting for threads to finish")
    #t0.join()   # WatchDogThread
    t1.join()    # Cam1Thread
    t2.join()    # Cam2Thread
    #t3.join()   # TimerThread

    LogWrite("main: exiting")
# End of main


# Execute main()
if __name__ == "__main__":
    sys.exit(main())
    
