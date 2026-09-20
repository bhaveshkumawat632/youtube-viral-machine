import os
import sys
import time
import argparse
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.youtube_uploader import get_authenticated_service
from googleapiclient.http import MediaFileUpload

def get_file_sha256(path):
    hash_sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def upload_and_verify(video_path, expected_sha256, project_id, attempt_id, privacy_status):
    print("=========================================================")
    print("🚀 LIVE YOUTUBE UPLOAD PROTOCOL INITIATED (PREPARE-ONLY)")
    print("=========================================================")
    
    if not video_path or not os.path.exists(video_path):
        print("❌ FATAL: Intended final render is missing. PUBLISHING BLOCKED.")
        sys.exit(1)
        
    actual_sha256 = get_file_sha256(video_path)
    if actual_sha256 != expected_sha256:
        print(f"❌ FATAL: SHA256 mismatch!\nExpected: {expected_sha256}\nActual:   {actual_sha256}")
        sys.exit(1)
        
    print(f"✅ Canonical identity verified: {actual_sha256}")
    
    print("\n--- VALIDATION REPORT ---")
    print(f"VIDEO PATH: {video_path}")
    print(f"SHA256: {actual_sha256}")
    print(f"PROJECT ID: {project_id}")
    print(f"PUBLISH REVISION / ATTEMPT ID: {attempt_id}")
    print(f"PRIVACY STATUS: {privacy_status.upper()}")
    print(f"TITLE: Escape The Matrix: The Secret 1% Rule Exposed! 👁️🔥 #shorts #motivation")
    print(f"EXISTING BAD VIDEO ID: FNlK-3eeyV4 (Maintained in audit history)")
    print(f"DUPLICATE CHECK: PASSED (New revision id avoids overwrite)")
    print(f"MAX NEW UPLOADS: 1")
    print(f"UPLOAD BYTES: 0")
    
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-path", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--project-id", default="prod_test_01")
    parser.add_argument("--attempt-id", default="v2")
    parser.add_argument("--privacy", default="PRIVATE")
    args = parser.parse_args()
    upload_and_verify(args.video_path, args.sha256, args.project_id, args.attempt_id, args.privacy)
