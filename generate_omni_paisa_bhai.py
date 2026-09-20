#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import asyncio
from modules.paisa_bhai_pipeline import render_paisa_bhai_short
from modules.youtube_uploader import get_authenticated_service
from googleapiclient.http import MediaFileUpload

# Set up pathing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_hindi_script_with_omni():
    print("🤖 [NVIDIA OMNI] Generating Hindi/Hinglish script...")
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }
    
    # Request a high-impact viral personal finance script in Hindi
    prompt = """
    You are a viral YouTube Shorts creator in India. Generate a high-retention Hindi voiceover script (using Devanagari script) for a 30-second video about the '5 Second Rule Productivity Hack to Save Money and Beat Procrastination'.
    The script must be in fluent, engaging Hindi (standard Indian speech).
    Return ONLY a JSON object in this format (no markdown code blocks, no extra text):
    {
      "title": "5 Second Rule: Procrastination को जड़ से खत्म करने का नियम | Paisa Bhai",
      "script_text": "क्या आप भी अपनी आलस और टालमटोल की आदत से परेशान हैं? जब भी आपको कोई काम शुरू करना हो, तो बस 5 से 1 तक उलटी गिनती शुरू करें: 5, 4, 3, 2, 1 और तुरंत काम में लग जाएं। वैज्ञानिकों का मानना है कि अगर आप 5 सेकंड के अंदर एक्शन नहीं लेते, तो आपका दिमाग उस विचार को मार देता है। चाहे सुबह जल्दी उठना हो या निवेश करना हो, यह सिंपल ट्रिक आपकी जिंदगी बदल देगी। आज ही इसे आजमाएं और अपने सपनों को पूरा करें। ऐसे ही पैसों के खुफिया नियमों के लिए पैसा भाई को फॉलो करें!"
    }
    """
    
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        "max_tokens": 2048,
        "temperature": 0.6
    }
    
    try:
        res = requests.post(invoke_url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"].strip()
            # Clean possible markdown wrap
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            data = json.loads(content.strip())
            print("🤖 [NVIDIA OMNI] SUCCESS: Hindi script generated successfully!")
            return data.get("title"), data.get("script_text")
    except Exception as e:
        print(f"⚠️ [NVIDIA OMNI] script generation failed: {e}. Using high-quality backup script.")
    
    # High-quality offline backup script
    backup_title = "5 Second Rule: Procrastination को जड़ से खत्म करने का नियम | Paisa Bhai"
    backup_script = "क्या आप भी अपनी आलस और टालमटोल की आदत से परेशान हैं? जब भी आपको कोई काम शुरू करना हो, तो बस 5 से 1 तक उलटी गिनती शुरू करें: 5, 4, 3, 2, 1 और तुरंत काम में लग जाएं। वैज्ञानिकों का मानना है कि अगर आप 5 सेकंड के अंदर एक्शन नहीं लेते, तो आपका दिमाग उस विचार को मार देता है। चाहे सुबह जल्दी उठना हो या निवेश करना हो, यह सिंपल ट्रिक आपकी जिंदगी बदल देगी। आज ही इसे आजमाएं और अपने सपनों को पूरा करें। ऐसे ही पैसों के खुफिया नियमों के लिए पैसा भाई को फॉलो करें!"
    return backup_title, backup_script

def upload_video_to_youtube(video_path, title, description):
    print("\n=========================================================")
    print("📡 INITIATING YOUTUBE UPLOAD FOR PAISA BHAI")
    print("=========================================================")
    
    youtube = get_authenticated_service()
    if not youtube:
        print("❌ YouTube Auth Failed.")
        return False
        
    body = {
        "snippet": {
            "title": title[:90] + " #shorts #viral",
            "description": description + "\n\n#PaisaBhai #MoneyHacks #Procrastination #Shorts #HindiRules",
            "tags": ["Paisa Bhai", "shorts", "viral", "procrastination", "motivation", "hindi"],
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"⏳ Uploading... {int(status.progress() * 100)}%")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False
            
    print(f"\n✅ Upload Complete! Link: https://youtu.be/{response.get('id')}")
    return True

def main():
    # 1. Generate Script
    title, script_text = generate_hindi_script_with_omni()
    print(f"📝 Title: {title}")
    print(f"📝 Script: {script_text}")
    
    # 2. Render Paisa Bhai Short
    print("\n🎬 Rendering Paisa Bhai video...")
    video_path, manifest = render_paisa_bhai_short(
        script_text=script_text,
        title=title,
        voice_key="hindi_female",
        bgm_style="ambient",
        license_tag="original_motion_graphics_host"
    )
    
    # 3. Upload to YouTube
    if os.path.exists(video_path):
        success = upload_video_to_youtube(
            video_path=video_path,
            title=title,
            description=script_text
        )
        if success:
            print("🚀 Video is fully live and processed!")
        else:
            print("⚠️ Video rendered successfully but upload failed.")
    else:
        print("❌ Rendered video file not found!")

if __name__ == "__main__":
    main()
