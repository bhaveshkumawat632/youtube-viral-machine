import os
import sys
import json
import random
import requests
import subprocess
import urllib.parse
from pathlib import Path

OUTPUT_DIR = "/home/junglee01/youtube-viral-machine/output/test_vidrush"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Monkey-patch DNS resolution for image.pollinations.ai due to local network DNS issues
try:
    import urllib3.util.connection as connection
    orig_create_connection = connection.create_connection
    def patched_create_connection(address, *args, **kwargs):
        host, port = address
        if host == "image.pollinations.ai":
            host = random.choice(["172.67.173.121", "104.21.30.173"])
        return orig_create_connection((host, port), *args, **kwargs)
    connection.create_connection = patched_create_connection
except Exception as e:
    print(f"⚠️ Failed to apply DNS patch: {e}")

def test_pollinations():
    print("Testing Pollinations...")
    prompts = ["cyberpunk city", "glowing matrix code", "wealth businessman"]
    images = []
    for i, p in enumerate(prompts):
        encoded = urllib.parse.quote(p)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true"
        img_path = f"{OUTPUT_DIR}/img_{i}.jpg"
        res = requests.get(url)
        with open(img_path, "wb") as f:
            f.write(res.content)
        images.append(img_path)
    
    print("Images downloaded. Creating slideshow...")
    # Simple ffmpeg command to make a slideshow
    list_file = f"{OUTPUT_DIR}/images.txt"
    with open(list_file, "w") as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write("duration 10\n")
        # repeat last image for safe duration
        f.write(f"file '{images[-1]}'\n")
    
    video_path = f"{OUTPUT_DIR}/slideshow.mp4"
    cmd = f"ffmpeg -y -f concat -safe 0 -i {list_file} -vf 'zoompan=z=1.1:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):d=250' -c:v libx264 -pix_fmt yuv420p -t 30 {video_path}"
    subprocess.run(cmd, shell=True)
    print("Video created at", video_path)

if __name__ == "__main__":
    test_pollinations()
