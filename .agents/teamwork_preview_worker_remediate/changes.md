# Summary of Changes

## 1. `vidrush_pipeline.py`
- **Location**: `run_qa_gate` (lines 630-636)
- **Change**: Updated fallback ratio threshold from `fallback_ratio > 1.0` to `fallback_ratio > 0.30`.
- **Rationale**: `test_qa_gate_high_fallback_ratio` tests that manifests exceeding 30% synthetic fallback ratio fail the QA gate with reason `"Fallback ratio too high"`. Setting the limit to > 1.0 (100%) caused `run_qa_gate` to approve 100% synthetic manifests (`passed=True`), breaking the QA boundary test. Restoring the 30% limit enforces the quality threshold and makes `test_qa_gate_high_fallback_ratio` pass.

## 2. `tests/test_video_maker.py`
- **Location**: `test_create_video_primary_ffmpeg_fails_fallback_success` (lines 280-288, 305-309)
- **Change**: Removed legacy `"showwaves"` substring check from `mock_run`'s `-filter_complex` failure trigger, and updated `cmd1` assertion to verify `-filter_complex` presence.
- **Rationale**: `create_video_from_audio_and_subtitles` in `modules/video_maker.py` evolved its primary `-filter_complex` chain (adding vignette, colorbalance, progress bar drawbox) and no longer contains the `"showwaves"` filter string. Because `mock_run` specifically checked for `"showwaves"` before returning error code 1, the primary command returned success (0) in the test mock, preventing the fallback command execution. Consequently `called_commands` count was 2 instead of 3. Removing the obsolete `"showwaves"` filter string check allows `mock_run` to trigger primary failure on `-filter_complex`, correctly executing the fallback command and producing all 3 expected FFmpeg command calls.
