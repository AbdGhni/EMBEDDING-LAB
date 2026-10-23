"""Variables des couples (X récent, Y ancien) pour les modèles R1 à R3."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

TYPES = ("fact", "idea", "decision", "question", "answer", "action", "commitment", "risk")
# indices lexicaux de changement ou de négation dans l'unité récente (liste fixée a priori)
CUES = ("finalement", "plutôt", "au lieu", "à la place", "change", "non", "pas", "plus",
        "annul", "report", "d'accord", "ok", "oui", "parce que", "donc")
_WORD = re.compile(r"[a-zàâçéèêëîïôûùüÿœæ0-9_']+")
_NUM = re.compile(r"\d|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|cent|mille|euro")


def words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower().replace("_", " ")) if len(w) > 2}


def turn_index(u: Mapping[str, Any]) -> int | None:
    seg = (u["evidence"].get("segment_ids") or [None])[0]
    if not seg:
        return None
    m = re.search(r"t(\d+)$", seg)
    return int(m.group(1)) if m else None


def structural(x: Mapping[str, Any], y: Mapping[str, Any]) -> list[float]:
    """Variables sans plongement. Les statuts ne sont **pas** utilisés : dans les annotations,
    le statut d'une question (« resolved ») découle de la relation elle-même (fuite)."""
    tx = [1.0 if x["type"] == t else 0.0 for t in TYPES]
    ty = [1.0 if y["type"] == t else 0.0 for t in TYPES]
    pair = [1.0 if (x["type"], y["type"]) == (a, b) else 0.0 for a in TYPES for b in TYPES]
    same_meeting = float(x["source_id"] == y["source_id"])
    gap = abs((x.get("source_order") or 0) - (y.get("source_order") or 0))
    ix, iy = turn_index(x), turn_index(y)
    turn_gap = math.log1p(abs(ix - iy)) if same_meeting and ix is not None and iy is not None \
        else 0.0
    wx, wy = words(x["evidence"]["text"]), words(y["evidence"]["text"])
    jacc = len(wx & wy) / len(wx | wy) if wx | wy else 0.0
    tx_low = x["evidence"]["text"].lower()
    cues = [1.0 if c in tx_low else 0.0 for c in CUES]
    return [*tx, *ty, *pair, same_meeting, float(gap == 1), float(gap >= 2), turn_gap,
            float(x.get("speaker") == y.get("speaker")), jacc,
            float(bool(_NUM.search(tx_low))),
            float(bool(_NUM.search(y["evidence"]["text"].lower()))), *cues]


def structural_matrix(pairs: Sequence[Mapping[str, Any]],
                      units: Mapping[str, Mapping[str, Any]]) -> np.ndarray:
    return np.array([structural(units[p["x"]], units[p["y"]]) for p in pairs], dtype=np.float32)


def embedding_matrix(pairs: Sequence[Mapping[str, Any]], vec: Mapping[str, np.ndarray]
                     ) -> np.ndarray:
    """``[x, y, x·y, |x − y|]`` à partir de plongements normalisés par unité."""
    rows = []
    for p in pairs:
        a, b = vec[p["x"]], vec[p["y"]]
        rows.append(np.concatenate([a, b, a * b, np.abs(a - b)]))
    return np.array(rows, dtype=np.float32)
