"""
VidRush Paisa Bhai Production Pipeline — copyright-safe, high-quality Shorts.
Uses only original assets: Paisa Bhai host PNG + original motion graphics + edge-tts voiceover.
No stock footage / Pexels in final render to avoid reused-content claims.
"""
import os
import sys
import time
import json
import asyncio
import random
import subprocess
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SHORTS_WIDTH, SHORTS_HEIGHT, FPS, OUTPUT_DIR, TEMP_DIR,
    VOICES, DEFAULT_VOICE, SPEECH_RATE, ASSETS_DIR
)
from modules.animated_builder import build_animated_scene
from modules.subtitle_generator import transcribe_audio, generate_ass_subtitles, words_from_edge_tts
from modules.background_music import generate_background_tone, mix_audio, generate_sfx
from modules.quality_review import run_quality_review
from modules.compliance import compliance_report



def _run(cmd, **kwargs):
    res = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    return res


def _get_duration(path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", path
    ]
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return max(3.0, float(r.stdout.decode().strip() or "0"))
    except Exception:
        return 8.0


def _concat_videos(paths, output_path, crossfade=0.4):
    """Concat videos with simple xfade where possible; fallback to concat demuxer."""
    if len(paths) == 1:
        cmd = ["ffmpeg", "-y", "-i", paths[0], "-c", "copy", output_path]
        _run(cmd)
        return output_path

    # Use concat demuxer for robustness
    list_path = os.path.join(TEMP_DIR, f"_pbp_concat_{int(time.time())}.txt")
    os.makedirs(TEMP_DIR, exist_ok=True)
    with open(list_path, "w") as f:
        for p in paths:
            f.write(f"file '{p}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c:v", "libx264", "-preset", "medium", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M", "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        output_path
    ]
    res = _run(cmd)
    try:
        os.remove(list_path)
    except OSError:
        pass
    return output_path


