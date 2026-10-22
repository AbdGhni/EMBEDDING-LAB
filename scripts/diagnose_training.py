"""EL-013 — diagnostics avant entraînement (protocole § 6). Ce n'est PAS un entraînement.

1. dimensions des tenseurs ; 2. perte d'un batch connu comparée à log(2B) (hasard) ;
3. sur-apprentissage volontaire d'un mini-lot (la perte doit tendre vers 0) ;
4. temps et mémoire par étape au batch nominal.

Usage : uv run python -I scripts/diagnose_training.py [--device cuda] [--batch 64]
"""

import argparse
import json
import math
import resource
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import torch
from sentence_transformers import SentenceTransformer

from embedding_lab.retrieval.dense import E5_SMALL
from embedding_lab.train.contrastive import embed, mnrl_loss, set_seed
from embedding_lab.train.data import cluster_batches


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", default="data/train/e2_hard.jsonl")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--overfit-steps", type=int, default=40)
    args = ap.parse_args()
    set_seed(0)
    started = datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")
    with open(args.examples, encoding="utf-8") as f:
        ex = [json.loads(line) for line in f]
    model = SentenceTransformer(E5_SMALL[0], revision=E5_SMALL[1], device=args.device)
    model.max_seq_length = 128
    batch = [ex[i] for i in cluster_batches(ex, 8, seed=0)[0]]
    out: dict = {"started": started, "device": args.device}

    a = embed(model, ["query: " + e["anchor"] for e in batch], args.device)
    p = embed(model, ["passage: " + e["positive"] for e in batch], args.device)
    n = embed(model, ["passage: " + e["negative"] for e in batch], args.device)
    loss, scores = mnrl_loss(a, p, n, 20.0)
    out["shapes"] = {"anchor": list(a.shape), "scores": list(scores.shape)}
    assert list(scores.shape) == [len(batch), 2 * len(batch)]
    out["initial_loss"] = float(loss)
    out["chance_loss_log2B"] = math.log(2 * len(batch))
    out["initial_pos_minus_hardneg_cos"] = float((a * p).sum(-1).mean() - (a * n).sum(-1).mean())

    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=5e-5)
    curve = []
    for _ in range(args.overfit_steps):
        a = embed(model, ["query: " + e["anchor"] for e in batch], args.device)
        p = embed(model, ["passage: " + e["positive"] for e in batch], args.device)
        n = embed(model, ["passage: " + e["negative"] for e in batch], args.device)
        loss, _ = mnrl_loss(a, p, n, 20.0)
        opt.zero_grad()
        loss.backward()
        gnorm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
        opt.step()
        curve.append(round(float(loss), 4))
    out["overfit_curve"] = curve
    out["overfit_last_grad_norm"] = gnorm
    out["overfit_ok"] = curve[-1] < 0.1 * curve[0]

    big = [ex[i] for i in cluster_batches(ex, args.batch, seed=1)[0]]
    t0 = time.perf_counter()
    for _ in range(2):
        a = embed(model, ["query: " + e["anchor"] for e in big], args.device)
        p = embed(model, ["passage: " + e["positive"] for e in big], args.device)
        n = embed(model, ["passage: " + e["negative"] for e in big], args.device)
        loss, _ = mnrl_loss(a, p, n, 20.0)
        opt.zero_grad()
        loss.backward()
        opt.step()
    step_s = (time.perf_counter() - t0) / 2
    steps_per_epoch = len(cluster_batches(ex, args.batch, seed=0))
    out["timing"] = {"batch": len(big), "seconds_per_step": round(step_s, 2),
                     "steps_per_epoch": steps_per_epoch,
                     "estimated_epoch_minutes": round(step_s * steps_per_epoch / 60, 1),
                     "max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)}
    out["finished"] = datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")
    run = Path("runs") / f"DIAG-e2-{args.device}-{started[:16].replace(':', '')}"
    run.mkdir(parents=True, exist_ok=True)
    (run / "diagnostics.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print("run :", run.name)


if __name__ == "__main__":
    main()
