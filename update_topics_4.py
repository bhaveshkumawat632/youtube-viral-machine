import json

new_topics = [
    {
        "name": "meteor",
        "search": "meteor asteroid space meteor shower 4k stock video free",
        "bgm_freq": 90,
        "color": "&H0000FF&", # Red
        "script": "Every day, thousands of meteors bombard the Earth, but most burn up harmlessly in our atmosphere. However, it only takes one massive asteroid to change history forever. The dinosaurs learned this the hard way, and astronomers say it's not a matter of if it will happen again, but when. Subscribe to stay alert."
    },
    {
        "name": "desert",
        "search": "desert sahara sand dunes 4k stock video free",
        "bgm_freq": 70,
        "color": "&H00FFFF&", # Yellow
        "script": "The Sahara Desert is one of the harshest environments on the planet. Spanning over three million square miles, it is a vast ocean of sand where temperatures can exceed one hundred and thirty degrees. Yet, ancient civilizations once thrived here when it was a lush, green paradise. Subscribe to explore Earth's extremes."
    },
    {
        "name": "quantum",
        "search": "quantum physics atom particle futuristic 4k stock video free",
        "bgm_freq": 130,
        "color": "&HFF00FF&", # Purple
        "script": "Quantum mechanics is the most bizarre branch of science. At the subatomic level, particles can exist in multiple places at once and communicate instantly across the universe through quantum entanglement. It completely defies human logic and suggests our reality might just be an illusion. Subscribe to bend your mind."
    },
    {
        "name": "glacier",
        "search": "glacier ice antarctica melting 4k stock video free",
        "bgm_freq": 50,
        "color": "&HFFFFFF&", # White
        "script": "Antarctica holds ninety percent of the world's ice. These colossal glaciers have stood for millions of years, trapping ancient secrets and unknown viruses deep within them. But as the planet warms, this ice is melting at an unprecedented rate, threatening to reshape coastlines globally. Subscribe to protect our planet."
    },
    {
        "name": "mars",
        "search": "mars rover space colonization red planet 4k stock video free",
        "bgm_freq": 110,
        "color": "&H0000FF&", # Red
        "script": "Mars is a dead, frozen wasteland, but it wasn't always this way. Billions of years ago, it had oceans and a thick atmosphere, much like Earth. Now, humanity is on the verge of returning, aiming to colonize the Red Planet and ensure our species survives the test of time. Subscribe for the future of space travel."
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
    print("Successfully added 5 more topics (Phase 4).")
else:
    print("Failed to find boundaries.")
