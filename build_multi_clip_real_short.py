#!/usr/bin/env python3
"""
Multi-Clip Real Stock Footage Short Generator:
Combines real 4K stock video clips (Luxury Cars, Money Counting, Gold Bars),
adds Hindi Neural TTS voiceover, animated ASS subtitles, ambient music, and WHOOSH SFX.
"""

import os
import sys
import asyncio
import subprocess
import edge_tts

BASE_DIR = "/home/junglee01/youtube-viral-machine"
STOCK_DIR = os.path.join(BASE_DIR, "real_stock_clips")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "REAL_STOCK_MULTI_CLIP_MASTER.mp4")
TEMP_DIR = os.path.join(BASE_DIR, "Testing", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

# 3 Real Stock Footage Clips
CLIPS = [
    os.path.join(STOCK_DIR, "clip_0q-ZEE8IMSI.mp4"),  # Luxury lifestyle & Supercars
    os.path.join(STOCK_DIR, "clip_MNG2_t_juvg.mp4"),  # Money counting machine
    os.path.join(STOCK_DIR, "clip_u07cLS8Hy2Q.mp4"),  # Gold bars & Wealth
]

SCRIPT_TEXT = "क्या आप जानते हैं कि दुनिया के 99% लोग अपनी जिंदगी सिर्फ नौकरी करने में बिता देते हैं? जबकि 1% लोग पैसे के असली खेल को समझकर अपने पैसे से काम करवाते हैं! लक्जरी गाड़ियां, बेहिसाब पैसा और असली वित्तीय आजादी सिर्फ एक सपने से नहीं, बल्कि सही समय पर सही निवेश करने से मिलती है। अगर आप भी 2026 में अपनी तकदीर बदलना चाहते हैं, तो आज ही सही कदम उठाएं और पैसा भाई को फॉलो करें!"

VOICE = "hi-IN-SwaraNeural"

async def generate_voice_and_subs():
    print("🎙️ Generating Hindi Neural Voiceover & Subtitles...")
    voice_path = os.path.join(TEMP_DIR, "real_multi_voice.mp3")
    ass_path = os.path.join(TEMP_DIR, "real_multi_subs.ass")
    
    communicate = edge_tts.Communicate(SCRIPT_TEXT, VOICE)
    submaker = edge_tts.SubMaker()
    
    with open(voice_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub(chunk["offset"], chunk["duration"], chunk["text"])

    ass_header = """[Script Info]
Title: Real Multi Clip Subtitles
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
    bgm_path = os.path.join(TEMP_DIR, "real_multi_bgm.mp3")
    
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", voice_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "30.0")
    print(f"⏱️ Audio duration: {duration:.2f}s")
    
    # Generate BGM
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"sine=frequency=110:sample_rate=48000:duration={duration}",
        "-af", f"volume=0.08,afade=t=in:st=0:d=0.5,afade=t=out:st={duration-0.5}:d=0.5",
        bgm_path
    ], capture_output=True)
    
    # Prepare individual scaled vertical stock segments
    segment_duration = duration / len(CLIPS)
    prepared_clips = []
    for i, clip_path in enumerate(CLIPS):
        out_seg = os.path.join(TEMP_DIR, f"real_seg_{i}.mp4")
        cmd_seg = [
            "ffmpeg", "-y",
            "-ss", "1.0",
            "-i", clip_path,
            "-t", str(segment_duration),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.15:saturation=1.2:brightness=0.02,unsharp=3:3:0.5:3:3:0.5",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            out_seg
        ]
        subprocess.run(cmd_seg, capture_output=True)
        if os.path.exists(out_seg):
            prepared_clips.append(out_seg)

    print(f"🎥 Prepared {len(prepared_clips)} real stock video segments.")
    
    # Concat segments
    concat_list = os.path.join(TEMP_DIR, "real_concat_list.txt")
    with open(concat_list, "w") as f:
        for c in prepared_clips:
            f.write(f"file '{c}'\n")
            
    concat_video = os.path.join(TEMP_DIR, "real_concat_video.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", concat_video
    ], capture_output=True)

    # Burn subtitles and overlay voiceover + BGM
    print("🎬 Burning ASS Subtitles & mixing audio into final Master Real Short...")
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
        
    print(f"🎉 REAL MULTI-CLIP STOCK FOOTAGE SHORT RENDERED: {OUTPUT_VIDEO}")
    return OUTPUT_VIDEO

if __name__ == "__main__":
    main()
