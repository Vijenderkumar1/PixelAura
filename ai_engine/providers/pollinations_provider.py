import requests
from urllib.parse import quote
from PIL import Image
import io


class PollinationsProvider:

    BASE_URL = "https://image.pollinations.ai/prompt/"

    def generate(self, prompt, output_file):

        url = self.BASE_URL + quote(prompt)

        response = requests.get(url, timeout=300)

        response.raise_for_status()

        # Parse downloaded image and save as compressed WebP format
        img = Image.open(io.BytesIO(response.content))
        if img.mode in ("RGBA", "LA"):
            img = img.convert("RGB")
        img.save(output_file, "WEBP", quality=85)

        return output_file