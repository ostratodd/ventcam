import time
import Jetson.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)

while True:
    GPIO.output(12, GPIO.HIGH)
    time.sleep(0.5)  # Adjust as needed
    GPIO.output(12, GPIO.LOW)
    time.sleep(0.5)  # Adjust as needed