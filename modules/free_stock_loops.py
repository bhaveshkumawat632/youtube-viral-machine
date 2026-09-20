"""
Free stock loop cache for VidRush.
Downloads and reuses royalty-free vertical stock clips via yt-dlp when available.
Falls back gracefully so Tier 4 synthetic motion still works.
"""
import os
import subprocess
import shutil
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(BASE_DIR)
CACHE_DIR = os.path.join(REPO_DIR, "assets", "stock_loops")
os.makedirs(CACHE_DIR, exist_ok=True)


def _search_query(keyword: str) -> str:
    k = (keyword or "").strip().lower()
    if any(w in k for w in ["money", "cash", "finance", "bank", "market", "stock"]):
        return "vertical stock footage finance money background loop"
    if any(w in k for w in ["tech", "coding", "computer", "office", "startup"]):
        return "vertical stock footage tech office background loop"
    if any(w in k for w in ["car", "drive", "road", "travel", "city"]):
        return "vertical stock footage city drive night background loop"
    if any(w in k for w in ["nature", "mountain", "forest", "ocean", "water"]):
        return "vertical stock footage nature water background loop"
    return "vertical stock footage abstract background loop 4k"


def get_or_download_loop(keyword: str, duration: float, output_path: str) -> str:
    """
    Return a local cached stock loop path trimmed to duration, or None on failure.
    """
    # reuse any cached loop if available
    cached = glob.glob(os.path.join(CACHE_DIR, "*.mp4"))
    if cached:
        try:
            src = cached[0]
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", src,
                    "-t", str(max(3.0, float(duration))),
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "26",
                    "-an", output_path,
                ],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if os.path.exists(output_path) and os.path.getsize(output_path) > 50000:
                return output_path
        except Exception:
            pass

    query = _search_query(keyword)
    cache_raw = os.path.join(CACHE_DIR, f"raw_{int(duration)}_{hash(keyword) % 1000}.mp4")
    try:
        print(f"   [Tier 3] Searching free stock loop: {query}")
        cmd = [
            "yt-dlp",
            f"ytsearch1:{query}",
            "--match-filter", "duration < 120",
            "-f", "best[ext=mp4]/best",
            "-o", cache_raw,
            "--force-overwrites",
            "--no-warnings",
            "--quiet",
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        if not os.path.exists(cache_raw) or os.path.getsize(cache_raw) < 50000:
            return None

        subprocess.run(
            [
                "ffmpeg", "-y", "-i", cache_raw,
                "-t", str(max(3.0, float(duration))),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                "-c:v", "libx264", "-preset", "medium", "-crf", "26",
                "-an", output_path,
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if os.path.exists(cache_raw):
            os.remove(cache_raw)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 50000:
            return output_path
    except Exception as e:
        print(f"   [Tier 3] stock loop failed: {e}")
    return None
