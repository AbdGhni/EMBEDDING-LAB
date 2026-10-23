"""Couples d'unités orientés dans le temps (X récent, Y ancien) et leurs étiquettes.

Le sens chronologique est imposé par construction : le module ne voit jamais un couple où
l'unité « remplaçante » serait la plus ancienne (exigence C-06).
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

LABELS = ("supersedes", "contradicts", "answers", "supports", "creates_action", "none")
RELATIONS = LABELS[:-1]


def order_key(u: Mapping[str, Any]) -> tuple:
    """Position chronologique : rang de réunion, tour, position dans le texte.

    >>> a = {"unit_id": "a", "source_order": 0,
    ...      "evidence": {"segment_ids": ["m:t0009"], "char_start": 5}}
    >>> b = {"unit_id": "b", "source_order": 1,
    ...      "evidence": {"segment_ids": ["n:t0001"], "char_start": 0}}
    >>> order_key(a) < order_key(b)
    True
    """
    ev = u["evidence"]
    seg = (ev.get("segment_ids") or [""])[0].rsplit(":", 1)[-1]
    return (u.get("source_order") or 0, u.get("source_date") or "", seg, ev["char_start"],
            u["unit_id"])


def group_of(u: Mapping[str, Any]) -> str:
    return str(u["project"])


def orient(a: Mapping[str, Any], b: Mapping[str, Any]) -> tuple[Mapping, Mapping]:
    """(plus récente, plus ancienne)."""
    return (a, b) if order_key(a) > order_key(b) else (b, a)


def positive_pairs(relations: Iterable[Mapping[str, Any]],
                   units: Mapping[str, Mapping[str, Any]]) -> list[dict]:
    """Relations annotées, remises dans le sens (récente, ancienne).

    ``creates_action`` est annotée de la décision (ancienne) vers l'action (récente) : la
    réorientation garde la classe. Les doublons (même couple) gardent la première relation
    rencontrée ; ils sont comptés pour être rapportés.
    """
    out, seen = [], set()
    for r in relations:
        if r["relation"] == "unrelated":
            continue
        x, y = orient(units[r["from_id"]], units[r["to_id"]])
        key = (x["unit_id"], y["unit_id"])
        if key in seen:
            continue
        seen.add(key)
        out.append({"x": x["unit_id"], "y": y["unit_id"], "label": r["relation"],
                    "group": group_of(x), "flipped": x["unit_id"] != r["from_id"]})
    return out


def none_pairs(relations: Iterable[Mapping[str, Any]], units: Mapping[str, Mapping[str, Any]],
               n_per_group: Mapping[str, int], seed: int = 0) -> list[dict]:
    """Couples non reliés, tirés dans le même groupe ; même réunion ou réunion voisine d'abord.

    B-SYN fournit ses propres couples ``unrelated`` : ils sont utilisés tels quels.
    """
    rels = list(relations)
    linked = {frozenset((r["from_id"], r["to_id"])) for r in rels}
    explicit = [r for r in rels if r["relation"] == "unrelated"]
    if explicit:
        out = []
        for r in explicit:
            x, y = orient(units[r["from_id"]], units[r["to_id"]])
            out.append({"x": x["unit_id"], "y": y["unit_id"], "label": "none",
                        "group": group_of(x), "flipped": False})
        return out
    rng = random.Random(seed)
    by_group: dict[str, list[Mapping]] = defaultdict(list)
    for u in units.values():
        by_group[group_of(u)].append(u)
    out = []
    for g in sorted(n_per_group):
        members = sorted(by_group[g], key=order_key)
        near, far = [], []
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if frozenset((a["unit_id"], b["unit_id"])) in linked:
                    continue
                gap = abs((a.get("source_order") or 0) - (b.get("source_order") or 0))
                (near if gap <= 1 else far).append((a, b))
        rng.shuffle(near)
        rng.shuffle(far)
        for a, b in (near + far)[: n_per_group[g]]:
            x, y = orient(a, b)
            out.append({"x": x["unit_id"], "y": y["unit_id"], "label": "none", "group": g,
                        "flipped": False})
    return out


def build_pairs(relations: Sequence[Mapping[str, Any]],
                units: Mapping[str, Mapping[str, Any]], seed: int = 0) -> list[dict]:
    """Positifs + un négatif ``none`` par positif et par groupe (sauf négatifs explicites)."""
    pos = positive_pairs(relations, units)
    counts: dict[str, int] = defaultdict(int)
    for p in pos:
        counts[p["group"]] += 1
    return pos + none_pairs(relations, units, counts, seed=seed)
