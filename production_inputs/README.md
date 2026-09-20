# Production Input Package

The engine will not generate production videos from random movie clips anymore.
Put deliberate source assets here, then create `manifest.json`.

Required files:

- `host_clip`: centered real face/host footage, vertical preferred.
- `screen_clip`: screen recording, website/app proof, or tutorial footage.
- `audio`: original dialogue or approved human voice audio.
- `shot_plan`: at least four planned beats/cuts.

Example `manifest.json`:

```json
{
  "host_clip": "host.mp4",
  "screen_clip": "screen_recording.mp4",
  "audio": "voice_or_original_audio.mp3",
  "allow_synthetic_voice": false,
  "shot_plan": [
    {"start": 0.0, "end": 2.5, "type": "host", "caption": "POV: you found the workflow"},
    {"start": 2.5, "end": 6.0, "type": "screen", "caption": "show repo proof"},
    {"start": 6.0, "end": 10.0, "type": "screen", "caption": "highlight exact button"},
    {"start": 10.0, "end": 14.0, "type": "host", "caption": "final CTA"}
  ]
}
```

Rules:

- No blind face tracking on 16:9 movie footage.
- No robotic replacement of original dialogue.
- No upload before local visual review.
- If source footage is horizontal, add a precise shot plan before cropping.
