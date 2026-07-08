import json
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "history" / "prompts.json"

WEBSITE_JSON = (
    Path(__file__).parent.parent
    / "website"
    / "data"
    / "wallpapers.json"
)


def update_website():

    if not HISTORY_FILE.exists():
        print("History file not found.")
        return

    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        history = json.load(file)

    wallpapers = []

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