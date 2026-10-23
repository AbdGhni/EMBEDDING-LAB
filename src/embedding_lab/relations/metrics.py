"""Macro-F1, précision/rappel par classe, matrice de confusion, IC bootstrap par grappes."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


def per_class(gold: Sequence[str], pred: Sequence[str], labels: Sequence[str]
              ) -> dict[str, dict[str, float]]:
    out = {}
    for c in labels:
        tp = sum(1 for g, p in zip(gold, pred, strict=True) if g == c and p == c)
        fp = sum(1 for g, p in zip(gold, pred, strict=True) if g != c and p == c)
        fn = sum(1 for g, p in zip(gold, pred, strict=True) if g == c and p != c)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        out[c] = {"precision": prec, "recall": rec, "f1": f1, "support": tp + fn}
    return out


def macro_f1(gold: Sequence[str], pred: Sequence[str], labels: Sequence[str]) -> float:
    """Moyenne des F1 sur les classes **présentes dans l'or** (une classe absente n'est pas
    comptée, pour que B-SYN, sans ``supports``, reste comparable à lui-même).

    >>> round(macro_f1(["a", "a", "b"], ["a", "b", "b"], ["a", "b", "c"]), 3)
    0.667
    """
    present = [c for c in labels if c in set(gold)]
    pc = per_class(gold, pred, present)
    return sum(pc[c]["f1"] for c in present) / len(present) if present else 0.0


def confusion(gold: Sequence[str], pred: Sequence[str], labels: Sequence[str]
              ) -> dict[str, dict[str, int]]:
    m = {g: {p: 0 for p in labels} for g in labels}
    for g, p in zip(gold, pred, strict=True):
        m[g][p] += 1
    return m


def bootstrap_macro_f1(gold: Sequence[str], pred: Sequence[str], clusters: Sequence[str],
                       labels: Sequence[str], n_resamples: int = 10_000, seed: int = 0,
                       other: Sequence[str] | None = None) -> dict[str, Any]:
    """IC 95 % du macro-F1 (ou de la différence avec ``other``), en tirant des grappes."""
    by_c: dict[str, list[int]] = defaultdict(list)
    for i, c in enumerate(clusters):
        by_c[c].append(i)
    keys = sorted(by_c)
    rng = random.Random(seed)

    def stat(idx: list[int]) -> float:
        g = [gold[i] for i in idx]
        v = macro_f1(g, [pred[i] for i in idx], labels)
        if other is not None:
            v -= macro_f1(g, [other[i] for i in idx], labels)
        return v

    observed = stat(list(range(len(gold))))
    stats = sorted(stat([i for k in rng.choices(keys, k=len(keys)) for i in by_c[k]])
                   for _ in range(n_resamples))
    return {"value": observed, "ci_low": stats[int(0.025 * n_resamples)],
            "ci_high": stats[int(0.975 * n_resamples) - 1], "n_clusters": len(keys)}


def report(gold: Sequence[str], pred: Sequence[str], labels: Sequence[str]) -> dict[str, Any]:
    pos = [i for i, g in enumerate(gold) if g != "none"]
    rel_labels = [c for c in labels if c != "none"]
    return {"macro_f1": macro_f1(gold, pred, labels),
            "macro_f1_relations_only": macro_f1([gold[i] for i in pos], [pred[i] for i in pos],
                                                rel_labels),
            "accuracy": sum(g == p for g, p in zip(gold, pred, strict=True)) / len(gold),
            "per_class": per_class(gold, pred, labels),
            "confusion": confusion(gold, pred, labels), "n": len(gold)}


def majority(train_labels: Sequence[str]) -> str:
    counts: Mapping[str, int] = defaultdict(int)
    for x in train_labels:
        counts[x] += 1  # type: ignore[index]
    return max(sorted(counts), key=lambda k: counts[k])
