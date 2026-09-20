"""Daily full-auto pipeline: generate a fresh real-world Short and upload it to YouTube.

Usage:
    python3 daily_auto_short.py            # random topic
    python3 daily_auto_short.py space      # specific topic
    YVM_PRIVACY=private python3 daily_auto_short.py   # override privacy (default: public)

Env:
    VIDRUSH_AUTO_UPLOAD_APPROVED=1 is set automatically by this driver.
"""
import os
import sys
import glob
import random
import subprocess
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "daily_auto.log")

TOPIC_META = {
    "ai":        ("AI & The Future of Human Jobs", "technology,ai,future,jobs,shorts"),
    "space":     ("Mars Colonization & Space Future", "space,mars,colonization,science,shorts"),
    "ocean":     ("The Mariana Trench & Deep Ocean", "ocean,mariana trench,mystery,shorts"),
    "dino":      ("Dinosaurs & The Extinction Asteroid", "dinosaurs,extinction,history,shorts"),
    "history":   ("Ancient Pyramids & Lost Civilizations", "history,pyramids,egypt,shorts"),
    "volcano":   ("Deadliest Volcanoes on Earth", "volcano,nature,science,shorts"),
    "blackhole": ("Black Holes & The End of the Universe", "black hole,space,universe,shorts"),
    "samurai":   ("The Last Samurai Warriors", "samurai,japan,history,shorts"),
    "everest":   ("Mount Everest & The Death Zone", "everest,mountain,survival,shorts"),
    "amazon":    ("The Amazon Rainforest - Lungs of the Earth", "amazon,rainforest,nature,shorts"),
    "alien":     ("Aliens & UFO Sightings Explained", "aliens,ufo,mystery,shorts"),
    "robot":     ("Robots & The Future of Humanity", "robots,technology,future,shorts"),
    "hacker":    ("Hackers & Cyber Warfare", "hacker,cybersecurity,technology,shorts"),
    "viking":    ("Viking Warriors & Their World", "vikings,history,warriors,shorts"),
    "tornado":   ("The Most Extreme Tornadoes Ever", "tornado,weather,extreme,shorts"),
    "shark":     ("Great White Sharks Up Close", "sharks,ocean,predators,shorts"),
    "ninja":     ("The Secret World of Ninjas", "ninja,japan,history,shorts"),
    "tsunami":   ("The Deadliest Tsunamis in History", "tsunami,ocean,disaster,shorts"),
    "spider":    ("The World's Deadliest Spiders", "spiders,nature,deadly,shorts"),
    "castle":    ("Medieval Castles & Knights", "castle,medieval,knights,history,shorts"),
    "meteor":    ("Meteors & Asteroid Impacts", "meteor,asteroid,space,shorts"),
    "desert":    ("The Sahara Desert & Ancient Secrets", "sahara,desert,nature,shorts"),
    "quantum":   ("Quantum Physics Explained Simply", "quantum physics,science,shorts"),
    "glacier":   ("Antarctic Glaciers & Climate", "glacier,antarctica,climate,shorts"),
    "mars":      ("Life on Mars in 2050", "mars,space,colony,shorts"),
    "isro":      ("ISRO: India's Space Miracle", "isro,chandrayaan,india,space,shorts"),
    "himalaya":  ("The Himalayas: Roof of the World", "himalaya,mountains,india,shorts"),
    "mahabharat": ("Mahabharat: The Greatest Epic", "mahabharat,history,india,shorts"),
    "ganga":     ("The Eternal Ganga & Varanasi", "ganga,varanasi,india,shorts"),
    "taj":       ("Taj Mahal: Secrets of Love", "taj mahal,india,history,shorts"),
    "tiger":     ("Bengal Tiger: King of the Jungle", "tiger,wildlife,india,shorts"),
    "kailash":   ("Mount Kailash: The Untouched Peak", "kailash,mystery,himalaya,shorts"),
    "vedic":     ("Ancient Indian Science & Inventions", "vedic,ancient india,science,shorts"),
    "monsoon":   ("The Great Indian Monsoon", "monsoon,india,nature,shorts"),
    "holi":      ("Holi: The Festival of Colors", "holi,india,festival,shorts"),
}


