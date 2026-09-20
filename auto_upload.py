import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.youtube_uploader import upload_video

def main():
    if os.environ.get("VIDRUSH_AUTO_UPLOAD_APPROVED") != "1":
        print("YouTube upload blocked: VIDRUSH_AUTO_UPLOAD_APPROVED is not 1.")
        print("Review and approve the local render before enabling uploads.")
        sys.exit(0)

    video_path = "/home/junglee01/youtube-viral-machine/output/vidrush/math_masterpiece/FINAL_VIRAL_SHORT.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video not found at {video_path}")
        sys.exit(1)
        
    # Generate dynamic metadata
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    title = f"The 1% Math Rule That Explains Reality 👁️🔥 #shorts #motivation"
    desc = "This quantum geometric matrix proves that wealth and energy follow mathematical laws. 🚀 Become the architect of your own reality.\n\n💰 Learn the exact systems to automate your income: https://bhaveshkumawat632.github.io/money-making-blog/\n\n#matrix #wealth #escape #motivation #sigma"
    tags = ["shorts", "motivation", "wealth", "matrix", "sigma", "money", "passive income"]
    
    metadata = {
        "title": title,
        "description": desc,
        "tags": tags,
        "category_id": "27"  # 27 = Education
    }
    
    success = upload_video(video_path, metadata)
    if success:
        print("✅ YouTube Upload Module Success.")
    else:
        print("❌ YouTube Upload Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
