# API Mocking & Visual Fallback Strategy Design — YouTube Viral Machine

This report maps the external API integrations in the video generation and visual sourcing modules and defines a comprehensive mocking and verification strategy. These designs allow running the automated verification suite inside a network-isolated environment (such as `CODE_ONLY` mode) while ensuring that fallback ladders and error handling are robustly tested.

---

## 1. External API Endpoint & Parameters Mapping

The YouTube Viral Machine uses multiple cloud and stock API integrations to fetch and compile video frames. Below is the detailed mapping of all endpoints, clients, request parameters, and response formats.

### A. Private Colab GPU (Gradio Client)
* **Library/Client**: `gradio_client.Client`
* **Initialization**: `Client(PRIVATE_API_URL)`
* **Method & API Endpoint**: `predict(...)` targeting `/predict`
* **Request Arguments**:
  * `prompt`: `str` — Text description appended with cinematic prompts.
  * `num_frames`: `int` — Hardcoded to `16`.
  * `num_inference_steps`: `int` — Hardcoded to `20`.
  * `api_name`: `str` — `"/predict"`
* **Response Return Type**:
  * Success: Either a `str` file path (e.g. `"/tmp/gradio/.../video.mp4"`) or a `tuple` with a single string path at index 0 (e.g. `("/tmp/gradio/.../video.mp4",)`).
* **Validation & Extraction**:
  * Checked using `isinstance(result, tuple)` or `isinstance(result, str)`.
  * Checks if the extracted path exists and its size is larger than 200KB (`os.path.getsize(path) > 200000`).

### B. Hugging Face Spaces (Gradio Client)
* **Library/Client**: `gradio_client.Client`
* **Initialization**: `Client(space_name)`

#### 1. Lightricks LTX Video Space (`Lightricks/ltx-video-distilled`)
* **Method & API Endpoint**: `predict(...)` targeting `/text_to_video`
* **Request Arguments**:
  * `prompt`: `str` — Optimized prompt.
  * `negative_prompt`: `str` — `"worst quality, inconsistent motion, blurry, jittery, distorted, text, watermark"`
  * `height_ui`: `int` — `384`
  * `width_ui`: `int` — `512`
  * `mode`: `str` — `"text-to-video"`
  * `duration_ui`: `int` — `2`
  * `ui_frames_to_use`: `int` — `9`
  * `seed_ui`: `int` — `0`
  * `randomize_seed`: `bool` — `True`
  * `ui_guidance_scale`: `float` — `1.5`
  * `improve_texture_flag`: `bool` — `True`
  * `api_name`: `str` — `"/text_to_video"`
* **Response Return Type**:
  * Success: A tuple where index 0 is a dict: `({"video": "/path/to/video.mp4"},)`
  * Success Fallbacks: Tuple of string path `("/path/to/video.mp4",)`, plain string `"/path/to/video.mp4"`, or a plain dict `{"video": "/path/to/video.mp4"}`.

#### 2. THUDM CogVideoX Space (`THUDM/CogVideoX-5B-Space`)
* **Method & API Endpoint**: `predict(...)` targeting `/generate`
* **Request Arguments**:
  * `prompt`: `str` — Optimized prompt.
  * `image_input`: `None`
  * `video_input`: `None`
  * `video_strength`: `float` — `0.8`
  * `seed_value`: `int` — `-1`
  * `scale_status`: `bool` — `True`
  * `rife_status`: `bool` — `False`
  * `api_name`: `str` — `"/generate"`
* **Response Return Type**:
  * Success: A tuple of 4 elements: `(video_dict, download_path, gif_path, seed)` where `download_path` is the primary path string, or `video_dict` contains `"video": "/path/to/video.mp4"`.

### C. FAL.AI API
* **Library/Client**: `fal_client` (dynamically imported inside `_generate_via_fal`)
* **Authentication**: Read from environment variable `FAL_KEY`
* **API Endpoints (Models)**:
  * `fal-ai/ltx-video/v0.9.7`
  * `fal-ai/cogvideox-5b`
* **Request Arguments**:
  * `model_name`: `str` — One of the above endpoints.
  * `arguments`: `dict` containing:
    * `prompt`: `str`
    * `num_frames`: `int` — `49`
    * `aspect_ratio`: `str` — `"9:16"`
* **Response Return Type**:
  * Success: A dict containing `{"video": {"url": "https://fal.media/files/hash.mp4"}}` or `{"video_url": "https://fal.media/files/hash.mp4"}`.
