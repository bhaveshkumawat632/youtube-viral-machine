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
    last_known_x = orig_w / 2
    
    transform = T.Compose([T.ToTensor()])
    
    frame_count = 0
    active_speaker_idx = 0 # 0 for first person, 1 for second
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # Switch speaker every ~3 seconds (90 frames)
        if frame_count % 90 == 0:
            active_speaker_idx = 1 - active_speaker_idx
        
        # Heavy AI every 6 frames
        if frame_count % 6 == 0:
            small_frame = cv2.resize(frame, (320, 320))
            img_tensor = transform(small_frame).unsqueeze(0).to(device)
            
            with torch.no_grad():
                preds = model(img_tensor)[0]
                
            boxes = preds['boxes'].cpu().numpy()
            labels = preds['labels'].cpu().numpy()
            scores = preds['scores'].cpu().numpy()
            
            # class 1 is person
            person_boxes = boxes[(labels == 1) & (scores > 0.3)]
            
            if len(person_boxes) > 0:
                # Sort boxes by X coordinate (left to right)
                centers = (person_boxes[:, 0] + person_boxes[:, 2]) / 2.0
                sorted_indices = np.argsort(centers)
                sorted_boxes = person_boxes[sorted_indices]
                
                # Pick the active speaker box
                idx = active_speaker_idx if active_speaker_idx < len(sorted_boxes) else 0
                box = sorted_boxes[idx]
                
                scale_x = orig_w / 320.0
                last_known_x = ((box[0] + box[2]) / 2.0) * scale_x
            
        # Fast snap pan (0.25) to simulate cinematic camera cut
        current_x = current_x * 0.75 + last_known_x * 0.25
        
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
