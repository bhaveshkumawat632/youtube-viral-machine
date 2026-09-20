#!/usr/bin/env python3
import os
import sys
import subprocess
import glob
import requests
import json
import base64

BASE_DIR = "/home/junglee01/youtube-viral-machine"
STOCK_DIR = os.path.join(BASE_DIR, "real_dino_clips")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "REAL_WORLD_DINO_MASTER.mp4")
TEMP_DIR = os.path.join(BASE_DIR, "Testing", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

# Find clips
CLIPS = sorted(glob.glob(os.path.join(STOCK_DIR, "*.mp4")))
if not CLIPS:
    print("❌ No clips found")
    sys.exit(1)

SCRIPT_TEXT = "Did you know that the exact day the dinosaurs died is written in the Earth's crust? 66 million years ago, a massive asteroid the size of a city crashed into our planet. The impact was so violent it triggered global tsunamis and blocked out the sun for years. But out of this total destruction, mammals finally had the chance to evolve. If you want to uncover more epic mysteries of our world, hit that subscribe button!"

def _load_env_key(name: str) -> str:
    """Read a key from process env or the gitignored .env file (never hardcode secrets)."""
    value = os.environ.get(name, "")
    if value:
        return value.strip()
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(env_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


ELEVENLABS_KEY = _load_env_key("ELEVENLABS_API_KEY")
VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17" # Roger

print("🎙️ Generating ElevenLabs Human Voiceover with timestamps...")
voice_path = os.path.join(TEMP_DIR, "real_dino_voice.mp3")
ass_path = os.path.join(TEMP_DIR, "real_dino_subs.ass")

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps"
headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
data = {"text": SCRIPT_TEXT, "model_id": "eleven_multilingual_v2"}

resp = requests.post(url, json=data, headers=headers)
if resp.status_code != 200:
    print("❌ ElevenLabs error:", resp.text)
    sys.exit(1)
    
j = resp.json()
with open(voice_path, "wb") as f:
    f.write(base64.b64decode(j["audio_base64"]))

# Reconstruct words from character alignment
chars = j["alignment"]["characters"]
start_times = j["alignment"]["character_start_times_seconds"]
end_times = j["alignment"]["character_end_times_seconds"]

words = []
curr_word = ""
word_start = None
word_end = None

for c, s, e in zip(chars, start_times, end_times):
    if c == " ":
        if curr_word:
            words.append((curr_word, word_start, word_end))
            curr_word = ""
            word_start = None
    else:
        if curr_word == "":
            word_start = s
        curr_word += c
        word_end = e

if curr_word:
    words.append((curr_word, word_start, word_end))

ass_header = """[Script Info]
Title: Real World Dino Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,3,2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
dialogues = []

def format_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec))*100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

# Group into 4-5 words per subtitle
chunk_size = 4
for i in range(0, len(words), chunk_size):
    chunk = words[i:i+chunk_size]
    start_str = format_time(chunk[0][1])
    end_str = format_time(chunk[-1][2])
    text = " ".join([w[0] for w in chunk])
    dialogues.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{{\\c&H0000FF&\\b1}}{text}{{\\r}}\\N")

with open(ass_path, "w", encoding="utf-8") as f:
    f.write(ass_header + "".join(dialogues))

print("✅ Subtitles & Voice ready.")

probe = subprocess.run([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "csv=p=0", voice_path
], capture_output=True, text=True)
duration = float(probe.stdout.strip() or "30.0")
print(f"⏱️ Audio duration: {duration:.2f}s")

bgm_path = os.path.join(TEMP_DIR, "real_dino_bgm.mp3")
subprocess.run([
    "ffmpeg", "-y", "-f", "lavfi", "-i",
    f"sine=frequency=65:sample_rate=48000:duration={duration}",
    "-af", f"volume=0.08,afade=t=in:st=0:d=0.5,afade=t=out:st={duration-0.5}:d=0.5",
    bgm_path
], capture_output=True)

segment_dur = duration / len(CLIPS)
prepared_clips = []
for i, clip_path in enumerate(CLIPS):
    out_seg = os.path.join(TEMP_DIR, f"real_dinoseg_{i}.mp4")
    cmd_seg = [
        "ffmpeg", "-y", "-stream_loop", "-1", "-ss", "0.5", "-i", clip_path, "-t", str(segment_dur),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.15:saturation=1.2",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", out_seg
    ]
    subprocess.run(cmd_seg, capture_output=True)
    prepared_clips.append(out_seg)

concat_list = os.path.join(TEMP_DIR, "real_dinoconcat_list.txt")
with open(concat_list, "w") as f:
    for c in prepared_clips:
        f.write(f"file '{c}'\n")
        
concat_video = os.path.join(TEMP_DIR, "real_dinoconcat_video.mp4")
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", concat_video
], capture_output=True)

ass_escaped = ass_path.replace(":", "\\:")
cmd_final = [
    "ffmpeg", "-y", "-i", concat_video, "-i", voice_path, "-i", bgm_path, "-t", str(duration),
    "-filter_complex", f"[0:v]subtitles='{ass_escaped}'[v];[1:a][2:a]amix=inputs=2:weights=1.0 0.1[a]",
    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast", "-b:v", "8M",
    "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", OUTPUT_VIDEO
]
subprocess.run(cmd_final, capture_output=True)
print(f"🎉 RENDERED: {OUTPUT_VIDEO}")
