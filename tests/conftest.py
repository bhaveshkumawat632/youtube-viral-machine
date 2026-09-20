import sys
import os
import time
import io
import json
import urllib.request
import subprocess
import requests
import pytest
from unittest.mock import MagicMock

# ---------------------------------------------------------
# 0. COLLECTION-TIME ISOLATION (runs at conftest import,
#    i.e. BEFORE pytest imports test modules, which in turn
#    import vidrush_pipeline with its makedirs side effects)
# ---------------------------------------------------------
import tempfile as _tempfile
import shutil as _shutil
import atexit as _atexit

_INCOMING_RUNTIME_DIR = os.environ.get("VIRUSH_RUNTIME_DIR")

# Always allocate a fresh directory owned by this test session. A
# caller-supplied VIRUSH_RUNTIME_DIR is NEVER adopted as a cleanup target:
# it is preserved and restored at session end, so caller-owned data cannot
# be deleted by test teardown.
_SESSION_RUNTIME_DIR = _tempfile.mkdtemp(prefix="yt-vm-session-")
os.environ["VIRUSH_RUNTIME_DIR"] = _SESSION_RUNTIME_DIR
_SESSION_CLEANED = False


def _cleanup_session_runtime_dir():
    global _SESSION_CLEANED
    if _SESSION_CLEANED:
        return
    _SESSION_CLEANED = True
    # Restricted to the exact directory created above — never anything else.
    try:
        if os.path.isdir(_SESSION_RUNTIME_DIR):
            _shutil.rmtree(_SESSION_RUNTIME_DIR, ignore_errors=True)
    except Exception:
        pass
    finally:
        # Restore the caller's environment.
        if _INCOMING_RUNTIME_DIR is None:
            os.environ.pop("VIRUSH_RUNTIME_DIR", None)
        else:
            os.environ["VIRUSH_RUNTIME_DIR"] = _INCOMING_RUNTIME_DIR


_atexit.register(_cleanup_session_runtime_dir)


def pytest_sessionfinish(session, exitstatus):
    _cleanup_session_runtime_dir()

original_requests_get = requests.get
original_requests_post = requests.post

# ---------------------------------------------------------
# 1. HELPER FUNCTIONS TO CREATE VALID MOCK MEDIA
# ---------------------------------------------------------
original_subprocess_run = subprocess.run

def create_mock_image(path):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    from PIL import Image
    img = Image.new('RGB', (1080, 1920), color='blue')
    img.save(path, 'JPEG')

def create_mock_video(path, duration=5.0):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    try:
        # Generate a video using FFmpeg with high bitrate to naturally exceed 250KB without raw padding
        original_subprocess_run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=1080x1920:r=30",
            "-t", str(duration), "-c:v", "libx264", "-b:v", "500k", "-pix_fmt", "yuv420p", "-preset", "ultrafast", path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Fallback to dummy file if ffmpeg failed or file is not created
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(b"\0" * 250000)
    else:
        size = os.path.getsize(path)
        if size < 250000:
            with open(path, "ab") as f:
                f.write(b"\0" * (250000 - size))

def create_mock_audio(path, duration=3.0):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    try:
        original_subprocess_run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", str(duration), "-c:a", "libmp3lame", path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(b"\0" * 10000)

# ---------------------------------------------------------
# 2. MOCK MODULES (Gradio, Fal, Edge TTS, Whisper)
# ---------------------------------------------------------
mock_gradio_client = MagicMock()
mock_client_instance = MagicMock()

def mock_predict(*args, **kwargs):
    # Generates a valid temporary mock MP4 file
    from config import TEMP_DIR
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_video = os.path.join(TEMP_DIR, f"mock_gradio_{time.time_ns()}_{args[0][:5] if args else 'video'}.mp4")
    create_mock_video(temp_video)
    return (temp_video, temp_video)

mock_client_instance.predict.side_effect = mock_predict
mock_gradio_client.Client.return_value = mock_client_instance
sys.modules["gradio_client"] = mock_gradio_client

# Mock fal_client
mock_fal_client = MagicMock()
def mock_subscribe(model, arguments):
    return {
        "video": {
            "url": "https://videos.pexels.com/mock_video_from_fal.mp4"
        }
    }
mock_fal_client.subscribe.side_effect = mock_subscribe
sys.modules["fal_client"] = mock_fal_client

# Mock edge_tts
mock_edge_tts = MagicMock()
class MockCommunicate:
    def __init__(self, text, voice, rate=None, pitch=None):
        self.text = text
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        
    async def stream(self):
        # Create a temporary silent mp3 file
        from config import TEMP_DIR
        os.makedirs(TEMP_DIR, exist_ok=True)
        temp_audio = os.path.join(TEMP_DIR, f"temp_stream_{time.time_ns()}.mp3")
        create_mock_audio(temp_audio, duration=3.0)
        with open(temp_audio, "rb") as f:
            audio_bytes = f.read()
        try:
            os.remove(temp_audio)
        except OSError:
            pass
            
        yield {"type": "audio", "data": audio_bytes}
        
        words = self.text.split()
        time_per_word = 3.0 / len(words) if words else 0.5
        for i, word in enumerate(words):
            yield {
                "type": "WordBoundary",
                "offset": int(i * time_per_word * 10000000),  # in ticks
                "duration": int(time_per_word * 10000000),
                "text": word
            }

