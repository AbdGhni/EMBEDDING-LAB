"""EL-008 — splits SUMM-RE par composante de personnes, puis rapport de fuites.

Usage :
    uv run python -I scripts/make_splits.py

Sortie versionnée (identifiants seulement, aucun texte) : splits/summre_v1.json
"""

import argparse
import collections
import hashlib
import json
from pathlib import Path

from embedding_lab.data.splits import assign_splits, group_components, leakage_report

TARGETS = {  # ~20 % des réunions manuelles en test, ~15 % en validation
    "test": {"manual": 15, "manual_decision": 5},
    "val": {"manual": 11, "manual_decision": 4},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meetings", type=Path, default=Path("data/processed/summre_meetings.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("splits/summre_v1.json"))
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--trials", type=int, default=20000)
    args = ap.parse_args()

    raw = args.meetings.read_bytes()
    meetings = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    split_of = assign_splits(meetings, TARGETS, seed=args.seed, trials=args.trials)
    report = leakage_report(meetings, split_of)

    stats = collections.defaultdict(collections.Counter)
    for m in meetings:
        s = split_of[m["meeting_id"]]
        stats[s]["meetings"] += 1
        stats[s][f"{m['transcription']}_{m['meeting_type']}"] += 1
        stats[s][f"scenario_{m['scenario']}"] += 1
    groups = collections.defaultdict(set)
    for m in meetings:
        groups[split_of[m["meeting_id"]]].add(m["group_id"])

    out = {
        "version": "summre_v1",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "seed": args.seed,
        "trials": args.trials,
        "targets": TARGETS,
        "unit": "connected component of experiment groups sharing a speaker id",
        "n_components": len(group_components(meetings)),
        "stats": {s: dict(sorted(c.items())) for s, c in sorted(stats.items())},
        "groups": {s: sorted(g) for s, g in sorted(groups.items())},
        "leakage": report,
        "split_of": dict(sorted(split_of.items())),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(out, indent=1, ensure_ascii=False)
    args.out.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_components", "stats", "leakage")}, indent=1))
    print("sha256(splits):", hashlib.sha256((text + "\n").encode()).hexdigest())


if __name__ == "__main__":
    main()
