# Project: YouTube Viral Machine Core Module Coverage Upgrade

## Architecture
- Target files: `modules/video_maker.py` and `modules/audio_mixer.py`.
- Framework: `pytest` with `pytest-cov`.
- Execution environment: Local offline mode (network disabled). All external processes/API calls must be mocked.

## Code Layout
- `modules/audio_mixer.py`: Mixing voiceover, BGM, and SFX with dynamic ducking.
- `modules/video_maker.py`: Final render/compilation of video clips, subtitles, and audio.
- `tests/`: Directory containing pytest suite.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | Audio Mixer Coverage | Write pytest unit tests targeting `modules/audio_mixer.py` to achieve 100% line coverage | None | COMPLETED |
| 2 | Video Maker Coverage | Write pytest unit tests targeting `modules/video_maker.py` to achieve 100% line coverage | M1 | COMPLETED |
| 3 | Verification & Audit | Execute forensic audit, confirm fast offline execution, and verify 100% line coverage of both files | M2 | COMPLETED |

## Interface Contracts
### `modules/audio_mixer.py`
- Exposes `mix_audio(voiceover_path, bgm_path, sfx_list, output_path, voice_volume=1.0, bgm_volume=0.25, duck_db=-15, duck_threshold=-30, filter_voice=True)`
- Must use FFmpeg commands via `subprocess` which must be mocked in tests.

### `modules/video_maker.py`
- Exposes functions for visual rendering, subtitles merging, and media concatenation.
- Calls FFmpeg commands, stock video source logic, etc. All must be mocked.
