import requests
from urllib.parse import quote


class PollinationsProvider:

    BASE_URL = "https://image.pollinations.ai/prompt/"

    def generate(self, prompt, output_file):

        url = self.BASE_URL + quote(prompt)

        response = requests.get(url, timeout=300)

        response.raise_for_status()

        with open(output_file, "wb") as file:

            file.write(response.content)

        return output_file