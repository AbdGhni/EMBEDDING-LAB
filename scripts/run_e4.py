"""EL-016 — E4 : RRF (BM25 + E2), rétrogradation des unités remplacées (R2), combinaisons.

Usage (Colab, poids E2 sur le Drive) :
  python -I scripts/run_e4.py --tag s13 \
      --weights /content/drive/MyDrive/embedding_lab_checkpoints/<E2 run>/best
  python -I scripts/run_e4.py --bm25-only           # E0-dem (indépendant des graines)
  python -I scripts/run_e4.py --smoke               # E1 à la place de E2, préfixe SMOKE (VM)

Écrit un run par système dans runs/. Le split test exige --test-reason.
"""

import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from embedding_lab.eval.harness import load_benchmark, run_benchmark, write_run
from embedding_lab.relations.predictor import R2Predictor
from embedding_lab.retrieval.bm25 import BM25Retriever
from embedding_lab.retrieval.hybrid import DemoteSystem, RRFSystem


def now() -> str:
    return datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")


def weights_sha(ckpt: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(ckpt.rglob("*.safetensors")):
        h.update(p.read_bytes())
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", type=Path)
    ap.add_argument("--tag", default="")
    ap.add_argument("--bm25-only", action="store_true")
    ap.add_argument("--dense-only", action="store_true",
                    help="seulement l'encodeur dense (évaluation finale de E2 ou E3)")
    ap.add_argument("--name", default="E4-dense", help="nom du run dense (ex. E2, E3)")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--split", choices=["val", "test"], default="val")
    ap.add_argument("--test-reason")
    args = ap.parse_args()
    started = now()
    stamp = started[:16].replace(":", "")
    pred = R2Predictor()
    bm25 = BM25Retriever()
    systems = {}
    if args.bm25_only:
        systems["E0-dem"] = DemoteSystem(bm25, pred.p_supersedes, pred.config())
    else:
        import torch
        from sentence_transformers import SentenceTransformer

        from embedding_lab.retrieval.dense import DenseRetriever

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if args.smoke:
            dense = DenseRetriever(device=device)
        else:
            if not args.weights:
                raise SystemExit("--weights obligatoire (ou --smoke)")
            model = SentenceTransformer(str(args.weights), device=device)
            dense = DenseRetriever(model=model, device=device,
                                   weights=f"{args.weights.parent.name}/best@"
                                           f"{weights_sha(args.weights)[:16]}")
        fused = RRFSystem([bm25, dense])
        if args.dense_only:
            systems = {args.name: dense}
        else:
            systems = {"E4-dense": dense,  # contrôle : doit reproduire l'évaluation de E2
                       "E4-rrf": fused,
                       "E4-dem": DemoteSystem(dense, pred.p_supersedes, pred.config()),
                       "E4-rrf-dem": DemoteSystem(fused, pred.p_supersedes, pred.config())}
    prefix = "SMOKE-" if args.smoke else ""
    for name, system in systems.items():
        tag = f"-{args.tag}" if args.tag else ""
        run_id = f"{prefix}{name}{tag}-{args.split}-{stamp}"
        results = {}
        for b in ("bsyn", "breal"):
            bench = load_benchmark(b, args.split, test_reason=args.test_reason, run_id=run_id)
            results[f"{b}_{args.split}"] = r = run_benchmark(system, bench)
            s = r["summary"]
            print(f"{run_id} {b}: nDCG@10 {s['ndcg@10']:.4f}  R@1 {s['recall@1']:.4f}  "
                  f"paires {s['pairwise_accuracy']:.4f}")
        write_run(Path("runs") / run_id, system, results, started, now())
        if hasattr(system, "applied"):
            print(f"  rétrogradations appliquées : {system.applied}")


if __name__ == "__main__":
    main()
