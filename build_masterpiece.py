import os
import random
import requests
import subprocess

PEXELS_KEY = "cBBsobTILBswJ5myAoj74hr3Vw2ylE4zUpXCRtbLsrQGvGvzPQYGEEzf"
OUTPUT_DIR = "/home/junglee01/youtube-viral-machine/output/vidrush/real_masterpiece"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# highly-curated hooks and visually striking Pexels keywords
SCRIPTS = [
    {
        "text": "Ninety nine percent of people watching this will skip. But you are different. You stayed because you know something is wrong with the system. They want you distracted. They want you working a job you hate, buying things you do not need, to impress people you do not like. The matrix is real, and it feeds on your attention. But you can break out. The secret isn't working harder. It is building systems that work for you while you sleep. Follow us to escape the matrix.",
        "clips": ["neon city night", "cyberpunk", "hacker screen", "crowd walking", "supercar driving", "server room", "luxury watch", "cyber security", "city time lapse"]
    }
]

def get_pexels_video(query, filename):
    print(f"🔍 Fetching cinematic clip for: {query}")
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&size=large&per_page=3"
    headers = {"Authorization": PEXELS_KEY}
    try:
        res = requests.get(url, headers=headers).json()
        if res.get("videos"):
            # pick a random one from top 3 to keep it fresh
            video = random.choice(res["videos"])
            # get the highest quality HD file
            hd_files = [f for f in video["video_files"] if f.get("quality") == "hd"]
            best_file = hd_files[0] if hd_files else video["video_files"][0]
            vid_res = requests.get(best_file["link"], stream=True)
            with open(filename, "wb") as f:
                for chunk in vid_res.iter_content(8192):
                    f.write(chunk)
            return filename
    except Exception as e:
        print(f"Error fetching {query}: {e}")
    return None

def generate_subtitles(text, audio_duration):
    words = text.split()
    total_words = len(words)
    time_per_word = audio_duration / total_words
    
    # HORMOZI STYLE: Huge, Yellow, Centered, Black Outline, No Fade, Word-by-Word
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,140,&H0000D7FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,4,5,10,10,900,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    current_time = 0.0
    for word in words:
        duration = time_per_word
        
        start_h, start_m, start_s = int(current_time // 3600), int((current_time % 3600) // 60), current_time % 60
        end_time = current_time + duration
        end_h, end_m, end_s = int(end_time // 3600), int((end_time % 3600) // 60), end_time % 60
        
        start_fmt = f"{start_h}:{start_m:02d}:{start_s:05.2f}"
        end_fmt = f"{end_h}:{end_m:02d}:{end_s:05.2f}"
        
        # Upper case, instant cut (no fade)
        ass_content += f"Dialogue: 0,{start_fmt},{end_fmt},Default,,0,0,0,,{word.upper()}\n"
        current_time = end_time
        
    with open(f"{OUTPUT_DIR}/subs.ass", "w") as f:
        f.write(ass_content)

def get_audio_duration(filepath):
    result = subprocess.run(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {filepath}", shell=True, stdout=subprocess.PIPE)
    return float(result.stdout)

def run():
    print("🎬 Starting VIRAL Masterpiece Build V3...")
    chosen = SCRIPTS[0]
    script_text = chosen["text"]
    
    # 1. Voice
    print("🎙️ Generating Ultra-Realistic Voice...")
    voice_path = f"{OUTPUT_DIR}/voice.mp3"
    subprocess.run(f'edge-tts --text "{script_text}" --voice en-US-SteffanNeural --rate="+15%" --write-media {voice_path}', shell=True)
    audio_duration = get_audio_duration(voice_path)
    
    # 2. Word-by-word dynamic subs
    generate_subtitles(script_text, audio_duration)

    # 3. High energy BGM - we will download a free creative commons phonk/synth track
    print("🎵 Downloading energetic BGM...")
    bgm_path = f"{OUTPUT_DIR}/bgm.mp3"
    # A royalty free energetic aggressive track from FreePD or similar (Using a known direct MP3 link)
    subprocess.run(f'wget -q -O {bgm_path} "https://freepd.com/music/Action%20Strike.mp3" || echo "wget failed"', shell=True)
    
    mixed_audio = f"{OUTPUT_DIR}/mixed_audio.mp3"
    if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 1000:
        # Mix with BGM at 10% volume so voice is clear
        subprocess.run(f'ffmpeg -y -i {voice_path} -i {bgm_path} -filter_complex "[1:a]volume=0.15[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2" {mixed_audio}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        mixed_audio = voice_path

    # 4. Fetch Clips
    valid_clips = []
    for i, q in enumerate(chosen["clips"]):
        path = f"{OUTPUT_DIR}/clip{i+1}.mp4"
        if get_pexels_video(q, path):
            valid_clips.append(path)
            
    # Very fast pacing - cut clips every 1.5 - 2 seconds max
    clip_duration = audio_duration / len(valid_clips) if valid_clips else 2.0
    processed_clips = []
    
    for i, clip in enumerate(valid_clips):
        out = f"{OUTPUT_DIR}/p_{i}.mp4"
        # Aggressive scaling to ensure it fills 1080x1920 without stretching, plus a faster zoom effect
        cmd = f'ffmpeg -y -i "{clip}" -t {clip_duration} -c:v libx264 -preset ultrafast -crf 22 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z=\'min(zoom+0.003,1.5)\':d=125:s=1080x1920" -an "{out}"'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processed_clips.append(out)

    print("🔗 Concatenating Fast-Paced Clips...")
    with open(f"{OUTPUT_DIR}/list.txt", "w") as f:
        for p in processed_clips:
            f.write(f"file '{os.path.basename(p)}'\n")
            
    subprocess.run(f"cd {OUTPUT_DIR} && ffmpeg -y -f concat -safe 0 -i list.txt -c copy raw_video.mp4", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("🔥 Finalizing Render (Video + Audio + Pop-up Subs)...")
    final_cmd = f'cd {OUTPUT_DIR} && ffmpeg -y -i raw_video.mp4 -i {mixed_audio} -vf "subtitles=subs.ass" -c:v libx264 -preset fast -b:v 8M -c:a aac -b:a 192k -shortest FINAL_VIRAL_SHORT.mp4'
    subprocess.run(final_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("✅ VIRAL Masterpiece V3 Created!")

if __name__ == "__main__":
    run()
