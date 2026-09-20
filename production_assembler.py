#!/usr/bin/env python3
"""Assemble a production Short from validated real assets."""

from __future__ import annotations

import json
import shlex
import subprocess
import time
from pathlib import Path

from production_gate import INPUT_DIR, validate_manifest


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output" / "production"
LEGACY_OUTPUT = BASE_DIR / "output" / "vidrush" / "math_masterpiece" / "FINAL_VIRAL_SHORT.mp4"
WIDTH = 1080
HEIGHT = 1920
FPS = 30
FONT = BASE_DIR / "assets" / "fonts" / "Montserrat-ExtraBold.ttf"


def run(cmd: list[str], *, timeout: int = 300) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed: {}\n{}".format(" ".join(shlex.quote(c) for c in cmd), result.stderr[-3000:])
        )


def total_duration(shot_plan: list[dict]) -> float:
    total = 0.0
    for beat in shot_plan:
        total += max(0.4, float(beat["end"]) - float(beat["start"]))
    return total


def drawtext_filter(text: str, y: int) -> str:
    escaped = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    font_part = f"fontfile={FONT}:" if FONT.exists() else ""
    return (
        "drawtext="
        f"{font_part}text='{escaped}':"
        "fontcolor=white:fontsize=54:line_spacing=10:"
        "borderw=5:bordercolor=black:"
        "box=1:boxcolor=black@0.35:boxborderw=18:"
        f"x=(w-text_w)/2:y={y}"
    )


def scene_filter(beat: dict) -> str:
    caption = str(beat.get("caption", "")).strip()
    scene_type = str(beat.get("type", "screen")).lower()
    base = [
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={WIDTH}:{HEIGHT}",
        f"fps={FPS}",
        "setsar=1",
        "eq=contrast=1.08:saturation=1.12:brightness=0.01",
        "unsharp=5:5:0.7:5:5:0.35",
    ]

    if scene_type == "screen":
        base.append("drawbox=x=58:y=58:w=964:h=1804:color=white@0.16:t=3")
        base.append("drawbox=x=90:y=720:w=900:h=210:color=red@0.92:t=10")
        y = 1540
    else:
        base.append("drawbox=x=0:y=0:w=1080:h=1920:color=red@0.18:t=12:enable='lt(t,0.18)'")
        y = 126

    if caption:
        base.append(drawtext_filter(caption, y))
    return ",".join(base)


def render_scene(source: Path, beat: dict, index: int) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    duration = max(0.4, float(beat["end"]) - float(beat["start"]))
    out = OUTPUT_DIR / f"scene_{index:02d}.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-vf",
            scene_filter(beat),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-b:v",
            "8M",
            "-minrate",
            "8M",
            "-maxrate",
            "8M",
            "-bufsize",
            "8M",
            "-x264-params",
            "nal-hrd=cbr:filler=1:force-cfr=1",
            "-pix_fmt",
            "yuv420p",
            str(out),
        ],
        timeout=300,
    )
    return out


def concat_scenes(paths: list[Path]) -> Path:
    list_path = OUTPUT_DIR / "scene_list.txt"
    list_path.write_text("".join(f"file '{p}'\n" for p in paths), encoding="utf-8")
    out = OUTPUT_DIR / "video_no_audio.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            str(out),
        ],
        timeout=180,
    )
    return out


def mux_audio(video_path: Path, audio_path: Path, duration: float) -> Path:
    out = OUTPUT_DIR / "FINAL_PRODUCTION_SHORT.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out),
        ],
        timeout=240,
    )
    return out


def make_contact_sheet(video_path: Path) -> Path:
    out = OUTPUT_DIR / "contact_sheet.jpg"
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            "fps=1,scale=180:-1,tile=6x6",
            str(out),
        ],
        timeout=120,
    )
    return out


def assemble() -> Path:
    manifest = validate_manifest()
    host = (INPUT_DIR / manifest["host_clip"]).resolve()
    screen = (INPUT_DIR / manifest["screen_clip"]).resolve()
    audio = (INPUT_DIR / manifest["audio"]).resolve()
    shot_plan = manifest["shot_plan"]

    scenes = []
    for index, beat in enumerate(shot_plan):
        scene_type = str(beat.get("type", "screen")).lower()
        source = host if scene_type == "host" else screen
        scenes.append(render_scene(source, beat, index))

    video_no_audio = concat_scenes(scenes)
    duration = total_duration(shot_plan)
    final = mux_audio(video_no_audio, audio, duration)
    contact = make_contact_sheet(final)

    LEGACY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    run(["cp", "-f", str(final), str(LEGACY_OUTPUT)], timeout=30)

    build_manifest = {
        "created_at": int(time.time()),
        "final_video": str(final),
        "legacy_output": str(LEGACY_OUTPUT),
        "contact_sheet": str(contact),
        "duration_seconds": round(duration, 2),
        "resolution": f"{WIDTH}x{HEIGHT}",
        "voice_policy": "source audio preserved; no synthetic voice inserted",
        "shot_plan": shot_plan,
    }
    (OUTPUT_DIR / "build_manifest.json").write_text(json.dumps(build_manifest, indent=2), encoding="utf-8")
    return final


def main() -> int:
    final = assemble()
    print(f"Production render complete: {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
