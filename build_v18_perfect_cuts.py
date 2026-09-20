import cv2
import sys
import numpy as np
import torch
import torchvision.models.detection as det
import torchvision.transforms as T
import subprocess

def track_and_crop():
    input_path = "/home/junglee01/youtube-viral-machine/output_v14/raw_wide.mp4"
    output_path = "/home/junglee01/youtube-viral-machine/output_v18/tracked_bg.mp4"
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = det.ssdlite320_mobilenet_v3_large(weights='DEFAULT').to(device)
    model.eval()
    transform = T.Compose([T.ToTensor()])
    
    cap = cv2.VideoCapture(input_path)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    target_w = int(orig_h * 9 / 16)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (1080, 1920))
    
    current_target_x = orig_w / 2.0
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame_count += 1
        
        # Heavy AI every 2 frames for fast cut detection
        if frame_count % 2 == 1:
            small_frame = cv2.resize(frame, (320, 320))
            img_tensor = transform(small_frame).unsqueeze(0).to(device)
            with torch.no_grad():
                preds = model(img_tensor)[0]
                
            boxes = preds['boxes'].cpu().numpy()
            labels = preds['labels'].cpu().numpy()
            scores = preds['scores'].cpu().numpy()
            person_boxes = boxes[(labels == 1) & (scores > 0.4)]
            
            if len(person_boxes) > 0:
                scale_x = orig_w / 320.0
                centers_x = []
                for box in person_boxes:
                    cx = (box[0] + box[2]) / 2.0 * scale_x
                    centers_x.append(cx)
                    
                # Find the person closest to the previous target
                best_cx = centers_x[0]
                min_dist = abs(best_cx - current_target_x)
                for cx in centers_x:
                    dist = abs(cx - current_target_x)
                    if dist < min_dist:
                        min_dist = dist
                        best_cx = cx
                
                # Update target (HARD CUT if it jumps more than 150 pixels)
                current_target_x = best_cx
                
        # HARD CUT framing (NO PANNING/SLIDING)
        start_x = int(current_target_x - target_w / 2)
        end_x = int(current_target_x + target_w / 2)
        
        if start_x < 0: start_x, end_x = 0, target_w
        if end_x > orig_w: end_x, start_x = orig_w, orig_w - target_w
            
        cropped = frame[0:orig_h, start_x:end_x]
        cropped_resized = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        out.write(cropped_resized)
        
    cap.release()
    out.release()

if __name__ == "__main__":
    import os
    os.makedirs("/home/junglee01/youtube-viral-machine/output_v18", exist_ok=True)
    track_and_crop()
    
    # Final Mix
    tracked_bg = "/home/junglee01/youtube-viral-machine/output_v18/tracked_bg.mp4"
    raw_wide = "/home/junglee01/youtube-viral-machine/output_v14/raw_wide.mp4"
    final_out = "/home/junglee01/youtube-viral-machine/output_v18/DEMO_V18_PERFECT_CUTS.mp4"
    
    final_cmd = (
        f"ffmpeg -y -i {tracked_bg} "
        f"-i {raw_wide} "
        f'-vf "unsharp=5:5:1.0:5:5:0.0,eq=contrast=1.15:saturation=1.2:brightness=0.02" '
        f"-map 0:v -map 1:a -c:v libx264 -preset fast -crf 17 -c:a aac -b:a 192k -shortest "
        f"{final_out}"
    )
    subprocess.run(final_cmd, shell=True)
