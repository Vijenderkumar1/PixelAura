import requests
from urllib.parse import quote
from PIL import Image
import io
import time


class PollinationsProvider:

    BASE_URL = "https://image.pollinations.ai/prompt/"

    def generate(self, prompt, output_file, max_retries=3):

        url = self.BASE_URL + quote(prompt)

        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()

                # Parse downloaded image and save as compressed WebP format
                img = Image.open(io.BytesIO(response.content))
                if img.mode in ("RGBA", "LA"):
                    img = img.convert("RGB")
                img.save(output_file, "WEBP", quality=85)

                return output_file

            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    print(f"    [Retry {attempt}/{max_retries}] Pollinations API error: {e}. Retrying in {attempt * 2}s...")
                    time.sleep(attempt * 2)

        raise last_exception