def _load_env_key(name: str) -> str:
    """Read a key from process env or the gitignored .env file."""
    value = os.environ.get(name, "")
    if value:
        return value.strip()
    env_file = os.path.join(BASE_DIR, ".env")
    try:
        with open(env_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def log(msg):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def main():
    topic_arg = sys.argv[1] if len(sys.argv) > 1 else None
    force = os.environ.get("FORCE", "") == "1"

    # Dedup guard (auto mode only): max one upload per day. Both the daily cron
    # and the @reboot catch-up call this script, so skip if today's video
    # already went out. Manual topic runs and FORCE=1 always execute.
    if not topic_arg and not force:
        state_file = os.path.join(BASE_DIR, ".daily_auto_state")
        today = datetime.date.today().isoformat()
        try:
            if os.path.exists(state_file) and open(state_file, encoding="utf-8").read().strip() == today:
                log(f"Already uploaded today ({today}) - skipping. Pass a topic or FORCE=1 to override.")
                return
        except OSError:
            pass

    topic_key = topic_arg or random.choice(list(TOPIC_META))
    if topic_key not in TOPIC_META:
        log(f"Unknown topic '{topic_key}', picking random instead")
        topic_key = random.choice(list(TOPIC_META))

    privacy = os.environ.get("YVM_PRIVACY", "public").strip().lower()
    log(f"=== Daily run: topic='{topic_key}' privacy={privacy} ===")

    # Smart voice routing (quota-safe): the ElevenLabs key is TTS-scoped, so we
    # probe with a tiny 2-letter TTS ping (~15 credits) on the same endpoint the
    # render uses. HTTP 200 = quota available -> premium voice allowed. Any
    # quota/auth error -> FREE_ONLY locked, edge-tts handles the voice.
    try:
        import requests as _requests
        _probe_key = _load_env_key("ELEVENLABS_API_KEY")
        probe = _requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/CwhRBWXzGAHq8TQ4Fs17",
            headers={"xi-api-key": _probe_key, "Content-Type": "application/json"},
            json={"text": "Hi.", "model_id": "eleven_multilingual_v2"},
            timeout=30,
        )
        if probe.status_code == 200:
            log("ElevenLabs probe OK (200) - premium voice available this run")
        else:
            detail = ""
            try:
                detail = probe.json().get("detail", {}).get("status", "")
            except Exception:
                pass
            log(f"ElevenLabs probe HTTP {probe.status_code} ({detail}) - FREE_ONLY locked (edge-tts voice)")
            os.environ["YVM_FREE_ONLY"] = "1"
    except Exception as exc:
        log(f"ElevenLabs probe failed ({exc}) - FREE_ONLY locked for this run")
        os.environ["YVM_FREE_ONLY"] = "1"

    # 1. Render (master script handles stock clips, TTS fallback, subtitles, looping)
    result = subprocess.run(
        ["python3", os.path.join(BASE_DIR, "build_master_real_world_short.py"), topic_key],
        cwd=BASE_DIR, capture_output=True, text=True, timeout=1200,
    )
    tail = "\n".join((result.stdout or "").splitlines()[-5:])
    log(f"render exit={result.returncode} tail:\n{tail}")
    if result.returncode != 0:
        log("Render FAILED - skipping upload this run")
        sys.exit(1)

    video_path = os.path.join(BASE_DIR, "output", f"REAL_WORLD_{topic_key.upper()}_MASTER.mp4")
    if not os.path.exists(video_path):
        candidates = sorted(glob.glob(os.path.join(BASE_DIR, "output", "*_MASTER.mp4")), key=os.path.getmtime)
        if not candidates:
            log("No output video found - aborting")
            sys.exit(1)
        video_path = candidates[-1]
    log(f"Video ready: {video_path} ({os.path.getsize(video_path)//1048576} MB)")

    # 2. Metadata
    title_base, tags = TOPIC_META[topic_key]
    today = datetime.date.today().strftime("%b %d")
    metadata = {
        "title": f"{title_base} 🌍 #{today.replace(' ', '')} #shorts #facts",
        "description": (
            f"{title_base} - a real-world documentary short.\n\n"
            "💰 Learn exact systems to automate your income: "
            "https://bhaveshkumawat632.github.io/money-making-blog/\n\n"
            f"#{' #'.join(tags.split(','))}"
        ),
        "tags": tags.split(","),
        "category_id": "27",  # Education
        "privacyStatus": privacy,
    }

    # 3. Upload (token.pickle auto-refreshes; first run needs one browser consent)
    os.environ["VIDRUSH_AUTO_UPLOAD_APPROVED"] = "1"
    from modules.youtube_uploader import upload_video
    video_id = upload_video(video_path, metadata)
    if video_id:
        try:
            with open(os.path.join(BASE_DIR, ".daily_auto_state"), "w", encoding="utf-8") as fh:
                fh.write(datetime.date.today().isoformat() + "\n")
        except OSError:
            pass
        log(f"✅ UPLOADED successfully ({privacy}) - video ID/link printed above")
    else:
        log("❌ Upload returned None - check YouTube auth (token.pickle)")
        sys.exit(1)


if __name__ == "__main__":
    main()
