from abc import ABC, abstractmethod


class BaseProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str, output_file: str):
        """
        Generate an image from a prompt and save it.
        """
        pass