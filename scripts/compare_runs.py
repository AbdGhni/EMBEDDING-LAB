"""Compare des systèmes à partir de leurs runs (moyenne des graines, tests par grappes).

Usage :
  uv run python -I scripts/compare_runs.py --split val \
      --system E0=runs/E0-bm25-val-* --system E1=runs/E1-e5-small-val-* \
      --system E2=runs/E2-e5s-s*-bs64-* --system E3=runs/E3-e5s-s*-bs64-* \
      --pair E2:E1 --pair E3:E1 --pair E2:E3 --pair E1:E0

Sortie : runs/CMP-<split>-<horodatage>/comparison.json + tableau Markdown sur la sortie standard.
Le split test exige --test-reason (inscrit dans runs/TEST_ACCESS.log).
"""

import argparse
import glob
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from embedding_lab.data.splits import group_components
from embedding_lab.eval.compare import (
    compare,
    component_of_groups,
    mean_over_seeds,
    read_per_query,
    read_wins,
)
from embedding_lab.eval.test_access import log_test_access
from embedding_lab.ingest.breal import load_meetings

BENCHES = ("bsyn", "breal")


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def clusters(split: str) -> dict[str, dict[str, str]]:
    """Grappe de chaque requête et de chaque triplet, par benchmark."""
    out = {}
    comp = component_of_groups(group_components(
        load_meetings(Path("data/processed/summre_meetings.jsonl")).values()))
    for b in BENCHES:
        base = Path(f"data/{b}/{split}")
        qs = read_jsonl(base / "queries.jsonl")
        of_q = {q["query_id"]: (q["cluster"] if b == "bsyn" else comp[q["group_id"]])
                for q in qs}
        trip = read_jsonl(base / "triplets.jsonl")
        of_t = {f"t{i:05d}": of_q[t["query_id"]] for i, t in enumerate(trip)}
        out[b] = {**of_q, **of_t}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="val", choices=["val", "test"])
    ap.add_argument("--system", action="append", required=True, help="NOM=motif de runs")
    ap.add_argument("--pair", action="append", default=[], help="A:B (différence A − B)")
    ap.add_argument("--test-reason")
    args = ap.parse_args()
    started = datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")
    run_id = f"CMP-{args.split}-{started[:16].replace(':', '')}"
    if args.split == "test":
        if not args.test_reason:
            raise SystemExit("accès au test refusé : --test-reason obligatoire")
        log_test_access(run_id, args.test_reason, "compare/test", Path("runs/TEST_ACCESS.log"))
    systems = {}
    for spec in args.system:
        name, pattern = spec.split("=", 1)
        dirs = sorted(Path(p) for p in glob.glob(pattern))
        if not dirs:
            raise SystemExit(f"aucun run pour {name} ({pattern})")
        systems[name] = dirs
    cl = clusters(args.split)
    scores = {}
    for name, dirs in systems.items():
        for b in BENCHES:
            key = f"{b}_{args.split}"
            per_seed = [read_per_query(d, key) for d in dirs]
            wins = [read_wins(d, key) for d in dirs]
            scores[(name, b)] = {
                "ndcg@10": mean_over_seeds(per_seed), "pairwise": mean_over_seeds(wins),
                "per_seed_ndcg@10": [sum(s.values()) / len(s) for s in per_seed],
                "per_seed_pairwise": [sum(w.values()) / len(w) for w in wins]}
    report = {"run_id": run_id, "started": started, "split": args.split,
              "systems": {n: [d.name for d in ds] for n, ds in systems.items()},
              "means": {}, "pairs": {}}
    print("| Système | graines | B-SYN nDCG@10 | B-SYN paires | B-REAL nDCG@10 | B-REAL paires |")
    print("|---|---|---|---|---|---|")
    for name, dirs in systems.items():
        row = {}
        for b in BENCHES:
            s = scores[(name, b)]
            row[b] = {m: sum(s[m].values()) / len(s[m]) for m in ("ndcg@10", "pairwise")}
            row[b]["per_seed_ndcg@10"] = s["per_seed_ndcg@10"]
            row[b]["per_seed_pairwise"] = s["per_seed_pairwise"]
        report["means"][name] = row
        print(f"| {name} | {len(dirs)} | {row['bsyn']['ndcg@10']:.3f} | "
              f"{row['bsyn']['pairwise']:.3f} | {row['breal']['ndcg@10']:.3f} | "
              f"{row['breal']['pairwise']:.3f} |")
    print()
    print("| Différence | Benchmark | Mesure | Δ | IC 95 % (bootstrap) | p (permutation) "
          "| grappes |")
    print("|---|---|---|---|---|---|---|")
    for pair in args.pair:
        a, b_ = pair.split(":")
        for bench in BENCHES:
            for m in ("ndcg@10", "pairwise"):
                res = compare(scores[(a, bench)][m], scores[(b_, bench)][m], cl[bench])
                report["pairs"][f"{a}-{b_}|{bench}|{m}"] = res
                bo, pe = res["bootstrap"], res["permutation"]
                print(f"| {a} − {b_} | {bench} | {m} | {bo['diff']:+.3f} | "
                      f"[{bo['ci_low']:+.3f} ; {bo['ci_high']:+.3f}] | {pe['p_value']:.4f} "
                      f"({pe['method']}) | {res['n_clusters']} |")
    out = Path("runs") / run_id
    out.mkdir(parents=True, exist_ok=False)
    (out / "comparison.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"\n{out}/comparison.json")


if __name__ == "__main__":
    main()
