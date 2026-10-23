import json
from datetime import datetime
from src.config import LOG_DIR

class RunLogger:
    def __init__(self, run_id: str):
        self.log_file = LOG_DIR / f"{run_id}.jsonl"

    def log(self, step: str, message: str, payload: dict | None = None):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "message": message,
            "payload": payload or {}
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry