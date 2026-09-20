import json

new_topics = [
    {
        "name": "alien",
        "search": "alien ufo spaceship sci-fi 4k stock video free",
        "bgm_freq": 140,
        "color": "&H00FF00&", # Green
        "script": "Are we truly alone in the universe? For decades, military pilots have reported high-speed UFOs pulling maneuvers that defy our understanding of physics. If these objects aren't from Earth, what do they want? Some believe they are here to observe us, while others fear a darker agenda. Subscribe for more cosmic mysteries."
    },
    {
        "name": "robot",
        "search": "robot factory assembly line 4k stock video free",
        "bgm_freq": 70,
        "color": "&H00FFFF&", # Cyan
        "script": "The age of robotics is no longer science fiction. In massive factories around the world, intelligent machines are already building everything from cars to microchips, working endlessly without rest. Soon, they will walk among us. But what happens when robots become smarter than their creators? Subscribe to see the future."
    },
    {
        "name": "hacker",
        "search": "hacker typing code matrix 4k stock video free",
        "bgm_freq": 100,
        "color": "&H00FF00&", # Green Matrix
        "script": "Right now, a silent war is being fought in cyberspace. Anonymous hackers are constantly breaching secure networks, stealing billions of dollars and exposing state secrets. The next world war won't be fought with bombs, but with code. Your digital life is never completely safe. Subscribe for more cyber secrets."
    },
    {
        "name": "viking",
        "search": "viking ship ocean warrior 4k stock video free",
        "bgm_freq": 80,
        "color": "&H0000FF&", # Red
        "script": "The Vikings were fierce warriors who conquered the seas and struck fear into the hearts of empires. Using their legendary longships, they navigated treacherous oceans to raid and trade across the known world. Their brutal tactics and legendary gods made them unstoppable. Subscribe for more history."
    },
    {
        "name": "tornado",
        "search": "tornado storm weather extreme 4k stock video free",
        "bgm_freq": 60,
        "color": "&HFFFFFF&", # White
        "script": "Tornadoes are the most violent storms on the planet, capable of producing winds over three hundred miles per hour. These monstrous funnels of destruction can flatten entire neighborhoods in seconds, leaving nothing but devastation in their wake. Mother nature is a force you cannot stop. Subscribe for more extreme weather."
    }
]

with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "r") as f:
    content = f.read()

start_idx = content.find("TOPICS = [")
end_idx = content.find("def format_time(sec):")

if start_idx != -1 and end_idx != -1:
    old_topics_str = content[start_idx:end_idx]
    
    # Extract just the list part
    list_str = old_topics_str.replace("TOPICS = ", "").strip()
    
    import ast
    old_topics = ast.literal_eval(list_str)
    
    combined = old_topics + new_topics
    
    import pprint
    new_topics_str = "TOPICS = " + pprint.pformat(combined, width=120, sort_dicts=False)
    
    content = content[:start_idx] + new_topics_str + "\n\n" + content[end_idx:]
    
    with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "w") as f:
        f.write(content)
    print("Successfully added 5 new topics (Phase 2).")
else:
    print("Failed to find boundaries.")
