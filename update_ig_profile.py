import os
import sys

# Load env variables safely
env_path = "/home/junglee01/youtube-viral-machine/.env"
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, _, val = line.partition('=')
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

from instagrapi import Client

def update_profile():
    sessionid = os.environ.get("IG_SESSIONID")
    if not sessionid:
        print("❌ Session ID not found. Cannot update profile.")
        sys.exit(1)
        
    print("📡 Logging in via SessionID to update profile...")
    cl = Client()
    try:
        cl.login_by_sessionid(sessionid)
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        sys.exit(1)
        
    new_bio = "Architecting Digital Wealth ⚙️\nAI Systems | Automation | Leverage\nBuilding the 1% mindset.\nAccess the ecosystem 👇"
    new_url = "https://bhaveshkumawat632.github.io/money-making-blog/"
    
    print("🛠️ Updating Instagram Bio and Link...")
    try:
        cl.account_edit(biography=new_bio, external_url=new_url)
        print("✅ Profile successfully customized!")
    except Exception as e:
        print(f"❌ Failed to update profile: {e}")

if __name__ == "__main__":
    update_profile()
