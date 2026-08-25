import json
import time
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "speedtest_history.json"
MAX_HISTORY = 10


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_result(download: float, upload: float, ping: float, jitter: float) -> None:
    history = load_history()
    history.append({
        "download": download,
        "upload": upload,
        "ping": ping,
        "jitter": jitter,
        "timestamp": time.time(),
    })
    history = history[-MAX_HISTORY:]
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
