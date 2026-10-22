"""Baseline lexicale E0 : BM25 (Okapi) avec une tokenisation adaptée à SUMM-RE.

Tokenisation : minuscules, « _ » des mots composés SUMM-RE remplacé par une espace,
jetons de masquage ``w_N`` / ``sil`` retirés, puis mots ``\\w+``. Pas de racinisation ni de
mots vides (choix simple et documenté : tout raffinement serait une autre baseline).

Exemple ::

    >>> tokenize("bon c'est validé on_part sur w_3 sil juin")
    ['bon', 'c', 'est', 'validé', 'on', 'part', 'sur', 'juin']
    >>> r = BM25Retriever()
    >>> units = [{"unit_id": "u-1", "retrieval_text": "le budget est validé"},
    ...          {"unit_id": "u-2", "retrieval_text": "la date de lancement"}]
    >>> [uid for uid, _ in r.rank("quel budget", units)]
    ['u-1', 'u-2']
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from rank_bm25 import BM25Okapi

_MASK = re.compile(r"\bw_\d+\b|\bsil\b")
_WORD = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    text = _MASK.sub(" ", text.lower()).replace("_", " ")
    return _WORD.findall(text)


def unit_text(unit: Mapping[str, Any]) -> str:
    return unit.get("retrieval_text") or unit["evidence"]["text"]


class BM25Retriever:
    """Classe les unités candidates d'une requête. L'IDF est calculé sur les candidats,
    c'est-à-dire sur le corpus de recherche de la requête (split pour B-SYN, groupe pour
    B-REAL)."""

    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self._cache: dict[tuple[str, ...], BM25Okapi] = {}

    def config(self) -> dict[str, Any]:
        return {"system": self.name, "k1": self.k1, "b": self.b,
                "tokenizer": "lower|underscore->space|drop w_N,sil|\\w+",
                "text_field": "retrieval_text"}

    def _index(self, units: Sequence[Mapping[str, Any]]) -> BM25Okapi:
        key = tuple(u["unit_id"] for u in units)
        if key not in self._cache:
            self._cache[key] = BM25Okapi([tokenize(unit_text(u)) for u in units],
                                         k1=self.k1, b=self.b)
        return self._cache[key]

    def score(self, query: str, units: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        scores = self._index(units).get_scores(tokenize(query))
        return {u["unit_id"]: float(s) for u, s in zip(units, scores, strict=True)}

    def rank(self, query: str, units: Sequence[Mapping[str, Any]]) -> list[tuple[str, float]]:
        scores = self.score(query, units)
        return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
