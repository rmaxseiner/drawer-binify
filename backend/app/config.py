import os
from pathlib import Path

class Settings:
    BASE_DIR = Path(__file__).resolve().parent.parent
    MODEL_OUTPUT_DIR = os.getenv("MODEL_OUTPUT_DIR", str(BASE_DIR / "model-output"))
    MODEL_OUTPUT_URL_PATH = "/files"

settings = Settings()