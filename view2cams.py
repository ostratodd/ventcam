import cv2
import subprocess

dev1 = "/dev/video0"
dev2 = "/dev/video2"

def v4l2_set(dev, ctrl, val):
    subprocess.run(f"v4l2-ctl -d {dev} --set-ctrl {ctrl}={val}".split(), check=False)

# Set max exposure/gain from what your camera allows
for dev in [dev1, dev2]:
    v4l2_set(dev, "exposure_auto", 1)
    v4l2_set(dev, "exposure_absolute", 5)   # increase if your camera supports more
    v4l2_set(dev, "gain", 100)                  # max usable gain
    v4l2_set(dev, "brightness", 64)
    v4l2_set(dev, "contrast", 32)
    v4l2_set(dev, "backlight_compensation", 1)

cap1 = cv2.VideoCapture(dev1, cv2.CAP_V4L2)
cap2 = cv2.VideoCapture(dev2, cv2.CAP_V4L2)

for cap in [cap1, cap2]:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 2)

while True:
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()

    if not ret1 or not ret2:
        print("Error grabbing frames.")
        break

    # Resize for monitor display
    frame1_small = cv2.resize(frame1, (640, 360))
    frame2_small = cv2.resize(frame2, (640, 360))
    stacked = cv2.hconcat([frame1_small, frame2_small])

    cv2.imshow("Stereo IMX462 - Scaled Display", stacked)
    if cv2.waitKey(1) == 27:  # ESC
        break

cap1.release()
cap2.release()
cv2.destroyAllWindows()
