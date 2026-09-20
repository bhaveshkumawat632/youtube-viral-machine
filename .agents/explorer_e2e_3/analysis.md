# Coverage Analysis and Test Design: `modules/audio_mixer.py`

## 1. Executive Summary
This report presents the findings of our investigation into the test coverage of `modules/audio_mixer.py`. 
- **Baseline Coverage**: The module currently stands at **94% line coverage** (51 of 54 statements executed, 3 statements missed).
- **Missed Paths**: 
  1. The default output path generation branch when `output_path=None` (Lines 24–25).
  2. The module's standard execution entry point guard `if __name__ == "__main__":` (Line 93).
- **Proposed Solution**: A suite of five comprehensive, fast, offline unit tests using `unittest.mock` for `subprocess.run` and `runpy` to execute the module script entrypoint. Implementing these proposed test cases will raise the line coverage of `modules/audio_mixer.py` to **100%**.

---

## 2. Existing Test Coverage Inventory
We searched the `tests/` directory for references to `audio_mixer` and `mix_audio` and identified the following existing tests:

| Test File | Test Function | Purpose / Scope | Execution Mode |
|---|---|---|---|
| `tests/test_tier1_coverage.py` | `test_mix_audio_vo_only` | Verify mixing single voiceover track with default parameters and explicit output path | Runs actual FFmpeg |
| `tests/test_tier1_coverage.py` | `test_mix_audio_vo_bgm` | Verify layering voiceover and background music with sidechain ducking filter | Runs actual FFmpeg |
| `tests/test_tier1_coverage.py` | `test_mix_audio_full_layering` | Verify layering voiceover, background music, and a single SFX track with start delay and volume | Runs actual FFmpeg |
| `tests/test_tier2_boundary.py` | `test_mix_audio_missing_voice` | Verify that `mix_cinematic_audio` propagates error (RuntimeError) when voice file is missing | Runs actual FFmpeg |
| `tests/test_tier2_boundary.py` | `test_mix_audio_negative_sfx_delay` | Verify error-handling or clean execution when negative start time is provided in SFX track | Runs actual FFmpeg |
| `tests/test_tier2_boundary.py` | `test_mix_audio_extreme_volumes` | Verify that mixing behaves stably under extreme volumes (0.0 or 100.0) | Runs actual FFmpeg |
| `tests/test_tier2_boundary.py` | `test_mix_audio_nonexistent_outdir` | Verify that target parent directory is automatically created if it doesn't exist | Runs actual FFmpeg |

### Observation on Existing Mocks
While `tests/conftest.py` installs monkey-patches for `subprocess.run` to mock download tools (`wget` and `curl`), it falls back to executing the real system-level `subprocess` for FFmpeg operations. This makes the existing test suite dependent on having `ffmpeg` installed on the host system.

---

## 3. Code Path and Branch Analysis
An exhaustive code path analysis of `mix_cinematic_audio` in `modules/audio_mixer.py` reveals the following logical paths:

### Path A: Output Path Selection
- **Branch A1 (`output_path is None`)** *(Missed Line 24-25)*:
  ```python
  if output_path is None:
      os.makedirs(TEMP_DIR, exist_ok=True)
      output_path = os.path.join(TEMP_DIR, f"cinematic_mix_{int(time.time())}.mp3")
  ```
  - *Trigger*: Caller invokes `mix_cinematic_audio` without passing an `output_path` argument.
  - *Observation*: This block is currently unreached because all existing tests supply a specific `tmp_path`-derived filename.

- **Branch A2 (`output_path` provided)**:
  - *Trigger*: Caller specifies a custom output path.
  - *Observation*: Covered by all existing tests.

### Path B: Audio Inputs Compilation
- **Branch B1 (BGM Path Included)**:
  - *Trigger*: `bgm_path` is not empty or `None`.
  - *Code*: Appends BGM path to `inputs` list, configures BGM volume adjustment (`volume=0.3`), and attaches the `sidechaincompress` ducking filter chain.

- **Branch B2 (SFX List Included)**:
  - *Trigger*: `sfx_list` contains one or more dictionaries representing SFX inputs.
  - *Code*: Loops through list, retrieves volume and start offset with default values, and constructs `adelay` and `volume` filter components.
  - *Untested edge cases*: The default fallback logic (`vol = sfx.get("volume", 0.5)` and `delay = int(sfx.get("start", 0) * 1000)`) is never tested with dictionaries missing these keys.

