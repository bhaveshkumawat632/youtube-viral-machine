## 2026-07-10T00:04:23Z
You are a worker agent (teamwork_preview_worker). Your working directory is `/home/junglee01/youtube-viral-machine/.agents/worker_e2e_impl`.
Your task is to implement the E2E Testing Track for the YouTube Viral Machine upgrade:

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

### Deliverables & Steps:
1. Create `TEST_INFRA.md` in the project root mapping out the E2E test methodology, feature inventory (subtitles, audio layering, visual fallback sourcing, verification suite), and coverage thresholds.
2. Implement the automated verification test suite in `tests/` using pytest. It must follow the 4-tier test case design:
   - Tier 1: Feature Coverage (>=5 test cases per feature, happy-path).
   - Tier 2: Boundary & Corner Cases (>=5 test cases per feature, e.g., missing API keys, empty text, extreme audio levels).
   - Tier 3: Cross-Feature Combinations (pairwise interactions).
   - Tier 4: Real-world Application Scenarios (E2E run assertions on duration, safe-zone margins, clipping levels, and H.264/AAC codecs via ffprobe/ffmpeg).
3. Design proper mocks or mock fixtures for external API calls (fal.ai, Gradio client, Pexels, Coverr) so the test suite can run deterministically locally. Place them in `tests/conftest.py` so they are automatically loaded.
   - Note: Since some modules check that downloaded files exist and exceed a minimum size threshold of 200KB (e.g. `os.path.getsize(path) > 200000`), your mock fixtures must create valid dummy files containing at least 250KB of mock data to bypass size checks.
4. Execute/verify the tests on the existing codebase (they may fail due to missing features, but should be syntactically correct and run). Record the test run outputs and failure logs.
5. Once complete, publish `TEST_READY.md` in the project root with the test runner details, expected test output, and coverage checklist.
6. Write a handoff report at `/home/junglee01/youtube-viral-machine/.agents/worker_e2e_impl/handoff.md` summarizing the files created, commands run, test results, and layout compliance.
7. Send a handoff message to parent.

### Test Architecture Details (from Explorer reports):
- Mock fixtures for `gradio_client.Client`, `fal_client` (patched `sys.modules`), Pexels API (`requests.get`), Coverr (`urllib.request.urlopen`), and subprocess `wget` or `curl` downloads (redirecting to mock files >200KB).
- **Tier 1 (Unit)**: Fast local tests for component logic (`hex_to_ass_color`, `seconds_to_ass_time`, `get_emotion_voice_settings`, `group_words_into_lines`, `check_copyright_killswitch`).
- **Tier 2 (Integration)**: Tests for `subtitle_generator.py` ASS file structure, `audio_mixer.py` FFmpeg compiler command builder, and `vidrush_pipeline.py` fallback cascade.
- **Tier 3 (E2E Render)**: Tests that compile a full 5-second video, using `ffprobe` to assert container format (`mp4`), video codec (`h264`), audio codec (`aac`), portrait layout (`1080x1920`), framerate (`30`), and subtitle vertical safe-zone bounds (avoiding top 12% and bottom 15% player overlays).
- **Tier 4 (QA Gate)**: Checks for business gates: fallback visuals ratio <=30%, license manifest logger, alert generation on crash, and dry-run upload safety.
