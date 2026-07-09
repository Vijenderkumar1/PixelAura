import json
import random
from pathlib import Path
from datetime import datetime

from prompts.styles import STYLES
from prompts.quality import QUALITY
from prompts.negative import NEGATIVE

HISTORY_FILE = Path(__file__).parent / "history" / "prompts.json"

CATEGORIES = [
    "AMOLED", "Space", "Nature", "Cyberpunk", "Minimal", "Fantasy",
    "Ocean", "Galaxy", "Cars", "Forest", "Anime", "Abstract",
    "Neon", "Tech", "Texture", "Architecture", "Retro", "Pastel",
    "Aurora", "3D Render"
]

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
        "subjects": ["magical stardust swirling portal", "floating crystal island", "ancient mystical glowing tree", "dreamlike celestial palace", "floating abstract silk ribbons"],
        "backgrounds": ["mystical glowing fog", "dreamlike fairy-tale horizon sky", "ethereal starry fantasy backdrop"],
        "colors": ["lavender and gold", "shimmering fairy pink", "mystical twilight blue", "ethereal silver white"],
        "lighting": ["magical stardust shine", "soft mystical moonlight", "ethereal divine glow"],
        "effects": ["floating magical sparkles", "dreamy stardust dust clouds", "ethereal soft particles"]
    },
    "Ocean": {
        "subjects": ["underwater coral reef barrier", "bioluminescent jellyfish swarm", "mysterious deep sea trench", "majestic sea turtle silhouette", "sun rays breaking underwater"],
        "backgrounds": ["deep blue ocean abyss", "crystal clear tropical sea depths", "sunlit underwater backdrop"],
        "colors": ["aquamarine and turquoise", "indigo blue and seafoam", "coral pink and warm gold"],
        "lighting": ["caustics underwater sunlight", "soft bioluminescent glow", "deep water blue glow"],
        "effects": ["floating water bubbles", "glowing coral reflection", "deep sea particles"]
    },
    "Galaxy": {
        "subjects": ["swirling stellar cluster", "massive supernova cosmic dust", "colliding dwarf galaxies", "supermassive black hole gravitational wave", "cosmic dust cosmic web"],
        "backgrounds": ["interstellar space sky", "deep starry galaxy backdrop", "infinite cosmos dust clouds"],
        "colors": ["cosmic gold and magenta", "stellar violet and cyan", "nebula pink and deep purple"],
        "lighting": ["ambient celestial starlight", "luminous stellar core radiation", "glow of a distant star"],
        "effects": ["stellar rays", "cosmic gaseous clouds", "glowing interstellar dust particles"]
    },
    "Cars": {
        "subjects": ["futuristic hypercar concept", "classic aerodynamic muscle car", "neon-lit drift car", "sleek futuristic hovercar", "concept electric super car"],
        "backgrounds": ["wet cyber city street corner", "minimalist geometric showroom", "misty race track night sky"],
        "colors": ["crimson red and matte black", "liquid chrome silver", "neon yellow and carbon black", "electric orange"],
        "lighting": ["bright headlights reflection", "glowing underglow light", "cinematic streetlamp rim lights"],
        "effects": ["wet asphalt reflection", "motion blur light trails", "metallic glossy sheen"]
    },
    "Forest": {
        "subjects": ["giant ancient redwood trees", "enchanted mossy pathway", "sunlit wild bamboo grove", "foggy forest stream rocks", "ancient pine tree silhouettes"],
        "backgrounds": ["misty dense forest backdrop", "early morning forest canopy", "sunlit nature trail background"],
        "colors": ["moss green and deep forest brown", "golden sun rays and autumn bronze", "emerald green and silver lichen"],
        "lighting": ["dappled sunbeams hitting moss", "soft misty morning skylight", "warm sunset glowing trees"],
        "effects": ["floating forest dust particles", "ethereal fog layers", "glowing water reflections"]
    },
    "Anime": {
        "subjects": ["cyberpunk anime cityscape silhouette", "cel-shaded floating island", "retro anime mech silhouette", "mystical cherry blossom tree branches", "glowing futuristic anime terminal"],
        "backgrounds": ["vibrant pastel sky with clouds", "starry retro anime night sky", "sunset over anime city horizon"],
        "colors": ["cotton candy pink and sky blue", "electric purple and peach", "neon mint and violet"],
        "lighting": ["soft dreamy sun rays", "glow from a warm twilight horizon", "colorful ambient outline lighting"],
        "effects": ["floating cherry blossom petals", "hand-drawn cel-shaded outlines", "soft anime light bloom"]
    },
    "Abstract": {
        "subjects": ["flowing liquid glass swirls", "interacting magnetic fields force lines", "twisted chrome dimensional rings", "abstract morphing fluid blob", "complex geometric wireframe"],
        "backgrounds": ["smooth dark gradient studio background", "clean abstract studio stage", "mystic empty void"],
        "colors": ["iridescent pearl pink", "metallic teal and silver", "fluid warm gold and copper", "chrome and slate grey"],
        "lighting": ["dramatic studio keylight", "soft wrap-around highlights", "moody ambient reflections"],
        "effects": ["liquid chrome textures", "iridescent metallic surfaces", "smooth optical depth of field"]
    },
    "Neon": {
        "subjects": ["glowing neon wireframe patterns", "futuristic neon sign design", "glowing futuristic light sculptures", "cyberpunk neon triangle portal", "abstract neon helix structure"],
        "backgrounds": ["pitch black void", "dark reflective carbon floor", "mystic dark mist background"],
        "colors": ["electric hot pink", "neon cyan and blue", "acid green and lime", "saturated magenta and orange"],
        "lighting": ["intense neon glow reflections", "vibrant colored volumetric light", "flickering electric arc lights"],
        "effects": ["glowing light halos", "rain-like glossy reflections", "futuristic wireframe projections"]
    },
    "Tech": {
        "subjects": ["holographic neural circuit network", "quantum computing motherboard microchips", "nanotech self-assembling particles", "glowing fiber optic data lines", "holographic database cube"],
        "backgrounds": ["dark cyber technology laboratory", "digital data stream backdrop", "minimal dark clean server rack"],
        "colors": ["digital neon cyan", "quantum blue and teal", "clean silver chrome and black"],
        "lighting": ["bright laser beams", "data transmission pulse glow", "glow from indicators and screens"],
        "effects": ["holographic projections", "glowing circuitry grids", "digital data rain overlay"]
    },
    "Texture": {
        "subjects": ["organic crystal line structures", "macro brushed steel textures", "flowing carbon fiber weaves", "detailed golden sand waves", "cracked basalt stone geometric plates"],
        "backgrounds": ["abstract close-up details background", "minimal texture backdrop", "macro photorealistic canvas"],
        "colors": ["matte black and charcoal", "metallic copper and gold", "brushed silver grey", "earthy textured stone tones"],
        "lighting": ["grazing relief shadow light", "directional studio key highlights", "soft diffuse details light"],
        "effects": ["ultra-high micro detail textures", "brushed metallic reflections", "geometric crystal facets"]
    },
    "Architecture": {
        "subjects": ["monolithic brutalist towers", "futuristic organic skyscraper facade", "geometric minimalist concrete arches", "brutalist concrete platform over water", "futuristic clean glass dome structures"],
        "backgrounds": ["dramatic empty clear sky", "soft dusk sky horizon", "minimal concrete empty space"],
        "colors": ["concrete grey and stark white", "bronze metallic and dark charcoal", "warm gold cladding and plaster"],
        "lighting": ["dramatic sun shadows", "warm interior architectural lighting", "sharp linear silhouettes lights"],
        "effects": ["brutalist raw textures", "clean reflection facade glasses", "geometric scale shadows"]
    },
    "Retro": {
        "subjects": ["retro sunset vector sun", "80s grid mountain skyline", "chrome mountain peaks horizon", "retro sports car silhouette", "vintage cassette tape wireframe"],
        "backgrounds": ["magenta dusk synthwave sky", "outrun grid landscape horizon", "80s retro cyber wireframe grid"],
        "colors": ["synthwave magenta and purple", "neon pink and cyber orange", "vintage sunset yellow and teal"],
        "lighting": ["glowing horizontal sun rays", "retro grid laser light beams", "vibrant warm dusk glow"],
        "effects": ["retro scanlines overlay", "glitch distortion outline", "80s chrome texturing"]
    },
    "Pastel": {
        "subjects": ["soft fluffy pastel cloud formations", "simple matte ceramic block shapes", "minimalist gentle floating balloons", "soft abstract curves", "pastel stone spheres aligned"],
        "backgrounds": ["flat soft pastel gradient backdrop", "warm light pastel background", "empty minimalist studio setup"],
        "colors": ["blush peach pink", "mint green and soft sage", "lavender and lilac", "baby blue and warm beige"],
        "lighting": ["ultra-soft ambient diffusion light", "gentle shadow-free fill light", "warm morning ambient brightness"],
        "effects": ["soft matte ceramic texture", "dreamy visual blur", "clean dust-free layout"]
    },
    "Aurora": {
        "subjects": ["swirling emerald green auroral belt", "curving magenta atmospheric lights", "atmospheric wave light curtains", "aurora borealis sky lines", "northern lights sky curtains"],
        "backgrounds": ["starry cold winter night sky", "snow-covered pine forest horizon", "misty frozen lake mountains"],
        "colors": ["emerald green and turquoise", "neon magenta and violet", "cold sky blue and deep indigo"],
        "lighting": ["atmospheric auroral glowing curtains", "mystic starlight glow", "luminous sky brightness"],
        "effects": ["soft atmospheric light leak", "glowing stars dots", "auroral reflections on ice"]
    },
    "3D Render": {
        "subjects": ["sculptural glass loops", "glossy plastic interlocking objects", "floating metallic organic blobs", "minimalist architectural abstract blocks", "matte clay abstract figures"],
        "backgrounds": ["clean studio photorealistic backdrop", "empty soft rendering stage", "geometric clean studio table"],
        "colors": ["vibrant teal and warm orange", "bubblegum pink and glossy red", "liquid chrome and matte black", "vibrant violet"],
        "lighting": ["photorealistic studio keylights", "colorful ambient reflections", "clean soft rim lighting"],
        "effects": ["photorealistic octane render style", "glossy plastic material reflections", "micro depth of field blur"]
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


def get_todays_categories(cats_per_day=4):
    """
    Rotate through ALL_CATEGORIES based on today's date.
    Every day a different set of `cats_per_day` categories is chosen.
    After (len(CATEGORIES) / cats_per_day) days the full cycle repeats.
    """
    day_number = (datetime.now() - datetime(2024, 1, 1)).days
    total      = len(CATEGORIES)
    start      = (day_number * cats_per_day) % total
    # Wrap around the list if needed
    indices = [(start + i) % total for i in range(cats_per_day)]
    chosen  = [CATEGORIES[i] for i in indices]
    return chosen


def generate_prompts(count_per_category=5, categories=None):
    """
    Generate `count_per_category` unique prompts for each category in
    `categories`. If categories is None, today's rotating set is used.
    """
    if categories is None:
        categories = get_todays_categories()

    history     = load_history()
    old_prompts = {item["prompt"] for item in history}
    generated   = []

    print(f"\n[Today's categories]: {', '.join(categories)}")
    print(f"[Generating]: {count_per_category} wallpapers each = {count_per_category * len(categories)} total\n")

    for category in categories:
        category_generated = 0
        attempts = 0
        while category_generated < count_per_category and attempts < 100:
            attempts += 1
            prompt = create_prompt_for_category(category)
            if prompt in old_prompts:
                continue

            wallpaper = {
                "id":        len(history) + 1,
                "title":     f"{category} {len(history)+1:03}",
                "category":  category,
                "date":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status":    "pending",
                "provider":  "",
                "image":     "",
                "thumbnail": "",
                "uploaded":  False,
                "prompt":    prompt
            }

            history.append(wallpaper)
            generated.append(wallpaper)
            old_prompts.add(prompt)
            category_generated += 1

    save_history(history)
    return generated