* **Extraction**:
  * The URL is downloaded to the target path using a shell wrapper: `subprocess.run(["wget", "-q", "-O", output_path, video_url], check=True)`.

### D. Pexels API
* **Library/Client**: `requests`
* **Authentication**: Authorization header: `{"Authorization": api_key}` (loaded from `PEXELS_API_KEY`)
* **API Endpoint**: `https://api.pexels.com/videos/search`
* **Request Arguments (GET)**:
  * `query`: `str` — URL-encoded search term.
  * `orientation`: `str` — `"portrait"` or `"landscape"`
  * `per_page`: `int` — `1` or `5`
* **Response Return Type**:
  * Success: JSON payload containing list of matching videos and nested video files:
    ```json
    {
      "videos": [
        {
          "id": 99999,
          "duration": 10,
          "video_files": [
            {
              "id": 1234,
              "quality": "hd",
              "file_type": "video/mp4",
              "width": 1080,
              "height": 1920,
              "link": "https://player.vimeo.com/external/123.hd.mp4"
            }
          ]
        }
      ]
    }
    ```
* **Extraction**:
  * The link is selected by sorting `video_files` by `height` in descending order.
  * The selected URL is downloaded via `requests.get(best_file, stream=True)` and written to disk in chunks of 8192 bytes.

### E. Coverr (Scraped)
* **Library/Client**: `urllib.request`
* **API Endpoint**: `https://coverr.co/s?q={query}`
* **Request Arguments (GET)**:
  * User-Agent: `'Mozilla/5.0'` to avoid scrapers detection.
* **Response Return Type**:
  * Success: Raw HTML string containing matching video link patterns: `https://cdn.coverr.co/videos/[^"]*1080p.mp4`.
* **Extraction**:
  * Evaluated via regex `re.findall` on the HTML.
  * The first matching link (excluding previously used URLs) is selected.
  * Downloaded via `subprocess.run(["wget", "-q", "-O", output_path, video_url], check=True)`.

### F. Pollinations AI (Anime Visual Generation)
* **Library/Client**: `requests`
* **DNS Resolution Patch**: Intercepts connections to `image.pollinations.ai` and resolves them using pre-resolved Cloudflare IPs (`"172.67.173.121"`, `"104.21.30.173"`) to bypass DNS timeouts.
* **API Endpoints**:
  * Primary: `https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&seed={seed}&private=true`
  * Secondary: `https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&seed={seed}`
* **Request Arguments (GET)**:
  * `encoded_prompt`: `str` — URL-encoded sentence prompt.
  * `seed`: `int` — Random seed integer between 1 and 999999.
* **Response Return Type**:
  * Success: Stream of raw JPEG bytes with Header `Content-Type: image/jpeg`.
* **Extraction**:
  * Downloaded via `requests.get(url, stream=True, timeout=40)` and written to output path in chunks of 8192 bytes.

---

## 2. Robust Pytest Mock Fixture Strategy

To isolate the E2E verification tests from live APIs and prevent network requests, we mock the external APIs using `pytest`. The strategy mocks not only success outputs but also failure exceptions (e.g. Quota Exceeded and Cooldowns).

### Key Dependency: The size validator bypass
Since all generators verify that downloaded files exist and exceed a minimum size threshold of **200KB** (i.e. `os.path.getsize(path) > 200000`), our mock fixtures must create valid dummy files containing at least **250KB** of mock data.

Put the following fixtures in `tests/conftest.py`:

