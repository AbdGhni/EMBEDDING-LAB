"""EL-007b — assemble les annotations brutes B-REAL en benchmark (val et test).

Usage : uv run python -I scripts/assemble_breal.py [--splits val test]
Sorties (hors Git, régénérables depuis annotations/) : data/breal/<split>/{units,relations,
queries,triplets}.jsonl, qrels.json ; data/breal/manifest.json.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from embedding_lab.ingest.breal import assemble, contract_errors, load_meetings, validate_raw


def dump(path: Path, rows) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows, dict):
        text = json.dumps(rows, ensure_ascii=False, indent=0, sort_keys=True) + "\n"
    else:
        text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", nargs="+", default=["val", "test"])
    ap.add_argument("--out", type=Path, default=Path("data/breal"))
    args = ap.parse_args()
    meetings = load_meetings(Path("data/processed/summre_meetings.jsonl"))
    split_of = json.loads(Path("splits/summre_v1.json").read_text())["split_of"]
    manifest_path = args.out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for split in args.splits:
        tasks = sorted(p.stem for p in (Path("data/breal/tasks") / split).glob("*.txt"))
        missing = [g for g in tasks if not Path(f"annotations/breal/raw/{g}.json").exists()]
        if missing:
            raise SystemExit(f"{split} : annotations manquantes {missing}")
        agg = {"units": [], "relations": [], "queries": [], "triplets": [], "qrels": {}}
        raw_hashes = {}
        for g in tasks:
            path = Path(f"annotations/breal/raw/{g}.json")
            raw = json.loads(path.read_text(encoding="utf-8"))
            group = {k: m for k, m in meetings.items() if m["group_id"] == g}
            assert all(split_of[k] == split for k in group), f"groupe {g} hors du split {split}"
            errs = validate_raw(raw, group)
            out = assemble(raw, group, split, f"claude-subagent:EL-007b:{g}")
            errs += contract_errors(out, group)
            if errs:
                raise SystemExit(f"{g} : {errs[:5]}")
            for k in ("units", "relations", "queries", "triplets"):
                agg[k] += out[k]
            agg["qrels"].update(out["qrels"])
            raw_hashes[g] = hashlib.sha256(path.read_bytes()).hexdigest()
        files = {k: dump(args.out / split / f"{k}.jsonl", agg[k])
                 for k in ("units", "relations", "queries", "triplets")}
        files["qrels"] = dump(args.out / split / "qrels.json", agg["qrels"])
        manifest[split] = {
            "groups": tasks, "units": len(agg["units"]),
            "units_by_type": dict(Counter(u["type"] for u in agg["units"])),
            "relations": dict(Counter(r["relation"] for r in agg["relations"])),
            "queries": len(agg["queries"]),
            "answerable": sum(q["answerable"] for q in agg["queries"]),
            "triplets": dict(Counter(t["trap"] for t in agg["triplets"])),
            "raw_sha256": raw_hashes, "sha256": files,
        }
        print(split, json.dumps({k: v for k, v in manifest[split].items()
                                 if k not in ("raw_sha256", "sha256")}, ensure_ascii=False))
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
