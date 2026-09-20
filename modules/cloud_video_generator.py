import os
import subprocess
import shutil
import time

class Client:
    """Mock placeholder for tests patching Client class."""
    pass

def generate_video_from_prompt_hf(prompt, output_path):
    """
    Tier 1 AI Video Generator.
    If REPLICATE_API_TOKEN is set, attempts paid AI video generation.
    Otherwise, performs zero-cost fallback using Pollinations AI image + local FFmpeg zoompan motion.
    """
    token = os.environ.get("REPLICATE_API_TOKEN", "")
    if token:
        try:
            import replicate
            client = replicate.Client(api_token=token)
            output = client.run(
                "minimax/video-01",
                input={"prompt": prompt, "prompt_optimizer": True}
            )
            video_url = str(output[0]) if isinstance(output, list) else str(output)
            import requests
            r = requests.get(video_url, timeout=60)
            if r.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(r.content)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 20000:
                    return output_path
        except Exception as e:
            print(f"   ⚠️ Replicate generation failed ({e}), falling back to Pollinations motion loop...")

    # Zero-Cost Free Fallback: Pollinations AI + FFmpeg Ken Burns Motion
    try:
        from modules.image_motion_generator import get_pollinations_image
        temp_img = output_path.replace(".mp4", "_temp.jpg")
        img_res = get_pollinations_image(prompt, temp_img)
        if img_res and os.path.exists(temp_img):
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", temp_img,
                "-vf", "scale=1080x1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0015,1.3)':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':d=900:s=1080x1920,setsar=1",
                "-t", "30.0", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", output_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(temp_img):
                os.remove(temp_img)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 20000:
                print(f"   [Tier 1 Fallback] SUCCESS: Free Pollinations motion loop generated: {output_path}")
                return output_path
    except Exception as fe:
        print(f"   ⚠️ Free visual fallback failed ({fe})")

    return None