```python
import pytest
import os
import tempfile
import shutil
import subprocess
from unittest.mock import MagicMock, patch

@pytest.fixture(scope="session")
def dummy_video_file():
    """Generates a reusable, valid 250KB dummy MP4 file to pass validator size checks."""
    temp_dir = tempfile.mkdtemp()
    filepath = os.path.join(temp_dir, "dummy_video.mp4")
    # Write 250KB of null bytes
    with open(filepath, "wb") as f:
        f.write(b"\x00" * 250000)
    yield filepath
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_gradio_client(dummy_video_file):
    """
    Mocks gradio_client.Client predicting successful video generation.
    Supports api_name parameter variations for Private Colab, LTX, and CogVideoX.
    """
    with patch("gradio_client.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        def predict_side_effect(*args, **kwargs):
            api_name = kwargs.get("api_name")
            if api_name == "/predict":  # Private Colab
                return (dummy_video_file,)
            elif api_name == "/text_to_video":  # LTX space
                return ({"video": dummy_video_file},)
            elif api_name == "/generate":  # CogVideoX space
                return ({"video": dummy_video_file}, dummy_video_file, None, 1234)
            return dummy_video_file
            
        mock_client.predict.side_effect = predict_side_effect
        yield mock_client_class

@pytest.fixture
def mock_fal_client(dummy_video_file):
    """
    Mocks fal_client subscribe returns and patches sys.modules to mock dynamic imports.
    """
    import sys
    mock_fal = MagicMock()
    mock_fal.subscribe.return_value = {
        "video": {"url": "https://fal.media/files/mock_video.mp4"},
        "video_url": "https://fal.media/files/mock_video.mp4"
    }
    sys.modules["fal_client"] = mock_fal
    yield mock_fal
    sys.modules.pop("fal_client", None)

@pytest.fixture
def mock_subprocess_downloader(dummy_video_file):
    """
    Intercepts subprocess.run for 'wget' commands and copies dummy_video_file instead.
    Preserves all other system subprocess commands (e.g. ffmpeg, ffprobe).
    """
    original_run = subprocess.run
    
    def patched_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and cmd[0] == "wget":
            # Command pattern: ["wget", "-q", "-O", output_path, video_url]
            output_path = cmd[3] if "-O" in cmd else cmd[-2]
            shutil.copy(dummy_video_file, output_path)
            res = MagicMock()
            res.returncode = 0
            return res
        return original_run(cmd, *args, **kwargs)
        
    with patch("subprocess.run", side_effect=patched_run) as mock_run:
        yield mock_run

@pytest.fixture
def mock_requests_pexels_and_pollinations(dummy_video_file):
    """
    Mocks requests.get to return fake JSON search results for Pexels,
    stream-writes dummy MP4 bytes for Vimeo/Pexels download URLs,
    and returns JPEG headers and dummy bytes for Pollinations AI prompts.
    """
    with patch("requests.get") as mock_get:
        def get_side_effect(url, *args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            
            if "api.pexels.com" in url:
                resp.json.return_value = {
                    "videos": [
                        {
                            "id": 999,
                            "duration": 8,
                            "video_files": [
                                {
                                    "height": 1920,
                                    "width": 1080,
                                    "link": "https://player.vimeo.com/external/999.mp4"
                                }
                            ]
                        }
                    ]
                }
            elif "player.vimeo.com" in url:
                # Mock iter_content to stream read dummy video bytes
                def iter_content(chunk_size=1024):
                    with open(dummy_video_file, "rb") as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk
                resp.iter_content = iter_content
            elif "image.pollinations.ai" in url:
                resp.headers = {"content-type": "image/jpeg"}
                def iter_content(chunk_size=1024):
                    yield b"\xff\xd8\xff\xe0" + b"\x00" * 200000  # JPEG header + filler bytes
                resp.iter_content = iter_content
            else:
                resp.status_code = 404
                
            return resp
            
        mock_get.side_effect = get_side_effect
        yield mock_get

@pytest.fixture
def mock_urllib_coverr():
    """
    Mocks urllib.request.urlopen to return mock HTML containing static Coverr video URLs.
    """
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = (
            b'<html><body>'
            b'<a href="https://cdn.coverr.co/videos/mock_coverr_1080p.mp4">Video Link</a>'
            b'</body></html>'
        )
        mock_urlopen.return_value = mock_resp
        yield mock_urlopen
```

### Simulating Quotas, Server Errors, and Cooldown Rotation
To test error handling, we can override the fixtures dynamically within specific tests:

```python
# Simulating Hugging Face space ZeroGPU Quota Exceeded exception
def test_hf_space_quota_rotation(mock_gradio_client, dummy_video_file):
    from modules.cloud_video_generator import generate_video_from_prompt_hf, _space_cooldowns
    
    # Reset cooldowns
    _space_cooldowns.clear()
    
    # Configure Client.predict to raise Quota exception for the first space, then succeed
    call_count = 0
    def predict_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("ZeroGPU quota exceeded for this Space")
        return (dummy_video_file,)
        
    mock_gradio_client.return_value.predict.side_effect = predict_side_effect
    
    output = generate_video_from_prompt_hf("Cyberpunk astronaut neon glows")
    
    assert os.path.exists(output)
    # The first space (Lightricks/ltx-video-distilled) should be in cooldown now
    assert "Lightricks/ltx-video-distilled" in _space_cooldowns
```

---

## 3. Fallback Visual Sourcing Verification Strategy

