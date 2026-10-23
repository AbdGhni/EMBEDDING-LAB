"""EL-019 — écrit I-SYN (train/val/test) dans data/intents/ et affiche les empreintes.

Usage : uv run python -I scripts/make_intents.py
"""

import hashlib
import json
from pathlib import Path

from embedding_lab.intents.data import generate

PER_FAMILY = 60


def main() -> None:
    out = Path("data/intents")
    out.mkdir(parents=True, exist_ok=True)
    texts = {}
    for split in ("train", "val", "test"):
        rows = generate(split, PER_FAMILY)
        texts[split] = {r["text"].lower().strip(" .?") for r in rows}
        blob = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
        (out / f"{split}.jsonl").write_text(blob, encoding="utf-8")
        print(split, len(rows), hashlib.sha256(blob.encode()).hexdigest())
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        shared = texts[a] & texts[b]
        if shared:
            raise SystemExit(f"textes partagés entre {a} et {b} : {sorted(shared)[:5]}")
    print("aucun texte partagé entre splits")


if __name__ == "__main__":
    main()
