"""Métriques de recherche, précision sur pièges et bootstrap par grappes (protocole v1.0, § 3–4).

Conventions :
- ``ranking`` : liste d'identifiants d'unités, du plus au moins pertinent selon le système.
- ``qrels`` : dict unit_id -> pertinence graduée (0, 1, 2). Les absents valent 0.
- Une requête sans unité de pertinence >= 1 lève une erreur : elle doit être exclue en amont
  (le protocole la mesure séparément, comme cas d'abstention).

Exemple (calculable à la main) ::

    >>> qrels = {"u-a": 2, "u-b": 1}
    >>> # DCG = 3/log2(3) + 1/log2(4) = 2.3928 ; IDCG = 3/log2(2) + 1/log2(3) = 3.6309
    >>> round(ndcg_at_k(["u-x", "u-a", "u-b"], qrels, 10), 3)
    0.659
    >>> mrr_at_k(["u-x", "u-a"], qrels, 10)
    0.5
    >>> recall_at_k(["u-x", "u-a"], qrels, 1)
    0.0
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence


def _check(qrels: Mapping[str, int]) -> None:
    if not any(r >= 1 for r in qrels.values()):
        raise ValueError("requête sans unité pertinente : à exclure des métriques de recherche")


def dcg_at_k(ranking: Sequence[str], qrels: Mapping[str, int], k: int) -> float:
    return sum((2 ** qrels.get(u, 0) - 1) / math.log2(i + 2) for i, u in enumerate(ranking[:k]))


def ndcg_at_k(ranking: Sequence[str], qrels: Mapping[str, int], k: int = 10) -> float:
    _check(qrels)
    ideal = sorted(qrels.values(), reverse=True)[:k]
    idcg = sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg_at_k(ranking, qrels, k) / idcg


def recall_at_k(ranking: Sequence[str], qrels: Mapping[str, int], k: int) -> float:
    _check(qrels)
    relevant = {u for u, r in qrels.items() if r >= 1}
    return len(relevant & set(ranking[:k])) / len(relevant)


def mrr_at_k(ranking: Sequence[str], qrels: Mapping[str, int], k: int = 10) -> float:
    _check(qrels)
    for i, u in enumerate(ranking[:k]):
        if qrels.get(u, 0) >= 1:
            return 1.0 / (i + 1)
    return 0.0


def pairwise_accuracy(pairs: Sequence[tuple[float, float]]) -> float:
    """(score_positif, score_négatif) -> proportion de victoires ; ex æquo = 0,5."""
    if not pairs:
        raise ValueError("aucun triplet")
    return sum(1.0 if p > n else 0.5 if p == n else 0.0 for p, n in pairs) / len(pairs)


def evaluate_run(
    rankings: Mapping[str, Sequence[str]],
    qrels: Mapping[str, Mapping[str, int]],
    ks: Sequence[int] = (1, 5, 10),
) -> dict[str, dict[str, float]]:
    """Scores par requête : {query_id: {"ndcg@10": ..., "recall@1": ..., "mrr@10": ...}}.

    Une requête jugée mais absente de ``rankings`` reçoit 0 (le système n'a rien renvoyé).
    """
    out = {}
    for qid, rel in qrels.items():
        r = list(rankings.get(qid, []))
        scores = {"ndcg@10": ndcg_at_k(r, rel, 10), "mrr@10": mrr_at_k(r, rel, 10)}
        scores.update({f"recall@{k}": recall_at_k(r, rel, k) for k in ks})
        out[qid] = scores
    return out


def mean_metric(per_query: Mapping[str, Mapping[str, float]], metric: str) -> float:
    return sum(s[metric] for s in per_query.values()) / len(per_query)


def paired_cluster_bootstrap(
    a: Mapping[str, float],
    b: Mapping[str, float],
    cluster_of: Mapping[str, str],
    n_resamples: int = 10_000,
    seed: int = 0,
    alpha: float = 0.05,
    stat: Callable[[Sequence[float]], float] | None = None,
) -> dict[str, float]:
    """IC de la différence moyenne (a − b), en rééchantillonnant des grappes entières.

    ``a`` et ``b`` : score par requête des deux systèmes (mêmes requêtes). ``cluster_of`` :
    requête -> grappe (projet, composante de personnes).
    """
    if set(a) != set(b):
        raise ValueError("les deux systèmes doivent être évalués sur les mêmes requêtes")
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for q in a:
        by_cluster[cluster_of[q]].append(a[q] - b[q])
    clusters = sorted(by_cluster)
    mean = stat or (lambda xs: sum(xs) / len(xs))
    observed = mean([d for c in clusters for d in by_cluster[c]])
    rng = random.Random(seed)
    stats = []
    for _ in range(n_resamples):
        sample = [d for c in rng.choices(clusters, k=len(clusters)) for d in by_cluster[c]]
        stats.append(mean(sample))
    stats.sort()
    lo = stats[int(math.floor(alpha / 2 * n_resamples))]
    hi = stats[min(n_resamples - 1, int(math.ceil((1 - alpha / 2) * n_resamples)) - 1)]
    return {"diff": observed, "ci_low": lo, "ci_high": hi,
            "n_queries": len(a), "n_clusters": len(clusters)}
