import os
import sys
import subprocess
import requests

OUTPUT_DIR = "/home/junglee01/youtube-viral-machine/output_v12"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run():
    stock_bg = "/home/junglee01/Downloads/movie.mp4"
    start_time = 4000
    duration = 15
    
    raw_clip = f"{OUTPUT_DIR}/raw_clip.mp4"
    # Extract 15 seconds with its original audio!
    subprocess.run(f"ffmpeg -y -ss {start_time} -t {duration} -i {stock_bg} -c:v libx264 -preset ultrafast -crf 18 -c:a aac {raw_clip}", shell=True, stdout=subprocess.DEVNULL)
    
    # We will generate subtitles for this 15 second clip using whisper!
    # But since whisper might take time, let's just make a hype hardcoded ASS subtitle for the split screen!
    # Or just a static text "Wait for it..." to make it viral.
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,90,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,6,5,10,10,900,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:15.00,Default,,0,0,0,,WHO WAS RIGHT?
"""
    with open(f"{OUTPUT_DIR}/subs.ass", "w") as f:
        f.write(ass_content)

    # Split screen filter:
    # 1. Take left half (0 to 960), scale to 1080x1215, crop center to 1080x960
    # 2. Take right half (960 to 1920), scale to 1080x1215, crop center to 1080x960
    # 3. Vstack them to get 1080x1920
    # 4. Draw a white line in the middle (optional, but looks good)
    filter_complex = (
        "[0:v]crop=960:1080:0:0,scale=1080:1215,crop=1080:960:0:127[top];"
        "[0:v]crop=960:1080:960:0,scale=1080:1215,crop=1080:960:0:127[bottom];"
        "[top][bottom]vstack=inputs=2[stacked];"
        "[stacked]drawbox=x=0:y=955:w=1080:h=10:color=white@0.8:t=fill[vid];"
        "[vid]subtitles={subs}:force_style='OutlineColour=&H40000000,BorderStyle=3'[outv]"
    ).format(subs=f"{OUTPUT_DIR}/subs.ass")

    final_cmd = (
        f"ffmpeg -y -i {raw_clip} "
        f'-filter_complex "{filter_complex}" '
        f"-map '[outv]' -map 0:a -c:v libx264 -preset fast -crf 17 -c:a aac -b:a 192k "
        f"{OUTPUT_DIR}/DEMO_V12_SPLITSCREEN.mp4"
    )
    subprocess.run(final_cmd, shell=True)

if __name__ == "__main__":
    run()
