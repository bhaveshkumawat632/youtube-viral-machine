import os
import sys
import subprocess

OUTPUT_DIR = "/home/junglee01/youtube-viral-machine/output_v16"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run():
    stock_bg = "/home/junglee01/Downloads/movie.mp4"
    start_time = 4000
    duration = 15
    
    raw_wide = f"{OUTPUT_DIR}/raw_wide.mp4"
    subprocess.run(f"ffmpeg -y -ss {start_time} -t {duration} -i {stock_bg} -c:v libx264 -preset ultrafast -crf 18 -c:a aac -b:a 192k {raw_wide}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    tracked_bg = f"{OUTPUT_DIR}/tracked_bg.mp4"
    fps_cmd = f"ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate {raw_wide}"
    fps_raw = subprocess.check_output(fps_cmd, shell=True).decode().strip()
    fps = str(eval(fps_raw)) if '/' in fps_raw else fps_raw
    
    track_cmd = f"python3 perfect_lip_sync_director.py {raw_wide} | ffmpeg -y -f rawvideo -pix_fmt bgr24 -s 1080x1920 -r {fps} -i pipe:0 -c:v libx264 -preset fast -crf 17 {tracked_bg}"
    subprocess.run(track_cmd, shell=True)

    final_cmd = (
        f"ffmpeg -y -i {tracked_bg} "
        f"-i {raw_wide} "
        f'-vf "unsharp=5:5:1.0:5:5:0.0,eq=contrast=1.15:saturation=1.2:brightness=0.02" '
        f"-map 0:v -map 1:a -c:v libx264 -preset fast -crf 17 -c:a aac -b:a 192k -shortest "
        f"{OUTPUT_DIR}/DEMO_V16_LIPSYNC_HARDCUT.mp4"
    )
    subprocess.run(final_cmd, shell=True)

if __name__ == "__main__":
    run()
