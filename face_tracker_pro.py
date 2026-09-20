import cv2
import sys
import numpy as np

def track_and_crop(input_path):
    cap = cv2.VideoCapture(input_path)
    
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    target_w = int(orig_h * 9 / 16)
    target_h = orig_h
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    current_x = orig_w / 2
    last_known_x = orig_w / 2
    
    # Sharpening kernel
    kernel = np.array([[0, -0.5, 0], 
                       [-0.5, 3, -0.5], 
                       [0, -0.5, 0]])
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Tweak minSize to avoid detecting tiny background things
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(50, 50))
        
        if len(faces) > 0:
            faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
            x, y, w, h = faces[0]
            last_known_x = x + w/2
            
        # VERY smooth tracking (slow pan)
        current_x = current_x * 0.90 + last_known_x * 0.10
        
        start_x = int(current_x - target_w / 2)
        end_x = int(current_x + target_w / 2)
        
        if start_x < 0:
            start_x = 0
            end_x = target_w
        if end_x > orig_w:
            end_x = orig_w
            start_x = orig_w - target_w
            
        cropped = frame[0:target_h, start_x:end_x]
        
        # High quality resize
        cropped_resized = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        
        # Apply sharpening to improve clarity
        sharpened = cv2.filter2D(cropped_resized, -1, kernel)
        
        sys.stdout.buffer.write(sharpened.tobytes())
        
    cap.release()

if __name__ == "__main__":
    track_and_crop(sys.argv[1])
