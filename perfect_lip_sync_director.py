import cv2
import sys
import numpy as np
import mediapipe as mp
import math

def get_lip_aspect_ratio(landmarks, iw, ih):
    # Upper lip points: 13, lower lip points: 14
    # Left corner: 78, Right corner: 308
    top_lip = (landmarks[13].x * iw, landmarks[13].y * ih)
    bottom_lip = (landmarks[14].x * iw, landmarks[14].y * ih)
    left_lip = (landmarks[78].x * iw, landmarks[78].y * ih)
    right_lip = (landmarks[308].x * iw, landmarks[308].y * ih)
    
    vertical_dist = math.hypot(top_lip[0] - bottom_lip[0], top_lip[1] - bottom_lip[1])
    horizontal_dist = math.hypot(left_lip[0] - right_lip[0], left_lip[1] - right_lip[1])
    
    if horizontal_dist == 0: return 0
    return vertical_dist / horizontal_dist

def track_and_crop(input_path):
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=5,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    cap = cv2.VideoCapture(input_path)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    target_w = int(orig_h * 9 / 16)
    
    active_center_x = orig_w / 2.0
    
    # Store history for faces
    # Because face order from mediapipe isn't guaranteed, we match by X coordinate
    face_histories = {} 
    
    active_face_id = None
    cooldown = 0
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)
        
        current_faces = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Get center X of face
                xs = [lm.x for lm in face_landmarks.landmark]
                center_x = sum(xs) / len(xs) * orig_w
                
                lar = get_lip_aspect_ratio(face_landmarks.landmark, orig_w, orig_h)
                current_faces.append((center_x, lar))
                
        # Match current faces to histories
        new_histories = {}
        for cx, lar in current_faces:
            # find closest history
            best_id = None
            best_dist = float('inf')
            for fid, hist in face_histories.items():
                last_cx = hist['cx']
                if abs(last_cx - cx) < 100: # 100 pixels threshold
                    if abs(last_cx - cx) < best_dist:
                        best_dist = abs(last_cx - cx)
                        best_id = fid
                        
            if best_id is None:
                best_id = len(face_histories) + len(new_histories)
                
            history_list = face_histories.get(best_id, {}).get('lars', [])
            history_list.append(lar)
            if len(history_list) > 15: history_list.pop(0) # 0.5 second window
            
            new_histories[best_id] = {
                'cx': cx,
                'lars': history_list
            }
            
        face_histories = new_histories
        
        # Decide active speaker based on LAR variance (moving lips)
        if len(face_histories) > 0:
            if cooldown > 0:
                cooldown -= 1
            else:
                best_speaker = None
                max_variance = -1
                for fid, hist in face_histories.items():
                    lars = hist['lars']
                    if len(lars) >= 5:
                        variance = np.var(lars)
                        if variance > max_variance:
                            max_variance = variance
                            best_speaker = fid
                            
                # If variance is significant, switch speaker
                if max_variance > 0.0001: 
                    if active_face_id != best_speaker:
                        active_face_id = best_speaker
                        cooldown = 45 # 1.5s cooldown to prevent strobe
                        
        if active_face_id in face_histories:
            active_center_x = face_histories[active_face_id]['cx']
            
        # Hard cut framing
        start_x = int(active_center_x - target_w / 2)
        end_x = int(active_center_x + target_w / 2)
        
        if start_x < 0: start_x, end_x = 0, target_w
        if end_x > orig_w: end_x, start_x = orig_w, orig_w - target_w
            
        cropped = frame[0:orig_h, start_x:end_x]
        cropped_resized = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        sys.stdout.buffer.write(cropped_resized.tobytes())

if __name__ == "__main__":
    track_and_crop(sys.argv[1])