### Path C: Output Directory Setup
- **Branch C1 (Parent Directory Exists / Direct Filename)**:
  - *Code*:
    ```python
    if output_path:
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
    ```
  - *Trigger*: If `output_path` is a direct file path without a parent directory (e.g. `"output.mp3"`), `parent_dir` is `""`, and the nested `if parent_dir:` evaluations skip `os.makedirs`. This code path is currently untested.

### Path D: subprocess Execution Results
- **Branch D1 (Success: returncode == 0)**:
  - *Trigger*: FFmpeg exits cleanly.

- **Branch D2 (Failure: returncode != 0)**:
  - *Trigger*: FFmpeg exits with error code, raising `RuntimeError`.
  - *Observation*: Currently tested implicitly via a missing audio file that causes actual `ffmpeg` to fail. For fast offline testing, this should be tested using a mocked `subprocess.run` return structure.

### Path E: Module Entry Point Guard
- **Branch E1 (`__name__ == "__main__"`)** *(Missed Line 93)*:
  ```python
  if __name__ == "__main__":
      print("Testing Cinematic Audio Mixer...")
  ```
  - *Trigger*: Running `python3 modules/audio_mixer.py` directly.
  - *Observation*: This script block is missed because tests import `mix_cinematic_audio` as a library function.

---

## 4. Proposed Test Design for 100% Coverage

To achieve full line coverage while prioritizing fast offline execution, we propose the following test cases to be integrated into `tests/test_tier1_coverage.py` or a dedicated test file.

### Test Case 1: Default Output Path Generation (Covers Lines 24–25)
- **Objective**: Execute the `output_path is None` branch, verify directory creation, and assert the output file is named correctly.
- **Input**: `voice_path="voice.mp3"`, `output_path=None`.
- **Mock setup**: Intercept `subprocess.run` to create a dummy file at the generated output path and return a success `CompletedProcess`. Patch `TEMP_DIR` to point to a temporary folder (`tmp_path`).
- **Assertion**:
  - Returned path starts with the patched `TEMP_DIR`.
  - Returned path ends with `.mp3`.
  - Output file is successfully created.

### Test Case 2: SFX Parameter Defaults (Covers Lines 59–60 defaults)
- **Objective**: Verify that optional parameters `volume` and `start` fallback to `0.5` and `0` respectively when omitted from SFX dictionaries.
- **Input**: `sfx_list=[{"path": "sfx.mp3"}]` (lacking `volume` and `start` keys).
- **Mock setup**: Mock `subprocess.run` and capture the constructed command list.
- **Assertion**:
  - The generated FFmpeg filter complex string contains `adelay=0|0` and `volume=0.5`.

### Test Case 3: Output Path Without Parent Directory (Covers Line 80–82 inner branch)
- **Objective**: Execute the case where `output_path` does not contain a directory component, ensuring no `os.makedirs` is invoked on an empty path.
- **Input**: `output_path="test_direct_mix.mp3"`.
- **Mock setup**: Mock `subprocess.run` to write a file to `"test_direct_mix.mp3"`.
- **Assertion**:
  - The function returns `"test_direct_mix.mp3"`.
  - File exists and is cleaned up post-test.

### Test Case 4: Pure Offline Subprocess Error Handling (Covers Lines 85–87)
- **Objective**: Validate the `RuntimeError` raising logic on non-zero exit codes using mock execution.
- **Input**: Standard voice path input.
- **Mock setup**: Stub `subprocess.run` to return a `CompletedProcess` with `returncode=1` and `stderr=b"FFmpeg error: Invalid filter configuration"`.
- **Assertion**:
  - `pytest.raises(RuntimeError)` matches the stderr output message.

### Test Case 5: Main Script Entry Block Execution (Covers Line 93)
- **Objective**: Verify the main block prints the correct message when run as the primary script.
- **Mock setup**: Use `runpy.run_path` to execute the file under `__name__ = "__main__"`. Patch `sys.stdout` to capture the print output.
- **Assertion**:
  - Consumed output contains the string `"Testing Cinematic Audio Mixer..."`.

---

## 5. Mock Setup and Implementation Guide

To implement these tests without executing actual FFmpeg binaries (ensuring extremely fast and isolated test execution), the following mock wrapper is recommended:

