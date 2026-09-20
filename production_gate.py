#!/usr/bin/env python3
"""Hard quality gate for production Shorts generation.

This prevents the engine from silently producing low-quality videos when the
required real assets are missing. The earlier failed outputs came from making
guesses with movie clips, robot voice, and unstable auto-crop. Production now
requires a deliberate source package.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "production_inputs"
MANIFEST = INPUT_DIR / "manifest.json"

REQUIRED_FILES = {
    "host_clip": "Centered real face/host clip, vertical preferred",
    "screen_clip": "Screen recording or proof/demo clip",
    "audio": "Original dialogue or approved human voice audio",
}


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    width: int | None
    height: int | None
    duration: float
    has_audio: bool


class GateError(RuntimeError):
    pass


def _probe(path: Path) -> MediaInfo:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type,width,height",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise GateError(f"Cannot read media file: {path}")

    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    duration = float(data.get("format", {}).get("duration", 0.0) or 0.0)
    return MediaInfo(
        path=path,
        width=int(video["width"]) if "width" in video else None,
        height=int(video["height"]) if "height" in video else None,
        duration=duration,
        has_audio=has_audio,
    )


def load_manifest() -> dict:
    if not MANIFEST.exists():
        raise GateError(
            f"Missing production manifest: {MANIFEST}\n"
            "Create it from production_inputs/README.md before rendering."
        )
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GateError(f"Invalid JSON in {MANIFEST}: {exc}") from exc
    if not isinstance(data, dict):
        raise GateError("production_inputs/manifest.json must be a JSON object.")
    return data


def validate_manifest() -> dict:
    data = load_manifest()
    errors: list[str] = []

    for key, label in REQUIRED_FILES.items():
        value = data.get(key)
        if not value:
            errors.append(f"Missing `{key}`: {label}")
            continue
        path = (INPUT_DIR / value).resolve()
        if not path.exists():
            errors.append(f"`{key}` file not found: {path}")
            continue

        try:
            info = _probe(path)
        except GateError as exc:
            errors.append(str(exc))
            continue

        if key in {"host_clip", "screen_clip"}:
            if not info.width or not info.height:
                errors.append(f"`{key}` has no video stream: {path}")
            elif info.height < info.width:
                errors.append(
                    f"`{key}` is horizontal ({info.width}x{info.height}). "
                    "Use vertical source or add an explicit shot_plan."
                )
            if info.duration < 3.0:
                errors.append(f"`{key}` is too short ({info.duration:.1f}s). Need at least 3s.")

        if key == "audio":
            if info.duration < 5.0:
                errors.append(f"`audio` is too short ({info.duration:.1f}s). Need real usable voice/dialogue.")

    shot_plan = data.get("shot_plan")
    if not isinstance(shot_plan, list) or len(shot_plan) < 4:
        errors.append("Missing `shot_plan`: add at least 4 planned beats/cuts.")

    if data.get("allow_synthetic_voice") is True:
        errors.append("Synthetic voice is blocked for this style unless the user explicitly approves it.")

    if errors:
        raise GateError("Production gate failed:\n- " + "\n- ".join(errors))

    return data


def main() -> int:
    try:
        validate_manifest()
    except GateError as exc:
        print(exc)
        return 2
    print("Production gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
