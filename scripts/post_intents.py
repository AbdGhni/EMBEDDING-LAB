"""EL-029 — correction post hoc du modèle d'intentions (I2+), mesurée hors test.

Contexte : sur le test, I2 (retenu sur val) classe « Est-ce qu'on a validé… ? » en `compare`
(scénario 2 de la démonstration, scénario C2). Cette famille d'erreurs a été découverte APRÈS
l'évaluation et la démonstration ; tout ce qui suit est donc étiqueté post hoc.

Données ajoutées (écrites par Claude, donc non indépendantes de l'auteur du système) :
  annotations/intents/post_train_v1.jsonl    48 exemples d'entraînement (28 questions de
                                              vérification, 8 comparaisons de contraste, 12 autres)
  annotations/intents/post_control_v1.jsonl  64 requêtes de contrôle, 8 par classe, autres
                                              noms et tournures, écrites avant la mesure

Règle de décision écrite avant la première mesure : I2+ remplace I2 dans l'agent si et seulement si
  (1) macro-F1 val I-SYN de I2+ >= celui de I2 - 0,02   (pas de régression sur la validation)
  (2) macro-F1 sur le contrôle post hoc de I2+ > celui de I2.
Le test (I-SYN test, I-MAN) n'est ni lu ni mesuré ici : il a déjà été évalué une fois.

Usage : uv run python -I scripts/post_intents.py
Sortie : runs/IP-post-<horodatage>/
"""

import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from embedding_lab.intents.data import INTENTS
from embedding_lab.intents.rules import classify
from embedding_lab.relations.metrics import macro_f1, per_class

TRAIN = Path("data/intents/train.jsonl")
VAL = Path("data/intents/val.jsonl")
POST_TRAIN = Path("annotations/intents/post_train_v1.jsonl")
POST_CONTROL = Path("annotations/intents/post_control_v1.jsonl")
C = 10.0
MARGIN = 0.02


def now() -> str:
    return datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report(rows: list[dict], pred: list[str]) -> dict:
    gold = [r["intent"] for r in rows]
    pc = per_class(gold, pred, INTENTS)
    return {"n": len(rows), "macro_f1": macro_f1(gold, pred, INTENTS),
            "accuracy": sum(g == p for g, p in zip(gold, pred, strict=True)) / len(gold),
            "f1_answer": pc["answer"]["f1"], "f1_compare": pc["compare"]["f1"],
            "per_class_f1": {k: v["f1"] for k, v in pc.items()},
            "errors": [{"id": r["id"], "text": r["text"], "gold": g, "pred": p}
                       for r, g, p in zip(rows, gold, pred, strict=True) if g != p]}


def main() -> None:
    started = now()
    run_id = f"IP-post-{started[:16].replace(':', '')}"
    from sklearn.linear_model import LogisticRegression

    from embedding_lab.retrieval.dense import DenseRetriever

    train, post, val, ctrl = read(TRAIN), read(POST_TRAIN), read(VAL), read(POST_CONTROL)
    enc = DenseRetriever()

    def emb(rows):
        return enc._encode(["query: " + r["text"] for r in rows])

    def fit(rows):
        m = LogisticRegression(C=C, max_iter=3000, random_state=0)
        m.fit(emb(rows), [r["intent"] for r in rows])
        return m

    models = {"I2": fit(train), "I2+": fit(train + post)}
    results = {}
    for split, rows in (("isyn_val", val), ("post_control", ctrl)):
        x = emb(rows)
        results[split] = {"I0": report(rows, [classify(r["text"]) for r in rows])}
        for name, m in models.items():
            results[split][name] = report(rows, [str(p) for p in m.predict(x)])
    c_val = results["isyn_val"]
    c_ctl = results["post_control"]
    adopt = (c_val["I2+"]["macro_f1"] >= c_val["I2"]["macro_f1"] - MARGIN
             and c_ctl["I2+"]["macro_f1"] > c_ctl["I2"]["macro_f1"])
    out = Path("runs") / run_id
    out.mkdir(parents=True)
    (out / "metrics.json").write_text(json.dumps(
        {"decision_rule": f"val(I2+) >= val(I2) - {MARGIN} et controle(I2+) > controle(I2)",
         "adopt_i2_plus": adopt, "results": results}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (out / "config.json").write_text(json.dumps(
        {"C": C, "post_hoc": True, "test_accessed": False,
         "data_sha256": {str(p): sha(p) for p in (TRAIN, VAL, POST_TRAIN, POST_CONTROL)},
         "n_train": len(train), "n_post_train": len(post)}, indent=1), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(
        {"run_id": run_id, "started": started, "finished": now(),
         "git_commit": git("rev-parse", "HEAD"),
         "git_dirty": bool(git("status", "--porcelain")), "python": platform.python_version()},
        indent=1), encoding="utf-8")
    for split, res in results.items():
        for name, r in res.items():
            print(f"{split:13s} {name:4s} macro-F1 {r['macro_f1']:.3f}  "
                  f"F1 answer {r['f1_answer']:.2f}  F1 compare {r['f1_compare']:.2f}  "
                  f"erreurs {len(r['errors'])}/{r['n']}")
    print("règle de décision :", "I2+ adopté" if adopt else "I2 conservé", "—", out)


if __name__ == "__main__":
    main()
