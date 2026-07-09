import json
import zipfile
from pathlib import Path

# Paths
HISTORY_FILE = Path(__file__).parent / "history" / "prompts.json"
WEBSITE_DIR = Path(__file__).parent.parent / "website"
WEBSITE_JSON = WEBSITE_DIR / "data" / "wallpapers.json"
BUNDLES_DIR = WEBSITE_DIR / "assets" / "bundles"
IMAGES_DIR = WEBSITE_DIR / "assets" / "images" / "generated"


def get_category_by_subject(prompt_text):
    prompt_lower = prompt_text.lower()
    if "nebula" in prompt_lower:
        return "Space"
    elif "particles" in prompt_lower or "smoke" in prompt_lower:
        return "Minimal"
    elif "electric" in prompt_lower or "hexagonal" in prompt_lower or "energy" in prompt_lower:
        return "Cyberpunk"
    elif "crystal" in prompt_lower or "glass" in prompt_lower or "silk" in prompt_lower:
        return "Fantasy"
    elif "liquid" in prompt_lower:
        return "Nature"
    else:
        return "AMOLED"


def create_zip_bundle(zip_path, wallpaper_list):
    if not wallpaper_list:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.writestr("info.txt", "No wallpapers generated for this pack yet.")
        return

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for wp in wallpaper_list:
            image_filename = wp["image"].split("/")[-1]
            source_file = IMAGES_DIR / image_filename
            if source_file.exists():
                zipf.write(source_file, arcname=image_filename)
    print(f"Created bundle: {zip_path.name} with {len(wallpaper_list)} images.")


def update_website():
    if not HISTORY_FILE.exists():
        print("History file not found.")
        return

    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        history = json.load(file)

    wallpapers = []
    history_updated = False

    # Migrate older AMOLED wallpapers to dynamic categories,
    # but preserve correct category for newly generated wallpapers
    for item in history:
        category = item.get("category", "")
        # If the category is AMOLED but the title matches AMOLED 0xx (indicating it's from the old run),
        # migrate it dynamically to diversify the starting library.
        if not category or category == "AMOLED":
            title = item.get("title", "")
            # Only migrate older numbered wallpapers (e.g. "AMOLED 001" to "AMOLED 070")
            # to prevent overwriting new category-specific generations
            try:
                num_part = int(title.split()[-1])
                if num_part <= 70:
                    prompt = item.get("prompt", "")
                    new_category = get_category_by_subject(prompt)
                    if category != new_category:
                        item["category"] = new_category
                        item["title"] = f"{new_category} {num_part:03}"
                        history_updated = True
            except (ValueError, IndexError):
                pass

    if history_updated:
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)

    for item in history:
        if item["status"] != "completed":
            continue

        wallpapers.append({
            "id": item["id"],
            "title": item["title"],
            "category": item["category"],
            "image": f"assets/images/generated/{item['image']}",
            "download": f"assets/images/generated/{item['image']}",
            "provider": item["provider"],
            "date": item["date"]
        })

    WEBSITE_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(WEBSITE_JSON, "w", encoding="utf-8") as file:
        json.dump(wallpapers, file, indent=4)

    print(f"Website updated with {len(wallpapers)} wallpapers.")

    # Generate bundles
    BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    CATEGORIES = [
        "AMOLED", "Space", "Nature", "Cyberpunk", "Minimal", "Fantasy",
        "Ocean", "Galaxy", "Cars", "Forest", "Anime", "Abstract",
        "Neon", "Tech", "Texture", "Architecture", "Retro", "Pastel",
        "Aurora", "3D Render"
    ]

    for cat in CATEGORIES:
        cat_lower = cat.lower().replace(" ", "_")
        cat_wallpapers = [w for w in wallpapers if w["category"].lower() == cat.lower()]
        create_zip_bundle(BUNDLES_DIR / f"{cat_lower}_pack.zip", cat_wallpapers)

    create_zip_bundle(BUNDLES_DIR / "ultimate_bundle.zip", wallpapers)