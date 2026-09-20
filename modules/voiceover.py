"""
YouTube Viral Machine - Voiceover Engine
Uses Edge TTS for free, high-quality AI voiceover
"""
import asyncio
import os
import sys
import json
import time
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VOICES, DEFAULT_VOICE, SPEECH_RATE, TEMP_DIR

try:
    import edge_tts
except ImportError:
    print("❌ edge-tts not installed. Run: pip install edge-tts")
    sys.exit(1)


def _write_boundaries(output_path, boundaries):
    boundaries_path = output_path.replace(".mp3", "_words.json")
    with open(boundaries_path, "w", encoding="utf-8") as f:
        json.dump(boundaries, f, ensure_ascii=False, indent=2)
    return boundaries_path


def _offline_espeak_fallback(text, output_path):
    """Generate bounded, fully local Hindi speech when network TTS is down."""
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak:
        raise RuntimeError("No offline espeak engine is installed")

    wav_path = os.path.splitext(output_path)[0] + "_offline.wav"
    subprocess.run(
        [espeak, "-v", "hi", "-s", "155", "-w", wav_path, text],
        check=True,
        timeout=90,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", output_path],
        check=True,
        timeout=90,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        os.remove(wav_path)
    except OSError:
        pass

    duration = get_audio_duration(output_path)
    words = text.split()
    word_duration = duration / max(1, len(words))
    boundaries = [
        {
            "text": word,
            "offset": int(index * word_duration * 10_000_000),
            "duration": int(word_duration * 10_000_000),
            "start_ms": index * word_duration * 1000,
            "end_ms": (index + 1) * word_duration * 1000,
        }
        for index, word in enumerate(words)
    ]
    boundaries_path = _write_boundaries(output_path, boundaries)
    print("✅ Offline Hindi espeak fallback generated voiceover.")
    return output_path, boundaries_path, boundaries


async def _edge_tts_voiceover(text, output_path, voice_key=None, rate=None):
    voice_name = VOICES.get(voice_key or DEFAULT_VOICE, VOICES[DEFAULT_VOICE])
    communicate = edge_tts.Communicate(text, voice_name, rate=rate or SPEECH_RATE)
    word_boundaries = []
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            word_boundaries.append({
                "text": chunk["text"],
                "offset": chunk["offset"],
                "duration": chunk["duration"],
                "start_ms": chunk["offset"] / 10000,
                "end_ms": (chunk["offset"] + chunk["duration"]) / 10000,
            })

    if not audio_chunks:
        raise RuntimeError("Edge-TTS returned no audio")
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)
    return output_path, _write_boundaries(output_path, word_boundaries), word_boundaries


async def _generate_voiceover(text, output_path, voice_key=None, rate=None):
    """Generate bounded TTS; default directly to Edge, then local espeak."""
    if os.environ.get("VIDRUSH_USE_UNIFIED_TTS", "").lower() in {"1", "true", "yes"}:
        try:
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from jarvis_universal.core.api_router import UnifiedRouter
            voice_preference = "female" if voice_key and "female" in voice_key.lower() else "male"
            print("🎙️ Generating Voiceover via JARVIS UnifiedRouter...")
            return UnifiedRouter().tts(text, output_path, voice_preference)
        except Exception as exc:
            print(f"⚠️ UnifiedRouter TTS failed: {exc}. Falling back to bounded Edge-TTS...")

    timeout_seconds = float(os.environ.get("VIDRUSH_EDGE_TTS_TIMEOUT", "60"))
    try:
        print(f"🎙️ Generating voiceover via Edge-TTS ({timeout_seconds:.0f}s timeout)...")
        return await asyncio.wait_for(
            _edge_tts_voiceover(text, output_path, voice_key, rate),
            timeout=timeout_seconds,
        )
    except Exception as exc:
        print(f"⚠️ Edge-TTS failed or timed out: {exc}. Using offline Hindi voice...")
        return _offline_espeak_fallback(text, output_path)


def generate_voiceover(text, output_path=None, voice_key=None, rate=None):
    """
    Generate voiceover from text using Edge TTS.

    Args:
        text: The text to convert to speech
        output_path: Path for output MP3 file (auto-generated if None)
        voice_key: Key from VOICES dict (e.g., 'hindi_male', 'english_female')
        rate: Speech rate (e.g., '+10%', '-20%')

    Returns:
        tuple: (audio_path, word_boundaries_path, word_boundaries_list)
    """
    if output_path is None:
        os.makedirs(TEMP_DIR, exist_ok=True)
        output_path = os.path.join(TEMP_DIR, f"voiceover_{int(time.time())}.mp3")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    import nest_asyncio
    nest_asyncio.apply()
    result = asyncio.run(
        _generate_voiceover(text, output_path, voice_key, rate)
    )

    return result


def get_audio_duration(audio_path):
    """Get duration of an audio file using ffprobe"""
    import subprocess
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def list_available_voices():
    """List all available Edge TTS voices"""
    voices_info = []
    for key, name in VOICES.items():
        voices_info.append(f"  {key:20s} → {name}")
    return "\n".join(voices_info)


async def _list_all_voices():
    """List ALL available Edge TTS voices"""
    voices = await edge_tts.list_voices()
    return voices


def list_all_voices(language_filter=None):
    """List all Edge TTS voices, optionally filtered by language"""
    voices = asyncio.run(_list_all_voices())
    if language_filter:
        voices = [v for v in voices if language_filter.lower() in v["Locale"].lower()]
    return voices


if __name__ == "__main__":
    print("🎤 YouTube Viral Machine - Voiceover Engine")
    print("=" * 50)
    print("\nAvailable voices:")
    print(list_available_voices())
    print("\n🔊 Generating test voiceover...")

    test_text = "Yeh sunke aapko yakeen nahi hoga. Duniya ka sabse powerful computer aapke dimaag mein hai."
    audio_path, words_path, words = generate_voiceover(
        test_text,
        os.path.join(TEMP_DIR, "test_voice.mp3"),
        "hindi_male"
    )
    duration = get_audio_duration(audio_path)
    print(f"✅ Audio generated: {audio_path}")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📝 Word timestamps: {words_path}")
    print(f"📊 Total words: {len(words)}")
