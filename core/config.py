import os
from pathlib import Path
from dotenv import load_dotenv

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env ONLY ONCE (stable for uvicorn reload)
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# Read API key safely
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Optional debug (remove later if you want)
if not ANTHROPIC_API_KEY:
    print("⚠️ WARNING: ANTHROPIC_API_KEY not loaded")