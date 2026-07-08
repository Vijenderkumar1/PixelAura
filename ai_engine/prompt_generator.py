import json
import random
from pathlib import Path
from datetime import datetime

from prompts.styles import STYLES
from prompts.quality import QUALITY
from prompts.negative import NEGATIVE

HISTORY_FILE = Path(__file__).parent / "history" / "prompts.json"

CATEGORIES = ["AMOLED", "Space", "Nature", "Cyberpunk", "Minimal", "Fantasy"]

CATEGORY_ASSETS = {
    "AMOLED": {
        "subjects": ["liquid metal flow", "sleek glass ribbons", "hexagonal grid patterns", "sharp crystal shards", "minimal geometric structures", "energy ripples"],
        "backgrounds": ["deep black backdrop", "deep AMOLED black", "matte black surface", "pitch black background"],
        "colors": ["neon blue", "luxurious gold", "emerald green", "vibrant magenta", "neon cyan"],
        "lighting": ["neon glowing elements", "dramatic rim lighting", "bright edge highlights", "cyber glow"],
        "effects": ["high contrast reflections", "subtle metallic sheen", "luminous glow"]
    },
    "Space": {
        "subjects": ["stellar nebula clouds", "distant spiral galaxy", "cosmic dust clouds", "massive glowing black hole", "stellar star cluster", "interstellar cosmic energy"],
        "backgrounds": ["deep space cosmos", "starry cosmic backdrop", "vast dark universe filled with stars"],
        "colors": ["deep purple and indigo", "electric blue and magenta", "cosmic gold and silver", "violet and stellar dust"],
        "lighting": ["distant stellar glow", "supernova ambient light", "mystic starlight"],
        "effects": ["nebula gas dust clouds", "magical floating stardust", "glowing stellar particles"]
    },
    "Nature": {
        "subjects": ["misty forest morning trees", "ocean waves crashing at sunset", "autumn leaves falling in wind", "morning dew drops on green leaves", "cascading waterfall in deep forest"],
        "backgrounds": ["soft blurred nature background", "misty natural fog horizon", "beautiful outdoor sunset glow"],
        "colors": ["emerald green and forest teal", "golden hour orange and yellow", "ocean blue and seafoam", "warm earth tones"],
        "lighting": ["soft morning sun rays", "warm golden hour lighting", "dappled forest tree sunlight"],
        "effects": ["soft natural bokeh", "glowing dew reflections", "ethereal morning mist"]
    },
    "Cyberpunk": {
        "subjects": ["futuristic neon skyscraper outline", "glowing hologram city map", "cybernetic interface lines", "neon circuit board grid", "cyber vehicle light trails"],
        "backgrounds": ["dark rainy city street at night", "futuristic terminal room with displays", "neon illuminated dark alleyway"],
        "colors": ["neon pink and cyan", "cyber orange and purple", "bright neon green and violet", "electric blue and red"],
        "lighting": ["flickering neon streetlamps", "bright holographic projections", "vibrant cyber glow"],
        "effects": ["rain puddles reflections", "digital noise scanlines", "futuristic glowing HUD overlays"]
    },
    "Minimal": {
        "subjects": ["simple abstract 3d sphere", "minimalist curved ribbon curve", "geometric circle design", "clean thin lines", "shadow geometry"],
        "backgrounds": ["clean solid colored studio backdrop", "soft gray minimalist surface", "empty neutral background"],
        "colors": ["pastel pink", "muted soft blue", "warm minimalist beige", "monochrome slate gray", "matte white"],
        "lighting": ["soft studio diffusion light", "clean sharp directional shadow", "ambient fill light"],
        "effects": ["smooth matte textures", "clean clean aesthetic", "minimalist visual depth"]
    },
    "Fantasy": {
        "subjects": ["magical stardust swirling portal", "floating crystal shards island", "ancient mystical glowing tree", "dreamlike celestial palace", "floating abstract silk ribbons"],
        "backgrounds": ["mystical glowing fog", "dreamlike fairy-tale horizon sky", "ethereal starry fantasy backdrop"],
        "colors": ["lavender and gold", "shimmering fairy pink", "mystical twilight blue", "ethereal silver white"],
        "lighting": ["magical stardust shine", "soft mystical moonlight", "ethereal divine glow"],
        "effects": ["floating magical sparkles", "dreamy stardust dust clouds", "ethereal soft particles"]
    }
}


def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)


def create_prompt_for_category(category):
    assets = CATEGORY_ASSETS[category]
    subject = random.choice(assets["subjects"])
    background = random.choice(assets["backgrounds"])
    color = random.choice(assets["colors"])
    lighting = random.choice(assets["lighting"])
    effect = random.choice(assets["effects"])
    style = random.choice(STYLES)
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
        category = random.choice(CATEGORIES)
        prompt = create_prompt_for_category(category)
        if prompt in old_prompts:
            continue

        wallpaper = {
            "id": len(history) + 1,
            "title": f"{category} {len(history)+1:03}",
            "category": category,
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