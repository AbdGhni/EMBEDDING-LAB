"""Évalue un système sur B-SYN et B-REAL via le point d'entrée commun.

Usage :
    uv run python -I scripts/run_eval.py --system bm25 --split val
    uv run python -I scripts/run_eval.py --system bm25 --split test \
        --test-reason "évaluation finale E0"
"""

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from embedding_lab.eval.harness import load_benchmark, run_benchmark, write_run
from embedding_lab.retrieval.baselines import RandomRetriever
from embedding_lab.retrieval.bm25 import BM25Retriever


def _e5_small():
    from embedding_lab.retrieval.dense import DenseRetriever
    return DenseRetriever()


SYSTEMS = {"bm25": BM25Retriever, "random": RandomRetriever, "e5-small": _e5_small}
EXP = {"bm25": "E0", "random": "E0r", "e5-small": "E1"}


def now() -> str:
    return datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", choices=sorted(SYSTEMS), required=True)
    ap.add_argument("--split", choices=["val", "test"], default="val")
    ap.add_argument("--benchmarks", nargs="+", default=["bsyn", "breal"])
    ap.add_argument("--test-reason")
    args = ap.parse_args()
    started = now()
    run_id = f"{EXP[args.system]}-{args.system}-{args.split}-{started[:16].replace(':', '')}"
    system = SYSTEMS[args.system]()
    results = {}
    for b in args.benchmarks:
        bench = load_benchmark(b, args.split, test_reason=args.test_reason, run_id=run_id)
        results[f"{b}_{args.split}"] = run_benchmark(system, bench)
        s = results[f"{b}_{args.split}"]["summary"]
        print(f"{b}/{args.split}: nDCG@10 {s['ndcg@10']:.4f}  MRR@10 {s['mrr@10']:.4f}  "
              f"R@1 {s['recall@1']:.4f}  R@10 {s['recall@10']:.4f}  "
              f"paires {s['pairwise_accuracy']:.4f}")
    if hasattr(system, "truncated"):
        print("passages tronqués à max_seq_length :", system.truncated)
    write_run(Path("runs") / run_id, system, results, started, now())
    print("run :", run_id)


if __name__ == "__main__":
    main()
