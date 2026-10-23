"""R2 entraîné sur les trains, utilisable à la volée (rétrogradation E4, agent)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from embedding_lab.relations.features import structural, structural_matrix
from embedding_lab.relations.models import fit_logreg
from embedding_lab.relations.pairs import build_pairs

R2_C = 0.1  # choisi sur B-REAL val (run R-val-2026-10-23T1316)


def _read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class R2Predictor:
    def __init__(self, root: Path = Path("."), C: float = R2_C):
        X, y, shas = [], [], {}
        for bench in ("breal", "bsyn"):
            base = root / "data" / bench / "train"
            units = {u["unit_id"]: u for u in _read_jsonl(base / "units.jsonl")}
            pairs = build_pairs(_read_jsonl(base / "relations.jsonl"), units, seed=0)
            X.append(structural_matrix(pairs, units))
            y += [p["label"] for p in pairs]
            shas[bench] = hashlib.sha256((base / "relations.jsonl").read_bytes()).hexdigest()
        self.model = fit_logreg(np.vstack(X), y, C)
        self.idx = list(self.model.classes_).index("supersedes")
        self.C, self.shas = C, shas
        self._cache: dict[tuple[str, str], float] = {}

    def config(self) -> dict[str, Any]:
        return {"model": "R2", "C": self.C, "train_relations_sha256": self.shas}

    def p_supersedes(self, x: Mapping[str, Any], y: Mapping[str, Any]) -> float:
        key = (x["unit_id"], y["unit_id"])
        if key not in self._cache:
            v = np.array([structural(x, y)], dtype=np.float32)
            self._cache[key] = float(self.model.predict_proba(v)[0, self.idx])
        return self._cache[key]


@lru_cache(maxsize=1)
def default_predictor() -> R2Predictor:
    return R2Predictor()
