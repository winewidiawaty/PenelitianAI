import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / ".cache"
LOG_DIR = BASE_DIR / "logs"

for folder in [OUTPUT_DIR, CACHE_DIR, LOG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD-K_z9BZFt_e1-eK8ABFA1SlpxygxFJVs")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.8-flash-lite")
MAX_LLM_CALLS = int(os.getenv("MAX_LLM_CALLS", "60"))
S2_API_KEY = os.getenv("S2_API_KEY", "")