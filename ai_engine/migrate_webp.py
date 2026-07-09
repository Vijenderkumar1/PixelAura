import json
import os
from pathlib import Path
from PIL import Image
from website_updater import update_website

print("=" * 60)
print("     PixelAura PNG-to-WebP Asset Migration Script")
print("=" * 60)

HISTORY_FILE = Path(__file__).parent / "history" / "prompts.json"
img_dir = Path(__file__).parent.parent / "website" / "assets" / "images" / "generated"

if not HISTORY_FILE.exists():
    print("Error: prompts.json not found!")
    exit(1)

with open(HISTORY_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

migrated_count = 0
space_saved = 0

print("Converting assets... this may take a few seconds.")

for job in jobs:
    if job.get("image") and job["image"].endswith(".png"):
        png_filename = job["image"]
        png_filepath = img_dir / png_filename
        
        if png_filepath.exists():
            webp_filename = png_filename.replace(".png", ".webp")
            webp_filepath = img_dir / webp_filename
            
            try:
                # Get initial file size for savings calculation
                png_size = png_filepath.stat().st_size
                
                # Convert to WebP format
                with Image.open(png_filepath) as img:
                    if img.mode in ("RGBA", "LA"):
                        img = img.convert("RGB")
                    img.save(webp_filepath, "WEBP", quality=85)
                
                # Delete the original PNG file
                os.remove(png_filepath)
                
                # Calculate space savings
                webp_size = webp_filepath.stat().st_size
                savings = png_size - webp_size
                space_saved += savings
                
                # Update prompts.json database values
                job["image"] = webp_filename
                migrated_count += 1
                
                print(f"[SUCCESS] Migrated {png_filename} -> {webp_filename} (Saved {savings/1024:.1f} KB)")
                
            except Exception as e:
                print(f"[FAILED] Failed to migrate {png_filename}: {e}")

if migrated_count > 0:
    # Save the updated history database
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4)
    
    print("\nHistory file prompts.json updated successfully.")
    print(f"Total files migrated: {migrated_count}")
    print(f"Total storage space saved: {space_saved / (1024*1024):.2f} MB")
    
    print("\nRebuilding website database and ZIP archives...")
    update_website()
    print("Database and ZIP archives rebuilt successfully.")
else:
    print("\nNo PNG files needed migration.")

print("\nMigration finished successfully!")
