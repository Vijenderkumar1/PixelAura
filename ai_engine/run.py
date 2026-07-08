from pathlib import Path

from prompt_generator import generate_prompts
from job_queue import JobQueue
from image_manager import ImageManager
from website_updater import update_website

print("=" * 60)
print("        PixelAura AI Engine v1.0")
print("=" * 60)

generate_prompts()

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

    print(f"Generating {job['title']}...")

    queue.generating(job["id"])

    filename = f"amoled_{job['id']:04}.png"

    output_file = output_dir / filename

    try:

        manager.generate(job["prompt"], str(output_file))

        queue.completed(job["id"], filename)

        print(f"✓ {filename}")

    except Exception as e:

        queue.failed(job["id"])

        print(e)

print("\nUpdating website database...\n")

update_website()

print("\nEngine Finished Successfully!")