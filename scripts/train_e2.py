"""EL-013 — entraîne E2 (négatifs difficiles) ou E3 (négatifs aléatoires), puis évalue le
meilleur checkpoint sur **val** via le point d'entrée commun. Aucun accès au test.

Usage :
    python -I scripts/train_e2.py --variant e2 --seed 13
    python -I scripts/train_e2.py --variant e3 --seed 13 \
        --checkpoint-root /content/drive/MyDrive/el_ckpt
    python -I scripts/train_e2.py --variant e2 --smoke   # test de bout en bout, pas un résultat
"""

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

EXAMPLES = {"e2": "data/train/e2_hard.jsonl", "e3": "data/train/e3_random.jsonl",
            # ablation diagnostique (val seulement) : E2 sans les exemples B-REAL
            "e2s": "data/train/e2_bsyn_only.jsonl"}


def now() -> str:
    return datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")


def weights_sha(ckpt: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(ckpt.rglob("*.safetensors")):
        h.update(p.read_bytes())
    return h.hexdigest()


def main() -> None:
    import torch

    from embedding_lab.eval.harness import load_benchmark, run_benchmark, write_run
    from embedding_lab.retrieval.dense import DenseRetriever
    from embedding_lab.train.contrastive import TrainConfig, train

    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=sorted(EXAMPLES), required=True)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--eval-every", type=int, default=100)
    ap.add_argument("--max-steps", type=int)
    ap.add_argument("--checkpoint-root", default="checkpoints")
    ap.add_argument("--smoke", action="store_true",
                    help="3 étapes, batch 8 : vérifie la chaîne complète (préfixe SMOKE)")
    args = ap.parse_args()
    if args.smoke:
        args.max_steps, args.batch_size, args.eval_every = 3, 8, 3
    device = "cuda" if torch.cuda.is_available() else "cpu"
    started = now()
    prefix = "SMOKE-" if args.smoke else ""
    run_id = (f"{prefix}{args.variant.upper()}-e5s-s{args.seed}-bs{args.batch_size}-lr{args.lr:g}-"
              f"{started[:16].replace(':', '')}")
    cfg = TrainConfig(run_id=run_id, examples=EXAMPLES[args.variant], batch_size=args.batch_size,
                      lr=args.lr, epochs=args.epochs, eval_every=args.eval_every,
                      seed=args.seed, device=device, amp=device == "cuda",
                      max_steps=args.max_steps, checkpoint_root=args.checkpoint_root)
    summary = train(cfg)
    ckpt = Path(summary["checkpoint"])
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(ckpt), device=device)
    system = DenseRetriever(model=model, device=device,
                            weights=f"{ckpt.parent.name}/best@{weights_sha(ckpt)[:16]}")
    results = {f"{b}_val": run_benchmark(system, load_benchmark(b, "val"))
               for b in ("bsyn", "breal")}
    run_dir = Path("runs") / run_id
    write_run(run_dir, system, results, started, now())
    summary["weights_sha256"] = weights_sha(ckpt)
    summary["gpu"] = torch.cuda.get_device_name(0) if device == "cuda" else None
    summary["examples_sha256"] = hashlib.sha256(Path(cfg.examples).read_bytes()).hexdigest()
    (run_dir / "train_summary.json").write_text(json.dumps(summary, indent=1))
    for k, r in results.items():
        s = r["summary"]
        print(f"{k}: nDCG@10 {s['ndcg@10']:.4f}  R@1 {s['recall@1']:.4f}  "
              f"paires {s['pairwise_accuracy']:.4f}")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
