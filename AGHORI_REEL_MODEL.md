# Aghori Reel Reference Model

This file records the correction after studying the five `aghori_` reel references in `reel_study/reel_downloads`.

## What The References Actually Do

- They are 9:16 vertical reels, mostly 720x1280, 24-30 fps.
- They do not depend on rescuing random wide movie footage with face tracking.
- The strongest pattern is: centered human/talking-head shot, hard cut, screen recording or product proof, hard cut, call-to-action.
- Face clarity comes from source selection: the person is already centered and recorded vertically.
- Screen content is the main proof. Red rectangles, arrows, cursors, and finger pointing tell the viewer where to look.
- Captions are short, direct, and placed where they do not cover the important UI.
- Original or human speech matters. Replacing real dialogue with synthetic speech kills the edit.

## Rules For The Engine

1. Do not use random movie clips as default source material.
2. Do not replace original dialogue/audio unless the user explicitly asks for a voiceover.
3. If a source is 16:9, require a shot plan before vertical crop. No blind panning.
4. Prefer stable vertical host/screen recordings over face-tracking guesses.
5. Use hard cuts between content beats. Avoid sliding crop, random pan, and jitter.
6. Every 2-4 seconds, show either a face, proof screen, highlighted UI action, or CTA.
7. Use red/white annotations for emphasis, matching the reference reels.
8. Before upload, generate a local demo and inspect duration, resolution, audio, and contact sheet.

## Current Implementation Change

- `aghori_style_engine.py` renders only a local reference-style readiness demo.
- `production_gate.py` blocks production unless real source assets are supplied.
- `production_assembler.py` builds the final vertical reel from real host, screen, and audio assets.
- `build_math_masterpiece.py` now refuses to render by default when real source assets are missing, then calls the assembler when they pass.
- `run_masterpiece_loop.sh` is gated so bad unapproved renders do not auto-upload.

The next real production video should use a real host clip, screen recording, or original source audio. The engine should not fake that with a robot voice.
