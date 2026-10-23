"""EL-015 — entraîne et évalue les modèles de relations R0 à R3 (protocole § 10).

Usage :
  uv run python -I scripts/train_relations.py                 # sélection et mesure sur val
  uv run python -I scripts/train_relations.py --split test --test-reason "…"  # final, une fois

Entraînement : B-REAL train + B-SYN train. C choisi sur B-REAL val (macro-F1, 6 classes).
Sortie : runs/R-<split>-<horodatage>/ (config, manifeste, métriques, prédictions).
"""

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from embedding_lab.data.splits import group_components
from embedding_lab.eval.compare import component_of_groups
from embedding_lab.eval.test_access import log_test_access
from embedding_lab.ingest.breal import load_meetings
from embedding_lab.relations.features import embedding_matrix, structural_matrix
from embedding_lab.relations.metrics import bootstrap_macro_f1, report
from embedding_lab.relations.models import Majority, TypeTable, fit_logreg, type_key
from embedding_lab.relations.pairs import LABELS, build_pairs

GRID = (0.01, 0.1, 1.0, 10.0, 100.0)
BENCHES = ("breal", "bsyn")


def now() -> str:
    return datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load(bench: str, split: str) -> tuple[dict, list[dict], str]:
    base = Path(f"data/{bench}/{split}")
    units = {u["unit_id"]: u for u in read_jsonl(base / "units.jsonl")}
    rels = read_jsonl(base / "relations.jsonl")
    sha = hashlib.sha256((base / "relations.jsonl").read_bytes()).hexdigest()
    return units, build_pairs(rels, units, seed=0), sha


def encode(units: dict, encoder) -> dict[str, np.ndarray]:
    ids = sorted(units)
    vecs = encoder._encode([encoder.passage_prefix + units[i]["evidence"]["text"] for i in ids])
    return dict(zip(ids, vecs, strict=True))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="val", choices=["val", "test"])
    ap.add_argument("--test-reason")
    args = ap.parse_args()
    started = now()
    run_id = f"R-{args.split}-{started[:16].replace(':', '')}"
    if args.split == "test":
        if not args.test_reason:
            raise SystemExit("accès au test refusé : --test-reason obligatoire")
        log_test_access(run_id, args.test_reason, "relations/test", Path("runs/TEST_ACCESS.log"))

    from embedding_lab.retrieval.dense import DenseRetriever

    enc = DenseRetriever()
    data, shas = {}, {}
    for b in BENCHES:
        for s in ("train", "val", args.split):
            if (b, s) in data:
                continue
            units, pairs, sha = load(b, s)
            data[(b, s)] = (units, pairs, encode(units, enc))
            shas[f"{b}/{s}"] = sha

    def matrices(key):
        units, pairs, vec = data[key]
        st = structural_matrix(pairs, units)
        return st, np.hstack([st, embedding_matrix(pairs, vec)]), [p["label"] for p in pairs], \
            [type_key(units[p["x"]], units[p["y"]]) for p in pairs]

    tr = [matrices((b, "train")) for b in BENCHES]
    Xs_tr = np.vstack([t[0] for t in tr])
    Xe_tr = np.vstack([t[1] for t in tr])
    y_tr = sum((t[2] for t in tr), [])
    k_tr = sum((t[3] for t in tr), [])

    # sélection de C sur B-REAL val, macro-F1 6 classes
    val = matrices(("breal", "val"))
    selection = {}
    for name, Xtr, idx in (("R2", Xs_tr, 0), ("R3", Xe_tr, 1)):
        scores = {}
        for C in GRID:
            m = fit_logreg(Xtr, y_tr, C)
            scores[C] = report(val[2], list(m.predict(val[idx])), LABELS)["macro_f1"]
        best = max(GRID, key=lambda c: (scores[c], -c))
        selection[name] = {"scores": scores, "C": best}

    models = {"R0": Majority().fit(y_tr), "R1": TypeTable().fit(k_tr, y_tr),
              "R2": fit_logreg(Xs_tr, y_tr, selection["R2"]["C"]),
              "R3": fit_logreg(Xe_tr, y_tr, selection["R3"]["C"])}

    comp = component_of_groups(group_components(
        load_meetings(Path("data/processed/summre_meetings.jsonl")).values()))
    results, predictions = {}, {}
    for b in BENCHES:
        st, ext, gold, keys = matrices((b, args.split))
        pairs = data[(b, args.split)][1]
        clusters = [comp[p["group"].removeprefix("summre-")] if b == "breal" else p["group"]
                    for p in pairs]
        preds = {"R0": models["R0"].predict(len(gold)), "R1": models["R1"].predict(keys),
                 "R2": list(models["R2"].predict(st)), "R3": list(models["R3"].predict(ext))}
        for name, pred in preds.items():
            rep = report(gold, pred, LABELS)
            rep["macro_f1_ci"] = bootstrap_macro_f1(gold, pred, clusters, LABELS)
            if name != "R0":
                rep["diff_vs_R0_ci"] = bootstrap_macro_f1(gold, pred, clusters, LABELS,
                                                          other=preds["R0"])
                rep["diff_vs_R1_ci"] = bootstrap_macro_f1(gold, pred, clusters, LABELS,
                                                          other=preds["R1"])
            results[f"{name}|{b}"] = rep
        predictions[b] = [{**p, "cluster": c, **{n: preds[n][i] for n in preds}}
                          for i, (p, c) in enumerate(zip(pairs, clusters, strict=True))]

    out = Path("runs") / run_id
    out.mkdir(parents=True, exist_ok=False)
    config = {"task": "relations", "labels": LABELS, "train": ["breal/train", "bsyn/train"],
              "selection": "C sur breal/val, macro-F1 6 classes", "grid": GRID,
              "selection_scores": selection, "encoder": enc.config(),
              "embedding_text": "passage: + evidence.text", "class_weight": "balanced",
              "negatives": "1 couple non relié par positif et par groupe (B-REAL), "
                           "couples unrelated du générateur (B-SYN), graine 0"}
    (out / "config.json").write_text(json.dumps(config, indent=1, ensure_ascii=False))
    manifest = {"run_id": run_id, "git_commit": git("rev-parse", "HEAD"),
                "git_dirty": bool(git("status", "--porcelain", "--", "src", "scripts",
                                      "pyproject.toml", "uv.lock")),
                "python": platform.python_version(), "machine": platform.platform(),
                "started": started, "finished": now(), "relations_sha256": shas,
                "n_pairs": {f"{b}/{s}": len(data[(b, s)][1]) for (b, s) in data}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    (out / f"metrics_{args.split}.json").write_text(json.dumps(results, indent=1))
    for b, rows in predictions.items():
        with open(out / f"predictions_{b}_{args.split}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"sélection : { {k: v['C'] for k, v in selection.items()} }")
    for k, r in results.items():
        ci = r["macro_f1_ci"]
        print(f"{k:10s} macro-F1 {r['macro_f1']:.3f} [{ci['ci_low']:.3f} ; {ci['ci_high']:.3f}]"
              f"  relations seules {r['macro_f1_relations_only']:.3f}  exactitude "
              f"{r['accuracy']:.3f}  n={r['n']}")
    print(out)


if __name__ == "__main__":
    main()
