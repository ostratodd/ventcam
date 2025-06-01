#!/usr/bin/env python3

import cv2
import os
import argparse
from datetime import datetime
import tkinter as tk

def get_screen_size():
    root = tk.Tk()
    root.withdraw()
    return root.winfo_screenwidth(), root.winfo_screenheight()

def parse_args():
    parser = argparse.ArgumentParser(description='Display paired L/R images as a video.')
    parser.add_argument('-d', '--directory', type=str, default='/home/jetson/Pictures',
                        help='Directory containing the images')
    parser.add_argument('-f', '--fps', type=int, default=5,
                        help='Frames per second (default: 5)')
    return parser.parse_args()

def extract_timestamp(filename):
    # Assumes format: YYYYMMDD_HHMMSSL.png
    try:
        base = os.path.basename(filename)
        timestamp_str = base[:-5]  # Remove L.png or R.png
        return datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
    except Exception:
        return None

def resize_to_fit(img, max_width, max_height):
    h, w = img.shape[:2]
    scale = min(max_width / w, max_height / h)
    return cv2.resize(img, (int(w * scale), int(h * scale)))

def main():
    args = parse_args()
    files = sorted(os.listdir(args.directory))

    # Group left and right images by timestamp
    left_images = {}
    right_images = {}
    for f in files:
        if f.endswith('.png'):
            full_path = os.path.join(args.directory, f)
            timestamp = extract_timestamp(f)
            if timestamp:
                if f.endswith('L.png'):
                    left_images[timestamp] = full_path
                elif f.endswith('R.png'):
                    right_images[timestamp] = full_path

    # Match timestamps with both L and R
    paired_timestamps = sorted(set(left_images.keys()) & set(right_images.keys()))
    if not paired_timestamps:
        print("No valid L/R image pairs found.")
        return

    screen_width, screen_height = get_screen_size()
    max_img_width = screen_width // 2  # Half screen per image
    delay = int(1000 / args.fps)

    for ts in paired_timestamps:
        imgL = cv2.imread(left_images[ts])
        imgR = cv2.imread(right_images[ts])

        if imgL is None or imgR is None:
            print(f"Warning: Could not read one of the pair at {ts}")
            continue

        imgL_resized = resize_to_fit(imgL, max_img_width, screen_height)
        imgR_resized = resize_to_fit(imgR, max_img_width, screen_height)

        # Match heights exactly for horizontal stacking
        target_height = min(imgL_resized.shape[0], imgR_resized.shape[0])
        imgL_resized = cv2.resize(imgL_resized, (int(imgL_resized.shape[1] * target_height / imgL_resized.shape[0]), target_height))
        imgR_resized = cv2.resize(imgR_resized, (int(imgR_resized.shape[1] * target_height / imgR_resized.shape[0]), target_height))


        combined = cv2.hconcat([imgL_resized, imgR_resized])

        # Format timestamp for display
        timestamp_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6  # small text
        font_thickness = 1
        text_color = (255, 255, 255)  # white
        bg_color = (0, 0, 0)  # black for background rectangle

        # Text size to determine background rectangle
        (text_width, text_height), _ = cv2.getTextSize(timestamp_str, font, font_scale, font_thickness)
        padding = 6
        cv2.rectangle(combined, 
                      (5, 5), 
                      (5 + text_width + padding, 5 + text_height + padding), 
                      bg_color, 
                      thickness=-1)
        cv2.putText(combined, 
                    timestamp_str, 
                    (8, 5 + text_height), 
                    font, 
                    font_scale, 
                    text_color, 
                    font_thickness, 
                    cv2.LINE_AA)

        cv2.imshow('Stereo Video', combined)

        key = cv2.waitKey(delay)
        if key == 27:  # ESC
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