```python
import os
import runpy
import time
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from modules.audio_mixer import mix_cinematic_audio

# Test Case 1: Cover default output path generation (Lines 24-25)
@patch("subprocess.run")
def test_mix_audio_default_output_generation(mock_run, tmp_path):
    vo_path = os.path.join(tmp_path, "voice.mp3")
    with open(vo_path, "w") as f:
        f.write("mock voice")
        
    def side_effect_success(cmd, *args, **kwargs):
        # The output path is the final argument of the command
        out = cmd[-1]
        with open(out, "w") as f:
            f.write("mock output mixed audio")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
        
    mock_run.side_effect = side_effect_success
    
    # Patch TEMP_DIR inside modules.audio_mixer to target our temp path
    with patch("modules.audio_mixer.TEMP_DIR", str(tmp_path)):
        res = mix_cinematic_audio(vo_path, output_path=None)
        assert res.startswith(str(tmp_path))
        assert res.endswith(".mp3")
        assert os.path.exists(res)

# Test Case 2: Cover default SFX volumes and start offsets (Lines 59-60)
@patch("subprocess.run")
def test_mix_audio_sfx_defaults(mock_run, tmp_path):
    vo_path = os.path.join(tmp_path, "voice.mp3")
    sfx_path = os.path.join(tmp_path, "sfx.mp3")
    out_path = os.path.join(tmp_path, "out.mp3")
    
    # SFX dictionary only contains path
    sfx_list = [{"path": sfx_path}]
    
    captured_cmd = []
    def side_effect(cmd, *args, **kwargs):
        nonlocal captured_cmd
        captured_cmd = cmd
        with open(out_path, "w") as f:
            f.write("mock")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
        
    mock_run.side_effect = side_effect
    
    mix_cinematic_audio(vo_path, sfx_list=sfx_list, output_path=out_path)
    
    # Parse filter complex argument to assert default volume and delay are set
    filter_complex = captured_cmd[captured_cmd.index("-filter_complex") + 1]
    assert "adelay=0|0" in filter_complex
    assert "volume=0.5" in filter_complex

# Test Case 3: Cover parent directory check (Lines 80-82 branch bypass)
@patch("subprocess.run")
def test_mix_audio_no_parent_dir(mock_run, tmp_path):
    vo_path = os.path.join(tmp_path, "voice.mp3")
    out_file = "direct_filename.mp3"
    
    if os.path.exists(out_file):
        os.remove(out_file)
        
    def side_effect(cmd, *args, **kwargs):
        with open(out_file, "w") as f:
            f.write("mock")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
        
    mock_run.side_effect = side_effect
    
    try:
        res = mix_cinematic_audio(vo_path, output_path=out_file)
        assert res == out_file
        assert os.path.exists(out_file)
    finally:
        if os.path.exists(out_file):
            os.remove(out_file)

# Test Case 4: Cover FFmpeg subprocess failure (Lines 85-87)
@patch("subprocess.run")
def test_mix_audio_ffmpeg_subprocess_failure(mock_run, tmp_path):
    vo_path = os.path.join(tmp_path, "voice.mp3")
    out_path = os.path.join(tmp_path, "out.mp3")
    
    mock_run.return_value = subprocess.CompletedProcess(
        cmd=["ffmpeg"],
        returncode=1,
        stdout=b"",
        stderr=b"FFmpeg error: Invalid input format"
    )
    
    with pytest.raises(RuntimeError) as exc_info:
        mix_cinematic_audio(vo_path, output_path=out_path)
        
    assert "FFmpeg audio mixing failed: FFmpeg error: Invalid input format" in str(exc_info.value)

# Test Case 5: Cover main module entry point (Line 93)
def test_audio_mixer_main_block():
    with patch("builtins.print") as mock_print:
        runpy.run_path("modules/audio_mixer.py", run_name="__main__")
        mock_print.assert_any_call("Testing Cinematic Audio Mixer...")
```

---

## 6. Verification Method and Execution

To verify the test execution and code coverage of `modules/audio_mixer.py` after adding these test cases:

1. **Test Execution**:
   Run the pytest suite to ensure that all new unit tests pass successfully:
   ```bash
   PYTHONPATH=. /home/junglee01/venv/bin/pytest tests/ -v
   ```

2. **Coverage Verification**:
   Execute the test suite under the coverage runner to confirm that 100% line coverage is achieved:
   ```bash
   PYTHONPATH=. /home/junglee01/venv/bin/coverage run -m pytest tests/
   /home/junglee01/venv/bin/coverage report -m --include="modules/audio_mixer.py"
   ```
   **Expected Coverage Output**:
   ```text
   Name                     Stmts   Miss  Cover   Missing
   ------------------------------------------------------
   modules/audio_mixer.py      54      0   100%
   ------------------------------------------------------
   TOTAL                       54      0   100%
   ```
