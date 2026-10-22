"""Plancher de comparaison : classement aléatoire déterministe (graine fixe)."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any


class RandomRetriever:
    name = "random"

    def __init__(self, seed: int = 0):
        self.seed = seed

    def config(self) -> dict[str, Any]:
        return {"system": self.name, "seed": self.seed}

    def score(self, query: str, units: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        def h(uid: str) -> float:
            d = hashlib.sha256(f"{self.seed}|{query}|{uid}".encode()).digest()
            return int.from_bytes(d[:8], "big") / 2**64
        return {u["unit_id"]: h(u["unit_id"]) for u in units}
