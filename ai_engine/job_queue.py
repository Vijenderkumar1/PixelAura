import json
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "history" / "prompts.json"


class JobQueue:

    def __init__(self):
        self.jobs = self.load()

    def load(self):

        if not HISTORY_FILE.exists():
            return []

        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    def save(self):

        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(self.jobs, file, indent=4)

    def pending(self):

        return [
            job
            for job in self.jobs
            if job["status"] == "pending"
        ]

    def generating(self, job_id):

        for job in self.jobs:

            if job["id"] == job_id:

                job["status"] = "generating"

        self.save()

    def completed(self, job_id, image_name):

        for job in self.jobs:

            if job["id"] == job_id:

                job["status"] = "completed"

                job["image"] = image_name

        self.save()

    def failed(self, job_id):

        for job in self.jobs:

            if job["id"] == job_id:

                job["status"] = "failed"

        self.save()