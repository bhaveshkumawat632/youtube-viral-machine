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
    # It is already extracted but let's reuse it since it succeeded.
    
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,90,&H00FFFF,&H000000FF,&H000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,6,5,10,10,900,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:15.00,Default,,0,0,0,,WHO WAS RIGHT?
"""
    with open(f"{OUTPUT_DIR}/subs.ass", "w") as f:
        f.write(ass_content)

    # 1. Left side: crop=960:800:0:0 -> scale=1080:900 [top]
    # 2. Right side: crop=960:800:960:0 -> scale=1080:900 [bottom]
    # 3. vstack them -> 1080x1800 [stacked]
    # 4. pad to 1080x1920 with black bars on top and bottom: pad=1080:1920:0:60 [padded]
    # 5. draw a cool separator line in the middle
    filter_complex = (
        "[0:v]crop=960:800:0:0,scale=1080:900,setsar=1[top];"
        "[0:v]crop=960:800:960:0,scale=1080:900,setsar=1[bottom];"
        "[top][bottom]vstack=inputs=2[stacked];"
        "[stacked]pad=1080:1920:0:60:black[padded];"
        "[padded]drawbox=x=0:y=955:w=1080:h=10:color=white@0.9:t=fill[vid];"
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
