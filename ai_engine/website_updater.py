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


def generate_rss_feed(wallpapers):
    from datetime import datetime
    import email.utils
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    # Register namespaces first to ensure proper prefixes
    ET.register_namespace("media", "http://search.yahoo.com/mrss/")
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")

    # Build the RSS XML structure
    rss = ET.Element("rss", {
        "version": "2.0"
    })
    channel = ET.SubElement(rss, "channel")

    # Channel metadata
    title = ET.SubElement(channel, "title")
    title.text = "PixelAura – 4K AI Wallpapers & Packs"

    link = ET.SubElement(channel, "link")
    link.text = "https://pixelauraw.netlify.app/"

    description = ET.SubElement(channel, "description")
    description.text = "Download stunning 4K AI-generated wallpapers and premium mobile packs for your phone, desktop, and tablet. Get instant access to free high-resolution background downloads today."

    language = ET.SubElement(channel, "language")
    language.text = "en-us"

    # Since ElementTree subelement tags with prefix need QName or specific format,
    # we can use "{http://www.w3.org/2005/Atom}link"
    atom_link = ET.SubElement(channel, "{http://www.w3.org/2005/Atom}link", {
        "href": "https://pixelauraw.netlify.app/feed.xml",
        "rel": "self",
        "type": "application/rss+xml"
    })

    last_build = ET.SubElement(channel, "lastBuildDate")
    last_build.text = email.utils.format_datetime(datetime.now())

    def format_rfc822(date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return email.utils.format_datetime(dt)
        except Exception:
            return email.utils.format_datetime(datetime.now())

    # Sort wallpapers by date descending
    sorted_wallpapers = sorted(wallpapers, key=lambda x: x.get("date", ""), reverse=True)

    for wp in sorted_wallpapers[:100]:
        item = ET.SubElement(channel, "item")

        wp_title = ET.SubElement(item, "title")
        wp_title.text = wp["title"]

        wp_link = ET.SubElement(item, "link")
        wp_link.text = f"https://pixelauraw.netlify.app/?id={wp['id']}"

        image_url = f"https://pixelauraw.netlify.app/{wp['image']}"
        mime_type = "image/webp" if image_url.endswith(".webp") else "image/png"

        wp_desc = ET.SubElement(item, "description")
        category_name = wp.get("category", "AI Generated")
        wp_desc.text = f'<img src="{image_url}" alt="{wp["title"]}" /><br/><p>Download stunning {wp["title"]} AI-generated 4K wallpaper in {category_name} style for your phone, desktop, and tablet.</p>'

        wp_pubdate = ET.SubElement(item, "pubDate")
        wp_pubdate.text = format_rfc822(wp["date"])

        wp_guid = ET.SubElement(item, "guid", {"isPermaLink": "false"})
        wp_guid.text = f"pixel-aura-wallpaper-{wp['id']}"

        ET.SubElement(item, "enclosure", {
            "url": image_url,
            "length": "0",
            "type": mime_type
        })

        # Add media:content and media:thumbnail for Pinterest / RSS scrapers
        ET.SubElement(item, "{http://search.yahoo.com/mrss/}content", {
            "url": image_url,
            "medium": "image",
            "type": mime_type
        })

        ET.SubElement(item, "{http://search.yahoo.com/mrss/}thumbnail", {
            "url": image_url
        })

    rss_xml_path = WEBSITE_DIR / "feed.xml"
    try:
        raw_xml = ET.tostring(rss, encoding="utf-8")
        parsed_xml = minidom.parseString(raw_xml)
        pretty_xml = parsed_xml.toprettyxml(indent="  ", encoding="utf-8")
        
        with open(rss_xml_path, "wb") as f:
            f.write(pretty_xml)
        print(f"Generated RSS feed: {rss_xml_path.name} with {len(sorted_wallpapers[:100])} items.")
    except Exception as e:
        print(f"Error generating RSS feed: {e}")


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

    # Generate RSS feed
    generate_rss_feed(wallpapers)

    # Generate bundles
    BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    CATEGORIES = [
        "AMOLED", "Space", "Nature", "Cyberpunk", "Minimal", "Fantasy",
        "Ocean", "Galaxy", "Cars", "Forest", "Anime", "Abstract",
        "Neon", "Tech", "Texture", "Architecture", "Retro", "Pastel",
        "Aurora", "3D Render", "Krishna"
    ]

    for cat in CATEGORIES:
        cat_lower = cat.lower().replace(" ", "_")
        cat_wallpapers = [w for w in wallpapers if w["category"].lower() == cat.lower()]
        create_zip_bundle(BUNDLES_DIR / f"{cat_lower}_pack.zip", cat_wallpapers)

    create_zip_bundle(BUNDLES_DIR / "ultimate_bundle.zip", wallpapers)