from pathlib import Path

from image_manager import ImageManager

prompt = (
    "Premium AMOLED wallpaper, black background, purple neon glass ribbons, "
    "8K, smartphone wallpaper, no text"
)

output = (
    Path(__file__).parent.parent
    / "website"
    / "assets"
    / "images"
    / "generated"
    / "test.png"
)

manager = ImageManager()

manager.generate(prompt, output)

print("Wallpaper generated successfully!")