class MockSubMaker:
    def __init__(self):
        pass
    def feed(self, chunk):
        pass
    def create_sub(self, timing, text):
        pass
    def generate_subs(self):
        return "WEBVTT\n\n00:00:00.000 --> 00:00:03.000\nMock subtitles\n"

async def mock_list_voices():
    return [{"Locale": "en-US", "Name": "en-US-ChristopherNeural"}]

mock_edge_tts.Communicate = MockCommunicate
mock_edge_tts.SubMaker = MockSubMaker
mock_edge_tts.list_voices = mock_list_voices
sys.modules["edge_tts"] = mock_edge_tts

# Mock Whisper & faster_whisper
class MockWord:
    def __init__(self, word, start, end):
        self.word = word
        self.start = start
        self.end = end

class MockSegment:
    def __init__(self, words):
        self.words = words

class MockWhisperModel:
    def __init__(self, *args, **kwargs):
        pass
    def transcribe(self, audio_path, word_timestamps=True, language=None, *args, **kwargs):
        words = [
            MockWord("Yeh", 0.0, 0.3),
            MockWord("sunke", 0.3, 0.7),
            MockWord("aapko", 0.7, 1.1),
            MockWord("yakeen", 1.1, 1.5),
            MockWord("nahi", 1.5, 1.8),
            MockWord("hoga", 1.8, 2.2)
        ]
        return [MockSegment(words)], None

mock_faster_whisper = MagicMock()
mock_faster_whisper.WhisperModel = MockWhisperModel
sys.modules["faster_whisper"] = mock_faster_whisper

# Mock standard whisper
mock_whisper_lib = MagicMock()
def mock_load_model(name, *args, **kwargs):
    model = MagicMock()
    model.transcribe.return_value = {
        "segments": [
            {
                "words": [
                    {"word": "Yeh", "start": 0.0, "end": 0.3},
                    {"word": "sunke", "start": 0.3, "end": 0.7},
                    {"word": "aapko", "start": 0.7, "end": 1.1},
                    {"word": "yakeen", "start": 1.1, "end": 1.5},
                    {"word": "nahi", "start": 1.5, "end": 1.8},
                    {"word": "hoga", "start": 1.8, "end": 2.2}
                ]
            }
        ]
    }
    return model
mock_whisper_lib.load_model = mock_load_model
sys.modules["whisper"] = mock_whisper_lib

# Mock google api client for upload path
sys.modules["googleapiclient"] = MagicMock()
sys.modules["googleapiclient.http"] = MagicMock()
sys.modules["googleapiclient.discovery"] = MagicMock()

