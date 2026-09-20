#!/usr/bin/env python3
"""
Fast Real Video Builder:
Renders a 1080x1920 vertical Short using real video footage (NEW_WALA_VIDEO.mp4),
Hindi Neural TTS voiceover, animated ASS subtitles, and ambient background music.
"""

import os
import sys
import asyncio
import subprocess
import edge_tts

BASE_DIR = "/home/junglee01/youtube-viral-machine"
RAW_VIDEO = os.path.join(BASE_DIR, "NEW_WALA_VIDEO.mp4")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "REAL_VIRAL_SHORT_ULTIMATE.mp4")
TEMP_DIR = os.path.join(BASE_DIR, "Testing", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

SCRIPT_TEXT = "क्या आप जानते हैं कि दुनिया के 99% लोग गरीबी का शिकार क्यों बनते हैं? क्योंकि वे सोचते हैं कि पैसा कमाने के लिए सिर्फ मेहनत काफी है! लेकिन सच यह है कि स्मार्ट वर्क, सही निवेश और Compounding Power ही आपको असली अमीर बना सकती है। अगर आप भी 2026 में वित्तीय आजादी पाना चाहते हैं, तो आज ही अपने पैसे को काम पर लगाएं और पैसा भाई को फॉलो करें!"

VOICE = "hi-IN-SwaraNeural"

async def build_voice_and_subtitles():
    print("🎙️ Generating Hindi Neural Voiceover + Subtitles via Edge-TTS...")
    voice_path = os.path.join(TEMP_DIR, "real_hindi_voice.mp3")
    ass_path = os.path.join(TEMP_DIR, "real_hindi_subs.ass")
    
    communicate = edge_tts.Communicate(SCRIPT_TEXT, VOICE)
    submaker = edge_tts.SubMaker()
    
    with open(voice_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub(chunk["offset"], chunk["duration"], chunk["text"])

    # Write ASS Subtitles format
    ass_header = """[Script Info]
Title: Real Hindi Short Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,68,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,3,2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # Convert SRT/SubMaker output to ASS dialogue lines
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
    voice_path, ass_path = asyncio.run(build_voice_and_subtitles())
    bgm_path = os.path.join(TEMP_DIR, "real_bgm.mp3")
    
    # Get voice duration
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", voice_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "20.0")
    print(f"⏱️ Video Duration: {duration:.2f}s")
    
    # Generate background tone
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"sine=frequency=110:sample_rate=48000:duration={duration}",
        "-af", f"volume=0.08,afade=t=in:st=0:d=0.5,afade=t=out:st={duration-0.5}:d=0.5",
        bgm_path
    ], capture_output=True)
    
    # Encode final real video with FFmpeg
    print("🎬 Encoding 1080x1920 Real Video Short with subtitles & audio mix...")
    ass_escaped = ass_path.replace(":", "\\:")
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", "2.0",
        "-i", RAW_VIDEO,
        "-i", voice_path,
        "-i", bgm_path,
        "-t", str(duration),
        "-filter_complex", (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,eq=contrast=1.1:saturation=1.2:brightness=0.02,"
            f"unsharp=3:3:0.5:3:3:0.5,subtitles='{ass_escaped}'[v];"
            f"[1:a][2:a]amix=inputs=2:weights=1.0 0.1[a]"
        ),
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "faster", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        OUTPUT_VIDEO
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("❌ FFmpeg error:", res.stderr[-2000:])
        raise RuntimeError("FFmpeg render failed")
        
    print(f"🎉 REAL VIRAL SHORT SUCCESSFULLY RENDERED: {OUTPUT_VIDEO}")
    return OUTPUT_VIDEO

if __name__ == "__main__":
    main()
