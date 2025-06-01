#!/usr/bin/env python3

import cv2
import subprocess
import time
import argparse
import glob
import os
import configparser
import tkinter as tk


def list_video_devices():
    devices = sorted(glob.glob("/dev/video*"))
    usable = []
    for dev in devices:
        try:
            formats = subprocess.run(["v4l2-ctl", "-d", dev, "--list-formats"],
                                     capture_output=True, text=True, timeout=1)
            if any(fmt in formats.stdout for fmt in ["YUYV", "MJPG"]):
                usable.append(dev)
        except:
            continue
    return usable

def v4l2_set(dev, ctrl, val):
    subprocess.run(["v4l2-ctl", "-d", dev, f"--set-ctrl={ctrl}={val}"],
                   capture_output=True, text=True)

def v4l2_get(dev, ctrl):
    result = subprocess.run(["v4l2-ctl", "-d", dev, f"--get-ctrl={ctrl}"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None

def apply_autofocus_settings(dev):
    v4l2_set(dev, "auto_exposure", 0)
    v4l2_set(dev, "white_balance_automatic", 1)
    v4l2_set(dev, "gain", 30)
    v4l2_set(dev, "exposure_time_absolute", 20)

def apply_settings_from_conf(dev, conf_path="ds.conf"):
    config = configparser.ConfigParser()
    config.read(conf_path)
    ds = config["DS"]

    def getval(key, cast_type=int, default=None):
        try:
            return cast_type(ds[key])
        except:
            return default

    v4l2_set(dev, "auto_exposure", getval("AutoExposure", int, 1))
    v4l2_set(dev, "exposure_time_absolute", getval("Exposure", int, 2000))
    v4l2_set(dev, "gain", getval("Gain", int, 3000))
    v4l2_set(dev, "white_balance_automatic", getval("WhiteBalanceAutomatic", int, 0))
    v4l2_set(dev, "brightness", getval("Brightness", int, 64))
    v4l2_set(dev, "contrast", getval("Contrast", int, 32))

# Detect screen size using tkinter
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()

# --- Argument parser ---
parser = argparse.ArgumentParser()
parser.add_argument("--focus1", action="store_true", help="Only display camera 1 with auto exposure")
parser.add_argument("--focus2", action="store_true", help="Only display camera 2 with auto exposure")
args = parser.parse_args()

# --- Get devices ---
video_devices = list_video_devices()
if len(video_devices) < 2:
    raise RuntimeError("Need at least two valid /dev/video* devices")

dev1, dev2 = video_devices[0], video_devices[1]
print(f"[INFO] Using devices: {dev1} and {dev2}")

# --- Open cameras ---
cap1 = cv2.VideoCapture(dev1)
cap2 = cv2.VideoCapture(dev2)
time.sleep(1)

# --- Apply settings ---
if args.focus1:
    apply_autofocus_settings(dev1)
    apply_autofocus_settings(dev2)
elif args.focus2:
    apply_autofocus_settings(dev1)
    apply_autofocus_settings(dev2)
else:
    for dev in [dev1, dev2]:
        apply_settings_from_conf(dev)

# Gather and format camera settings
ae = v4l2_get(dev1, "auto_exposure")
et = v4l2_get(dev1, "exposure_time_absolute")
g  = v4l2_get(dev1, "gain")
wb = v4l2_get(dev1, "white_balance_automatic")
br = v4l2_get(dev1, "brightness")
co = v4l2_get(dev1, "contrast")
settings_text = f"AE:{ae} ET:{et} Gain:{g} WB:{wb} Br:{br} Co:{co}"

# --- FPS and resolution ---
for cap in [cap1, cap2]:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 1)

font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
font_color = (255, 255, 255)
line_type = 1
bg_color = (0, 0, 0)

# --- Main loop ---
while True:
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()

    if args.focus1:
        if not ret1:
            print("[ERROR] Failed to read camera 1")
            break
        frame1_resized = cv2.resize(frame1, (screen_width, screen_height))
        (w, h), _ = cv2.getTextSize(settings_text, font, font_scale, line_type)
        cv2.rectangle(frame1_resized, (5, 5), (5 + w + 10, 5 + h + 10), bg_color, -1)
        cv2.putText(frame1_resized, settings_text, (10, 20), font, font_scale, font_color, line_type)
        cv2.imshow("Focus: Camera 1", frame1_resized)

    elif args.focus2:
        if not ret2:
            print("[ERROR] Failed to read camera 2")
            break
        frame2_resized = cv2.resize(frame2, (screen_width, screen_height))
        (w, h), _ = cv2.getTextSize(settings_text, font, font_scale, line_type)
        cv2.rectangle(frame2_resized, (5, 5), (5 + w + 10, 5 + h + 10), bg_color, -1)
        cv2.putText(frame2_resized, settings_text, (10, 20), font, font_scale, font_color, line_type)
        cv2.imshow("Focus: Camera 2", frame2_resized)

    else:
        if not ret1 or not ret2:
            print("[ERROR] Failed to grab both frames")
            break
        half_width = screen_width // 2
        height = int(screen_height * 0.9)
        small1 = cv2.resize(frame1, (half_width, height))
        small2 = cv2.resize(frame2, (half_width, height))

        (w, h), _ = cv2.getTextSize(settings_text, font, font_scale, line_type)
        for img in [small1, small2]:
            cv2.rectangle(img, (5, 5), (5 + w + 10, 5 + h + 10), bg_color, -1)
            cv2.putText(img, settings_text, (10, 20), font, font_scale, font_color, line_type)

        stacked = cv2.hconcat([small1, small2])
        cv2.imshow("Stereo IMX462", stacked)

    if cv2.waitKey(1) == 27:
        break

cap1.release()
cap2.release()
cv2.destroyAllWindows()