# ---------------------------------------------------------
# 3. MONKEY PATCH SUBPROCESS.RUN, REQUESTS.GET, URLOPEN
# ---------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def sample_color_video():
    """Provide the repository-local media fixture required by integration tests.

    The binary fixture is generated for the test session instead of being
    committed to source control.  Preserve a developer-supplied file if one is
    already present.
    """
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_color.mp4")
    created = not os.path.exists(path)
    if created:
        create_mock_video(path, duration=1.0)
    yield path
    if created:
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def isolate_vidrush_mutable_paths(monkeypatch, tmp_path):
    # Keep alert/log/state/output writes exercised by the suite inside a
    # per-test temporary directory instead of the operator checkout.
    # vidrush_pipeline anchors OUTPUT_DIR/ASSETS_DIR/MANIFEST_FILE/FAILED_DIR/
    # LOG_FILE/ALERT_FILE at its BASE_DIR; redirect all six before first use.
    # (Collection-time makedirs in the module are exist_ok no-ops on the
    # already-present checkout dirs; every destructive file op below is
    # redirected.) Reverted automatically after each test.
    import vidrush_pipeline
    base = tmp_path / "vidrush"
    out_dir = base / "output" / "vidrush"
    assets_dir = base / "assets"
    failed_dir = out_dir / "failed"
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(vidrush_pipeline, "OUTPUT_DIR", str(out_dir))
    monkeypatch.setattr(vidrush_pipeline, "ASSETS_DIR", str(assets_dir))
    monkeypatch.setattr(vidrush_pipeline, "MANIFEST_FILE", str(assets_dir / "manifest.json"))
    monkeypatch.setattr(vidrush_pipeline, "FAILED_DIR", str(failed_dir))
    monkeypatch.setattr(vidrush_pipeline, "LOG_FILE", str(base / "daily_log.txt"))
    monkeypatch.setattr(vidrush_pipeline, "ALERT_FILE", str(base / "ALERT.txt"))
    # Compliance seen-db is checkout-anchored too; keep it per-test as well.
    try:
        from modules import compliance as _compliance
        monkeypatch.setattr(
            _compliance, "SEEN_DB", str(base / "_compliance_seen.json")
        )
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def patch_external_calls(monkeypatch, tmp_path):
    # Keep queue lifecycle tests and dry-run pipeline tests isolated from the
    # operator's real persisted queue state.
    from modules import state_manager
    monkeypatch.setattr(state_manager, "STATE_FILE", str(tmp_path / "video_queue_state.json"))

    # Patch subprocess.run
    def mock_subprocess_run(cmd, *args, **kwargs):
        is_download = False
        out_path = None
        
        if isinstance(cmd, list):
            # Check if downloading via wget or curl
            if "wget" in cmd:
                is_download = True
                if "-O" in cmd:
                    idx = cmd.index("-O")
                    out_path = cmd[idx+1]
            elif "curl" in cmd:
                is_download = True
                if "-o" in cmd:
                    idx = cmd.index("-o")
                    out_path = cmd[idx+1]
                    
        if is_download and out_path:
            # Generate mock video or image
            if out_path.endswith(".jpg") or out_path.endswith(".jpeg") or out_path.endswith(".png"):
                create_mock_image(out_path)
            else:
                create_mock_video(out_path)
            return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
            
        return original_subprocess_run(cmd, *args, **kwargs)
        
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    # Patch requests.get
    def mock_requests_get(url, *args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code, content=b"", headers=None):
                self.json_data = json_data
                self.status_code = status_code
                self.text = json.dumps(json_data)
                self.content = content
                self.headers = headers or {}
            
            def json(self):
                return self.json_data
                
            def iter_content(self, chunk_size=1):
                if self.content:
                    for i in range(0, len(self.content), chunk_size):
                        yield self.content[i:i+chunk_size]
                    return
                # We need to return valid video bytes if downloaded
                import tempfile
                temp_video = tempfile.mktemp(suffix=".mp4")
                create_mock_video(temp_video)
                with open(temp_video, "rb") as f:
                    data = f.read()
                try:
                    os.remove(temp_video)
                except OSError:
                    pass
                # Yield in chunks
                for i in range(0, len(data), chunk_size):
                    yield data[i:i+chunk_size]
                    
        if "api.pexels.com/videos/search" in url or "api.pexels.com/videos" in url:
            mock_data = {
                "videos": [
                    {
                        "id": 12345,
                        "duration": 5,
                        "video_files": [
                            {
                                "width": 1080,
                                "height": 1920,
                                "link": "https://videos.pexels.com/mock_video.mp4"
                            }
                        ]
                    }
                ]
            }
            return MockResponse(mock_data, 200)

        if "image.pollinations.ai/prompt/" in url:
            from PIL import Image
            image_bytes = io.BytesIO()
            Image.new("RGB", (1080, 1920), color="blue").save(image_bytes, "JPEG")
            return MockResponse(
                {}, 200, image_bytes.getvalue(), {"content-type": "image/jpeg"}
            )
            
        if "videos.pexels.com/mock_video.mp4" in url or url.endswith(".mp4"):
            import tempfile
            temp_video = tempfile.mktemp(suffix=".mp4")
            create_mock_video(temp_video)
            with open(temp_video, "rb") as f:
                data = f.read()
            try:
                os.remove(temp_video)
            except OSError:
                pass
            return MockResponse({}, 200) # iter_content is the primary consumer

        return original_requests_get(url, *args, **kwargs)
        
    monkeypatch.setattr(requests, "get", mock_requests_get)

    # Patch requests.post
    def mock_requests_post(url, *args, **kwargs):
        if "api.elevenlabs.io" in url:
            class MockResponse:
                def __init__(self, content, status_code):
                    self.content = content
                    self.status_code = status_code
                def json(self):
                    return {}
            # Generate valid silent MP3 audio bytes (use create_mock_audio output)
            import tempfile
            temp_audio = tempfile.mktemp(suffix=".mp3")
            create_mock_audio(temp_audio, duration=3.0)
            with open(temp_audio, "rb") as f:
                audio_bytes = f.read()
            try:
                os.remove(temp_audio)
            except OSError:
                pass
            return MockResponse(audio_bytes, 200)
        return original_requests_post(url, *args, **kwargs)
        
    monkeypatch.setattr(requests, "post", mock_requests_post)

    # Patch urllib.request.urlopen
    original_urlopen = urllib.request.urlopen
    def mock_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else (req if isinstance(req, str) else "")
        if "coverr.co" in url:
            html_content = '<html><body><a href="https://cdn.coverr.co/videos/mock_coverr_video_1080p.mp4">Mock Coverr</a></body></html>'
            return io.BytesIO(html_content.encode('utf-8'))
        elif "api.pexels.com" in url:
            # Pexels image request
            mock_data = {
                "photos": [
                    {
                        "src": {
                            "large2x": "https://images.pexels.com/mock_image.jpg"
                        }
                    }
                ]
            }
            return io.BytesIO(json.dumps(mock_data).encode('utf-8'))
        return original_urlopen(req, *args, **kwargs)
        
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
