import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

MT5_HOST = os.getenv("MT5_HOST", "127.0.0.1")
MT5_PULL_PORT = int(os.getenv("MT5_PULL_PORT", "15555"))
MT5_SUB_PORT = int(os.getenv("MT5_SUB_PORT", "15556"))

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///trading_dashboard.db")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
