import cv2
import sys
import numpy as np
import torch
import torchvision.models.detection as det
import torchvision.transforms as T

def compute_iou(box1, box2):
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
        
    intersection = (x_right - x_left) * (y_bottom - y_top)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    return intersection / float(area1 + area2 - intersection)

def track_and_crop(input_path):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = det.ssdlite320_mobilenet_v3_large(weights='DEFAULT').to(device)
    model.eval()
    transform = T.Compose([T.ToTensor()])
    
    cap = cv2.VideoCapture(input_path)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    target_w = int(orig_h * 9 / 16)
    
    current_x = orig_w / 2.0
    target_x = orig_w / 2.0
    last_box = None
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame_count += 1
        
        # Heavy AI every 2 frames for precision
        if frame_count % 2 == 1:
            small_frame = cv2.resize(frame, (320, 320))
            img_tensor = transform(small_frame).unsqueeze(0).to(device)
            with torch.no_grad():
                preds = model(img_tensor)[0]
                
            boxes = preds['boxes'].cpu().numpy()
            labels = preds['labels'].cpu().numpy()
            scores = preds['scores'].cpu().numpy()
            person_boxes = boxes[(labels == 1) & (scores > 0.3)]
            
            if len(person_boxes) > 0:
                scale_x, scale_y = orig_w / 320.0, orig_h / 320.0
                scaled_boxes = person_boxes.copy()
                scaled_boxes[:, 0] *= scale_x
                scaled_boxes[:, 2] *= scale_x
                scaled_boxes[:, 1] *= scale_y
                scaled_boxes[:, 3] *= scale_y
                
                if last_box is None:
                    # Pick largest person
                    areas = (scaled_boxes[:, 2] - scaled_boxes[:, 0]) * (scaled_boxes[:, 3] - scaled_boxes[:, 1])
                    best_idx = np.argmax(areas)
                    last_box = scaled_boxes[best_idx]
                else:
                    # Pick person with highest IOU to last_box
                    best_iou = 0
                    best_idx = -1
                    for i, box in enumerate(scaled_boxes):
                        iou = compute_iou(last_box, box)
                        if iou > best_iou:
                            best_iou = iou
                            best_idx = i
                            
                    if best_iou > 0.1:
                        last_box = scaled_boxes[best_idx]
                    else:
                        # Fallback to largest if we lost the target completely
                        areas = (scaled_boxes[:, 2] - scaled_boxes[:, 0]) * (scaled_boxes[:, 3] - scaled_boxes[:, 1])
                        last_box = scaled_boxes[np.argmax(areas)]
                        
                target_x = (last_box[0] + last_box[2]) / 2.0

        # Ultra-smooth cinematic pan (stronger smoothing)
        current_x = current_x * 0.92 + target_x * 0.08
        
        start_x = int(current_x - target_w / 2)
        end_x = int(current_x + target_w / 2)
        
        if start_x < 0: start_x, end_x = 0, target_w
        if end_x > orig_w: end_x, start_x = orig_w, orig_w - target_w
            
        cropped = frame[0:orig_h, start_x:end_x]
        cropped_resized = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        sys.stdout.buffer.write(cropped_resized.tobytes())

if __name__ == "__main__":
    track_and_crop(sys.argv[1])
