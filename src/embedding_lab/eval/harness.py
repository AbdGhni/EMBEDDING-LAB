"""Point d'entrée **unique** d'évaluation (protocole v1.4, § 5 et § 7).

Tous les systèmes (BM25, encodeurs initial et fine-tuné, hybrides) passent par
``run_benchmark``, qui ne diffère d'un système à l'autre que par l'objet ``system`` :
mêmes requêtes, mêmes corpus, mêmes métriques, mêmes triplets. Un système expose
``config()`` et ``score(query, units) -> {unit_id: score}``.

Le split ``test`` n'est chargé qu'avec un motif, inscrit dans ``runs/TEST_ACCESS.log``.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import time
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from embedding_lab.eval.metrics import evaluate_run, mean_metric, pairwise_win
from embedding_lab.eval.test_access import DEFAULT_LOG, log_test_access

HARNESS_VERSION = "1.0"
BENCHMARKS = {"bsyn": "data/bsyn", "breal": "data/breal"}
METRICS = ("ndcg@10", "mrr@10", "recall@1", "recall@5", "recall@10")


class System(Protocol):
    def config(self) -> dict[str, Any]: ...
    def score(self, query: str, units: list[Mapping[str, Any]]) -> dict[str, float]: ...


def _read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_benchmark(name: str, split: str, *, test_reason: str | None = None,
                   run_id: str = "unknown", root: Path = Path("."),
                   access_log: Path = DEFAULT_LOG) -> dict[str, Any]:
    if name not in BENCHMARKS:
        raise ValueError(f"benchmark inconnu : {name}")
    if split == "test":
        if not test_reason:
            raise PermissionError("accès au test refusé : motif obligatoire (protocole § 7)")
        log_test_access(run_id, test_reason, f"{name}/test", root / access_log)
    base = root / BENCHMARKS[name] / split
    files = {k: base / f"{k}.jsonl" for k in ("units", "queries", "triplets")}
    files["qrels"] = base / "qrels.json"
    units = _read_jsonl(files["units"])
    queries = [q for q in _read_jsonl(files["queries"]) if q["answerable"]]
    qrels = json.loads(files["qrels"].read_text(encoding="utf-8"))
    triplets = _read_jsonl(files["triplets"])
    # portée de recherche : tout le split (B-SYN) ou le groupe de la requête (B-REAL)
    if name == "bsyn":
        scope_of = {q["query_id"]: "all" for q in queries}
        scopes = {"all": units}
        cluster_of = {q["query_id"]: q["cluster"] for q in queries}
    else:
        by_group: dict[str, list] = defaultdict(list)
        for u in units:
            by_group[u["project"].removeprefix("summre-")].append(u)
        scopes = dict(by_group)
        scope_of = {q["query_id"]: q["group_id"] for q in queries}
        cluster_of = {q["query_id"]: q["group_id"] for q in queries}
    return {"name": name, "split": split, "units": {u["unit_id"]: u for u in units},
            "queries": queries, "qrels": qrels, "triplets": triplets, "scopes": scopes,
            "scope_of": scope_of, "cluster_of": cluster_of,
            "sha256": {k: _sha(p) for k, p in files.items()}}


def config_fingerprint(system_config: Mapping[str, Any], bench: Mapping[str, Any]) -> str:
    blob = json.dumps({"system": system_config, "data": bench["sha256"],
                       "harness": HARNESS_VERSION}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def run_benchmark(system: System, bench: Mapping[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    rankings, scores_by_q = {}, {}
    for q in bench["queries"]:
        cands = bench["scopes"][bench["scope_of"][q["query_id"]]]
        scores = system.score(q["text"], cands)
        scores_by_q[q["query_id"]] = scores
        rankings[q["query_id"]] = [u for u, _ in sorted(scores.items(),
                                                         key=lambda kv: (-kv[1], kv[0]))]
    qrels = {q["query_id"]: bench["qrels"][q["query_id"]] for q in bench["queries"]}
    per_query = evaluate_run(rankings, qrels)
    wins, by_trap = {}, defaultdict(list)
    for i, t in enumerate(bench["triplets"]):
        s = scores_by_q.get(t["query_id"])
        if s is None:
            continue
        if t["neg"] not in s or t["pos"] not in s:
            raise ValueError(f"triplet hors du corpus de recherche : {t}")
        w = pairwise_win(s[t["pos"]], s[t["neg"]])
        wins[f"t{i:05d}"] = w
        by_trap[t["trap"]].append(w)
    elapsed = time.perf_counter() - t0
    summary = {m: mean_metric(per_query, m) for m in METRICS}
    summary["pairwise_accuracy"] = sum(wins.values()) / len(wins) if wins else None
    summary["pairwise_by_trap"] = {k: {"n": len(v), "acc": sum(v) / len(v)}
                                   for k, v in sorted(by_trap.items())}
    clusters = defaultdict(list)
    for qid, s in per_query.items():
        clusters[bench["cluster_of"][qid]].append(s["ndcg@10"])
    summary["ndcg@10_cluster_mean"] = sum(sum(v) / len(v) for v in clusters.values()) / len(
        clusters)
    return {"summary": summary, "per_query": per_query, "triplet_wins": wins,
            "n_queries": len(per_query), "n_clusters": len(clusters),
            "n_triplets": len(wins), "seconds": round(elapsed, 3),
            "fingerprint": config_fingerprint(system.config(), bench),
            "rankings_top10": {q: r[:10] for q, r in rankings.items()}}


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_run(run_dir: Path, system: System, results: Mapping[str, Mapping[str, Any]],
              started: str, finished: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(system.config(), indent=1))
    manifest = {"run_id": run_dir.name, "harness_version": HARNESS_VERSION,
                "git_commit": _git("rev-parse", "HEAD"),
                # fichiers suivis modifiés OU nouveaux fichiers de code non commités
                "git_dirty": bool(_git("status", "--porcelain", "--", "src", "scripts",
                                       "pyproject.toml", "uv.lock")),
                "python": platform.python_version(), "machine": platform.platform(),
                "started": started, "finished": finished,
                "benchmarks": {k: {"fingerprint": v["fingerprint"], "n_queries": v["n_queries"],
                                   "n_clusters": v["n_clusters"], "n_triplets": v["n_triplets"],
                                   "seconds": v["seconds"]} for k, v in results.items()}}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    for key, res in results.items():
        (run_dir / f"metrics_{key}.json").write_text(json.dumps(res["summary"], indent=1))
        with open(run_dir / f"per_query_{key}.jsonl", "w", encoding="utf-8") as f:
            for qid, s in sorted(res["per_query"].items()):
                f.write(json.dumps({"query_id": qid, **s,
                                    "top10": res["rankings_top10"][qid]}) + "\n")
        (run_dir / f"triplet_wins_{key}.json").write_text(json.dumps(res["triplet_wins"]))
