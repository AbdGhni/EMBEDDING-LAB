"""Comparaison de systèmes à partir des fichiers de runs (protocole v1.4, § 5).

Lit ``per_query_<bench>_<split>.jsonl`` et ``triplet_wins_<bench>_<split>.json`` de chaque run,
moyenne les graines **requête par requête** (aucune graine n'est sélectionnée), puis compare
deux systèmes avec le test de permutation apparié par grappes (décision) et l'IC bootstrap par
grappes (estimation).

Grappes : projet pour B-SYN ; **composante de personnes** pour B-REAL (groupes d'expérience
reliés par un locuteur commun), comme le prévoit le protocole. Le harnais, lui, regroupe
B-REAL par groupe pour son indicateur de contrôle ``ndcg@10_cluster_mean`` ; les décisions
passent par ce module.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from embedding_lab.eval.metrics import paired_cluster_bootstrap, paired_cluster_permutation_test


def mean_over_seeds(runs: Sequence[Mapping[str, float]]) -> dict[str, float]:
    """Moyenne élément par élément ; toutes les graines doivent couvrir les mêmes éléments.

    >>> mean_over_seeds([{"q1": 1.0, "q2": 0.0}, {"q1": 0.5, "q2": 1.0}])
    {'q1': 0.75, 'q2': 0.5}
    """
    keys = set(runs[0])
    for r in runs[1:]:
        if set(r) != keys:
            raise ValueError("les graines ne couvrent pas les mêmes éléments")
    return {k: sum(r[k] for r in runs) / len(runs) for k in sorted(keys)}


def component_of_groups(groups_by_component: Iterable[Iterable[str]]) -> dict[str, str]:
    """Groupe -> identifiant stable de sa composante (« c » + groupes triés joints par « + »).

    >>> component_of_groups([{"014", "002", "015"}, {"021"}])["015"]
    'c002+014+015'
    """
    out = {}
    for comp in groups_by_component:
        name = "c" + "+".join(sorted(comp))
        for g in comp:
            out[g] = name
    return out


def read_per_query(run_dir: Path, key: str, metric: str = "ndcg@10") -> dict[str, float]:
    path = run_dir / f"per_query_{key}.jsonl"
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return {r["query_id"]: float(r[metric]) for r in rows}


def read_wins(run_dir: Path, key: str) -> dict[str, float]:
    return {k: float(v) for k, v in
            json.loads((run_dir / f"triplet_wins_{key}.json").read_text()).items()}


def compare(a: Mapping[str, float], b: Mapping[str, float], cluster_of: Mapping[str, str],
            n_resamples: int = 10_000, seed: int = 0) -> dict[str, Any]:
    """Différence moyenne a − b, IC 95 % bootstrap par grappes et p de permutation."""
    if set(a) != set(b):
        raise ValueError("systèmes évalués sur des éléments différents")
    boot = paired_cluster_bootstrap(a, b, cluster_of, n_resamples=n_resamples, seed=seed)
    perm = paired_cluster_permutation_test(a, b, cluster_of, n_resamples=n_resamples, seed=seed)
    return {"mean_a": sum(a.values()) / len(a), "mean_b": sum(b.values()) / len(b),
            "n_items": len(a), "n_clusters": len(set(cluster_of[k] for k in a)),
            "bootstrap": boot, "permutation": perm}
