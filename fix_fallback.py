import re

with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "r") as f:
    content = f.read()

# Replace the whole subtitle generation part
start_str = "chars = j[\"alignment\"][\"characters\"]"
end_str = "print(f\"⏱️ Audio duration: {duration:.2f}s\")"

start_idx = content.find(start_str)
end_idx = content.find(end_idx_str := "print(f\"⏱️ Audio duration: {duration:.2f}s\")") + len(end_idx_str)

if start_idx != -1:
    new_sub_logic = """
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", voice_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "30.0")
    print(f"⏱️ Audio duration: {duration:.2f}s")

    ass_header = f'''[Script Info]
Title: Real World Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,72,&H00FFFFFF,{topic['color']},&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,3,2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

    dialogues = []
    if fallback_audio:
        import textwrap
        lines = textwrap.wrap(topic['script'], width=25)
        seg_dur = duration / max(len(lines), 1)
        curr_t = 0
        for line in lines:
            start_str = format_time(curr_t)
            curr_t += seg_dur
            end_str = format_time(curr_t)
            dialogues.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{{\\\\c{topic['color']}&\\\\b1}}{line}{{\\\\r}}\\\\N\\n")
    else:
        chars = j["alignment"]["characters"]
        start_times = j["alignment"]["character_start_times_seconds"]
        end_times = j["alignment"]["character_end_times_seconds"]

        words = []
        curr_word = ""
        word_start = None
        word_end = None

        for c, s, e in zip(chars, start_times, end_times):
            if c == " ":
                if curr_word:
                    words.append((curr_word, word_start, word_end))
                    curr_word = ""
                    word_start = None
            else:
                if curr_word == "":
                    word_start = s
                curr_word += c
                word_end = e

        if curr_word:
            words.append((curr_word, word_start, word_end))
            
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i+chunk_size]
            start_str = format_time(chunk[0][1])
            end_str = format_time(chunk[-1][2])
            text = " ".join([w[0] for w in chunk])
            dialogues.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{{\\\\c{topic['color']}&\\\\b1}}{text}{{\\\\r}}\\\\N\\n")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "".join(dialogues))
"""
    content = content[:start_idx] + new_sub_logic + content[end_idx:]
    with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "w") as f:
        f.write(content)
    print("Fixed logic")
