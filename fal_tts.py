import os
import fal_client
import urllib.request

FAL_KEY = os.environ.get("FAL_KEY")
SCRIPT = "The biggest lie you've been told is that saving money will make you rich. By the time you save enough, inflation has already stolen it. The top one percent do not save. They build automated wealth engines. Stop saving, start building."

try:
    print("🎙️ Generating FAL TTS...")
    result = fal_client.subscribe(
        "fal-ai/f5-tts",
        arguments={
            "gen_text": SCRIPT,
            "ref_audio_url": "https://github.com/SWivid/F5-TTS/raw/main/tests/ref_audio/test_en_1_ref_short.wav",
            "ref_text": "Some people call me the space cowboy, some call me the gangster of love."
        }
    )
    
    audio_url = result['audio']['url']
    print(f"📥 Downloading audio from {audio_url}...")
    urllib.request.urlretrieve(audio_url, "/home/junglee01/youtube-viral-machine/output/vidrush/real_masterpiece/fal_voice.mp3")
    print("✅ Done!")
except Exception as e:
    print(f"❌ Error: {e}")
