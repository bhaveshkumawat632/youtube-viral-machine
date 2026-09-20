#!/usr/bin/env python3
"""
Real-World Topic Short Builder:
Assembles a 1080x1920 vertical Short on a real-world topic: "AI & The Future of Human Jobs in 2026".
Uses 6 real 4K stock video clips of AI Robots, Artificial Intelligence Brains, Microchips, and Data Centers.
"""

import os
import sys
import asyncio
import subprocess
import edge_tts

BASE_DIR = "/home/junglee01/youtube-viral-machine"
STOCK_DIR = os.path.join(BASE_DIR, "ai_stock_clips")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "REAL_WORLD_AI_FUTURE_MASTER.mp4")
TEMP_DIR = os.path.join(BASE_DIR, "Testing", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

# 6 Real AI & Technology Stock Clips
CLIPS = [
    os.path.join(STOCK_DIR, "clip_9oyFU2IQHIc.mp4"),  # AI Learning Robot
    os.path.join(STOCK_DIR, "clip_4OY07Bo5PnY.mp4"),  # AI 4K Glowing Brain
    os.path.join(STOCK_DIR, "clip_aw4WIzkLOwY.mp4"),  # AI Data Server Center
    os.path.join(STOCK_DIR, "clip_gdMvNDoDGqM.mp4"),  # Microchip 4K
    os.path.join(STOCK_DIR, "clip_qcSFsDfFvv0.mp4"),  # Futuristic Microchips
    os.path.join(STOCK_DIR, "clip_DZLlw5BNQ3g.mp4"),  # Artificial Intelligence Technology
]

SCRIPT_TEXT = "क्या 2026 में आर्टिफिशियल इंटेलिजेंस आपकी नौकरी छीन लेगा? आज दुनिया भर के बड़े डेटा सेंटर्स, माइक्रोचिप्स और एआई रोबोट्स इंसानी दिमाग से 100 गुना तेजी से काम कर रहे हैं! कोडिंग से लेकर अकाउंटिंग तक, हर फील्ड में एआई इंसानों को रिप्लेस कर रहा है। लेकिन जो लोग आज एआई टूल्स और फ्यूचर टेक्नोलॉजी को सीख रहे हैं, वे 2026 के असली लीडर्स बनेंगे। टेक्नोलॉजी की इस नई दुनिया से अपडेट रहने के लिए आज ही पैसा भाई को फॉलो करें!"

VOICE = "hi-IN-SwaraNeural"

async def generate_voice_and_subs():
    print("🎙️ Generating Real-World AI Hindi Neural Voiceover & Subtitles...")
    voice_path = os.path.join(TEMP_DIR, "real_ai_voice.mp3")
    ass_path = os.path.join(TEMP_DIR, "real_ai_subs.ass")
    
    communicate = edge_tts.Communicate(SCRIPT_TEXT, VOICE)
    submaker = edge_tts.SubMaker()
    
    with open(voice_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub(chunk["offset"], chunk["duration"], chunk["text"])

    ass_header = """[Script Info]
Title: Real World AI Future Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,3,2,40,40,280,1

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
            dialogues.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\c&H00FFFF&\\b1}}{text}{{\\r}}\n")
            
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "".join(dialogues))
        
    print(f"✅ Voiceover saved: {voice_path}")
    print(f"✅ Subtitles saved: {ass_path}")
    return voice_path, ass_path

def main():
    voice_path, ass_path = asyncio.run(generate_voice_and_subs())
    bgm_path = os.path.join(TEMP_DIR, "real_ai_bgm.mp3")
    
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", voice_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "30.0")
    print(f"⏱️ Total Audio duration: {duration:.2f}s")
    
    # BGM tone
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"sine=frequency=120:sample_rate=48000:duration={duration}",
        "-af", f"volume=0.08,afade=t=in:st=0:d=0.5,afade=t=out:st={duration-0.5}:d=0.5",
        bgm_path
    ], capture_output=True)
    
    # Prepare 6 individual vertical stock clips (~5s per clip)
    segment_dur = duration / len(CLIPS)
    prepared_clips = []
    
    for i, clip_path in enumerate(CLIPS):
        out_seg = os.path.join(TEMP_DIR, f"real_aiseg_{i}.mp4")
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

    print(f"🎥 Successfully prepared {len(prepared_clips)} real AI & tech stock video segments.")
    
    # Concat segments
    concat_list = os.path.join(TEMP_DIR, "real_aiconcat_list.txt")
    with open(concat_list, "w") as f:
        for c in prepared_clips:
            f.write(f"file '{c}'\n")
            
    concat_video = os.path.join(TEMP_DIR, "real_aiconcat_video.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", concat_video
    ], capture_output=True)

    # Burn ASS subtitles and mix audio
    print("🎬 Burning ASS Subtitles & mixing audio into final Real-World AI Short Master...")
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
        
    print(f"🎉 REAL-WORLD AI FUTURE MASTER SHORT RENDERED: {OUTPUT_VIDEO}")
    return OUTPUT_VIDEO

if __name__ == "__main__":
    main()
