# Baseline Test Results

This file contains the exact output and a summary of the initial test suite run.

## Summary of Results

- **Run Timestamp**: 2026-07-10T04:49:04+05:30
- **Total Tests Collected**: 43
- **Passed**: 42
- **Failed**: 1
- **Pass Rate**: 97.67%

### Failing Tests

1. `tests/test_tier1_coverage.py::test_build_scene_visuals_happy`
   - **Reason**: The generated video file `/home/junglee01/youtube-viral-machine/output/vidrush/motion_1_1.mp4` was 0 bytes in size, which failed the assertion `assert os.path.getsize(res) > 1000`.

---

## Exact Command Executed

```bash
PYTHONPATH=. pytest tests/ -v
```

## Exact Output

```text
============================= test session starts ==============================
platform linux -- Python 3.13.14, pytest-9.0.3, pluggy-1.6.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/junglee01/youtube-viral-machine
plugins: anyio-4.13.0, typeguard-4.4.4
collecting ... collected 43 items                                                             

tests/test_tier1_coverage.py::test_hex_to_ass_color_happy PASSED         [  2%]
tests/test_tier1_coverage.py::test_seconds_to_ass_time_happy PASSED      [  4%]
tests/test_tier1_coverage.py::test_group_words_into_lines_happy PASSED   [  6%]
tests/test_tier1_coverage.py::test_generate_ass_subtitles_happy PASSED   [  9%]
tests/test_tier1_coverage.py::test_generate_srt_subtitles_happy PASSED   [ 11%]
tests/test_tier1_coverage.py::test_emotion_settings_happy PASSED         [ 13%]
tests/test_tier1_coverage.py::test_generate_voiceover_happy PASSED       [ 16%]
tests/test_tier1_coverage.py::test_mix_audio_vo_only PASSED              [ 18%]
tests/test_tier1_coverage.py::test_mix_audio_vo_bgm PASSED               [ 20%]
tests/test_tier1_coverage.py::test_mix_audio_full_layering PASSED        [ 23%]
tests/test_tier1_coverage.py::test_cloud_video_generation_happy PASSED   [ 25%]
tests/test_tier1_coverage.py::test_pexels_stock_video_happy PASSED       [ 27%]
tests/test_tier1_coverage.py::test_pexels_downloader_multiple_happy PASSED [ 30%]
tests/test_tier1_coverage.py::test_build_scene_visuals_happy FAILED      [ 32%]
tests/test_tier1_coverage.py::test_build_scene_visuals_with_cuts_happy PASSED [ 34%]
tests/test_tier1_coverage.py::test_log_asset_happy PASSED                [ 37%]
tests/test_tier1_coverage.py::test_write_log_happy PASSED                [ 39%]
tests/test_tier1_coverage.py::test_create_alert_happy PASSED             [ 41%]
tests/test_tier1_coverage.py::test_run_qa_gate_happy PASSED              [ 44%]
tests/test_tier2_boundary.py::test_hex_to_ass_color_invalid PASSED       [ 46%]
tests/test_tier2_boundary.py::test_seconds_to_ass_time_negative PASSED   [ 48%]
tests/test_tier2_boundary.py::test_generate_ass_subtitles_empty PASSED   [ 51%]
tests/test_tier2_boundary.py::test_generate_srt_subtitles_empty PASSED   [ 53%]
tests/test_tier2_boundary.py::test_transcribe_missing_audio PASSED       [ 55%]
tests/test_tier2_boundary.py::test_mix_audio_missing_voice PASSED        [ 58%]
tests/test_tier2_boundary.py::test_mix_audio_negative_sfx_delay PASSED   [ 60%]
tests/test_tier2_boundary.py::test_mix_audio_extreme_volumes PASSED      [ 62%]
tests/test_tier2_boundary.py::test_mix_audio_nonexistent_outdir PASSED   [ 65%]
tests/test_tier2_boundary.py::test_generate_voiceover_empty PASSED       [ 67%]
tests/test_tier2_boundary.py::test_cloud_video_missing_api_keys PASSED   [ 69%]
tests/test_tier2_boundary.py::test_cloud_video_space_404 PASSED          [ 72%]
tests/test_tier2_boundary.py::test_pexels_stock_missing_key PASSED       [ 74%]
tests/test_tier2_boundary.py::test_pexels_stock_empty_results PASSED     [ 76%]
tests/test_tier2_boundary.py::test_visual_loop_fallback_to_gradient PASSED [ 79%]
tests/test_tier2_boundary.py::test_qa_gate_out_of_bounds_duration PASSED [ 81%]
tests/test_tier2_boundary.py::test_qa_gate_corrupted_manifest PASSED     [ 83%]
tests/test_tier2_boundary.py::test_qa_gate_unsafe_source PASSED          [ 86%]
tests/test_tier2_boundary.py::test_qa_gate_high_fallback_ratio PASSED    [ 88%]
tests/test_tier3_combinations.py::test_combination_voice_subtitles_sync PASSED [ 90%]
tests/test_tier3_combinations.py::test_combination_audio_video_assembly PASSED [ 93%]
tests/test_tier3_combinations.py::test_combination_fallback_cascade_to_local_loop PASSED [ 95%]
tests/test_tier3_combinations.py::test_combination_full_pipeline_dry_run[asyncio] PASSED [ 97%]
tests/test_tier4_e2e_render.py::test_tier4_e2e_render_and_technical_compliance PASSED [100%]

=================================== FAILURES ===================================
________________________ test_build_scene_visuals_happy ________________________

    def test_build_scene_visuals_happy():
        # Scene with low duration (no cuts)
        scene = {"text": "Hello", "suggested_visual_keyword": "neon light"}
        res = build_scene_visuals(scene, 1, duration=3.0)
        assert os.path.exists(res)
>       assert os.path.getsize(res) > 1000
E       AssertionError: assert 0 > 1000
E        +  where 0 = <function getsize at 0x7f77acb26e80>('/home/junglee01/youtube-viral-machine/output/vidrush/motion_1_1.mp4')
E        +    where <function getsize at 0x7f77acb26e80> = <module 'posixpath' (frozen)>.getsize
E        +      where <module 'posixpath' (frozen)> = os.path

tests/test_tier1_coverage.py:169: AssertionError
----------------------------- Captured stdout call -----------------------------
  -> Fetching visual for scene 1 (cut 1) using keyword 'neon light'...
  -> Applying Ken Burns effect for scene 1 (cut 1)...
=========================== short test summary info ============================
FAILED tests/test_tier1_coverage.py::test_build_scene_visuals_happy - Asserti...
======================== 1 failed, 42 passed in 46.77s =========================
```
