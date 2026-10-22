"""EL-012 — construit les exemples E2 (négatifs difficiles) et E3 (négatifs aléatoires).

Usage : uv run python -I scripts/build_training_data.py [--no-breal] [--mine-k 20]
Sorties (hors Git) : data/train/{e2_hard,e3_random}.jsonl + data/train/manifest.json
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from embedding_lab.train.data import build_examples, random_negative_variant


def read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load(base: Path):
    units = {u["unit_id"]: u for u in read(base / "units.jsonl")}
    queries = [q for q in read(base / "queries.jsonl") if q["answerable"]]
    qrels = json.loads((base / "qrels.json").read_text(encoding="utf-8"))
    return units, queries, qrels, read(base / "triplets.jsonl")


def mine_with_e1(units, queries, qrels, k: int) -> dict[str, list[str]]:
    """Négatifs extraits par l'encodeur initial, **sur le train uniquement**."""
    import numpy as np

    from embedding_lab.retrieval.dense import DenseRetriever

    enc = DenseRetriever()
    ids = list(units)
    mat = enc._units([units[i] for i in ids])
    qv = enc._encode(["query: " + q["text"] for q in queries])
    sims = qv @ mat.T
    out = {}
    for q, row in zip(queries, sims, strict=True):
        rel = qrels[q["query_id"]]
        order = np.argsort(-row)
        out[q["query_id"]] = [ids[j] for j in order if rel.get(ids[j], 0) == 0][:k]
    return out


def dump(path: Path, rows) -> str:
    text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-breal", action="store_true")
    ap.add_argument("--mine-k", type=int, default=20)
    ap.add_argument("--max-neg-per-pos", type=int, default=3)
    ap.add_argument("--out", type=Path, default=Path("data/train"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    hard, pools, all_qrels, inputs = [], {}, {}, {}
    su, sq, sr, st = load(Path("data/bsyn/train"))
    mined = mine_with_e1(su, sq, sr, args.mine_k)
    hard += build_examples(sq, sr, su, st, "bsyn", mined=mined,
                           max_neg_per_pos=args.max_neg_per_pos)
    pools["bsyn"] = list(su.values())
    all_qrels.update(sr)
    inputs["bsyn"] = hashlib.sha256(Path("data/bsyn/train/qrels.json").read_bytes()).hexdigest()
    breal = Path("data/breal/train")
    if not args.no_breal:
        if not (breal / "qrels.json").exists():
            raise SystemExit("B-REAL train absent : lancer assemble_breal.py --splits train "
                             "ou passer --no-breal")
        ru, rq, rr, rt = load(breal)
        hard += build_examples(rq, rr, ru, rt, "breal", max_neg_per_pos=args.max_neg_per_pos)
        pools["breal"] = list(ru.values())
        all_qrels.update(rr)
        inputs["breal"] = hashlib.sha256((breal / "qrels.json").read_bytes()).hexdigest()
    rnd = random_negative_variant(hard, pools, all_qrels, seed=0)
    manifest = {
        "inputs_qrels_sha256": inputs, "mine_k": args.mine_k,
        "max_neg_per_pos": args.max_neg_per_pos,
        "e2_hard": {"n": len(hard), "sha256": dump(args.out / "e2_hard.jsonl", hard),
                    "by_source": dict(Counter(e["source"] for e in hard)),
                    "by_neg_origin": dict(Counter(e["neg_origin"] for e in hard)),
                    "clusters": len({e["cluster"] for e in hard})},
        "e3_random": {"n": len(rnd), "sha256": dump(args.out / "e3_random.jsonl", rnd)},
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
