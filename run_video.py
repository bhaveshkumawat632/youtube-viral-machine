import sys
import os
import json
import time
from openai import OpenAI

sys.path.append("/home/junglee01/youtube-viral-machine")
from modules.paisa_bhai_pipeline import render_paisa_bhai_short

def generate_viral_script():
    print("Generating script via NVIDIA Nemotron Nano Omni Reasoning (30B)...")
    client = OpenAI(
        base_url = "https://integrate.api.nvidia.com/v1",
        api_key = "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"
    )

    prompt = (
        "Write a 40-second viral YouTube Shorts script in Hindi (written in English alphabets / Hinglish). "
        "Topic: 1 Secret psychological trick to force yourself to work. "
        "Must be highly engaging, dramatic, and punchy. "
        "Use frequent commas (,) and periods (.) so the TTS engine takes natural pauses and sounds less robotic. "
        "Do NOT include any visual directions, tags, or brackets like [Hook]. Just output the spoken text directly. "
        "Keep it around 70-80 words maximum so it fits perfectly in a Short."
    )

    response = client.chat.completions.create(
        model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        messages=[{"role":"user","content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    
    script = response.choices[0].message.content.strip()
    
    # Clean up script in case model included reasoning block (NVIDIA models sometimes do)
    if "```" in script:
        lines = script.split("```")
        if len(lines) >= 3:
            script = lines[-2].strip() # usually the last code block contains the text
    
    # Remove any brackets the model might still add
    import re
    script = re.sub(r'\[.*?\]', '', script).strip()
    
    print("Generated Script:\n", script)
    return script

if __name__ == "__main__":
    script = generate_viral_script()
    print("Rendering video with new premium pipeline...")
    # Using MadhurNeural (hindi_male) and dramatic BGM
    path, man = render_paisa_bhai_short(
        script, 
        title="1 Secret Trick To Work", 
        voice_key="hindi_male", 
        bgm_style="dramatic"
    )
    print("\n" + "="*50)
    print("✅ NEW VIDEO READY:", path)
    print("="*50)
