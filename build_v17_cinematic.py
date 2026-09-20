import os
import subprocess

OUTPUT_DIR = "/home/junglee01/youtube-viral-machine/output_v17"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run():
    stock_bg = "/home/junglee01/Downloads/movie.mp4"
    start_time = 4000
    duration = 15
    
    raw_clip = f"{OUTPUT_DIR}/raw_clip.mp4"
    subprocess.run(f"ffmpeg -y -ss {start_time} -t {duration} -i {stock_bg} -c:v libx264 -preset ultrafast -crf 18 -c:a aac -b:a 192k {raw_clip}", shell=True, stdout=subprocess.DEVNULL)
    
    # Cinematic Blur Background Filter
    # [0:v] scale to 1080x1920 keeping aspect ratio for background, then crop and heavy blur
    # [0:v] scale to 1080 width keeping aspect ratio for foreground, then unsharp
    # Overlay foreground on background
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=40:luma_power=3:chroma_radius=40:chroma_power=3[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,format=yuv420p,unsharp=5:5:1.0:5:5:0.0[fg];"
        "[bg][fg]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2[vid]"
    )

    final_cmd = (
        f"ffmpeg -y -i {raw_clip} "
        f'-filter_complex "{filter_complex}" '
        f"-map '[vid]' -map 0:a -c:v libx264 -preset fast -crf 17 -c:a aac -b:a 192k "
        f"{OUTPUT_DIR}/DEMO_V17_CINEMATIC_BLUR.mp4"
    )
    subprocess.run(final_cmd, shell=True)

if __name__ == "__main__":
    run()
