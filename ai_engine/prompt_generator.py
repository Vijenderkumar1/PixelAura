import json
import random
from pathlib import Path
from datetime import datetime

from prompts.colors import COLORS
from prompts.subjects import SUBJECTS
from prompts.styles import STYLES
from prompts.lighting import LIGHTING
from prompts.backgrounds import BACKGROUNDS
from prompts.effects import EFFECTS
from prompts.quality import QUALITY
from prompts.negative import NEGATIVE

HISTORY_FILE = Path(__file__).parent / "history" / "prompts.json"


def load_history():

    if HISTORY_FILE.exists():

        with open(HISTORY_FILE, "r", encoding="utf-8") as file:

            return json.load(file)

    return []


def save_history(history):

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:

        json.dump(history, file, indent=4)


def create_prompt():

    color = random.choice(COLORS)

    subject = random.choice(SUBJECTS)

    style = random.choice(STYLES)

    lighting = random.choice(LIGHTING)

    background = random.choice(BACKGROUNDS)

    effect = random.choice(EFFECTS)

    quality = ", ".join(QUALITY)

    negative = ", ".join(NEGATIVE)

    return (
        f"{style} {subject} with {color} accents on {background}, "
        f"{lighting}, {effect}, "
        f"{quality}, {negative}"
    )


def generate_prompts(count=10):

    history = load_history()

    old_prompts = {item["prompt"] for item in history}

    generated = []

    while len(generated) < count:

        prompt = create_prompt()

        if prompt in old_prompts:

            continue

        wallpaper = {

            "id": len(history) + 1,

            "title": f"AMOLED {len(history)+1:03}",

            "category": "AMOLED",

            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "status": "pending",

            "provider": "",

            "image": "",

            "thumbnail": "",

            "uploaded": False,

            "prompt": prompt

        }

        history.append(wallpaper)

        generated.append(wallpaper)

        old_prompts.add(prompt)

    save_history(history)

    return generated