"""Encodeur dense (E1 : modèle initial ; E2 : même architecture, poids fine-tunés).

Conventions vérifiées sur la fiche du modèle à révision figée (protocole § 5) :
préfixes « query: » / « passage: », pooling moyen, normalisation L2, cosinus = produit
scalaire. Évaluation en fp32 pour E1 comme pour E2.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from embedding_lab.retrieval.bm25 import unit_text

E5_SMALL = ("intfloat/multilingual-e5-small", "614241f622f53c4eeff9890bdc4f31cfecc418b3")


class DenseRetriever:
    name = "dense"

    def __init__(self, model_name: str = E5_SMALL[0], revision: str | None = E5_SMALL[1],
                 max_seq_length: int = 128, batch_size: int = 64, device: str = "cpu",
                 query_prefix: str = "query: ", passage_prefix: str = "passage: ",
                 model: Any = None, weights: str | None = None):
        """``model`` : modèle déjà chargé (évaluation pendant l'entraînement) ; ``weights`` :
        identifiant des poids fine-tunés (dossier de checkpoint et empreinte), pour la config."""
        from sentence_transformers import SentenceTransformer

        self.model_name, self.revision, self.weights = model_name, revision, weights
        self.query_prefix, self.passage_prefix = query_prefix, passage_prefix
        self.batch_size, self.device = batch_size, device
        self.model = model or SentenceTransformer(model_name, revision=revision, device=device)
        self.model.max_seq_length = max_seq_length
        self._cache: dict[str, np.ndarray] = {}
        self.truncated = 0

    def config(self) -> dict[str, Any]:
        return {"system": self.name, "model": self.model_name, "revision": self.revision,
                "weights": self.weights or "pretrained",
                "max_seq_length": self.model.max_seq_length, "dtype": "float32",
                "pooling": "mean", "normalize": True, "query_prefix": self.query_prefix,
                "passage_prefix": self.passage_prefix, "batch_size": self.batch_size,
                "text_field": "retrieval_text"}

    def _encode(self, texts: list[str]) -> np.ndarray:
        self.model.float()  # même dtype pour E1 et E2 (protocole v1.3)
        return self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False)

    def _units(self, units: Sequence[Mapping[str, Any]]) -> np.ndarray:
        todo = [u for u in units if u["unit_id"] not in self._cache]
        if todo:
            texts = [self.passage_prefix + unit_text(u) for u in todo]
            tok = self.model.tokenizer(texts, add_special_tokens=True)["input_ids"]
            self.truncated += sum(len(t) > self.model.max_seq_length for t in tok)
            for u, v in zip(todo, self._encode(texts), strict=True):
                self._cache[u["unit_id"]] = v
        return np.stack([self._cache[u["unit_id"]] for u in units])

    def score(self, query: str, units: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        q = self._encode([self.query_prefix + query])[0]
        sims = self._units(units) @ q
        return {u["unit_id"]: float(s) for u, s in zip(units, sims, strict=True)}
