import cv2
import sys
import numpy as np
import torch
import torchvision.models.detection as det
import torchvision.transforms as T

def get_iou(box1, box2):
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])
    if x_right < x_left or y_bottom < y_top: return 0.0
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
    
    # Store persistent tracking targets
    left_person_box = None
    right_person_box = None
    
    left_motion_history = []
    right_motion_history = []
    
    active_target = "left"
    cooldown = 0
    
    prev_gray = None
    frame_count = 0
    
    # This stores the HARD CUT center!
    active_center_x = orig_w / 2.0
    
    while True:
        ret, frame = cap.read()
        if not ret: break
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
            person_boxes = boxes[(labels == 1) & (scores > 0.4)]
            
            if len(person_boxes) > 0:
                scale_x, scale_y = orig_w / 320.0, orig_h / 320.0
                scaled_boxes = person_boxes.copy()
                scaled_boxes[:, 0] *= scale_x; scaled_boxes[:, 2] *= scale_x
                scaled_boxes[:, 1] *= scale_y; scaled_boxes[:, 3] *= scale_y
                
                centers_x = (scaled_boxes[:, 0] + scaled_boxes[:, 2]) / 2.0
                sorted_idx = np.argsort(centers_x)
                sorted_boxes = scaled_boxes[sorted_idx]
                
                if len(sorted_boxes) >= 2:
                    left_person_box = sorted_boxes[0]
                    right_person_box = sorted_boxes[-1]
                elif len(sorted_boxes) == 1:
                    if left_person_box is not None and right_person_box is not None:
                        iou_left = get_iou(left_person_box, sorted_boxes[0])
                        iou_right = get_iou(right_person_box, sorted_boxes[0])
                        if iou_left > iou_right:
                            left_person_box = sorted_boxes[0]
                        else:
                            right_person_box = sorted_boxes[0]
                    else:
                        left_person_box = sorted_boxes[0]
                        
        if prev_gray is not None and left_person_box is not None and right_person_box is not None:
            def get_motion(box):
                x1, y1 = int(max(0, box[0])), int(max(0, box[1]))
                x2, y2 = int(min(orig_w, box[2])), int(min(orig_h, box[3]))
                face_y2 = min(orig_h, y1 + int((y2 - y1) * 0.35))
                if x2 > x1 and face_y2 > y1:
                    curr_face = gray[y1:face_y2, x1:x2]
                    prev_face = prev_gray[y1:face_y2, x1:x2]
                    diff = cv2.absdiff(curr_face, prev_face)
                    return np.mean(diff)
                return 0.0
                
            left_mot = get_motion(left_person_box)
            right_mot = get_motion(right_person_box)
            
            left_motion_history.append(left_mot)
            right_motion_history.append(right_mot)
            if len(left_motion_history) > 10: left_motion_history.pop(0)
            if len(right_motion_history) > 10: right_motion_history.pop(0)
            
            avg_l_mot = np.mean(left_motion_history)
            avg_r_mot = np.mean(right_motion_history)
            
            if cooldown > 0:
                cooldown -= 1
            else:
                if active_target == "left" and avg_r_mot > avg_l_mot + 3.0 and avg_r_mot > 8.0:
                    active_target = "right"
                    cooldown = 45 # 1.5 sec
                elif active_target == "right" and avg_l_mot > avg_r_mot + 3.0 and avg_l_mot > 8.0:
                    active_target = "left"
                    cooldown = 45
                    
        # GET EXACT CENTER OF TARGET
        if active_target == "left" and left_person_box is not None:
            active_center_x = (left_person_box[0] + left_person_box[2]) / 2.0
        elif active_target == "right" and right_person_box is not None:
            active_center_x = (right_person_box[0] + right_person_box[2]) / 2.0
            
        # NO SMOOTHING. HARD CUT INSTANTLY TO ACTIVE_CENTER_X
        start_x = int(active_center_x - target_w / 2)
        end_x = int(active_center_x + target_w / 2)
        
        # Keep inside bounds
        if start_x < 0: start_x, end_x = 0, target_w
        if end_x > orig_w: end_x, start_x = orig_w, orig_w - target_w
            
        cropped = frame[0:orig_h, start_x:end_x]
        cropped_resized = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        sys.stdout.buffer.write(cropped_resized.tobytes())
        
        prev_gray = gray
        
if __name__ == "__main__":
    track_and_crop(sys.argv[1])
