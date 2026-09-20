import cv2
import numpy as np
import math

width, height = 1080, 1920
fps = 30
duration = 10  # We will loop this 10 second clip in ffmpeg to match audio
total_frames = fps * duration

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('/tmp/infinity_grid.mp4', fourcc, fps, (width, height))

for f in range(total_frames):
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Render a mesmerizing moving grid
    t = f / fps
    speed = 200
    y_offset = int(t * speed) % 100
    
    # Horizon line
    horizon = height // 2
    
    for y in range(horizon, height, 10):
        # Calculate perspective depth
        depth = (y - horizon) / (height - horizon)
        if depth == 0: continue
        
        # Grid lines moving forward
        grid_y = y + int(y_offset * depth)
        if grid_y < height:
            color = int(255 * depth)
            cv2.line(img, (0, grid_y), (width, grid_y), (color, 0, color), max(1, int(3 * depth)))
            
    for x in range(0, width, 100):
        # Vertical perspective lines originating from center horizon
        # x_diff from center
        dx = x - (width//2)
        cv2.line(img, (width//2, horizon), (width//2 + dx * 10, height), (150, 0, 150), 2)
        
    # Add some floating particles
    for i in range(50):
        px = int((math.sin(i*7.1 + t) * 0.5 + 0.5) * width)
        py = int((math.cos(i*3.4 + t*1.5) * 0.5 + 0.5) * height)
        radius = int(2 + math.sin(t*2+i))
        cv2.circle(img, (px, py), max(1, radius), (0, 255, 255), -1)
        
    out.write(img)

out.release()
print("Art Generated: /tmp/infinity_grid.mp4")
