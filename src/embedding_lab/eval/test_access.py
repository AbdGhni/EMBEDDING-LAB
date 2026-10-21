"""Journal append-only des accès au test (protocole v1.0, § 7).

Toute fonction qui lit des requêtes ou pertinences de test doit d'abord appeler
``log_test_access`` ; sans motif, l'accès est refusé.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_LOG = Path("runs/TEST_ACCESS.log")


def log_test_access(run_id: str, reason: str, benchmark: str, log_path: Path = DEFAULT_LOG) -> dict:
    if not reason.strip():
        raise PermissionError("accès au test refusé : motif obligatoire")
    entry = {
        "time": datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds"),
        "run_id": run_id,
        "benchmark": benchmark,
        "reason": reason,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry
