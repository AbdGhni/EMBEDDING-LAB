"""Analyse confirmatoire du test (protocole § 1 et § 4) : H1–H5, correction de Holm sur H1–H2,
sous-ensemble B-REAL relu à la main rapporté à part.

Usage : uv run python -I scripts/final_analysis.py --test-reason "…"
Lit uniquement des runs de test déjà produits ; l'accès aux requêtes de test (grappes,
réunions) est consigné dans runs/TEST_ACCESS.log.
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

SYSTEMS = {"E0": "runs/E0-bm25-test-*", "E1": "runs/E1-e5-small-test-*",
           "E2": "runs/E4-dense-s*-test-*", "E3": "runs/E3-s*-test-*",
           "E4dem": "runs/E4-dem-s*-test-*", "E4rrf": "runs/E4-rrf-s*-test-*",
           "E0dem": "runs/E0-dem-test-*"}


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """p ajustées de Holm-Bonferroni.

    >>> holm({"a": 0.01, "b": 0.04})
    {'a': 0.02, 'b': 0.04}
    """
    order = sorted(pvals, key=pvals.get)
    m, out, running = len(order), {}, 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvals[k]))
        out[k] = round(running, 10)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-reason", required=True)
    args = ap.parse_args()
    started = datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")
    run_id = f"CMP-test-{started[:16].replace(':', '')}"
    log_test_access(run_id, args.test_reason, "analysis/test", Path("runs/TEST_ACCESS.log"))
    comp = component_of_groups(group_components(
        load_meetings(Path("data/processed/summre_meetings.jsonl")).values()))
    reviewed = set(Path("splits/summre_v1_test_human_review.txt").read_text().split())
    cl, about = {}, {}
    for b in ("bsyn", "breal"):
        qs = read_jsonl(f"data/{b}/test/queries.jsonl")
        of_q = {q["query_id"]: q["cluster"] if b == "bsyn" else comp[q["group_id"]] for q in qs}
        trip = read_jsonl(f"data/{b}/test/triplets.jsonl")
        cl[b] = {**of_q, **{f"t{i:05d}": of_q[t["query_id"]] for i, t in enumerate(trip)}}
        if b == "breal":
            about = {q["query_id"]: q.get("about_meeting") for q in qs}
    S = {}
    for name, pat in SYSTEMS.items():
        dirs = sorted(Path(p) for p in glob.glob(pat))
        if not dirs:
            raise SystemExit(f"aucun run pour {name} ({pat})")
        for b in ("bsyn", "breal"):
            key = f"{b}_test"
            S[(name, b, "ndcg")] = mean_over_seeds([read_per_query(d, key) for d in dirs])
            S[(name, b, "pair")] = mean_over_seeds([read_wins(d, key) for d in dirs])
        S[(name, "n")] = len(dirs)

    def cmp(a, b, bench, m):
        return compare(S[(a, bench, m)], S[(b, bench, m)], cl[bench])

    H = {"H1": cmp("E2", "E1", "bsyn", "ndcg"), "H2": cmp("E2", "E1", "bsyn", "pair"),
         "H3": cmp("E2", "E1", "breal", "ndcg"), "H4": cmp("E2", "E3", "bsyn", "pair"),
         "H5_bsyn": cmp("E4dem", "E2", "bsyn", "ndcg"),
         "H5_breal": cmp("E4dem", "E2", "breal", "ndcg")}
    adj = holm({k: H[k]["permutation"]["p_value"] for k in ("H1", "H2")})
    extra = {f"{a}-{b}|{bench}|{m}": cmp(a, b, bench, m)
             for a, b in (("E1", "E0"), ("E2", "E0"), ("E3", "E1"), ("E2", "E3"),
                          ("E4rrf", "E2"), ("E0dem", "E0"))
             for bench in ("bsyn", "breal") for m in ("ndcg", "pair")}
    subset = {}
    for name in ("E0", "E1", "E2", "E3"):
        sc = S[(name, "breal", "ndcg")]
        rev = [v for q, v in sc.items() if about.get(q, "") in reviewed]
        rest = [v for q, v in sc.items() if about.get(q, "") not in reviewed]
        subset[name] = {"reviewed": sum(rev) / len(rev), "n_reviewed": len(rev),
                        "rest": sum(rest) / len(rest), "n_rest": len(rest)}
    means = {}
    for name in SYSTEMS:
        means[name] = {f"{b}_{m}": sum(S[(name, b, m)].values()) / len(S[(name, b, m)])
                       for b in ("bsyn", "breal") for m in ("ndcg", "pair")}
        means[name]["seeds"] = S[(name, "n")]
    out = Path("runs") / run_id
    out.mkdir(parents=True, exist_ok=False)
    (out / "final.json").write_text(json.dumps(
        {"run_id": run_id, "started": started, "systems": SYSTEMS, "means": means,
         "hypotheses": H, "holm_H1_H2": adj, "other_comparisons": extra,
         "breal_reviewed_subset": subset}, indent=1, ensure_ascii=False))
    print("| Système | graines | B-SYN nDCG@10 | B-SYN paires | B-REAL nDCG@10 | B-REAL paires |")
    print("|---|---|---|---|---|---|")
    for n, mm in means.items():
        print(f"| {n} | {mm['seeds']} | {mm['bsyn_ndcg']:.3f} | {mm['bsyn_pair']:.3f} | "
              f"{mm['breal_ndcg']:.3f} | {mm['breal_pair']:.3f} |")
    print()
    for k, r in H.items():
        bo, pe = r["bootstrap"], r["permutation"]
        print(f"{k}: Δ {bo['diff']:+.3f} [{bo['ci_low']:+.3f} ; {bo['ci_high']:+.3f}] "
              f"p {pe['p_value']:.4f} ({pe['method']}, {r['n_clusters']} grappes)"
              + (f" p Holm {adj[k]:.4f}" if k in adj else ""))
    print("sous-ensemble relu :", json.dumps(subset, indent=None))
    print(out)


if __name__ == "__main__":
    main()
