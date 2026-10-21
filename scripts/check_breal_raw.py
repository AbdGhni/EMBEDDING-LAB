"""Valide une annotation brute B-REAL.

Usage : python -I scripts/check_breal_raw.py <fichier.json>
"""

import json
import sys
from pathlib import Path

from embedding_lab.ingest.breal import assemble, contract_errors, load_meetings, validate_raw

raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
meetings = load_meetings(Path("data/processed/summre_meetings.jsonl"))
group = {k: m for k, m in meetings.items() if m["group_id"] == raw["group_id"]}
errs = validate_raw(raw, group)
if not errs:
    errs = contract_errors(assemble(raw, group, "check", "check"), group)
n_q = len(raw.get("queries", []))
print(f"{len(raw.get('units', []))} unités, {len(raw.get('relations', []))} relations, "
      f"{n_q} requêtes")
print("OK" if not errs else f"{len(errs)} erreur(s) :\n" + "\n".join(errs[:60]))
sys.exit(1 if errs else 0)
