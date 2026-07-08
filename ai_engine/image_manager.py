from config import IMAGE_PROVIDER


class ImageManager:

    def __init__(self):

        self.provider = IMAGE_PROVIDER

    def generate(self, prompt, output_file):

        if self.provider == "pollinations":

            from providers.pollinations_provider import PollinationsProvider

            provider = PollinationsProvider()

            return provider.generate(prompt, output_file)

        raise Exception(f"Provider '{self.provider}' not supported.")