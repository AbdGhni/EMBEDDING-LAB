"""EL-007b — écrit une tâche d'annotation par groupe (val et test, groupes avec réunion manuelle).

Usage : uv run python -I scripts/prepare_breal_tasks.py
Sortie (hors Git, contient les transcriptions CC BY-SA) : data/breal/tasks/<split>/<groupe>.txt
"""

import json
from collections import defaultdict
from pathlib import Path

from embedding_lab.ingest.breal import load_meetings, task_text

meetings = load_meetings(Path("data/processed/summre_meetings.jsonl"))
split_of = json.loads(Path("splits/summre_v1.json").read_text())["split_of"]
for split in ("val", "test"):
    groups = defaultdict(list)
    for mid, s in split_of.items():
        if s == split:
            groups[meetings[mid]["group_id"]].append(meetings[mid])
    out = Path("data/breal/tasks") / split
    out.mkdir(parents=True, exist_ok=True)
    kept = [g for g, ms in sorted(groups.items())
            if any(m["transcription"] == "manual" for m in ms)]
    for g in kept:
        (out / f"{g}.txt").write_text(task_text(g, groups[g]), encoding="utf-8")
    print(split, len(kept), "groupes :", " ".join(kept))
