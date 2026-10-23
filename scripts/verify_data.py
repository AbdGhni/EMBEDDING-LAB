"""Vérifie que les données régénérées (Colab, autre machine) sont identiques à celles de la
VM de référence. Usage : python -I scripts/verify_data.py [--write]"""

import argparse
import hashlib
import json
from pathlib import Path

FILES = [
    "data/processed/summre_meetings.jsonl",
    *[f"data/bsyn/{s}/{k}" for s in ("train", "val", "test")
      for k in ("units.jsonl", "queries.jsonl", "qrels.json", "triplets.jsonl")],
    *[f"data/breal/{s}/{k}" for s in ("train", "val", "test")
      for k in ("units.jsonl", "queries.jsonl", "qrels.json", "triplets.jsonl")],
    "data/train/e2_hard.jsonl", "data/train/e3_random.jsonl", "data/train/e2_bsyn_only.jsonl",
]
EXPECTED = Path("splits/data_sha256.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="enregistrer les empreintes attendues")
    args = ap.parse_args()
    got = {f: hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in FILES if Path(f).exists()}
    if args.write:
        EXPECTED.write_text(json.dumps(got, indent=1) + "\n")
        print(f"{len(got)} empreintes écrites dans {EXPECTED}")
        return
    want = json.loads(EXPECTED.read_text())
    bad = [f for f in want if got.get(f) != want[f]]
    print("OK : données identiques" if not bad else f"DIFFÉRENCES : {bad}")
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
