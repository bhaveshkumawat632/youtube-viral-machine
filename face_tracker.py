import cv2
import sys
import numpy as np
import subprocess
import shutil
import os

def track_and_crop(input_path, output_path):
    print(f"Tracking motion in {input_path}...")
    cap = cv2.VideoCapture(input_path)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    target_w = int(orig_h * 9 / 16)
    target_h = orig_h
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    temp_out = output_path.replace(".mp4", "_temp.mp4")
    out = cv2.VideoWriter(temp_out, fourcc, fps, (1080, 1920))
    
    current_x = orig_w / 2
    
    ret, prev_frame = cap.read()
    if not ret:
        return
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(curr_gray, prev_gray)
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        M = cv2.moments(thresh)
        if M["m00"] > 1000: # Threshold for noise
            target_x = int(M["m10"] / M["m00"])
        else:
            target_x = orig_w / 2
            
        # Smooth tracking (Pan effect)
        current_x = current_x * 0.95 + target_x * 0.05
        
        start_x = int(current_x - target_w / 2)
        end_x = int(current_x + target_w / 2)
        
        if start_x < 0:
            start_x = 0
            end_x = target_w
        if end_x > orig_w:
            end_x = orig_w
            start_x = orig_w - target_w
            
        cropped = frame[0:target_h, start_x:end_x]
        cropped_resized = cv2.resize(cropped, (1080, 1920))
        out.write(cropped_resized)
        
        prev_gray = curr_gray
        
    cap.release()
    out.release()
    
    print("Muxing audio back...")
    subprocess.run(f"ffmpeg -y -i {temp_out} -i {input_path} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0? -shortest {output_path}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(output_path):
        os.remove(temp_out)
    else:
        shutil.move(temp_out, output_path)

if __name__ == "__main__":
    track_and_crop(sys.argv[1], sys.argv[2])
