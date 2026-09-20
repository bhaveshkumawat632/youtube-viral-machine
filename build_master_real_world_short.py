#!/usr/bin/env python3
"""
Master Real-World Topic Short Builder:
Randomly selects a real-world topic, downloads 4K stock video clips, 
generates hyper-realistic ElevenLabs human voice, loops clips to prevent lag,
and assembles the final Short.
"""

import os
import sys
import asyncio
import subprocess
import glob
import requests
import json
import base64
import random

BASE_DIR = "/home/junglee01/youtube-viral-machine"
TEMP_DIR = os.path.join(BASE_DIR, "Testing", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def _load_env_key(name: str) -> str:
    """Read a key from process env or the gitignored .env file (never hardcode secrets)."""
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


ELEVENLABS_KEY = _load_env_key("ELEVENLABS_API_KEY")
VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17" # Roger - Human Voice

TOPICS = [{'name': 'ai',
  'search': 'artificial intelligence robot futuristic 4k stock video free',
  'bgm_freq': 180,
  'color': '&H00FFFF&',
  'script': 'Did you know that Artificial Intelligence is learning faster than human evolution? What took us millions '
            "of years to achieve, AI is mastering in mere months. Very soon, it won't just assist us; it might "
            'completely outsmart us. Will it be our greatest creation or our final invention? Subscribe to uncover the '
            'truth.'},
 {'name': 'space',
  'search': 'space galaxy mars colonization 4k stock video free',
  'bgm_freq': 55,
  'color': '&H00A5FF&',
  'script': "We are on the verge of becoming an interplanetary species. Mars, a cold and dead planet, is humanity's "
            'next frontier. But survival there means battling extreme radiation, zero oxygen, and isolation. Are we '
            'truly ready to leave Earth behind? Hit subscribe to explore the deepest mysteries of space.'},
 {'name': 'ocean',
  'search': 'deep ocean coral reef scuba 4k stock video free',
  'bgm_freq': 120,
  'color': '&HFFFF00&',
  'script': 'We know more about the surface of the moon than the bottom of our own oceans. Hidden deep in the Mariana '
            'Trench are bizarre alien-like creatures that glow in the dark and survive crushing pressures. What else '
            'is lurking in the abyss? Subscribe to dive deeper into the unknown.'},
 {'name': 'dino',
  'search': 'dinosaur trex asteroid 4k stock video free',
  'bgm_freq': 65,
  'color': '&H0000FF&',
  'script': '66 million years ago, a massive asteroid crashed into Earth, wiping out the dinosaurs in a fiery '
            'apocalypse. The impact triggered mega-tsunamis and blocked out the sun, plunging the planet into '
            'darkness. Yet, out of the ashes, mammals rose to power. Subscribe for more epic history.'},
 {'name': 'history',
  'search': 'ancient pyramid egypt ruins 4k stock video free',
  'bgm_freq': 90,
  'color': '&H00FFFF&',
  'script': 'Thousands of years ago, ancient civilizations built towering pyramids and vast cities without modern '
            'technology. How did the Egyptians move colossal stones weighing tons across the desert? Some say they '
            'used advanced engineering lost to time, while others whisper of extraterrestrial help. Subscribe to '
            'unravel the secrets of the past.'},
 {'name': 'volcano',
  'search': 'volcano eruption lava 4k stock video free',
  'bgm_freq': 50,
  'color': '&H0000FF&',
  'script': 'Deep beneath our feet, the Earth is a boiling cauldron of liquid fire. When the pressure becomes too '
            'great, volcanoes erupt, unleashing destruction that can wipe out entire cities in minutes. Yet, this same '
            'violent force creates new land and fertile soil. Subscribe for more explosive facts.'},
 {'name': 'blackhole',
  'search': 'black hole galaxy universe 4k stock video free',
  'bgm_freq': 40,
  'color': '&HFF00FF&',
  'script': 'Black holes are the most terrifying monsters in the universe. Their gravity is so intense that not even '
            'light can escape. If you fell into one, time would slow down, and your body would be stretched into a '
            'single strand of atoms in a process called spaghettification. Subscribe to explore the dark side of '
            'space.'},
 {'name': 'samurai',
  'search': 'samurai katana japan history 4k stock video free',
  'bgm_freq': 110,
  'color': '&H0000FF&',
  'script': "The Samurai were ancient Japan's elite warriors, living by a strict code of honor known as Bushido. They "
            'wielded the katana, a sword so sharp it could cut through armor with a single strike. But to a Samurai, '
            'honor was more important than life itself. Subscribe for more legendary history.'},
 {'name': 'everest',
  'search': 'mount everest snow mountain climbing 4k stock video free',
  'bgm_freq': 130,
  'color': '&HFFFFFF&',
  'script': 'Mount Everest is the highest point on Earth, but reaching the summit comes at a deadly price. Above '
            'twenty-six thousand feet is the Death Zone, where oxygen levels are so low that your body slowly begins '
            'to die. Despite the risks, hundreds try to conquer it every year. Subscribe for more extreme adventures.'},
 {'name': 'amazon',
  'search': 'amazon rainforest jungle animals 4k stock video free',
  'bgm_freq': 160,
  'color': '&H00FF00&',
  'script': "The Amazon Rainforest is the lungs of the Earth, producing twenty percent of the world's oxygen. It is "
            'home to millions of undiscovered species, some of which hold the cure to deadly diseases. But this '
            'incredible jungle is disappearing at an alarming rate. Subscribe to learn more about our planet.'},
 {'name': 'alien',
  'search': 'alien ufo spaceship sci-fi 4k stock video free',
  'bgm_freq': 140,
  'color': '&H00FF00&',
  'script': 'Are we truly alone in the universe? For decades, military pilots have reported high-speed UFOs pulling '
            "maneuvers that defy our understanding of physics. If these objects aren't from Earth, what do they want? "
            'Some believe they are here to observe us, while others fear a darker agenda. Subscribe for more cosmic '
            'mysteries.'},
 {'name': 'robot',
  'search': 'robot factory assembly line 4k stock video free',
  'bgm_freq': 70,
  'color': '&H00FFFF&',
  'script': 'The age of robotics is no longer science fiction. In massive factories around the world, intelligent '
            'machines are already building everything from cars to microchips, working endlessly without rest. Soon, '
            'they will walk among us. But what happens when robots become smarter than their creators? Subscribe to '
            'see the future.'},
 {'name': 'hacker',
  'search': 'hacker typing code matrix 4k stock video free',
  'bgm_freq': 100,
  'color': '&H00FF00&',
  'script': 'Right now, a silent war is being fought in cyberspace. Anonymous hackers are constantly breaching secure '
            "networks, stealing billions of dollars and exposing state secrets. The next world war won't be fought "
            'with bombs, but with code. Your digital life is never completely safe. Subscribe for more cyber secrets.'},
 {'name': 'viking',
  'search': 'viking ship ocean warrior 4k stock video free',
  'bgm_freq': 80,
  'color': '&H0000FF&',
  'script': 'The Vikings were fierce warriors who conquered the seas and struck fear into the hearts of empires. Using '
            'their legendary longships, they navigated treacherous oceans to raid and trade across the known world. '
            'Their brutal tactics and legendary gods made them unstoppable. Subscribe for more history.'},
 {'name': 'tornado',
  'search': 'tornado storm weather extreme 4k stock video free',
  'bgm_freq': 60,
  'color': '&HFFFFFF&',
  'script': 'Tornadoes are the most violent storms on the planet, capable of producing winds over three hundred miles '
            'per hour. These monstrous funnels of destruction can flatten entire neighborhoods in seconds, leaving '
            'nothing but devastation in their wake. Mother nature is a force you cannot stop. Subscribe for more '
            'extreme weather.'},
 {'name': 'shark',
  'search': 'shark great white ocean underwater 4k stock video free',
  'bgm_freq': 60,
  'color': '&HFF0000&',
  'script': "The Great White Shark is the ocean's apex predator, perfectly evolved over millions of years for one "
            'purpose: hunting. With rows of razor-sharp teeth and a sense of smell that can detect a single drop of '
            'blood from miles away, it is the ultimate killing machine. Subscribe for more deep sea terrors.'},
 {'name': 'ninja',
  'search': 'ninja assassin japan martial arts 4k stock video free',
  'bgm_freq': 100,
  'color': '&H000000&',
  'script': 'Ninjas were the legendary shadow assassins of feudal Japan. Masters of stealth, espionage, and '
            'assassination, they operated entirely in the dark, using secret weapons like throwing stars and poison. '
            'They were the invisible ghosts of history. Subscribe for more untold secrets.'},
 {'name': 'tsunami',
  'search': 'tsunami wave ocean storm destruction 4k stock video free',
  'bgm_freq': 55,
  'color': '&HFFFFFF&',
  'script': 'A tsunami is a towering wall of water triggered by massive underwater earthquakes. Traveling at the speed '
            'of a jet airliner, these mega-waves can wipe out entire coastal cities in a matter of minutes, leaving '
            "nothing but devastation behind. Mother nature's fury is unstoppable. Subscribe for more extreme "
            'disasters.'},
 {'name': 'spider',
  'search': 'spider tarantula macro nature 4k stock video free',
  'bgm_freq': 110,
  'color': '&H00FF00&',
  'script': 'Spiders are some of the most misunderstood creatures on Earth. With venom that can liquefy the insides of '
            "their prey and silk stronger than steel, they are nature's perfect engineers and deadly hunters. Are you "
            'brave enough to look closer? Subscribe for more creepy crawlers.'},
 {'name': 'castle',
  'search': 'castle medieval knight history 4k stock video free',
  'bgm_freq': 85,
  'color': '&H00FFFF&',
  'script': 'During the Dark Ages, massive stone castles were built as impenetrable fortresses to survive brutal '
            'sieges and deadly wars. Protected by brave knights in shining armor and surrounded by moats, these '
            'strongholds shaped the course of history. Subscribe to step back in time.'},
 {'name': 'meteor',
  'search': 'meteor asteroid space meteor shower 4k stock video free',
  'bgm_freq': 90,
  'color': '&H0000FF&',
  'script': 'Every day, thousands of meteors bombard the Earth, but most burn up harmlessly in our atmosphere. '
            'However, it only takes one massive asteroid to change history forever. The dinosaurs learned this the '
            "hard way, and astronomers say it's not a matter of if it will happen again, but when. Subscribe to stay "
            'alert.'},
 {'name': 'desert',
  'search': 'desert sahara sand dunes 4k stock video free',
  'bgm_freq': 70,
  'color': '&H00FFFF&',
  'script': 'The Sahara Desert is one of the harshest environments on the planet. Spanning over three million square '
            'miles, it is a vast ocean of sand where temperatures can exceed one hundred and thirty degrees. Yet, '
            "ancient civilizations once thrived here when it was a lush, green paradise. Subscribe to explore Earth's "
            'extremes.'},
 {'name': 'quantum',
  'search': 'quantum physics atom particle futuristic 4k stock video free',
  'bgm_freq': 130,
  'color': '&HFF00FF&',
  'script': 'Quantum mechanics is the most bizarre branch of science. At the subatomic level, particles can exist in '
            'multiple places at once and communicate instantly across the universe through quantum entanglement. It '
            'completely defies human logic and suggests our reality might just be an illusion. Subscribe to bend your '
            'mind.'},
 {'name': 'glacier',
  'search': 'glacier ice antarctica melting 4k stock video free',
  'bgm_freq': 50,
  'color': '&HFFFFFF&',
  'script': "Antarctica holds ninety percent of the world's ice. These colossal glaciers have stood for millions of "
            'years, trapping ancient secrets and unknown viruses deep within them. But as the planet warms, this ice '
            'is melting at an unprecedented rate, threatening to reshape coastlines globally. Subscribe to protect our '
            'planet.'},
 {'name': 'mars',
  'search': 'mars rover space colonization red planet 4k stock video free',
  'bgm_freq': 110,
  'color': '&H0000FF&',
  'script': "Mars is a dead, frozen wasteland, but it wasn't always this way. Billions of years ago, it had oceans and "
            'a thick atmosphere, much like Earth. Now, humanity is on the verge of returning, aiming to colonize the '
            'Red Planet and ensure our species survives the test of time. Subscribe for the future of space travel.'},
 {'name': 'isro',
  'search': 'isro rocket launch chandrayaan india space 4k stock video free',
  'bgm_freq': 120,
  'color': '&H0045D0&',
  'script': "India touched the Moon for just 75 million dollars, a fraction of what other nations spend. ISRO, born in a "
            'rocket shed in Kerala, launched Chandrayaan and Mangalyaan on its first attempts. Now Gaganyaan will carry '
            'Indian astronauts to space. Subscribe to witness India\'s journey to the stars.'},
 {'name': 'himalaya',
  'search': 'himalaya monastery mountains snow peaks 4k stock video free',
  'bgm_freq': 90,
  'color': '&H00FFFFFF&',
  'script': "The Himalayas are still growing taller every single year, rising as India pushes into Asia. Hidden in these "
            'peaks are 9000-year-old monasteries, glaciers that feed half of humanity, and sages who renounced the world. '
            'Subscribe to explore the roof of the Earth.'},
 {'name': 'mahabharat',
  'search': 'ancient indian temple epic mythology art 4k stock video free',
  'bgm_freq': 140,
  'color': '&H0030D5FF&',
  'script': "The Mahabharata is the longest poem ever written, ten times the Iliad and Odyssey combined. Within it lies the "
            'Bhagavad Gita, a battlefield conversation about duty and destiny that guides billions even today. Was it myth '
            'or memory? Subscribe to unravel the greatest epic ever told.'},
 {'name': 'ganga',
  'search': 'ganges river varanasi ghats india 4k stock video free',
  'bgm_freq': 100,
  'color': '&H00FFFF00&',
  'script': "Varanasi is older than Rome, older than Athens, possibly the oldest living city on Earth. Here the Ganga flows "
            'past 88 ghats where life and death meet face to face every single day. Hindus believe dying here ends the cycle '
            'of rebirth. Subscribe for the mysteries of India\'s eternal river.'},
 {'name': 'taj',
  'search': 'taj mahal agra india marble 4k stock video free',
  'bgm_freq': 130,
  'color': '&H00FFFFFF&',
  'script': "Shah Jahan cut the hands of the Taj Mahal workers, or so the legend goes. The truth is stranger: 20,000 workers, "
            '1000 elephants, and 28 kinds of precious stones built this tomb of love. Its four minarets lean outward by '
            'design, to protect the dome from earthquakes. Subscribe for secrets of the Taj.'},
 {'name': 'tiger',
  'search': 'bengal tiger wildlife jungle india safari 4k stock video free',
  'bgm_freq': 150,
  'color': '&H0000A5FF&',
  'script': "India is the only country on Earth where lions, tigers, and leopards roam the same forests. The Bengal tiger's "
            'roar carries over three kilometers, yet fewer than 4000 remain in the wild. Project Tiger brought them back '
            'from the brink once before. Subscribe to protect the jungle king.'},
 {'name': 'kailash',
  'search': 'kailash mansarovar sacred mountain tibet 4k stock video free',
  'bgm_freq': 80,
  'color': '&H00FFB400&',
  'script': "Mount Kailash has never been climbed, and no one knows exactly why. NASA satellites show its shadow forms a "
            'perfect om, and pilgrims say time bends near its peak. Hindus, Buddhists, Jains, and Bons all hold it sacred. '
            'Subscribe to unravel Earth\'s holiest mystery.'},
 {'name': 'vedic',
  'search': 'ancient india history temple architecture 4k stock video free',
  'bgm_freq': 160,
  'color': '&H001CA5FF&',
  'script': "The zero, chess, plastic surgery, and the concept of atoms, ancient India gave the world ideas millennia ahead "
            'of their time. Sushruta performed cataract surgery 2600 years ago. Aryabhata calculated the Earth\'s rotation. '
            'Subscribe to rediscover the science of the ancients.'},
 {'name': 'monsoon',
  'search': 'monsoon rain kerala backwaters india 4k stock video free',
  'bgm_freq': 110,
  'color': '&H00FFFF00&',
  'script': "Every June, a wall of clouds 2000 kilometers wide crashes into Kerala, and a billion people hold their breath. "
            'The Indian monsoon delivers 80 percent of the year\'s rain in just four months, feeding farms, rivers, and '
            'entire civilizations. Subscribe to feel the magic of the rains.'},
 {'name': 'holi',
  'search': 'holi festival colors india celebration 4k stock video free',
  'bgm_freq': 170,
  'color': '&H00FF66FF&',
  'script': "Once a year, India dissolves every border of caste, class, and creed, under clouds of pink, yellow, and green. "
            'Holi celebrates the victory of good over evil and the arrival of spring. Even the streets forget their names. '
            'Subscribe to experience the world\'s most colorful festival.'}]

def format_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec))*100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def main():
    if len(sys.argv) > 1:
        topic_name = sys.argv[1]
        topic = next(t for t in TOPICS if t['name'] == topic_name)
    else:
        topic = random.choice(TOPICS)
    print(f"=====================================================")
    print(f"🌟 TOPIC SELECTED: {topic['name'].upper()}")
    print(f"=====================================================")
    
    # 1. Download Stock Clips
    STOCK_DIR = os.path.join(BASE_DIR, f"real_{topic['name']}_clips")
    os.makedirs(STOCK_DIR, exist_ok=True)
    
    # Cleanup old parts
    for p in glob.glob(os.path.join(STOCK_DIR, "*.part")):
        os.remove(p)
        
    clips = glob.glob(os.path.join(STOCK_DIR, "*.mp4"))
    if len(clips) < 3:
        print(f"📥 Downloading clips for '{topic['search']}'...")
        subprocess.run([
            "yt-dlp", "--js-runtimes", "node", f"ytsearch4:{topic['search']}",
            "-S", "res:1080,ext:mp4:m4a",
            "--merge-output-format", "mp4",
            "-o", f"{STOCK_DIR}/clip_%(autonumber)03d.%(ext)s",
            "--restrict-filenames", "--no-playlist", "--quiet", "--no-warnings"
        ])
        clips = glob.glob(os.path.join(STOCK_DIR, "*.mp4"))
        
    if not clips:
        print("⚠️ Failed to download any clips. YT-DLP 403 error!")
        print("🔄 Falling back to AI Image generation (Pollinations)...")
        from modules.image_motion_generator import get_pollinations_image
        import urllib.parse
        img_prompt = topic['search'].replace("4k stock video free", "cinematic highly detailed")
        fallback_img = f"{STOCK_DIR}/fallback_001.jpg"
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_prompt)}?width=1080&height=1920&nologo=true"
        r = requests.get(url)
        with open(fallback_img, 'wb') as img_f:
            img_f.write(r.content)
            
        # Convert image to a 5-second mp4 clip
        fallback_clip = f"{STOCK_DIR}/fallback_clip_001.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", fallback_img, "-t", "5", 
            "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.0015,1.5)':d=150:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1080x1920",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", fallback_clip
        ])
        clips = [fallback_clip]

        
    print(f"🎬 Found {len(clips)} stock clips.")

    # 2. Generate Voice & Subtitles
    print("🎙️ Generating ElevenLabs Human Voiceover with timestamps...")
    voice_path = os.path.join(TEMP_DIR, f"master_{topic['name']}_voice.mp3")
    ass_path = os.path.join(TEMP_DIR, f"master_{topic['name']}_subs.ass")

    # FREE_ONLY mode (skill: free-unlimited-models): when YVM_FREE_ONLY=1,
    # skip paid-engine calls entirely and go straight to the free path.
    FREE_ONLY = os.environ.get("YVM_FREE_ONLY", "") == "1"

    if FREE_ONLY:
        print("🆓 FREE_ONLY=1 - skipping paid ElevenLabs engine, using free neural voice")
        resp = None
        resp_status = 0
    else:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/with-timestamps"
        headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
        data = {"text": topic['script'], "model_id": "eleven_multilingual_v2"}

        resp = requests.post(url, json=data, headers=headers)
        resp_status = resp.status_code

    if resp_status != 200:
        print("⚠️ ElevenLabs error or quota exceeded:", resp.text)
        print("🔄 Falling back to edge-tts (Free Neural Voice)...")
        # Fallback to edge-tts
        import edge_tts
        communicate = edge_tts.Communicate(topic['script'], "en-US-ChristopherNeural")
        asyncio.run(communicate.save(voice_path))
        
        # We need to simulate word timings since we don't get them from edge-tts
        # We'll just generate simple subtitles by splitting sentences
        words = []
        sentences = topic['script'].split(". ")
        # We'll calculate real duration later, but for now we just write simple ASS later
        # Actually, let's just use a basic ffmpeg drawtext or simple ASS without word-level
        fallback_audio = True
    else:
        fallback_audio = False
        j = resp.json()
        with open(voice_path, "wb") as f:
            f.write(base64.b64decode(j["audio_base64"]))


    
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", voice_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "30.0")
    print(f"⏱️ Audio duration: {duration:.2f}s")

    ass_header = f'''[Script Info]
Title: Real World Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,72,&H00FFFFFF,{topic['color']},&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,5,3,2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

    dialogues = []
    if fallback_audio:
        import textwrap
        lines = textwrap.wrap(topic['script'], width=25)
        seg_dur = duration / max(len(lines), 1)
        curr_t = 0
        for line in lines:
            start_str = format_time(curr_t)
            curr_t += seg_dur
            end_str = format_time(curr_t)
            dialogues.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{{\\c{topic['color']}&\\b1}}{line}{{\\r}}\\N\n")
    else:
        chars = j["alignment"]["characters"]
        start_times = j["alignment"]["character_start_times_seconds"]
        end_times = j["alignment"]["character_end_times_seconds"]

        words = []
        curr_word = ""
        word_start = None
        word_end = None

        for c, s, e in zip(chars, start_times, end_times):
            if c == " ":
                if curr_word:
                    words.append((curr_word, word_start, word_end))
                    curr_word = ""
                    word_start = None
            else:
                if curr_word == "":
                    word_start = s
                curr_word += c
                word_end = e

        if curr_word:
            words.append((curr_word, word_start, word_end))
            
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i+chunk_size]
            start_str = format_time(chunk[0][1])
            end_str = format_time(chunk[-1][2])
            text = " ".join([w[0] for w in chunk])
            dialogues.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{{\\c{topic['color']}&\\b1}}{text}{{\\r}}\\N\n")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "".join(dialogues))


    # 3. Create BGM — cinematic ambient chord pad (root + fifth + octave),
    # slow tremolo breathing, warm low-pass, and cathedral echo. Much richer
    # than a raw sine beep; keeps each topic's signature base frequency.
    bgm_path = os.path.join(TEMP_DIR, f"master_{topic['name']}_bgm.mp3")
    root = float(topic['bgm_freq'])
    fifth = root * 1.5
    octave = root * 2.0
    fade_out_start = max(0.0, duration - 1.0)
    bgm_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency={root}:sample_rate=48000:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency={fifth}:sample_rate=48000:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency={octave}:sample_rate=48000:duration={duration}",
        "-filter_complex",
        "[0][1][2]amix=inputs=3:weights=1 0.6 0.4,"
        "tremolo=f=0.25:d=0.8,lowpass=f=900,"
        "aecho=0.6:0.4:250|500:0.3|0.2,"
        f"volume=0.14,afade=t=in:st=0:d=1,afade=t=out:st={fade_out_start}:d=1",
        bgm_path
    ]
    bgm_result = subprocess.run(bgm_cmd, capture_output=True)
    if bgm_result.returncode != 0:
        # Simple fallback: original single sine if chord build ever fails
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"sine=frequency={topic['bgm_freq']}:sample_rate=48000:duration={duration}",
            "-af", f"volume=0.08,afade=t=in:st=0:d=0.5,afade=t=out:st={duration-0.5}:d=0.5",
            bgm_path
        ], capture_output=True)

    # 4. Prepare Segments (WITH STREAM LOOP FIX)
    segment_dur = duration / len(clips)
    prepared_clips = []
    for i, clip_path in enumerate(clips):
        out_seg = os.path.join(TEMP_DIR, f"master_{topic['name']}_seg_{i}.mp4")
        # Added -stream_loop -1 to perfectly loop short clips and prevent freezing
        cmd_seg = [
            "ffmpeg", "-y", "-stream_loop", "-1", "-ss", "0.5", "-i", clip_path, "-t", str(segment_dur),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.15:saturation=1.2",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", out_seg
        ]
        subprocess.run(cmd_seg, capture_output=True)
        prepared_clips.append(out_seg)

    concat_list = os.path.join(TEMP_DIR, f"master_{topic['name']}_concat_list.txt")
    with open(concat_list, "w") as f:
        for c in prepared_clips:
            f.write(f"file '{c}'\n")
            
    concat_video = os.path.join(TEMP_DIR, f"master_{topic['name']}_concat_video.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", concat_video
    ], capture_output=True)

    # 5. Final Render
    print("🎬 Burning ASS Subtitles & mixing audio into Final Master...")
    OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", f"REAL_WORLD_{topic['name'].upper()}_MASTER.mp4")
    ass_escaped = ass_path.replace(":", "\\:")
    cmd_final = [
        "ffmpeg", "-y", "-i", concat_video, "-i", voice_path, "-i", bgm_path, "-t", str(duration),
        "-filter_complex", f"[0:v]subtitles='{ass_escaped}'[v];[1:a][2:a]amix=inputs=2:weights=1.0 0.1[a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast", "-b:v", "8M",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", OUTPUT_VIDEO
    ]
    subprocess.run(cmd_final, capture_output=True)
    print(f"🎉 FINAL REAL-WORLD MASTER RENDERED: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
