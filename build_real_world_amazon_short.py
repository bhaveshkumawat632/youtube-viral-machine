#!/usr/bin/env python3
"""
Real-World Topic Short Builder:
Assembles a 1080x1920 vertical Short on a real-world topic: "The Amazon Rainforest".
Uses real 4K stock video clips of Nature, Jungles, and Animals.
"""

import os
import sys
import asyncio
import subprocess
import glob
import edge_tts

BASE_DIR = "/home/junglee01/youtube-viral-machine"
STOCK_DIR = os.path.join(BASE_DIR, "real_amazon_clips")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "REAL_WORLD_AMAZON_MASTER.mp4")
TEMP_DIR = os.path.join(BASE_DIR, "Testing", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

# Find clips
CLIPS = sorted(glob.glob(os.path.join(STOCK_DIR, "*.mp4")))
if not CLIPS:
    print("❌ No amazon clips found in", STOCK_DIR)
    sys.exit(1)

print(f"🎬 Found {len(CLIPS)} amazon clips to use.")

SCRIPT_TEXT = "क्या आप जानते हैं कि दुनिया का 20 प्रतिशत ऑक्सीजन सिर्फ एक ही जगह से आता है? वो है अमेजॉन का जंगल! यह जंगल इतना बड़ा है कि अगर यह कोई देश होता, तो दुनिया का 9वां सबसे बड़ा देश कहलाता। यहाँ पेड़ इतने घने हैं कि सूरज की रोशनी को जमीन तक पहुँचने में 10 मिनट लग जाते हैं। इसके अंदर ऐसे-ऐसे जहरीले जीव और आदिवासी जनजातियाँ हैं जिनका बाहरी दुनिया से कोई संपर्क नहीं है। अमेजॉन के और रहस्य जानने के लिए पैसा भाई को सब्सक्राइब करें!"

VOICE = "hi-IN-SwaraNeural"

async def generate_voice_and_subs():
    print("🎙️ Generating Real-World Amazon Hindi Neural Voiceover & Subtitles...")
    voice_path = os.path.join(TEMP_DIR, "real_amazon_voice.mp3")
    ass_path = os.path.join(TEMP_DIR, "real_amazon_subs.ass")
    
    communicate = edge_tts.Communicate(SCRIPT_TEXT, VOICE)
    submaker = edge_tts.SubMaker()
    
    with open(voice_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub(chunk["offset"], chunk["duration"], chunk["text"])

    ass_header = """[Script Info]
Title: Real World Amazon Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,72,&H00FFFFFF,&H00008000,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,3,2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    srt_text = submaker.get_srt()
    dialogues = []
    
    for block in srt_text.strip().split("\n\n"):
        lines = block.split("\n")
        if len(lines) >= 3:
            times = lines[1].split(" --> ")
            start = times[0].replace(",", ".")
            end = times[1].replace(",", ".")
            text = " ".join(lines[2:])
            # Bright Green highlight for Nature theme
            dialogues.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\c&H00FF00&\\b1}}{text}{{\\r}}\n")
            
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "".join(dialogues))
        
    print(f"✅ Voiceover saved: {voice_path}")
    print(f"✅ Subtitles saved: {ass_path}")
    return voice_path, ass_path

def main():
    voice_path, ass_path = asyncio.run(generate_voice_and_subs())
    bgm_path = os.path.join(TEMP_DIR, "real_amazon_bgm.mp3")
    
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", voice_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "30.0")
    print(f"⏱️ Total Audio duration: {duration:.2f}s")
    
    # BGM tone (Mysterious / nature vibe, slightly higher freq)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"sine=frequency=110:sample_rate=48000:duration={duration}",
        "-af", f"volume=0.08,afade=t=in:st=0:d=0.5,afade=t=out:st={duration-0.5}:d=0.5",
        bgm_path
    ], capture_output=True)
    
    segment_dur = duration / len(CLIPS)
    prepared_clips = []
    
    for i, clip_path in enumerate(CLIPS):
        out_seg = os.path.join(TEMP_DIR, f"real_amazonseg_{i}.mp4")
        ss_time = 0.5 + (i * 0.2)
        cmd_seg = [
            "ffmpeg", "-y",
            "-ss", str(ss_time),
            "-i", clip_path,
            "-t", str(segment_dur),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.15:saturation=1.2:brightness=0.02,unsharp=3:3:0.5:3:3:0.5",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            out_seg
        ]
        subprocess.run(cmd_seg, capture_output=True)
        if os.path.exists(out_seg):
            prepared_clips.append(out_seg)

    print(f"🎥 Successfully prepared {len(prepared_clips)} real amazon stock video segments.")
    
    # Concat segments
    concat_list = os.path.join(TEMP_DIR, "real_amazonconcat_list.txt")
    with open(concat_list, "w") as f:
        for c in prepared_clips:
            f.write(f"file '{c}'\n")
            
    concat_video = os.path.join(TEMP_DIR, "real_amazonconcat_video.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", concat_video
    ], capture_output=True)

    # Burn ASS subtitles and mix audio
    print("🎬 Burning ASS Subtitles & mixing audio into final Real-World Amazon Short Master...")
    ass_escaped = ass_path.replace(":", "\\:")
    
    cmd_final = [
        "ffmpeg", "-y",
        "-i", concat_video,
        "-i", voice_path,
        "-i", bgm_path,
        "-t", str(duration),
        "-filter_complex", (
            f"[0:v]subtitles='{ass_escaped}'[v];"
            f"[1:a][2:a]amix=inputs=2:weights=1.0 0.1[a]"
        ),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        OUTPUT_VIDEO
    ]
    
    res = subprocess.run(cmd_final, capture_output=True, text=True)
    if res.returncode != 0:
        print("❌ FFmpeg error:", res.stderr[-2000:])
        raise RuntimeError("Final FFmpeg render failed")
        
    print(f"🎉 REAL-WORLD AMAZON MASTER SHORT RENDERED: {OUTPUT_VIDEO}")
    return OUTPUT_VIDEO

if __name__ == "__main__":
    main()
