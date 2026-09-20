import os
import sys
import subprocess
import re

OUTPUT_DIR = "/home/junglee01/youtube-viral-machine/output_v13"
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
Style: Default,Arial Black,130,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,6,5,10,10,900,1

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
    script_text = "The biggest lie you have ever been told is that working hard will make you rich. Look around! The hardest workers are struggling. The rich use systems and AI to print money while they sleep. Wake up!"
    
    voice_path = f"{OUTPUT_DIR}/voice.mp3"
    subprocess.run(f'edge-tts --text "{script_text}" --voice en-US-GuyNeural --rate="+20%" --pitch="+5Hz" --write-media {voice_path}', shell=True)
    
    result = subprocess.run(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {voice_path}", shell=True, stdout=subprocess.PIPE)
    audio_duration = float(result.stdout)
    
    generate_subtitles(script_text, audio_duration)
    
    bgm_path = f"{OUTPUT_DIR}/drone.wav"
    subprocess.run(f'ffmpeg -y -f lavfi -i "aevalsrc=\'sin(35*2*PI*t)*0.1\':d={audio_duration+1}" -af "volume=0.08" {bgm_path}', shell=True, stdout=subprocess.DEVNULL)
    
    mixed_audio = f"{OUTPUT_DIR}/mixed_audio.mp3"
    subprocess.run(f'ffmpeg -y -i {voice_path} -i {bgm_path} -filter_complex amix=inputs=2:duration=first {mixed_audio}', shell=True, stdout=subprocess.DEVNULL)

    stock_bg = "/home/junglee01/Downloads/movie.mp4"
    start_time = 4000
    
    raw_wide = f"{OUTPUT_DIR}/raw_wide.mp4"
    subprocess.run(f"ffmpeg -y -ss {start_time} -t {audio_duration + 0.5} -i {stock_bg} -c:v libx264 -preset ultrafast -crf 18 {raw_wide}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    tracked_bg = f"{OUTPUT_DIR}/tracked_bg.mp4"
    # Run SMART DIRECTOR
    fps_cmd = f"ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=r_frame_rate {raw_wide}"
    fps_raw = subprocess.check_output(fps_cmd, shell=True).decode().strip()
    fps = str(eval(fps_raw)) if '/' in fps_raw else fps_raw
    
    track_cmd = f"python3 smart_director.py {raw_wide} | ffmpeg -y -f rawvideo -pix_fmt bgr24 -s 1080x1920 -r {fps} -i pipe:0 -c:v libx264 -preset fast -crf 17 {tracked_bg}"
    subprocess.run(track_cmd, shell=True)

    # FINAL MIX WITH UNSHARP AND EQ FOR HIGH QUALITY
    final_cmd = (
        f"ffmpeg -y -i {tracked_bg} "
        f"-i {mixed_audio} "
        f'-vf "unsharp=5:5:1.0:5:5:0.0,eq=contrast=1.15:saturation=1.2:brightness=0.02,subtitles={OUTPUT_DIR}/subs.ass:force_style=\'OutlineColour=&H40000000,BorderStyle=3\'" '
        f"-c:v libx264 -preset fast -crf 17 -c:a aac -b:a 192k -shortest "
        f"{OUTPUT_DIR}/DEMO_V13_100_PERCENT.mp4"
    )
    subprocess.run(final_cmd, shell=True)

if __name__ == "__main__":
    run()
