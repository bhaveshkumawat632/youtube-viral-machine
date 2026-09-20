import os
import sys
import requests
import subprocess
import re
import random

OUTPUT_DIR = "/home/junglee01/youtube-viral-machine/output_v11"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_subtitles(text, audio_duration):
    clean_text = re.sub(r'[^a-zA-Z0-9 \n]', '', text)
    words = clean_text.split()
    total_chars = sum(len(w) for w in words)
    time_per_char = audio_duration / total_chars if total_chars > 0 else 0
    
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,120,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,6,5,10,10,800,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    current_time = 0.0
    for word in words:
        duration = len(word) * time_per_char
        start_h, start_m, start_s = int(current_time // 3600), int((current_time % 3600) // 60), current_time % 60
        end_time = current_time + duration
        end_h, end_m, end_s = int(end_time // 3600), int((end_time % 3600) // 60), end_time % 60
        start_fmt = f"{start_h}:{start_m:02d}:{start_s:05.2f}"
        end_fmt = f"{end_h}:{end_m:02d}:{end_s:05.2f}"
        ass_content += f"Dialogue: 0,{start_fmt},{end_fmt},Default,,0,0,0,,{word.upper()}\n"
        current_time = end_time
        
    with open(f"{OUTPUT_DIR}/subs.ass", "w") as f:
        f.write(ass_content)

def run():
    script_text = "The biggest lie you've ever been told is that working hard will make you rich. Look around. The hardest workers are struggling to pay rent. Meanwhile, the rich are leveraging systems and AI to print money while they sleep. Stop trading time for money. Wake up."
    
    voice_path = f"{OUTPUT_DIR}/voice.mp3"
    subprocess.run(f'edge-tts --text "{script_text}" --voice en-US-GuyNeural --rate="+15%" --pitch="+5Hz" --write-media {voice_path}', shell=True)
    
    result = subprocess.run(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {voice_path}", shell=True, stdout=subprocess.PIPE)
    audio_duration = float(result.stdout)
    
    generate_subtitles(script_text, audio_duration)
    
    bgm_path = f"{OUTPUT_DIR}/drone.wav"
    subprocess.run(f'ffmpeg -y -f lavfi -i "aevalsrc=\'sin(35*2*PI*t)*0.1\':d={audio_duration+1}" -af "volume=0.08" {bgm_path}', shell=True, stdout=subprocess.DEVNULL)
    
    mixed_audio = f"{OUTPUT_DIR}/mixed_audio.mp3"
    subprocess.run(f'ffmpeg -y -i {voice_path} -i {bgm_path} -filter_complex amix=inputs=2:duration=first {mixed_audio}', shell=True, stdout=subprocess.DEVNULL)

    stock_bg = "/home/junglee01/Downloads/movie.mp4"
    start_time = 4000
    
    # Cinematic Blur Background Filter
    # [0:v] scale to 1080x1920 and boxblur for background
    # [0:v] scale keeping aspect ratio for foreground
    # Overlay foreground on background
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=luma_radius=40:luma_power=3:chroma_radius=40:chroma_power=3[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,format=yuv420p,unsharp=5:5:1.0:5:5:0.0[fg];"
        "[bg][fg]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2[vid];"
        "[vid]subtitles={subs}:force_style='OutlineColour=&H40000000,BorderStyle=3'[outv]"
    ).format(subs=f"{OUTPUT_DIR}/subs.ass")

    final_cmd = (
        f"ffmpeg -y -ss {start_time} -t {audio_duration + 0.5} -i {stock_bg} "
        f"-i {mixed_audio} "
        f'-filter_complex "{filter_complex}" '
        f"-map '[outv]' -map 1:a -c:v libx264 -preset fast -crf 17 -c:a aac -b:a 192k "
        f"{OUTPUT_DIR}/DEMO_V11_HD_BLUR.mp4"
    )
    subprocess.run(final_cmd, shell=True)
    
if __name__ == "__main__":
    run()
