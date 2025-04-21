import cv2

# Change these indices to match your setup
cap1 = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(1)

def max_sensitivity(cam):
    # Manual exposure mode (0.25 means manual on many UVC drivers)
    cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)

    # Set very long exposure (experiment: try down to -13 for very dark)
    cam.set(cv2.CAP_PROP_EXPOSURE, -10)  # -13 = longest, -1 = shortest

    # High gain
    cam.set(cv2.CAP_PROP_GAIN, 15.0)  # Some cams go up to 20+

    # Optional: disable auto white balance
    cam.set(cv2.CAP_PROP_AUTO_WB, 0)
    cam.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 4000)

    # Optional: reduce frame rate to support long exposure (works better on Linux)
    cam.set(cv2.CAP_PROP_FPS, 5)

    # Optional: set brightness/contrast to neutral or low
    cam.set(cv2.CAP_PROP_BRIGHTNESS, 0.1)
    cam.set(cv2.CAP_PROP_CONTRAST, 0.3)

max_sensitivity(cap1)
max_sensitivity(cap2)

while True:
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()

    if not ret1 or not ret2:
        print("Error grabbing frames.")
        break

    combined = cv2.hconcat([
        cv2.resize(frame1, (640, 480)),
        cv2.resize(frame2, (640, 480))
    ])

    cv2.imshow("Watec-mode IMX462", combined)
    if cv2.waitKey(1) == 27:  # ESC
        break

cap1.release()
cap2.release()
cv2.destroyAllWindows()

