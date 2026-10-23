"""Modèles R0 à R3 (protocole § 10)."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np


class Majority:
    """R0 : classe majoritaire du train."""

    def fit(self, labels: Sequence[str]) -> Majority:
        counts = Counter(labels)
        self.label = max(sorted(counts), key=lambda k: counts[k])
        return self

    def predict(self, n: int) -> list[str]:
        return [self.label] * n


class TypeTable:
    """R1 : classe la plus fréquente du train pour chaque (type X, type Y, même réunion) ;
    repli sur (type X, type Y), puis sur la classe majoritaire.

    >>> t = TypeTable().fit([("answer", "question", True)] * 2 + [("idea", "idea", True)],
    ...                     ["answers", "answers", "none"])
    >>> t.predict([("answer", "question", False), ("risk", "fact", True)])
    ['answers', 'answers']
    """

    def fit(self, keys: Sequence[tuple[str, str, bool]], labels: Sequence[str]) -> TypeTable:
        full: dict[tuple, Counter] = defaultdict(Counter)
        short: dict[tuple, Counter] = defaultdict(Counter)
        for k, y in zip(keys, labels, strict=True):
            full[k][y] += 1
            short[k[:2]][y] += 1

        def top(c: Counter) -> str:
            return max(sorted(c), key=lambda k: c[k])

        self.full = {k: top(c) for k, c in full.items()}
        self.short = {k: top(c) for k, c in short.items()}
        self.default = top(Counter(labels))
        return self

    def predict(self, keys: Sequence[tuple[str, str, bool]]) -> list[str]:
        return [self.full.get(k) or self.short.get(k[:2]) or self.default for k in keys]


def type_key(x: Mapping[str, Any], y: Mapping[str, Any]) -> tuple[str, str, bool]:
    return (x["type"], y["type"], x["source_id"] == y["source_id"])


def fit_logreg(X: np.ndarray, y: Sequence[str], C: float, seed: int = 0):
    """Régression logistique multinomiale, variables standardisées, classes équilibrées."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    model = make_pipeline(StandardScaler(),
                          LogisticRegression(C=C, max_iter=3000, class_weight="balanced",
                                             random_state=seed))
    return model.fit(X, list(y))
