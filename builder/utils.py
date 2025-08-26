from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
RAW = CACHE / "raw"
TEXT = CACHE / "text"
SITE_DATA = ROOT / "site" / "data"

def ensure_dirs() -> None:
    # 필요 폴더 생성 (들여쓰기 주의)
    for p in (CACHE, RAW, TEXT, SITE_DATA):
        p.mkdir(parents=True, exist_ok=True)

ensure_dirs()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
