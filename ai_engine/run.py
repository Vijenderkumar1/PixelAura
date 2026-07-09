from pathlib import Path

from prompt_generator import generate_prompts, get_todays_categories
from job_queue import JobQueue
from image_manager import ImageManager
from website_updater import update_website

print("=" * 60)
print("        PixelAura AI Engine v2.0")
print("  [Rotating] Daily rotation: 4 categories x 5 images = 20/day")
print("=" * 60)

# Auto-select today's 4 categories from the 20-category rotation
# Every 5 days the full cycle completes. No repeats across days.
generate_prompts(count_per_category=5)  # categories=None → auto picks today's 4

queue = JobQueue()
manager = ImageManager()

pending = queue.pending()

print(f"\nPending Jobs : {len(pending)}\n")

output_dir = (
    Path(__file__).parent.parent
    / "website"
    / "assets"
    / "images"
    / "generated"
)

output_dir.mkdir(parents=True, exist_ok=True)

for job in pending:

    category_slug = job["category"].lower().replace(" ", "_")
    filename = f"{category_slug}_{job['id']:04}.png"

    print(f"Generating {job['title']} ({job['category']})...")

    queue.generating(job["id"])

    output_file = output_dir / filename

    try:

        manager.generate(job["prompt"], str(output_file))

        queue.completed(job["id"], filename)

        print(f"[SUCCESS] {filename}")

    except Exception as e:

        queue.failed(job["id"])

        print(e)

print("\nUpdating website database...\n")

update_website()

print("\nEngine Finished Successfully!")