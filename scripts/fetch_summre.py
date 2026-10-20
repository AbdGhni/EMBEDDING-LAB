"""EL-007 — acquisition de SUMM-RE (texte seul, révision figée) puis reconstruction des réunions.

Usage :
    uv run python -I scripts/fetch_summre.py --out data/raw/summre --processed data/processed

Sorties (hors Git) :
    data/raw/summre/tracks_{dev,test,train}.jsonl + manifest.json
    data/processed/summre_meetings.jsonl + summre_meetings.manifest.json
"""

import argparse
import json
from pathlib import Path

from embedding_lab.ingest.summre import (
    OFFICIAL_SPLITS,
    REVISION,
    build_meetings,
    fetch_tracks,
    read_jsonl,
    sha256_file,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/raw/summre"))
    ap.add_argument("--processed", type=Path, default=Path("data/processed"))
    ap.add_argument("--revision", default=REVISION)
    ap.add_argument("--skip-fetch", action="store_true",
                    help="réutiliser les pistes déjà téléchargées")
    ap.add_argument("--merge-gap", type=float, default=1.0)
    args = ap.parse_args()

    if not args.skip_fetch:
        manifest = fetch_tracks(args.out, args.revision)
        print(json.dumps(manifest["files"], indent=1))

    records = [r for s in OFFICIAL_SPLITS for r in read_jsonl(args.out / f"tracks_{s}.jsonl")]
    meetings = build_meetings(records, merge_gap=args.merge_gap)
    args.processed.mkdir(parents=True, exist_ok=True)
    path = args.processed / "summre_meetings.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for m in meetings:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    stats = {
        "source_revision": args.revision,
        "merge_gap_s": args.merge_gap,
        "meetings": len(meetings),
        "groups": len({m["group_id"] for m in meetings}),
        "turns": sum(len(m["turns"]) for m in meetings),
        "chars": sum(len(m["text"]) for m in meetings),
        "sha256": sha256_file(path),
    }
    (args.processed / "summre_meetings.manifest.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