When cloud APIs fail, return empty payloads, or timeout, the pipeline triggers fallbacks in a hierarchical sequence. Testing must guarantee that the fallback visual sourcing ladder functions correctly without crashing.

### The Visual Sourcing Ladder (Cascade Hierarchy)
1. **Tier 1: Cloud Video API (AI Video)** — HuggingFace Spaces (Private Colab $\rightarrow$ LTX $\rightarrow$ CogVideoX) $\rightarrow$ FAL.AI (LTX $\rightarrow$ CogVideoX).
2. **Tier 2: Stock Video APIs** — Coverr.co video search (scraped via URL query) $\rightarrow$ Pexels Video Search (Portrait HD mp4).
3. **Tier 3: Local Video Assets** — Randomly selected and trimmed segments from whitelisted video files under `backgrounds/` (e.g. gameplay or abstract patterns).
4. **Tier 4: Dynamic Gradient Loops** — Clean, animated loops generated programmatically via Pillow (`create_gradient_background`).
5. **Tier 5: Programmatic FFMPEG Solid Blocks** — Solid background color block (`color=c=0xColor`) generated dynamically using FFmpeg's `lavfi` color filter if Pillow drawing fails.

### Fallback Integration Test Cases

We can write test cases that verify the cascade by stubbing and mocking.

#### Test 1: Verify Cloud AI Failure triggers Stock Video Download (Coverr/Pexels)
```python
def test_fallback_cloud_to_stock(mock_gradio_client, mock_fal_client, mock_urllib_coverr, mock_subprocess_downloader):
    from auto_pilot import fetch_dynamic_background_video
    
    # Force cloud clients to fail
    mock_gradio_client.return_value.predict.side_effect = Exception("All spaces down")
    mock_fal_client.subscribe.side_effect = Exception("Fal.ai credit limit hit")
    
    # Mock script data (scenes)
    script_data = {
        "title": "Neon Light",
        "scenes": [{"visual_prompt": "Neon astronaut", "youtube_search_query": "astronaut spaceship"}]
    }
    
    # Run dynamic background fetching
    videos = fetch_dynamic_background_video(script_data, duration=8, timestamp_id=9999)
    
    # Assertions
    assert videos is not None
    assert len(videos) == 1
    # Check that it fell back to Coverr and downloaded the mock URL
    assert "dynamic_bg_9999_0.mp4" in videos[0]
```

#### Test 2: Verify Stock Failures trigger Local/Synthetic Background Gradients
```python
def test_fallback_stock_to_gradients(mock_gradio_client, mock_fal_client):
    from modules.video_maker import create_video_from_audio_and_subtitles
    
    # Force all cloud and stock methods to fail
    # When no background_video is provided, it must create a gradient background
    audio_path = "tests/assets/test_audio.mp3"  # assuming local test audio exists
    subtitle_path = "tests/assets/test_subtitles.ass"
    output_path = "Testing/output/test_fallback_render.mp4"
    
    # Create mock audio/subtitle files if they don't exist
    os.makedirs("tests/assets", exist_ok=True)
    if not os.path.exists(audio_path):
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=440:d=4", audio_path])
    if not os.path.exists(subtitle_path):
        with open(subtitle_path, "w") as f:
            f.write("[Script Info]\nPlayResX: 1080\nPlayResY: 1920\n")
            
    # Run compilation with background_video = None
    res = create_video_from_audio_and_subtitles(
        audio_path=audio_path,
        subtitle_path=subtitle_path,
        output_path=output_path,
        background_video=None,  # Triggers gradient fallback
        gradient_name="cosmic"
    )
    
    # Assertions
    assert res == output_path
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 10000  # verify non-empty file created
```

#### Test 3: Verify Pillow Failure triggers FFMPEG Solid Color Background Fallback
```python
def test_pillow_draw_failure_ffmpeg_fallback(mock_subprocess_downloader):
    from modules.video_maker import create_gradient_background
    
    output_path = "Testing/temp/gradient_fallback.mp4"
    os.makedirs("Testing/temp", exist_ok=True)
    
    # Mock PIL import/Draw exception to trigger FFmpeg solid color fallback
    with patch("PIL.ImageDraw.Draw", side_effect=Exception("Pillow canvas error")):
        res = create_gradient_background(
            output_path=output_path,
            duration=3,
            width=1080,
            height=1920,
            gradient_name="cyberpunk"
        )
        
    assert res == output_path
    assert os.path.exists(output_path)
    # The output file should be successfully created using FFmpeg Solid Color
```
