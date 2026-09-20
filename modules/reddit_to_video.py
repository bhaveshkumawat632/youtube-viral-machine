import requests
import json
import random
import sys
import os

# Ensure we can import free_ai_router
sys.path.append("/home/junglee01")
try:
    from free_ai_router import FreeAIRouter
except ImportError:
    FreeAIRouter = None

def fetch_top_reddit_post(subreddit="TrueOffMyChest"):
    """
    Fetches the top daily post from a given subreddit using the free JSON API.
    """
    url = f"https://www.reddit.com/r/{subreddit}/top/.json?t=day&limit=10"
    headers = {
        "User-Agent": "python:vidrush.script.bot:v2.0 (by /u/vidrush_dev)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        posts = data.get("data", {}).get("children", [])
        valid_posts = []
        
        for post in posts:
            post_data = post.get("data", {})
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            
            # Filter out overly short or long posts
            text_length = len(selftext.split())
            if 50 < text_length < 500 and not post_data.get("over_18", False):
                valid_posts.append({
                    "title": title,
                    "body": selftext,
                    "author": post_data.get("author", "")
                })
                
        if not valid_posts:
            raise Exception(f"No suitable posts found in r/{subreddit}")
            
        return random.choice(valid_posts)
        
    except Exception as e:
        print(f"⚠️ Reddit API failed ({e}). Using built-in fallback stories...")
        fallback_stories = [
            {
                "title": "I found out my husband's 'work trips' were actually him living a double life.",
                "body": "For 3 years, my husband said he was traveling to Chicago for sales. Yesterday, a woman messaged me on Facebook with pictures of him at their son's 2nd birthday party.",
                "author": "throwaway1234"
            },
            {
                "title": "My boss tried to fire me to give his nephew my job, so I deleted the master database.",
                "body": "He told me Friday was my last day. Since I built the entire client database from scratch on my own personal drive, I took it with me. Monday morning, the panic calls started.",
                "author": "IT_guy_007"
            },
            {
                "title": "I accidentally discovered a family secret that changes everything.",
                "body": "I took a DNA test for fun. It turns out the man I've called Dad my whole life isn't related to me, but my mom's best friend is a 99% paternal match.",
                "author": "confused_daughter"
            }
        ]
        return random.choice(fallback_stories)

def generate_script_from_reddit(subreddit="TrueOffMyChest", language="hindi"):
    """
    Fetches a Reddit story and converts it into a 5-scene viral script format.
    """
    print(f"\n🔍 Fetching viral story from r/{subreddit}...")
    post = fetch_top_reddit_post(subreddit)
    
    if not post:
        return None
        
    print(f"✅ Found Story: {post['title']}")
    
    if not FreeAIRouter:
        print("❌ FreeAIRouter not found. Cannot generate script.")
        return None
        
    router = FreeAIRouter()
    
    lang_instruction = "fluent, engaging Hindi (Devanagari script)" if language.lower() == "hindi" else "dramatic, engaging English"
    
    prompt = f"""
    You are a viral YouTube Shorts creator. Turn this Reddit story into a 5-scene high-retention video script.
    
    Reddit Title: {post['title']}
    Reddit Body: {post['body']}
    
    The narrative MUST be written in {lang_instruction}.
    The video_prompt MUST be written in ENGLISH (this is critical for the AI image generator). Make the visual descriptions intensely vivid and highly cinematic. Always append these EXACT keywords to the end of every video_prompt: "masterpiece, insanely detailed, ultra-realistic, photorealistic, 8k resolution, volumetric cinematic lighting, award-winning photography, trending on artstation".
    
    Return ONLY a JSON object in this format (no markdown blocks, no extra text):
    {{
      "scenes": [
        {{"narrative": "scene 1 text here", "video_prompt": "visual description for scene 1", "emotion": "shocked"}},
        {{"narrative": "scene 2 text here", "video_prompt": "visual description for scene 2", "emotion": "tense"}},
        {{"narrative": "scene 3 text here", "video_prompt": "visual description for scene 3", "emotion": "neutral"}},
        {{"narrative": "scene 4 text here", "video_prompt": "visual description for scene 4", "emotion": "tense"}},
        {{"narrative": "scene 5 text here", "video_prompt": "visual description for scene 5", "emotion": "triumphant"}}
      ]
    }}
    
    Emotions allowed: shocked, tense, triumphant, neutral.
    Keep each scene to 1-2 short sentences.
    """
    
    print(f"🤖 Generating viral script via Free AI Router...")
    result = router.chat(prompt, verbose=False)
    
    try:
        if result and "response" in result:
            content = result["response"]
            # Clean possible markdown wrap
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            data = json.loads(content)
            cin = data.get("scenes", [])
            
            if cin:
                mapped = []
                for s in cin:
                    narr = s.get("narrative", "") or s.get("text", "")
                    kw = s.get("video_prompt", "")
                    emo = s.get("emotion", "neutral")
                    
                    mapped.append({
                        "text": narr,
                        "emotion_tag": emo,
                        "suggested_visual_keyword": kw or narr[:60],
                    })
                    
                if mapped:
                    print(f"✅ SUCCESS: {len(mapped)} scenes generated from Reddit story.")
                    return mapped
    except Exception as e:
        print(f"❌ Failed to parse script from AI: {e}")
        
    return None

if __name__ == "__main__":
    script = generate_script_from_reddit()
    print(json.dumps(script, indent=2, ensure_ascii=False) if script else "Failed")
