import cv2
import sys
import numpy as np
import torch
import torchvision.models.detection as det
import torchvision.transforms as T

def track_and_crop(input_path):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = det.ssdlite320_mobilenet_v3_large(weights='DEFAULT')
    model = model.to(device)
    model.eval()
    
    cap = cv2.VideoCapture(input_path)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    target_w = int(orig_h * 9 / 16)
    target_h = orig_h
    
    current_x = orig_w / 2
    target_x = orig_w / 2
    
    transform = T.Compose([T.ToTensor()])
    
    frame_count = 0
    
    prev_gray = None
    speaker_scores = {}
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Heavy AI every 3 frames
        if frame_count % 3 == 0:
            small_frame = cv2.resize(frame, (320, 320))
            img_tensor = transform(small_frame).unsqueeze(0).to(device)
            
            with torch.no_grad():
                preds = model(img_tensor)[0]
                
            boxes = preds['boxes'].cpu().numpy()
            labels = preds['labels'].cpu().numpy()
            scores = preds['scores'].cpu().numpy()
            
            person_boxes = boxes[(labels == 1) & (scores > 0.3)]
            
            if len(person_boxes) > 0:
                scale_x = orig_w / 320.0
                scale_y = orig_h / 320.0
                
                best_motion = -1
                best_center_x = target_x
                
                if prev_gray is not None:
                    # Calculate motion for each person
                    for box in person_boxes:
                        x1 = int(box[0] * scale_x)
                        y1 = int(box[1] * scale_y)
                        x2 = int(box[2] * scale_x)
                        y2 = int(box[3] * scale_y)
                        
                        # Extract face region (top 30% of bounding box)
                        face_y2 = y1 + int((y2 - y1) * 0.3)
                        
                        # Clip to bounds
                        x1 = max(0, x1)
                        y1 = max(0, y1)
                        x2 = min(orig_w, x2)
                        face_y2 = min(orig_h, face_y2)
                        
                        if x2 > x1 and face_y2 > y1:
                            curr_face = gray[y1:face_y2, x1:x2]
                            prev_face = prev_gray[y1:face_y2, x1:x2]
                            
                            diff = cv2.absdiff(curr_face, prev_face)
                            motion = np.sum(diff) / (diff.size + 1)
                            
                            if motion > best_motion:
                                best_motion = motion
                                best_center_x = (x1 + x2) / 2.0
                                
                    if best_motion > 5.0: # Threshold for speaking motion
                        target_x = best_center_x
                else:
                    # If no prev_gray, just default to largest person
                    areas = (person_boxes[:, 2] - person_boxes[:, 0]) * (person_boxes[:, 3] - person_boxes[:, 1])
                    best_idx = np.argmax(areas)
                    box = person_boxes[best_idx]
                    target_x = ((box[0] + box[2]) / 2.0) * scale_x
        
        prev_gray = gray
        
        # Smooth camera panning to the active speaker
        current_x = current_x * 0.90 + target_x * 0.10
        
        start_x = int(current_x - target_w / 2)
        end_x = int(current_x + target_w / 2)
        
        if start_x < 0:
            start_x = 0
            end_x = target_w
        if end_x > orig_w:
            end_x = orig_w
            start_x = orig_w - target_w
            
        cropped = frame[0:target_h, start_x:end_x]
        cropped_resized = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        
        sys.stdout.buffer.write(cropped_resized.tobytes())
        
    cap.release()

if __name__ == "__main__":
    track_and_crop(sys.argv[1])
