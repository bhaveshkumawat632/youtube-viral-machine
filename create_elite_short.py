import os
import sys
import subprocess
from modules.voiceover import generate_voiceover
from modules.coverr_downloader import get_coverr_video

DIR = "/home/junglee01/youtube-viral-machine/output/vidrush/elite"
os.makedirs(DIR, exist_ok=True)

# 1. Audio
script = "The secret to financial freedom in 2026 isn't just saving money. It's building automated systems. While you sleep, these systems work. It's time to build your digital empire today."
print("🎙️ Generating Voiceover...")
audio_path, _, _ = generate_voiceover(script, voice_key="english_dramatic", rate="+0%")
os.system(f"cp {audio_path} {DIR}/voice.mp3")

# 2. Footage
print("🎥 Downloading Real Footage...")
try:
    get_coverr_video("office", f"{DIR}/clip1.mp4")
    get_coverr_video("money", f"{DIR}/clip2.mp4")
except Exception as e:
    print("Fallback to local footage...", e)
    os.system(f"cp /home/junglee01/youtube-viral-machine/backgrounds/money_loop.mp4 {DIR}/clip1.mp4")
    os.system(f"cp /home/junglee01/youtube-viral-machine/backgrounds/local_money_loop.mp4 {DIR}/clip2.mp4")

# 3. Assemble and Caption
print("🎬 Assembling & Captioning...")
ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,2,10,10,800,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.50,Default,,0,0,0,,The secret to financial freedom
Dialogue: 0,0:00:02.50,0:00:05.00,Default,,0,0,0,,in 2026 isn't saving money.
Dialogue: 0,0:00:05.00,0:00:07.50,Default,,0,0,0,,It's building automated systems.
Dialogue: 0,0:00:07.50,0:00:10.00,Default,,0,0,0,,While you sleep, these systems work.
Dialogue: 0,0:00:10.00,0:00:13.00,Default,,0,0,0,,It's time to build your empire.
"""
with open(f"{DIR}/subs.ass", "w") as f:
    f.write(ass_content)

bash_script = f"""
cd {DIR}
ffmpeg -y -i clip1.mp4 -t 6 -c:v libx264 -preset ultrafast -crf 24 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" -an c1.mp4
ffmpeg -y -i clip2.mp4 -t 8 -c:v libx264 -preset ultrafast -crf 24 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" -an c2.mp4
echo "file 'c1.mp4'" > list.txt
echo "file 'c2.mp4'" >> list.txt
ffmpeg -y -f concat -safe 0 -i list.txt -c copy bg.mp4
ffmpeg -y -i bg.mp4 -i voice.mp3 -vf "subtitles=subs.ass" -c:v libx264 -preset medium -b:v 8M -c:a aac -b:a 192k -shortest ELITE_MASTER.mp4
"""
with open(f"{DIR}/run.sh", "w") as f:
    f.write(bash_script)

os.system(f"bash {DIR}/run.sh")
print("✅ Elite Video Created at:", f"{DIR}/ELITE_MASTER.mp4")
