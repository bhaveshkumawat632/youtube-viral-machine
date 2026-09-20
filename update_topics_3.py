import json

new_topics = [
    {
        "name": "shark",
        "search": "shark great white ocean underwater 4k stock video free",
        "bgm_freq": 60,
        "color": "&HFF0000&", # Blue
        "script": "The Great White Shark is the ocean's apex predator, perfectly evolved over millions of years for one purpose: hunting. With rows of razor-sharp teeth and a sense of smell that can detect a single drop of blood from miles away, it is the ultimate killing machine. Subscribe for more deep sea terrors."
    },
    {
        "name": "ninja",
        "search": "ninja assassin japan martial arts 4k stock video free",
        "bgm_freq": 100,
        "color": "&H000000&", 
        "script": "Ninjas were the legendary shadow assassins of feudal Japan. Masters of stealth, espionage, and assassination, they operated entirely in the dark, using secret weapons like throwing stars and poison. They were the invisible ghosts of history. Subscribe for more untold secrets."
    },
    {
        "name": "tsunami",
        "search": "tsunami wave ocean storm destruction 4k stock video free",
        "bgm_freq": 55,
        "color": "&HFFFFFF&", 
        "script": "A tsunami is a towering wall of water triggered by massive underwater earthquakes. Traveling at the speed of a jet airliner, these mega-waves can wipe out entire coastal cities in a matter of minutes, leaving nothing but devastation behind. Mother nature's fury is unstoppable. Subscribe for more extreme disasters."
    },
    {
        "name": "spider",
        "search": "spider tarantula macro nature 4k stock video free",
        "bgm_freq": 110,
        "color": "&H00FF00&", 
        "script": "Spiders are some of the most misunderstood creatures on Earth. With venom that can liquefy the insides of their prey and silk stronger than steel, they are nature's perfect engineers and deadly hunters. Are you brave enough to look closer? Subscribe for more creepy crawlers."
    },
    {
        "name": "castle",
        "search": "castle medieval knight history 4k stock video free",
        "bgm_freq": 85,
        "color": "&H00FFFF&", 
        "script": "During the Dark Ages, massive stone castles were built as impenetrable fortresses to survive brutal sieges and deadly wars. Protected by brave knights in shining armor and surrounded by moats, these strongholds shaped the course of history. Subscribe to step back in time."
    }
]

with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "r") as f:
    content = f.read()

start_idx = content.find("TOPICS = [")
end_idx = content.find("def format_time(sec):")

if start_idx != -1 and end_idx != -1:
    old_topics_str = content[start_idx:end_idx]
    
    list_str = old_topics_str.replace("TOPICS = ", "").strip()
    
    import ast
    old_topics = ast.literal_eval(list_str)
    
    combined = old_topics + new_topics
    
    import pprint
    new_topics_str = "TOPICS = " + pprint.pformat(combined, width=120, sort_dicts=False)
    
    content = content[:start_idx] + new_topics_str + "\n\n" + content[end_idx:]
    
    with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "w") as f:
        f.write(content)
    print("Successfully added 5 more topics (Phase 3).")
else:
    print("Failed to find boundaries.")
