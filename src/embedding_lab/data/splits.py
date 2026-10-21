"""Découpage train / val / test sans fuite de personnes ni de projets.

Unité de découpage : **composante connexe** de groupes d'expérience reliés par au moins un
identifiant de locuteur commun. Deux groupes qui partagent une personne finissent toujours
dans le même split ; les trois réunions (a/b/c) d'un groupe aussi.

Exemple ::

    >>> ms = [
    ...   {"meeting_id": "001a_X", "group_id": "001", "speakers": ["p1", "p2"]},
    ...   {"meeting_id": "002a_X", "group_id": "002", "speakers": ["p2", "p3"]},
    ...   {"meeting_id": "003a_X", "group_id": "003", "speakers": ["p9"]},
    ... ]
    >>> sorted(sorted(c) for c in group_components(ms))
    [['001', '002'], ['003']]
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

SPLITS = ("train", "val", "test")


def group_components(meetings: Iterable[Mapping[str, Any]]) -> list[set[str]]:
    """Composantes connexes de groupes liés par un locuteur commun (union-find)."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_speaker: dict[str, set[str]] = defaultdict(set)
    for m in meetings:
        if not m["speakers"]:
            # une réunion sans locuteur échapperait au contrôle des personnes partagées
            raise ValueError(f"réunion sans locuteur : {m['meeting_id']}")
        parent.setdefault(m["group_id"], m["group_id"])
        for s in m["speakers"]:
            by_speaker[s].add(m["group_id"])
    for groups in by_speaker.values():
        first, *rest = sorted(groups)
        for g in rest:
            parent[find(g)] = find(first)
    comps: dict[str, set[str]] = defaultdict(set)
    for g in parent:
        comps[find(g)].add(g)
    return sorted(comps.values(), key=lambda c: (-len(c), min(c)))


def _counts(meetings: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    manual = [m for m in meetings if m.get("transcription") == "manual"]
    return {
        "meetings": len(meetings),
        "manual": len(manual),
        "manual_decision": sum(m.get("meeting_type") == "decision" for m in manual),
    }


def assign_splits(
    meetings: Sequence[Mapping[str, Any]],
    targets: Mapping[str, Mapping[str, int]],
    seed: int = 13,
    trials: int = 20000,
    max_component_share: float = 0.15,
) -> dict[str, str]:
    """Affecte chaque composante à un split ; renvoie meeting_id -> split.

    Les composantes trop grosses (> ``max_component_share`` des réunions) vont d'office en
    train : elles déséquilibreraient val/test. Pour les autres, on tire ``trials`` affectations
    aléatoires (graine fixe) et on garde celle qui s'approche le plus des cibles de val et test
    (nombre de réunions manuelles et de réunions manuelles de décision).
    """
    by_group: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for m in meetings:
        by_group[m["group_id"]].append(m)
    comps = group_components(meetings)
    n_total = len(meetings)
    comp_meetings = [[m for g in sorted(c) for m in by_group[g]] for c in comps]
    forced = [len(cm) > max_component_share * n_total for cm in comp_meetings]

    rng = random.Random(seed)
    best, best_score = None, float("inf")
    for _ in range(trials):
        choice = ["train" if forced[i] else rng.choice(SPLITS) for i in range(len(comps))]
        score = 0.0
        for split in ("val", "test"):
            sel = [m for i, cm in enumerate(comp_meetings) if choice[i] == split for m in cm]
            c = _counts(sel)
            score += sum(abs(c[k] - v) for k, v in targets[split].items())
        if score < best_score:
            best, best_score = choice, score
    assert best is not None
    return {m["meeting_id"]: best[i] for i, cm in enumerate(comp_meetings) for m in cm}


_WORD = re.compile(r"\w+", re.UNICODE)


def ngrams(text: str, n: int = 8) -> set[tuple[str, ...]]:
    toks = _WORD.findall(text.lower())
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def leakage_report(
    meetings: Sequence[Mapping[str, Any]], split_of: Mapping[str, str], n: int = 8
) -> dict[str, Any]:
    """Contrôles : groupes et locuteurs partagés entre splits, recouvrement de n-grammes."""
    groups: dict[str, set[str]] = defaultdict(set)
    speakers: dict[str, set[str]] = defaultdict(set)
    for m in meetings:
        s = split_of[m["meeting_id"]]
        groups[m["group_id"]].add(s)
        for p in m["speakers"]:
            speakers[p].add(s)
    train_grams: set[tuple[str, ...]] = set()
    for m in meetings:
        if split_of[m["meeting_id"]] == "train":
            train_grams |= ngrams(m["text"], n)
    overlap = {}
    for m in meetings:
        if split_of[m["meeting_id"]] != "train":
            g = ngrams(m["text"], n)
            overlap[m["meeting_id"]] = round(len(g & train_grams) / len(g), 4) if g else 0.0
    vals = sorted(overlap.values())
    return {
        "groups_in_several_splits": sorted(g for g, s in groups.items() if len(s) > 1),
        "speakers_in_several_splits": sorted(p for p, s in speakers.items() if len(s) > 1),
        f"{n}gram_overlap_with_train": {
            "max": vals[-1] if vals else 0.0,
            "median": vals[len(vals) // 2] if vals else 0.0,
            "top5": sorted(overlap.items(), key=lambda kv: -kv[1])[:5],
        },
    }
