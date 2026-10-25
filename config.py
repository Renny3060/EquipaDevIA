from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = BASE_DIR / "projetos"
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_NUM_CTX = 8192
TEMPERATURE = 0.2
MAX_FILES = 30