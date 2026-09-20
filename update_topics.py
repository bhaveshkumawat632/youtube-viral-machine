import json

new_topics = [
    {
        "name": "volcano",
        "search": "volcano eruption lava 4k stock video free",
        "bgm_freq": 50,
        "color": "&H0000FF&", # Red
        "script": "Deep beneath our feet, the Earth is a boiling cauldron of liquid fire. When the pressure becomes too great, volcanoes erupt, unleashing destruction that can wipe out entire cities in minutes. Yet, this same violent force creates new land and fertile soil. Subscribe for more explosive facts."
    },
    {
        "name": "blackhole",
        "search": "black hole galaxy universe 4k stock video free",
        "bgm_freq": 40,
        "color": "&HFF00FF&", # Purple
        "script": "Black holes are the most terrifying monsters in the universe. Their gravity is so intense that not even light can escape. If you fell into one, time would slow down, and your body would be stretched into a single strand of atoms in a process called spaghettification. Subscribe to explore the dark side of space."
    },
    {
        "name": "samurai",
        "search": "samurai katana japan history 4k stock video free",
        "bgm_freq": 110,
        "color": "&H000000&", # Black (but we use hex, wait, text is white, so maybe Red &H0000FF&)
        "script": "The Samurai were ancient Japan's elite warriors, living by a strict code of honor known as Bushido. They wielded the katana, a sword so sharp it could cut through armor with a single strike. But to a Samurai, honor was more important than life itself. Subscribe for more legendary history."
    },
    {
        "name": "everest",
        "search": "mount everest snow mountain climbing 4k stock video free",
        "bgm_freq": 130,
        "color": "&HFFFFFF&", # White
        "script": "Mount Everest is the highest point on Earth, but reaching the summit comes at a deadly price. Above twenty-six thousand feet is the Death Zone, where oxygen levels are so low that your body slowly begins to die. Despite the risks, hundreds try to conquer it every year. Subscribe for more extreme adventures."
    },
    {
        "name": "amazon",
        "search": "amazon rainforest jungle animals 4k stock video free",
        "bgm_freq": 160,
        "color": "&H00FF00&", # Green
        "script": "The Amazon Rainforest is the lungs of the Earth, producing twenty percent of the world's oxygen. It is home to millions of undiscovered species, some of which hold the cure to deadly diseases. But this incredible jungle is disappearing at an alarming rate. Subscribe to learn more about our planet."
    }
]

with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "r") as f:
    content = f.read()

# We'll just replace the TOPICS array entirely by finding it.
start_idx = content.find("TOPICS = [")
end_idx = content.find("]\n\ndef format_time")

if start_idx != -1 and end_idx != -1:
    old_topics_str = content[start_idx:end_idx+1]
    
    # We will reconstruct the TOPICS list.
    import ast
    old_topics = ast.literal_eval(old_topics_str.replace("TOPICS = ", ""))
    
    # fix Samurai color
    new_topics[2]["color"] = "&H0000FF&" # Red
    
    combined = old_topics + new_topics
    
    # Write it back nicely
    import pprint
    new_topics_str = "TOPICS = " + pprint.pformat(combined, width=120, sort_dicts=False)
    
    content = content[:start_idx] + new_topics_str + "\n" + content[end_idx+1:]
    
    with open("/home/junglee01/youtube-viral-machine/build_master_real_world_short.py", "w") as f:
        f.write(content)
    print("Successfully added 5 new topics.")

