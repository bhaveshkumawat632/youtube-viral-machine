import os
import requests

def get_coverr_video(query, output_path):
    url = f"https://coverr.co/api/videos?query={query}&orientation=portrait&per_page=1"
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"Coverr API error: {r.status_code}")
    data = r.json()
    if not data.get("videos"):
        raise RuntimeError(f"No Coverr videos for: {query}")
    video = data["videos"][0]
    dl = video.get("download_url") or video.get("url")
    if not dl:
        raise RuntimeError("Coverr response missing download url")
    vid = requests.get(dl, stream=True, timeout=60)
    with open(output_path, "wb") as f:
        for chunk in vid.iter_content(8192):
            f.write(chunk)
    return output_path
