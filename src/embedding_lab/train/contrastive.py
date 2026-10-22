"""EL-013 — fine-tuning contrastif d'un encodeur (E2) et sa variante à négatifs aléatoires (E3).

Perte : Multiple Negatives Ranking Loss (forme d'InfoNCE). Pour un batch de B exemples
(requête aᵢ, positif pᵢ, négatif nᵢ), on calcule la matrice de similarités cosinus
S = [cos(aᵢ, pⱼ) | cos(aᵢ, nⱼ)] de taille B × 2B, multipliée par l'échelle s = 20
(inverse d'une température 0,05), puis une entropie croisée dont la bonne « classe » de la
ligne i est la colonne i :

    L = −(1/B) Σᵢ log( exp(s·cos(aᵢ, pᵢ)) / Σⱼ [exp(s·cos(aᵢ, pⱼ)) + exp(s·cos(aᵢ, nⱼ))] )

Chaque requête voit donc 2B − 1 négatifs : les positifs et négatifs des autres exemples du
batch, plus son propre piège. Les batchs ne contiennent jamais deux exemples d'une même
grappe (projet ou groupe), sinon une autre bonne preuve servirait de faux négatif.

Sélection : nDCG@10 sur B-SYN val toutes les ``eval_every`` étapes ; B-REAL val journalisé
comme garde-fou ; arrêt anticipé après ``patience`` évaluations sans amélioration.
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class TrainConfig:
    run_id: str
    examples: str
    model_name: str = "intfloat/multilingual-e5-small"
    revision: str = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
    max_seq_length: int = 128
    batch_size: int = 64
    lr: float = 2e-5
    warmup_ratio: float = 0.1
    epochs: int = 3
    scale: float = 20.0
    eval_every: int = 100
    patience: int = 3
    seed: int = 13
    device: str = "cpu"
    amp: bool = False
    max_steps: int | None = None
    selection: str = "bsyn"
    guards: list[str] = field(default_factory=lambda: ["breal"])
    out_root: str = "runs"
    checkpoint_root: str = "checkpoints"


def set_seed(seed: int) -> None:
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def embed(model, texts: list[str], device: str):
    """Plongements normalisés **avec gradient** : forme (len(texts), dim)."""
    import torch.nn.functional as F

    feats = model.tokenize(texts)
    feats = {k: v.to(device) for k, v in feats.items()}
    return F.normalize(model(feats)["sentence_embedding"], p=2, dim=-1)


def mnrl_loss(a, p, n, scale: float):
    """Entropie croisée sur la matrice B × 2B (voir docstring du module)."""
    import torch
    import torch.nn.functional as F

    scores = scale * a @ torch.cat([p, n], dim=0).T
    labels = torch.arange(a.size(0), device=a.device)
    return F.cross_entropy(scores, labels), scores


def evaluate(model, splits: list[str], weights: str) -> dict[str, dict[str, float]]:
    from embedding_lab.eval.harness import load_benchmark, run_benchmark
    from embedding_lab.retrieval.dense import DenseRetriever

    was_training = model.training
    model.eval()
    system = DenseRetriever(model=model, weights=weights, device=str(model.device))
    out = {}
    for b in splits:
        res = run_benchmark(system, load_benchmark(b, "val"))
        out[b] = {k: v for k, v in res["summary"].items() if isinstance(v, float)}
        out[b]["fingerprint"] = res["fingerprint"]
    if was_training:
        model.train()
    return out


def train(cfg: TrainConfig) -> dict[str, Any]:
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import get_linear_schedule_with_warmup

    from embedding_lab.train.data import cluster_batches

    set_seed(cfg.seed)
    run_dir = Path(cfg.out_root) / cfg.run_id
    ckpt_dir = Path(cfg.checkpoint_root) / cfg.run_id / "best"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(asdict(cfg), indent=1))
    with open(cfg.examples, encoding="utf-8") as f:
        examples = [json.loads(line) for line in f]
    model = SentenceTransformer(cfg.model_name, revision=cfg.revision, device=cfg.device)
    model.max_seq_length = cfg.max_seq_length
    epochs_batches = [cluster_batches(examples, cfg.batch_size, seed=cfg.seed + e)
                      for e in range(cfg.epochs)]
    total = sum(len(b) for b in epochs_batches)
    if cfg.max_steps:
        total = min(total, cfg.max_steps)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr)
    sched = get_linear_schedule_with_warmup(opt, int(cfg.warmup_ratio * total), total)
    scaler = torch.amp.GradScaler("cuda", enabled=cfg.amp)
    log_path = run_dir / "train_log.jsonl"
    log_path.write_text("")

    def write(entry: dict) -> None:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    evals = evaluate(model, [cfg.selection, *cfg.guards], "step0")
    best, best_step, bad = evals[cfg.selection]["ndcg@10"], 0, 0
    write({"step": 0, "eval": evals})
    model.save(str(ckpt_dir))
    step, t0, stop = 0, time.time(), False
    model.train()
    for epoch, batches in enumerate(epochs_batches):
        for b in batches:
            if step >= total:
                stop = True
                break
            exs = [examples[i] for i in b]
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=cfg.amp):
                a = embed(model, ["query: " + e["anchor"] for e in exs], cfg.device)
                p = embed(model, ["passage: " + e["positive"] for e in exs], cfg.device)
                n = embed(model, ["passage: " + e["negative"] for e in exs], cfg.device)
                loss, _ = mnrl_loss(a.float(), p.float(), n.float(), cfg.scale)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            gnorm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
            scaler.step(opt)
            scaler.update()
            sched.step()
            step += 1
            write({"step": step, "epoch": epoch, "loss": float(loss), "grad_norm": gnorm,
                   "lr": sched.get_last_lr()[0], "batch": len(b),
                   "elapsed_s": round(time.time() - t0, 1)})
            if not math.isfinite(float(loss)):
                raise FloatingPointError(f"perte non finie à l'étape {step}")
            if step % cfg.eval_every == 0 or step == total:
                evals = evaluate(model, [cfg.selection, *cfg.guards], f"step{step}")
                score = evals[cfg.selection]["ndcg@10"]
                improved = score > best
                write({"step": step, "eval": evals, "improved": improved})
                if improved:
                    best, best_step, bad = score, step, 0
                    model.save(str(ckpt_dir))
                else:
                    bad += 1
                    if bad >= cfg.patience:
                        stop = True
                        break
        if stop:
            break
    summary = {"run_id": cfg.run_id, "steps": step, "best_step": best_step,
               "best_val_ndcg@10": best, "checkpoint": str(ckpt_dir),
               "train_seconds": round(time.time() - t0, 1), "n_examples": len(examples)}
    (run_dir / "train_summary.json").write_text(json.dumps(summary, indent=1))
    return summary
