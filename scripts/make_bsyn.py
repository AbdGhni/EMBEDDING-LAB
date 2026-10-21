"""EL-007c — génère B-SYN (train/val/test), valide chaque contrat et contrôle les fuites.

Usage :
    uv run python -I scripts/make_bsyn.py --out data/bsyn

Sorties (hors Git, régénérables à l'identique) : data/bsyn/<split>/{meetings,units,relations,
queries,triplets}.jsonl, qrels.json ; data/bsyn/manifest.json (effectifs, empreintes, contrôles).
"""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from embedding_lab.schemas import check_relation, check_unit
from embedding_lab.synth.bsyn import generate_split

PLAN = {"train": (240, 2024), "val": (32, 2025), "test": (48, 2026)}  # protocole v1.1
WORD = re.compile(r"\w+", re.UNICODE)


def dump(path: Path, rows) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(rows, dict):
        text = json.dumps(rows, ensure_ascii=False, indent=0, sort_keys=True) + "\n"
    else:
        text = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode()).hexdigest()


def grams(texts, n: int) -> set:
    out = set()
    for t in texts:
        toks = WORD.findall(t.lower())
        out |= {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}
    return out


def strip_entities(text: str, entities: set[str]) -> str:
    for e in sorted(entities, key=len, reverse=True):
        text = text.replace(e, " ")
    return re.sub(r"\d[\d  ]*", " ", text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/bsyn"))
    args = ap.parse_args()
    data = {s: generate_split(s, n, seed) for s, (n, seed) in PLAN.items()}
    manifest = {"plan": PLAN, "splits": {}, "checks": {}}
    for split, d in data.items():
        texts = {m["meeting_id"]: m["text"] for m in d["meetings"]}
        index = {u["unit_id"]: u for u in d["units"]}
        errors = [e for u in d["units"] for e in check_unit(u, texts[u["source_id"]])]
        errors += [e for r in d["relations"] for e in check_relation(r, index)]
        if errors:
            raise SystemExit(f"{split} : {len(errors)} contrats invalides, ex. {errors[:3]}")
        files = {k: dump(args.out / split / f"{k}.jsonl", d[k])
                 for k in ("meetings", "units", "relations", "queries", "triplets")}
        files["qrels"] = dump(args.out / split / "qrels.json", d["qrels"])
        manifest["splits"][split] = {
            "projects": len({m["project_id"] for m in d["meetings"]}),
            "meetings": len(d["meetings"]), "units": len(d["units"]),
            "relations": dict(Counter(r["relation"] for r in d["relations"])),
            "queries": len(d["queries"]),
            "answerable": sum(q["answerable"] for q in d["queries"]),
            "triplets": dict(Counter(t["trap"] for t in d["triplets"])),
            "sha256": files,
        }

    def ents(split):
        d = data[split]
        people = {p for m in d["meetings"] for p in m["speakers"]}
        return people, {m["project"] for m in d["meetings"]}

    checks = {}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        pa, ja = ents(a)
        pb, jb = ents(b)
        checks[f"{a}/{b}"] = {"shared_people": sorted(pa & pb), "shared_projects": sorted(ja & jb)}
    # recouvrement lexical des formulations (entités et nombres retirés)
    all_ents = set().union(*(ents(s)[0] | ents(s)[1] for s in data))
    for kind, field in (("units", "statement"), ("queries", "text")):
        tr = grams([strip_entities(x[field], all_ents) for x in data["train"][kind]], 4)
        te = grams([strip_entities(x[field], all_ents) for x in data["test"][kind]], 4)
        checks[f"{kind}_4gram_test_in_train"] = round(len(te & tr) / len(te), 4) if te else 0.0
    manifest["checks"] = checks
    leaks = [k for k, v in checks.items() if isinstance(v, dict) and any(v.values())]
    if leaks:
        raise SystemExit(f"fuite d'entités : {leaks}")
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(json.dumps(manifest, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
