import os
import urllib.parse
import requests
import time
import random

# Monkey-patch DNS resolution for image.pollinations.ai due to local network DNS issues
try:
    import urllib3.util.connection as connection
    orig_create_connection = connection.create_connection
    def patched_create_connection(address, *args, **kwargs):
        host, port = address
        if host == "image.pollinations.ai":
            # Cloudflare IPs for image.pollinations.ai resolved via public Google DNS API
            host = random.choice(["172.67.173.121", "104.21.30.173"])
        return orig_create_connection((host, port), *args, **kwargs)
    connection.create_connection = patched_create_connection
except Exception as e:
    print(f"⚠️ Failed to apply DNS patch: {e}")

def get_pollinations_image(prompt, output_path):
    print(f"🎨 Generating Image via Pollinations AI for: '{prompt}'")
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(1, 999999)
    
    endpoints = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&seed={seed}&private=true",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&seed={seed}"
    ]

    max_retries = 3
    for attempt in range(max_retries):
        for url in endpoints:
            try:
                print(f"   Trying endpoint: {url[:60]}... (Attempt {attempt+1}/{max_retries})")
                response = requests.get(url, stream=True, timeout=40)
                content_type = response.headers.get("content-type", "")
                if response.status_code == 200 and "image" in content_type:
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ Image downloaded successfully to: {output_path}")
                    return output_path
                elif response.status_code == 429:
                    print(f"   ⚠️ Rate limited (HTTP 429) on attempt {attempt+1}")
                else:
                    print(f"   ⚠️ Endpoint returned status {response.status_code} or content-type '{content_type}'")
            except Exception as e:
                print(f"   ⚠️ Endpoint failed: {e}")
        
        wait_time = (2 ** attempt) + random.uniform(1.0, 2.0)
        print(f"⏳ Retry wait: {wait_time:.1f}s before attempt {attempt+2}/{max_retries}...")
        time.sleep(wait_time)
        
    raise RuntimeError(f"Failed to generate image via Pollinations AI after {max_retries} attempts.")