def render_paisa_bhai_short(
    script_text,
    title="Paisa Bhai Short",
    voice_key="hindi_female",
    bgm_style="ambient",
    license_tag="original_motion_graphics_host",
    publish=False,
):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    start = time.time()
    run_id = int(time.time())

    # 1. Compliance pre-check
    comp = compliance_report(
        title=title,
        script_text=script_text,
        use_stock_footage=False,
        character_present=True,
    )
    if not comp:
        raise RuntimeError("Compliance pre-check blocked this script")

    # 2. Voiceover + word boundaries
    audio_path = os.path.join(TEMP_DIR, f"pbp_{run_id}_voice.mp3")
    boundaries_path = os.path.join(TEMP_DIR, f"pbp_{run_id}_words.json")

    audio_path, boundaries_path, words = __import__(
        "modules.voiceover", fromlist=["generate_voiceover"]
    ).generate_voiceover(
        script_text, audio_path, voice_key=voice_key, rate=SPEECH_RATE
    )

    duration = _get_duration(audio_path)

    # 3. Subtitles from voiceover words or re-transcribe for safety
    words_for_subs = words if words else []
    if not words_for_subs and os.path.exists(boundaries_path):
        try:
            words_for_subs = json.load(open(boundaries_path, encoding="utf-8"))
        except Exception:
            words_for_subs = []

    # Edge/JARVIS boundaries use millisecond keys; ASS generation consumes
    # normalized seconds. Keep the conversion at this pipeline boundary.
    if words_for_subs and "start" not in words_for_subs[0]:
        words_for_subs = words_from_edge_tts(boundaries_path)

    if not words_for_subs:
        words_for_subs = transcribe_audio(audio_path, language="hi")

    ass_path = os.path.join(TEMP_DIR, f"pbp_{run_id}_subs.ass")
    if words_for_subs:
        generate_ass_subtitles(words_for_subs, ass_path, video_width=SHORTS_WIDTH, video_height=SHORTS_HEIGHT)

    # 4. Split script into short scenes for animated host swaps
    sentences = [s.strip() for s in script_text.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        sentences = [script_text]

    # Target ~3-5 seconds per scene; cap at 8 scenes to avoid fatigue
    target_scene = max(3.0, min(5.0, duration / max(2, len(sentences))))
    scene_count = max(1, min(8, int(math.ceil(duration / target_scene))))
    scenes = []
    idx = 0
    for i in range(scene_count):
        chunk = sentences[i] if i < len(sentences) else (sentences[-1] if sentences else script_text)
        scenes.append({
            "text": chunk,
            "pose": random.choice([
                "host_neutral", "host_talk", "host_point", "host_think"
            ]),
        })

    # 5. Render animated host scenes. The builder creates branded original backgrounds,
    # so generating separate unused OpenCV clips would only waste production time.
    scene_videos = []
    for i, sc in enumerate(scenes):
        scene_path = os.path.join(TEMP_DIR, f"pbp_{run_id}_scene_{i}.mp4")
        build_animated_scene(
            scene_text=sc["text"],
            audio_path=None,
            out_path=scene_path,
            duration=min(target_scene + 0.5, duration),
            pose=sc["pose"],
        )
        if os.path.exists(scene_path) and os.path.getsize(scene_path) > 50000:
            scene_videos.append(scene_path)

    if not scene_videos:
        # fallback single scene
        scene_path = os.path.join(TEMP_DIR, f"pbp_{run_id}_scene_0.mp4")
        build_animated_scene(script_text, audio_path, scene_path, duration, "host_neutral")
        scene_videos = [scene_path]

    final_no_audio = os.path.join(OUTPUT_DIR, f"PaisaBhai_{run_id}_raw.mp4")
    _concat_videos(scene_videos, final_no_audio)

    # 6. Burn subtitles + original motion grade in final encode
    final_with_subs = os.path.join(OUTPUT_DIR, f"PaisaBhai_{run_id}_subs.mp4")
    sub_filter = None
    if ass_path and os.path.exists(ass_path):
        ass_escaped = ass_path.replace(chr(92), "/").replace(":", "\\\\:").replace("'", "")
        sub_filter = f"ass='{ass_escaped}'"

    vf_parts = [
        f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}:force_original_aspect_ratio=decrease,pad={SHORTS_WIDTH}:{SHORTS_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x0a1628",
        "eq=contrast=1.1:saturation=1.15:brightness=0.02",
        "unsharp=3:3:0.6:3:3:0.6",
        "vignette='PI/3.2 + 0.04 * sin(2*PI*t)'",
        "drawtext=text='Paisa Bhai':fontcolor=white:fontsize=28:box=1:boxcolor=black@0.55:boxborderw=6:x=40:y=60:enable='between(t,0,3)'",
    ]
    if sub_filter:
        vf_parts.append(sub_filter)

    vf = ",".join(vf_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", final_no_audio,
        "-i", audio_path,
        "-filter_complex", f"[0:v]{vf}[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M", "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        final_with_subs
    ]
    _run(cmd)

    # 7. Cinematic audio mix: voice + BGM + SFX
    final_audio_mix = os.path.join(TEMP_DIR, f"pbp_{run_id}_mix.mp3")
    music_path = os.path.join(TEMP_DIR, f"pbp_{run_id}_music.mp3")
    sfx_path = os.path.join(TEMP_DIR, f"pbp_{run_id}_sfx.wav")
    try:
        generate_background_tone(duration + 1, music_path, style=bgm_style)
        generate_sfx(sfx_path, "whoosh")
        mixed = mix_audio(audio_path, music_path, final_audio_mix, music_volume=0.06)
        if mixed and os.path.exists(mixed):
            # Attach mixed audio to video
            final_mixed = os.path.join(OUTPUT_DIR, f"PaisaBhai_{run_id}_FINAL.mp4")
            _run([
                "ffmpeg", "-y",
                "-i", final_with_subs, "-i", mixed,
                "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", final_mixed
            ])
            final_path = final_mixed if os.path.exists(final_mixed) else final_with_subs
        else:
            final_path = final_with_subs
    except Exception as e:
        print(f"⚠️ Audio mix fallback: {e}")
        final_path = final_with_subs

    # 8. Real quality review
    qa_ok = run_quality_review(final_path, license_tag=license_tag)

    # 9. Save manifest
    manifest = {
        "title": title,
        "script": script_text,
        "final_video": final_path,
        "duration_seconds": round(_get_duration(final_path), 2),
        "qa_passed": bool(qa_ok),
        "license": license_tag,
        "timestamp": int(time.time()),
    }
    manifest_path = os.path.join(OUTPUT_DIR, f"PaisaBhai_{run_id}_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    elapsed = round(time.time() - start, 1)
    print(f"✅ Paisa Bhai render done in {elapsed}s -> {final_path}")
    return final_path, manifest


if __name__ == "__main__":
    sample_script = (
        "अगर आप बिना किसी जानकारी के पैसे कमाने चाहते हैं तो ये वीडियो जरूर देखें.\n"
        "सबसे पहले छोटे स्टेप से शुरुआत करें और सीटीएससी या सर ple फ्रीलैन्सिंग सीखें.\n"
        "रोज 2 घंटे अभ्यास करने से 3 महीने में पहला ऑर्डर मिल जाता है.\n"
        "दूसरा, अपना गिटहब बनाओ और प्रोजेक्ट शेयर करो.\n"
        "तीसरा, क्लाइंट के फीडबैक को जल्दी करो और रेटिंग बढ़ाओ.\n"
        "चारवां, इन्वेस्टमेंट बनाने के बाद पैसा पैसा कमाओ.\n"
        "याद रखो, रुकना मत, शुरुआत करो आज ही."
    )
    path, man = render_paisa_bhai_short(sample_script, title="Paisa Bhai | पैसे बिना इंवेस्टमेंट के कमाने का रास्ता")
    print(json.dumps(man, ensure_ascii=False, indent=2))
