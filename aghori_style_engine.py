#!/usr/bin/env python3
"""
Reference-based Shorts renderer for the aghori_ reel style.

This intentionally avoids the failed pattern from the previous engine:
random wide movie clip + synthetic narrator + fragile auto-crop.

Observed reference pattern:
- 9:16 vertical frame.
- Talking-head/host is already centered, not rescued by face tracking.
- Screen proof and product UI are the main visual content.
- Hard cuts between host and proof shots.
- Red/white annotation text, red boxes, cursor/finger guidance.
- No robotic voice replacement. If no real source voice is provided, render
  visual proof with a simple music bed and captions only.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont


BASE_DIR = Path(__file__).resolve().parent
WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 18.0

OUTPUT_DIR = BASE_DIR / "output" / "aghori_style"
LEGACY_OUTPUT_DIR = BASE_DIR / "output" / "vidrush" / "math_masterpiece"
REFERENCE_DIR = BASE_DIR / "reel_study" / "reel_downloads"
HOST_IMAGE = BASE_DIR / "assets" / "character" / "transparent" / "host_talk.png"
FONT_BOLD = BASE_DIR / "assets" / "fonts" / "Montserrat-ExtraBold.ttf"


@dataclass(frozen=True)
class Scene:
    start: float
    end: float
    name: str
    draw: Callable[[Image.Image, float], None]


def run(cmd: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed: {}\n{}".format(" ".join(cmd), result.stderr[-2000:])
        )
    return result


def load_font(size: int, *, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        FONT_BOLD if bold else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_HUGE = load_font(78)
FONT_TITLE = load_font(56)
FONT_BODY = load_font(42)
FONT_SMALL = load_font(30)
FONT_TINY = load_font(24)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = word if not current else f"{current} {word}"
        if text_size(draw, test, font)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_centered(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    font: ImageFont.ImageFont,
    fill: str | tuple[int, int, int] = "white",
    max_width: int = 920,
    stroke_width: int = 5,
    stroke_fill: str = "black",
    line_gap: int = 12,
) -> int:
    lines = wrap_text(draw, text, font, max_width)
    cursor = y
    for line in lines:
        w, h = text_size(draw, line, font)
        draw.text(
            ((WIDTH - w) // 2, cursor),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        cursor += h + line_gap
    return cursor


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str | tuple[int, int, int, int],
    outline: str | tuple[int, int, int, int] | None = None,
    width: int = 1,
    radius: int = 18,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def make_gradient(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT))
    px = img.load()
    for y in range(HEIGHT):
        ratio = y / max(1, HEIGHT - 1)
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        for x in range(WIDTH):
            px[x, y] = (r, g, b)
    return img


BASE_BG = make_gradient((16, 19, 26), (8, 10, 14))
WHITE = (245, 247, 250)
MUTED = (170, 178, 190)
RED = (242, 35, 58)
GREEN = (42, 214, 117)
YELLOW = (255, 204, 71)


def alpha_paste(base: Image.Image, overlay: Image.Image, x: int, y: int) -> None:
    if overlay.mode != "RGBA":
        overlay = overlay.convert("RGBA")
    base.alpha_composite(overlay, (x, y))


def draw_host(base: Image.Image, x: int, y: int, height: int, bob: float = 0.0) -> None:
    if not HOST_IMAGE.exists():
        return
    host = Image.open(HOST_IMAGE).convert("RGBA")
    scale = height / host.height
    host = host.resize((int(host.width * scale), height), Image.Resampling.LANCZOS)
    shadow = Image.new("RGBA", host.size, (0, 0, 0, 0))
    mask = host.split()[-1]
    shadow.paste((0, 0, 0, 140), mask=mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    alpha_paste(base, shadow, x + 12, y + int(20 + bob))
    alpha_paste(base, host, x, y + int(bob))


def draw_repo_screen(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, progress: float) -> None:
    rounded_rect(draw, (x, y, x + w, y + h), fill=(10, 12, 18), outline=(64, 73, 88), width=3, radius=18)
    rounded_rect(draw, (x + 22, y + 24, x + w - 22, y + 92), fill=(22, 26, 36), radius=12)
    draw.text((x + 46, y + 43), "github.com / ai-tool-kit", font=FONT_SMALL, fill=WHITE)
    draw.ellipse((x + w - 145, y + 44, x + w - 122, y + 67), fill=RED)
    draw.ellipse((x + w - 105, y + 44, x + w - 82, y + 67), fill=YELLOW)
    draw.ellipse((x + w - 65, y + 44, x + w - 42, y + 67), fill=GREEN)

    draw.text((x + 42, y + 128), "AI Workflow Repo", font=FONT_TITLE, fill=WHITE)
    draw.text((x + 44, y + 194), "Claude + Codex + local tools in one shell", font=FONT_SMALL, fill=MUTED)

    colors = [RED, GREEN, (93, 173, 226), YELLOW]
    labels = ["MCP", "Plugins", "Local token tracking", "Agent routing"]
    for index, label in enumerate(labels):
        bx = x + 44 + (index % 2) * 350
        by = y + 260 + (index // 2) * 84
        rounded_rect(draw, (bx, by, bx + 310, by + 52), fill=(27, 32, 44), outline=colors[index], width=2, radius=10)
        draw.text((bx + 18, by + 12), label, font=FONT_TINY, fill=WHITE)

    list_y = y + 460
    for i in range(7):
        row_y = list_y + i * 70
        draw.rectangle((x + 44, row_y, x + w - 44, row_y + 1), fill=(50, 58, 72))
        draw.text((x + 72, row_y + 19), f"step-{i + 1}.md", font=FONT_SMALL, fill=WHITE)
        line_w = int(350 + 180 * math.sin(progress * math.pi * 2 + i))
        draw.rounded_rectangle((x + 300, row_y + 26, x + 300 + line_w, row_y + 43), radius=8, fill=(48, 59, 74))

    hi_x = x + 38
    hi_y = y + 245 + int(16 * math.sin(progress * math.pi * 2))
    draw.rounded_rectangle((hi_x, hi_y, hi_x + 690, hi_y + 205), radius=16, outline=RED, width=8)
    cursor_x = x + 730 + int(26 * math.sin(progress * math.pi * 4))
    cursor_y = y + 384 + int(22 * math.cos(progress * math.pi * 3))
    draw.polygon(
        [(cursor_x, cursor_y), (cursor_x + 48, cursor_y + 118), (cursor_x + 75, cursor_y + 75), (cursor_x + 130, cursor_y + 100)],
        fill=WHITE,
        outline=(0, 0, 0),
    )


def draw_phone_screen(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, progress: float) -> None:
    rounded_rect(draw, (x, y, x + w, y + h), fill=(242, 244, 247), outline=(36, 41, 48), width=6, radius=42)
    rounded_rect(draw, (x + 140, y + 22, x + w - 140, y + 54), fill=(18, 21, 28), radius=16)
    draw.text((x + 48, y + 94), "Free Domain", font=FONT_TITLE, fill=(20, 22, 28))
    draw.text((x + 50, y + 166), "1 available", font=FONT_SMALL, fill=(79, 92, 108))
    fields = ["Repository", "Domain", "Confirm"]
    for i, field in enumerate(fields):
        fy = y + 250 + i * 150
        draw.text((x + 54, fy - 42), field, font=FONT_TINY, fill=(68, 79, 94))
        rounded_rect(draw, (x + 52, fy, x + w - 52, fy + 76), fill=(255, 255, 255), outline=(210, 216, 226), radius=12)
        value = "junglee01-workflow" if i == 0 else "work.gd" if i == 1 else "Ready"
        draw.text((x + 78, fy + 20), value, font=FONT_SMALL, fill=(24, 27, 33))
    target_y = y + 400 + int(110 * progress)
    draw.rounded_rectangle((x + 38, target_y, x + w - 38, target_y + 92), radius=14, outline=RED, width=8)


def draw_hook_scene(base: Image.Image, progress: float) -> None:
    draw = ImageDraw.Draw(base)
    draw_host(base, 110, 132, 650, bob=10 * math.sin(progress * math.pi * 2))
    draw_centered(draw, 72, "POV: You found the AI workflow", FONT_TITLE, fill=RED, stroke_width=6)
    draw_centered(draw, 780, "proof first, then steps", FONT_HUGE, fill=RED, stroke_width=8)
    draw_repo_screen(draw, 84, 1005, 912, 760, progress)
    draw_centered(draw, 1782, "No random movie clips. No fake tracking.", FONT_SMALL, fill=WHITE, stroke_width=4)


def draw_face_quiz_scene(base: Image.Image, progress: float) -> None:
    draw = ImageDraw.Draw(base)
    draw.text((60, 70), "GitHub", font=FONT_HUGE, fill=WHITE, stroke_width=5, stroke_fill="black")
    draw.text((62, 165), "Do you really know agent workflows?", font=FONT_BODY, fill=WHITE, stroke_width=4, stroke_fill="black")
    draw_host(base, 208, 250, 840, bob=8 * math.sin(progress * math.pi * 2))

    card_x = 78
    card_y = 1095
    rounded_rect(draw, (card_x, card_y, WIDTH - 78, card_y + 420), fill=(246, 248, 252), radius=20)
    draw.text((card_x + 36, card_y + 34), "3 things the viewer must see", font=FONT_BODY, fill=(20, 24, 32))
    items = ["Real face / real screen", "One idea per shot", "Hard cut on every proof point"]
    for i, item in enumerate(items):
        iy = card_y + 118 + i * 86
        draw.ellipse((card_x + 42, iy + 8, card_x + 76, iy + 42), fill=RED)
        draw.text((card_x + 100, iy), item, font=FONT_SMALL, fill=(20, 24, 32))
    draw_centered(draw, 1588, "Face stays centered because the source is planned.", FONT_BODY, fill=WHITE, stroke_width=5)


def draw_screen_tutorial_scene(base: Image.Image, progress: float) -> None:
    draw = ImageDraw.Draw(base)
    draw_repo_screen(draw, 46, 120, 988, 1060, progress)
    rounded_rect(draw, (96, 1230, 984, 1525), fill=(255, 255, 255), radius=16)
    draw.text((132, 1272), "Editor rule", font=FONT_TITLE, fill=(20, 24, 32))
    draw.text((132, 1350), "Hard cuts beat random pan.", font=FONT_BODY, fill=(20, 24, 32))
    draw.text((132, 1412), "If source is wide, make a shot plan.", font=FONT_SMALL, fill=(70, 80, 95))
    draw.rounded_rectangle((122, 1340, 888, 1406), radius=12, outline=RED, width=7)
    draw_centered(draw, 1608, "Show the exact button, repo, result.", FONT_BODY, fill=WHITE, stroke_width=5)


def draw_phone_demo_scene(base: Image.Image, progress: float) -> None:
    draw = ImageDraw.Draw(base)
    draw_phone_screen(draw, 250, 105, 580, 1260, progress)
    draw.line((160, 1390, 884, 995), fill=(255, 130, 160), width=18)
    draw.polygon([(875, 993), (800, 994), (842, 932)], fill=(255, 130, 160))
    rounded_rect(draw, (112, 1462, 968, 1640), fill=(255, 255, 255), radius=14)
    draw_centered(draw, 1496, "Comment ANYTHING and I will DM the workflow", FONT_SMALL, fill=(20, 24, 32), stroke_width=0)
    draw_centered(draw, 1712, "Bottom CTA is clear. Product proof stays visible.", FONT_BODY, fill=WHITE, stroke_width=5)


def draw_final_scene(base: Image.Image, progress: float) -> None:
    draw = ImageDraw.Draw(base)
    draw_host(base, 560, 240, 720, bob=6 * math.sin(progress * math.pi * 2))
    draw.text((70, 100), "New engine rule-set", font=FONT_TITLE, fill=WHITE)
    rules = [
        ("KEEP", "original audio when source has dialogue"),
        ("USE", "centered host + screen-record proof"),
        ("CUT", "hard between host and UI evidence"),
        ("REJECT", "random movie crop + robot voice"),
    ]
    for i, (verb, text) in enumerate(rules):
        y = 610 + i * 205
        rounded_rect(draw, (70, y, 945, y + 128), fill=(23, 28, 38), outline=RED if i == 3 else (64, 73, 88), width=4, radius=16)
        draw.text((104, y + 28), verb, font=FONT_BODY, fill=RED if i == 3 else GREEN)
        draw.text((284, y + 34), text, font=FONT_SMALL, fill=WHITE)
    draw_centered(draw, 1542, "Ready for the next exam with the right format.", FONT_BODY, fill=WHITE, stroke_width=5)


def scenes() -> list[Scene]:
    return [
        Scene(0.0, 3.4, "hook_face_plus_screen", draw_hook_scene),
        Scene(3.4, 6.6, "centered_host_quiz", draw_face_quiz_scene),
        Scene(6.6, 10.4, "screen_proof_tutorial", draw_screen_tutorial_scene),
        Scene(10.4, 14.4, "phone_screen_cta", draw_phone_demo_scene),
        Scene(14.4, DURATION, "engine_rules", draw_final_scene),
    ]


def draw_frame(frame_index: int, scene_list: list[Scene]) -> Image.Image:
    t = frame_index / FPS
    scene = next((s for s in scene_list if s.start <= t < s.end), scene_list[-1])
    progress = (t - scene.start) / max(0.001, scene.end - scene.start)

    img = BASE_BG.copy().convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    shift = int(60 * math.sin(t * 1.2))
    od.rectangle((0, 0, WIDTH, 350 + shift), fill=(255, 255, 255, 10))
    od.rectangle((0, 1560 + shift, WIDTH, HEIGHT), fill=(255, 255, 255, 8))
    img.alpha_composite(overlay)

    scene.draw(img, progress)

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((60, 1842, 1020, 1856), radius=7, fill=(44, 50, 61))
    draw.rounded_rectangle((60, 1842, 60 + int(960 * min(1.0, t / DURATION)), 1856), radius=7, fill=RED)
    return img.convert("RGB")


def reference_stats() -> list[dict[str, object]]:
    stats = []
    for path in sorted(REFERENCE_DIR.glob("*.mp4")):
        try:
            probe = run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height,r_frame_rate",
                    "-show_entries",
                    "format=duration,size",
                    "-of",
                    "json",
                    str(path),
                ],
                timeout=30,
            )
            data = json.loads(probe.stdout)
            stream = data.get("streams", [{}])[0]
            fmt = data.get("format", {})
            stats.append(
                {
                    "file": path.name,
                    "width": int(stream.get("width", 0)),
                    "height": int(stream.get("height", 0)),
                    "fps": stream.get("r_frame_rate", ""),
                    "duration_seconds": round(float(fmt.get("duration", 0.0)), 2),
                    "size_bytes": int(fmt.get("size", 0)),
                }
            )
        except Exception as exc:
            stats.append({"file": path.name, "error": str(exc)})
    return stats


def render(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(DURATION * FPS)
    scene_list = scenes()

    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "warning",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "pipe:0",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=88:sample_rate=48000:duration={DURATION}",
        "-shortest",
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
        "16M",
        "-x264-params",
        "nal-hrd=cbr:filler=1:force-cfr=1",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-af",
        f"volume=0.20,afade=t=in:st=0:d=0.2,afade=t=out:st={DURATION - 0.6}:d=0.6",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for frame_index in range(frame_count):
            frame = draw_frame(frame_index, scene_list)
            proc.stdin.write(frame.tobytes())
    except BrokenPipeError:
        stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        raise RuntimeError(f"FFmpeg process died prematurely:\n{stderr}")
    finally:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()
    stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    code = proc.wait()
    if code != 0:
        raise RuntimeError(stderr[-3000:])
    return output_path


def write_manifest(final_path: Path, legacy_path: Path | None) -> Path:
    manifest = {
        "created_at": int(time.time()),
        "engine": "aghori_style_engine",
        "final_video": str(final_path),
        "legacy_loop_output": str(legacy_path) if legacy_path else None,
        "resolution": f"{WIDTH}x{HEIGHT}",
        "duration_seconds": DURATION,
        "source_model": "aghori_ reference reels",
        "voice_policy": "no synthetic narrator in this readiness demo; preserve real source audio in production",
        "style_rules": [
            "Use 9:16 vertical source or planned host/screen layouts.",
            "Do not auto-crop random wide movie scenes as the default content source.",
            "Keep talking-head faces centered by design instead of chasing them with unstable tracking.",
            "Use hard cuts between host and screen proof; no random pans or sliding crop.",
            "Use red/white annotations, red boxes, and cursor/finger guidance for product proof.",
            "Never replace original dialogue with robotic voice unless explicitly requested.",
        ],
        "reference_reels": reference_stats(),
    }
    path = OUTPUT_DIR / "aghori_style_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the aghori_ reference-style readiness demo.")
    parser.add_argument(
        "--no-legacy-copy",
        action="store_true",
        help="Do not copy the result to output/vidrush/math_masterpiece/FINAL_VIRAL_SHORT.mp4.",
    )
    args = parser.parse_args(argv)

    final_path = OUTPUT_DIR / "DEMO_AGHORI_STYLE_ENGINE.mp4"
    legacy_path = None if args.no_legacy_copy else LEGACY_OUTPUT_DIR / "FINAL_VIRAL_SHORT.mp4"

    print("[aghori-style] rendering reference-based readiness demo")
    rendered = render(final_path)
    root_demo = BASE_DIR / "DEMO_AGHORI_STYLE_ENGINE.mp4"
    shutil.copy2(rendered, root_demo)

    if legacy_path:
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(rendered, legacy_path)

    manifest_path = write_manifest(rendered, legacy_path)
    print(f"[aghori-style] final: {rendered}")
    print(f"[aghori-style] root copy: {root_demo}")
    if legacy_path:
        print(f"[aghori-style] legacy loop output: {legacy_path}")
    print(f"[aghori-style] manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
