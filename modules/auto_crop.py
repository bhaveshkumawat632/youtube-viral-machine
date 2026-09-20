import os
import subprocess
import time

def auto_crop_youtube_video(youtube_url, output_dir, start_time="00:00:30", duration="00:00:45"):
    """
    Downloads a segment of a YouTube video and auto-crops it to 9:16 vertical format using FFmpeg.
    """
    print(f"🎬 Starting Auto-Crop pipeline for {youtube_url}")
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time())
    downloaded_video = os.path.join(output_dir, f"downloaded_{timestamp}.mp4")
    final_short = os.path.join(output_dir, f"autocropped_short_{timestamp}.mp4")
    
    # 1. Download video using yt-dlp
    print("⬇️ Downloading video with yt-dlp...")
    try:
        # Download best mp4 up to 1080p
        simple_cmd = ["yt-dlp", "-f", "best[height<=1080][ext=mp4]", "-o", downloaded_video, youtube_url]
        subprocess.run(simple_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"❌ yt-dlp failed: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

    if not os.path.exists(downloaded_video):
        print("❌ Download failed.")
        return None

    # 2. Crop to 9:16 using FFmpeg
    print("✂️ Cropping to 9:16 vertical format...")
    # crop=w:h:x:y - for 1920x1080 to 9:16, width is 1080*(9/16)=607.5. 
    # x = (in_w-out_w)/2 = (1920-607)/2 = 656
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", downloaded_video,
        "-ss", start_time,
        "-t", duration,
        "-vf", "crop=ih*(9/16):ih:(iw-ih*(9/16))/2:0,scale=1080:1920",
        "-c:a", "copy",
        final_short
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Auto-cropped Short generated: {final_short}")
        
        # Clean up original download to save space
        os.remove(downloaded_video)
        
        return final_short
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg crop failed: {e.stderr.decode('utf-8', errors='ignore')}")
        return None

if __name__ == "__main__":
    # Test with a public domain / creative commons video (e.g. Big Buck Bunny)
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    out_path = auto_crop_youtube_video(test_url, "./Testing/autocrop")
    if out_path:
        print(f"Successfully created: {out_path}")
