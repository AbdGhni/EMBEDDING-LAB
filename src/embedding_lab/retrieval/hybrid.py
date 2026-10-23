"""E4 : fusion RRF et rétrogradation des unités remplacées (protocole § 11).

Chaque système garde l'interface du harnais : ``config()`` et ``score(query, units)``. Les
scores renvoyés respectent l'ordre final, pour que nDCG et la précision par paires mesurent
bien le classement après fusion ou rétrogradation.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from embedding_lab.relations.pairs import group_of, orient


def ranks(scores: Mapping[str, float]) -> dict[str, int]:
    """Rang (1 = meilleur), égalités départagées par identifiant comme dans le harnais."""
    order = sorted(scores, key=lambda u: (-scores[u], u))
    return {u: i + 1 for i, u in enumerate(order)}


def rrf(score_dicts: Sequence[Mapping[str, float]], k: int = 60) -> dict[str, float]:
    """Reciprocal Rank Fusion à poids égaux.

    >>> f = rrf([{"a": 3.0, "b": 1.0}, {"a": 0.1, "b": 0.9}], k=60)
    >>> round(f["a"], 5) == round(f["b"], 5)
    True
    """
    rk = [ranks(s) for s in score_dicts]
    return {u: sum(1.0 / (k + r[u]) for r in rk) for u in score_dicts[0]}


def demote(scores: Mapping[str, float], units: Mapping[str, Mapping[str, Any]],
           p_supersedes: Callable[[Mapping, Mapping], float], top: int = 20,
           threshold: float = 0.5) -> tuple[dict[str, float], list[tuple[str, str]]]:
    """Place chaque unité remplacée juste sous sa remplaçante, parmi les ``top`` premières.

    ``p_supersedes(x, y)`` : probabilité que x (récente) remplace y (ancienne). Seuls les
    couples d'un même projet ou groupe sont testés. Renvoie les nouveaux scores et les couples
    (remplaçante, remplacée) appliqués.
    """
    order = sorted(scores, key=lambda u: (-scores[u], u))
    head, tail = order[:top], order[top:]
    replaced_by: dict[str, str] = {}
    for i, a in enumerate(head):
        for b in head[i + 1:]:
            ua, ub = units[a], units[b]
            if group_of(ua) != group_of(ub):
                continue
            x, y = orient(ua, ub)
            if p_supersedes(x, y) >= threshold:
                xid, yid = x["unit_id"], y["unit_id"]
                if yid not in replaced_by:
                    replaced_by[yid] = xid
    applied = []
    new = list(head)
    for yid, xid in replaced_by.items():
        if new.index(yid) < new.index(xid):
            new.remove(yid)
            new.insert(new.index(xid) + 1, yid)
            applied.append((xid, yid))
    base = max(scores.values()) if scores else 0.0
    out = {u: scores[u] for u in tail}
    for i, u in enumerate(new):
        out[u] = base + 1.0 + (len(new) - i)
    return out, applied


class RRFSystem:
    name = "rrf"

    def __init__(self, systems: Sequence[Any], k: int = 60):
        self.systems, self.k = list(systems), k

    def config(self) -> dict[str, Any]:
        return {"system": self.name, "k": self.k, "components": [s.config() for s in self.systems]}

    def score(self, query: str, units: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        return rrf([s.score(query, units) for s in self.systems], k=self.k)


class DemoteSystem:
    name = "demote"

    def __init__(self, base: Any, p_supersedes: Callable[[Mapping, Mapping], float],
                 predictor_config: Mapping[str, Any], top: int = 20, threshold: float = 0.5):
        self.base, self.p = base, p_supersedes
        self.top, self.threshold, self.predictor_config = top, threshold, dict(predictor_config)
        self.applied = 0

    def config(self) -> dict[str, Any]:
        return {"system": self.name, "top": self.top, "threshold": self.threshold,
                "predictor": self.predictor_config, "base": self.base.config()}

    def score(self, query: str, units: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        by_id = {u["unit_id"]: u for u in units}
        new, applied = demote(self.base.score(query, units), by_id, self.p, self.top,
                              self.threshold)
        self.applied += len(applied)
        return new
