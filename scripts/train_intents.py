"""EL-019 — modèles d'intentions I0 (règles), I1 (TF-IDF + LogReg), I2 (e5 gelé + LogReg).

Usage :
  uv run python -I scripts/train_intents.py                       # sélection et mesure val
  uv run python -I scripts/train_intents.py --split test --test-reason "…"   # I-SYN test + I-MAN

C choisi sur I-SYN val. Sortie : runs/I-<split>-<horodatage>/.
"""

import argparse
import json
import platform
import random
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from embedding_lab.eval.test_access import log_test_access
from embedding_lab.intents.data import ENTITIES, INTENTS
from embedding_lab.intents.rules import classify, extract_slots
from embedding_lab.relations.metrics import macro_f1, per_class

GRID = (0.01, 0.1, 1.0, 10.0, 100.0)
ACTIONS = {"draft_email", "create_task", "schedule_event"}
MAN_PERSONS = ["Margaux", "Romain", "Élodie", "Samir", "Victor"]
MAN_PROJECTS = ["Opale", "Kestrel", "Saturne", "Brume"]


def now() -> str:
    return datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def wrong_action_rate(gold, pred) -> float:
    idx = [i for i, g in enumerate(gold) if g in ("no_action", "answer", "compare")]
    return sum(pred[i] in ACTIONS for i in idx) / len(idx) if idx else 0.0


def bootstrap(gold, pred, n=10_000, seed=0) -> tuple[float, float]:
    rng = random.Random(seed)
    k = len(gold)
    stats = []
    for _ in range(n):
        idx = [rng.randrange(k) for _ in range(k)]
        stats.append(macro_f1([gold[i] for i in idx], [pred[i] for i in idx], INTENTS))
    stats.sort()
    return stats[int(0.025 * n)], stats[int(0.975 * n) - 1]


def evaluate(rows, pred, persons, projects) -> dict:
    gold = [r["intent"] for r in rows]
    pc = per_class(gold, pred, INTENTS)
    slots = {}
    for key in ("person", "project", "deadline"):
        ok = 0
        for r in rows:
            got = extract_slots(r["text"], persons, projects)[key]
            want = r["slots"].get(key)
            ok += (got or None) == (want.lower() if key == "deadline" and want else want)
        slots[key] = ok / len(rows)
    lo, hi = bootstrap(gold, pred)
    return {"n": len(rows), "macro_f1": macro_f1(gold, pred, INTENTS), "macro_f1_ci": [lo, hi],
            "accuracy": sum(g == p for g, p in zip(gold, pred, strict=True)) / len(gold),
            "clarify": pc["clarify"], "no_action": pc["no_action"],
            "wrong_action_rate": wrong_action_rate(gold, pred), "per_class": pc,
            "slot_accuracy": slots,
            "errors": [{"id": r["id"], "text": r["text"], "gold": g, "pred": p}
                       for r, g, p in zip(rows, gold, pred, strict=True) if g != p]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="val", choices=["val", "test"])
    ap.add_argument("--test-reason")
    args = ap.parse_args()
    started = now()
    run_id = f"I-{args.split}-{started[:16].replace(':', '')}"
    if args.split == "test":
        if not args.test_reason:
            raise SystemExit("accès au test refusé : --test-reason obligatoire")
        log_test_access(run_id, args.test_reason, "intents/test", Path("runs/TEST_ACCESS.log"))

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline, make_union

    from embedding_lab.retrieval.dense import DenseRetriever

    train = read(Path("data/intents/train.jsonl"))
    val = read(Path("data/intents/val.jsonl"))
    evals = {"isyn_val": (val, ENTITIES["val"]["p"], ENTITIES["val"]["proj"])}
    if args.split == "test":
        evals = {"isyn_test": (read(Path("data/intents/test.jsonl")), ENTITIES["test"]["p"],
                               ENTITIES["test"]["proj"]),
                 "iman": (read(Path("annotations/intents/test_manual_v1.jsonl")),
                          MAN_PERSONS, MAN_PROJECTS)}
    ytr = [r["intent"] for r in train]
    enc = DenseRetriever()

    def emb(rows):
        return enc._encode(["query: " + r["text"] for r in rows])

    def tfidf(C):
        feats = make_union(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                           TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5),
                                           sublinear_tf=True))
        return make_pipeline(feats, LogisticRegression(C=C, max_iter=3000, random_state=0))

    Xtr_e = emb(train)
    Xval_e = emb(val)
    yval = [r["intent"] for r in val]
    sel = {"I1": {}, "I2": {}}
    for C in GRID:
        m1 = tfidf(C).fit([r["text"] for r in train], ytr)
        sel["I1"][C] = macro_f1(yval, list(m1.predict([r["text"] for r in val])), INTENTS)
        m2 = LogisticRegression(C=C, max_iter=3000, random_state=0).fit(Xtr_e, ytr)
        sel["I2"][C] = macro_f1(yval, list(m2.predict(Xval_e)), INTENTS)
    best = {k: max(GRID, key=lambda c, k=k: (sel[k][c], -c)) for k in sel}
    m1 = tfidf(best["I1"]).fit([r["text"] for r in train], ytr)
    m2 = LogisticRegression(C=best["I2"], max_iter=3000, random_state=0).fit(Xtr_e, ytr)
    chosen = max(("I1", "I2"), key=lambda k: sel[k][best[k]])

    results = {}
    for name, (rows, persons, projects) in evals.items():
        texts = [r["text"] for r in rows]
        preds = {"I0": [classify(t) for t in texts], "I1": list(m1.predict(texts)),
                 "I2": list(m2.predict(emb(rows)))}
        for model, pred in preds.items():
            results[f"{model}|{name}"] = evaluate(rows, pred, persons, projects)

    out = Path("runs") / run_id
    out.mkdir(parents=True, exist_ok=False)
    (out / "config.json").write_text(json.dumps(
        {"task": "intents", "labels": INTENTS, "grid": GRID, "selection": sel, "C": best,
         "chosen_for_agent": chosen, "encoder": enc.config(),
         "tfidf": "mots 1-2 + caractères 2-5 (char_wb), sublinear_tf"}, indent=1))
    (out / "manifest.json").write_text(json.dumps(
        {"run_id": run_id, "git_commit": git("rev-parse", "HEAD"),
         "git_dirty": bool(git("status", "--porcelain", "--", "src", "scripts",
                               "pyproject.toml", "uv.lock", "data/intents", "annotations")),
         "python": platform.python_version(), "started": started, "finished": now()},
        indent=1))
    (out / f"metrics_{args.split}.json").write_text(json.dumps(results, indent=1,
                                                               ensure_ascii=False))
    print("C :", best, "| retenu :", chosen)
    for k, r in results.items():
        print(f"{k:16s} macro-F1 {r['macro_f1']:.3f} [{r['macro_f1_ci'][0]:.3f} ; "
              f"{r['macro_f1_ci'][1]:.3f}]  clarify F1 {r['clarify']['f1']:.2f}  "
              f"action à tort {r['wrong_action_rate']:.3f}  slots {r['slot_accuracy']}")
    print(out)


if __name__ == "__main__":
    np.set_printoptions(precision=3)
    main()
