# Handoff Report — pytest Verification Findings

## 1. Observation
We ran the pytest suite on the YouTube Viral Machine project using the command:
`PYTHONPATH=. pytest tests/ -v`

Out of 43 tests, **41 passed** and **2 failed** (exit status code: 1):
- `tests/test_tier1_coverage.py::test_build_scene_visuals_happy`
- `tests/test_tier3_combinations.py::test_combination_full_pipeline_dry_run[asyncio]`

### Verbatim Errors:
**Failure 1:**
```
________________________ test_build_scene_visuals_happy ________________________

    def test_build_scene_visuals_happy():
        # Scene with low duration (no cuts)
        scene = {"text": "Hello", "suggested_visual_keyword": "neon light"}
        res = build_scene_visuals(scene, 1, duration=3.0)
        assert os.path.exists(res)
>       assert os.path.getsize(res) > 1000
E       AssertionError: assert 0 > 1000
E        +  where 0 = <function getsize at 0x7f2924222e80>('/home/junglee01/youtube-viral-machine/output/vidrush/motion_1_1.mp4')
```

**Failure 2:**
```
_______________ test_combination_full_pipeline_dry_run[asyncio] ________________
...
>       duration = float(result.stdout.decode().strip())
E       ValueError: could not convert string to float: '[mp3 @ 0x55eee12d4080] Failed to find two consecutive MPEG audio frames.\n/home/junglee01/youtube-viral-machine/output/vidrush/audio_scene_5.mp3: Invalid data found when processing input'

vidrush_pipeline.py:133: ValueError
```

Through direct manual commands, we observed that:
1. Running the ffmpeg command with `zoom_expr = "max(1.5-0.002*n,1.0)"` yields:
   `[Parsed_zoompan_1 @ 0x7f647800f9c0] [Eval @ 0x7f6486dbb770] Undefined constant or missing '(' in 'n,1.0)'`
   `Conversion failed!`
2. In `tests/conftest.py` lines 98-101:
   ```python
   temp_audio = os.path.join(TEMP_DIR, f"temp_stream_{int(time.time())}.mp3")
   create_mock_audio(temp_audio, duration=3.0)
   ```
3. Checking output directory sizes showed:
   `-rw-rw-r-- 1 junglee01 ... 0 Jul 10 00:21 audio_scene_5.mp3`

---

## 2. Logic Chain

### For Failure 1 (test_build_scene_visuals_happy):
1. `test_build_scene_visuals_happy` calls `build_scene_visuals(scene, 1, duration=3.0)`.
2. Under 4.0 seconds duration, this calls `generate_visual_cut` in `vidrush_pipeline.py`.
3. In `generate_visual_cut`, a random choice determines `zoom_in`:
   `zoom_expr = "min(zoom+0.002,1.5)" if zoom_in else "max(1.5-0.002*n,1.0)"`
4. If `zoom_in` is chosen as `False`, the expression `max(1.5-0.002*n,1.0)` is used.
5. In the FFmpeg `zoompan` filter, `n` is an undefined constant (FFmpeg expects `on` for the output frame count).
6. Thus, FFmpeg fails immediately with error code 234 (`Undefined constant ... in 'n,1.0)'`), writing 0 bytes to `motion_1_1.mp4`.
7. This causes `assert os.path.getsize(res) > 1000` to fail since size is `0`.

### For Failure 2 (test_combination_full_pipeline_dry_run):
1. Because the `zoompan` command fails immediately when `zoom_in` is `False`, the execution of that scene visual completes in a few milliseconds instead of taking the normal ~1.5 seconds.
2. The next scene's audio generation starts immediately.
3. In `tests/conftest.py`, the mock class `MockCommunicate` generates a temporary audio file named `temp_stream_{int(time.time())}.mp3`.
4. Because the time in seconds does not change between rapid scene iterations, the exact same filename is used (`temp_stream_X.mp3`).
5. This filename collision causes concurrent/subsequent file operations to overwrite or delete the active file while it is being read, resulting in empty (0-byte) audio being written (`audio_scene_5.mp3`).
6. `vidrush_pipeline.py` calls `ffprobe` to determine the audio duration.
7. `ffprobe` fails to parse `audio_scene_5.mp3` because it is empty, emitting an invalid data error and causing `float()` conversion in Python to raise a `ValueError`.

---

## 3. Caveats
- We did not modify any source code (per key constraints).
- Real Pexels API and edge-tts libraries were not tested with real networks, only their mocks in `conftest.py` were run.

---

## 4. Conclusion
The test suite contains two bugs:
1. **Flaky zoompan expression** in `vidrush_pipeline.py:229`: Uses undefined variable `n` instead of `on` in FFmpeg zoompan zoom-out expression, leading to random test failures when `zoom_in` is `False`.
2. **File collision in test mock** in `tests/conftest.py:98`: Uses `int(time.time())` for temp stream naming. When a fast execution occurs, the timestamp remains identical, causing filename collision, 0-byte audio outputs, and a pipeline crash in dry-runs.

---

## 5. Verification Method
- Execute the test command:
  `PYTHONPATH=. pytest tests/ -v`
- Inspect `tests/test_tier1_coverage.py` line 169 and `tests/test_tier3_combinations.py` line 99.
- Inspect the output directory `/home/junglee01/youtube-viral-machine/output/vidrush/` for 0-byte `.mp4` and `.mp3` files.
- Inspect `tests/conftest.py` line 98 for mock file generation.
