import os
import sys

# Monkey-patch builtins.open to hide /home/junglee01/.env from dotenv/moviepy
import builtins
import io
original_open = builtins.open
def safe_open(*args, **kwargs):
    if args and args[0] == '/home/junglee01/.env':
        return io.StringIO()
    return original_open(*args, **kwargs)
builtins.open = safe_open

# Safely parse .env file natively in python to avoid bash quoting issues
env_path = "/home/junglee01/youtube-viral-machine/.env"
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, _, val = line.partition('=')
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and val:
                    os.environ[key] = val

import datetime
import time
from instagrapi import Client

def main():
    print("=========================================================")
    print("🚀 INSTAGRAM REELS UPLOAD PROTOCOL INITIATED")
    print("=========================================================")

    if os.environ.get("VIDRUSH_AUTO_UPLOAD_APPROVED") != "1":
        print("Instagram upload blocked: VIDRUSH_AUTO_UPLOAD_APPROVED is not 1.")
        print("Review and approve the local render before enabling uploads.")
        sys.exit(0)
    
    # Check credentials
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")
    sessionid = os.environ.get("IG_SESSIONID")
    
    if not sessionid and (not username or not password or username == "tumhara_ig_username"):
        print("❌ SKIPPING INSTAGRAM UPLOAD: Valid IG_SESSIONID or credentials not found.")
        sys.exit(0)
        
    video_path = "/home/junglee01/youtube-viral-machine/output/vidrush/math_masterpiece/FINAL_VIRAL_SHORT.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Video not found at {video_path}")
        sys.exit(1)

    print(f"📡 Logging in to Instagram via SessionID...")
    try:
        cl = Client()
        if sessionid:
            cl.login_by_sessionid(sessionid)
        else:
            cl.login(username, password)
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        sys.exit(1)

    caption = "The 1% Math Rule That Explains Reality 👁️🔥\n\nThis quantum geometric matrix proves that wealth and energy follow mathematical laws. Become the architect of your own reality.\n\n💰 Want to build your own wealth systems? Link in bio!\n\n#matrix #wealth #escape #motivation #sigma #passiveincome #entrepreneur"

    print("⏳ Uploading to Reels... (This may take a minute)")
    try:
        media = cl.clip_upload(
            video_path,
            caption,
            extra_data={
                "custom_accessibility_caption": "Matrix 3D Math Illusion",
                "like_and_view_counts_disabled": False,
                "disable_comments": False,
            }
        )
        print(f"✅ Upload Complete! Instagram Media ID: {media.id}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Upload Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
