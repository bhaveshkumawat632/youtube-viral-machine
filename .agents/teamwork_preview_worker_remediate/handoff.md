# Handoff Report — Legacy Unit Test Remediation

## 1. Observation
- Pre-remediation state: `pytest tests/` failed 2 unit tests out of 101:
  1. `tests/test_tier2_boundary.py:227` (`test_qa_gate_high_fallback_ratio`): `AssertionError: assert True is False`
  2. `tests/test_video_maker.py:303` (`test_create_video_primary_ffmpeg_fails_fallback_success`): `AssertionError: assert 2 == 3`
- File inspection findings:
  - In `vidrush_pipeline.py`: `run_qa_gate` evaluated fallback ratio check as `if fallback_ratio > 1.0:`. When a manifest had 100% synthetic visuals (`fallback_ratio = 1.0`), the check failed to trigger, causing `passed = True` instead of `False`.
  - In `tests/test_video_maker.py`: `mock_run` required `"showwaves"` to be present in `-filter_complex` before returning exit code 1 for the primary FFmpeg render. Because `create_video_from_audio_and_subtitles` in `modules/video_maker.py` upgraded its primary filter complex (with vignette, colorbalance, unsharp, and drawbox progress bar) and removed `"showwaves"`, `mock_run` returned exit code 0 for primary render, bypassing fallback execution and causing `len(called_commands)` to equal 2 instead of 3.

## 2. Logic Chain
- Fix 1 (`vidrush_pipeline.py`):
  - Changed `if fallback_ratio > 1.0:` back to `if fallback_ratio > 0.30:`.
  - With a 30% limit, `fallback_ratio = 1.0` triggers `errors.append("Fallback ratio too high...")`, returning `passed = False` and reason `"Fallback ratio too high"`.
  - Manifests with valid ratios (e.g. 25% in `test_run_qa_gate_happy`) continue to pass.
- Fix 2 (`tests/test_video_maker.py`):
  - Updated `mock_run` to check `if isinstance(cmd, list) and "-filter_complex" in cmd:` to simulate failure on the primary command.
  - Updated assertion line 308 to verify `-filter_complex` presence in `cmd1` rather than stale `"showwaves"`.
  - When primary command with `-filter_complex` fails (code 1), `create_video_from_audio_and_subtitles` invokes the fallback FFmpeg command (with `-vf`), resulting in 3 commands recorded in `called_commands` (gradient background, primary render, fallback render).

## 3. Caveats
- No caveats. Both fixes restore genuine behavior and match current codebase expectations.

## 4. Conclusion
- All 101 unit tests pass with 100% success rate (`101 passed, 0 failed`).
- Remediation complete.

## 5. Verification Method
- Command: `PYTHONPATH=. python3 -m pytest tests/`
- Expected result: 101 passed in test session summary output.
