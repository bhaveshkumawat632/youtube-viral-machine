with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "r") as f:
    content = f.read()

import re

# find if not clips: sys.exit(1)
start_str = "if not clips:\n        print(\"❌ Failed to download any clips. YT-DLP 403 error?\")\n        sys.exit(1)"
new_str = """if not clips:
        print("⚠️ Failed to download any clips. YT-DLP 403 error!")
        print("🔄 Falling back to AI Image generation (Pollinations)...")
        from modules.image_motion_generator import get_pollinations_image
        import urllib.parse
        img_prompt = topic['search'].replace("4k stock video free", "cinematic highly detailed")
        fallback_img = f"{STOCK_DIR}/fallback_001.jpg"
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_prompt)}?width=1080&height=1920&nologo=true"
        r = requests.get(url)
        with open(fallback_img, 'wb') as img_f:
            img_f.write(r.content)
            
        # Convert image to a 5-second mp4 clip
        fallback_clip = f"{STOCK_DIR}/fallback_clip_001.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", fallback_img, "-t", "5", 
            "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.0015,1.5)':d=150:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1080x1920",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", fallback_clip
        ])
        clips = [fallback_clip]
"""

content = content.replace(start_str, new_str)
with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "w") as f:
    f.write(content)
print("Added YT-DLP fallback.")
