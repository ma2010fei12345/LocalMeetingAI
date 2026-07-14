from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "local-data"
UPLOAD_DIR = DATA_DIR / "uploads"
ENCRYPTED_DIR = DATA_DIR / "encrypted"
CHROMA_DIR = DATA_DIR / "chroma"
DB_PATH = DATA_DIR / "localmeetingai.db"
KEY_PATH = DATA_DIR / "key.bin"

DEFAULT_PROJECT_NAME = "默认项目"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120


def ensure_data_dirs() -> None:
    for path in (DATA_DIR, UPLOAD_DIR, ENCRYPTED_DIR, CHROMA_DIR):
        path.mkdir(parents=True, exist_ok=True)
