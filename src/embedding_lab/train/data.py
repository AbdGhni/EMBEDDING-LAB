"""EL-012 — exemples d'entraînement contrastif (protocole v1.4, § 6).

Un exemple = (requête, positif, négatif, grappe, source, origine du négatif). Les textes
reçoivent les préfixes e5 au moment de l'entraînement, pas ici.

Règles anti-fuite et anti-faux-négatif :
- uniquement les splits **train** de B-SYN et de B-REAL ;
- B-REAL : négatifs = unités **jugées 0** pour la requête (pièges annotés d'abord) ; une unité
  non jugée du groupe n'est jamais prise comme négatif (elle pourrait répondre) ;
- B-SYN : pièges du générateur, puis négatifs extraits par E1 parmi les unités non pertinentes
  (les unités d'autres projets sont sûres : leur nom de projet diffère).

Variante E3 : même requêtes, mêmes positifs, même nombre d'exemples, mais négatif tiré au
hasard parmi les unités non pertinentes du même split (graine fixe).

Exemple ::

    >>> units = {"u1": {"unit_id": "u1", "retrieval_text": "décision : budget validé"},
    ...          "u2": {"unit_id": "u2", "retrieval_text": "proposition de budget"}}
    >>> q = [{"query_id": "q1", "text": "budget validé", "cluster": "p1"}]
    >>> ex = build_examples(q, {"q1": {"u1": 2, "u2": 0}}, units,
    ...                     [{"query_id": "q1", "pos": "u1", "neg": "u2", "trap": "status"}],
    ...                     source="bsyn")
    >>> (ex[0]["positive"], ex[0]["negative"], ex[0]["neg_origin"])
    ('décision : budget validé', 'proposition de budget', 'trap:status')
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from embedding_lab.retrieval.bm25 import unit_text


def build_examples(queries: Sequence[Mapping[str, Any]], qrels: Mapping[str, Mapping[str, int]],
                   units: Mapping[str, Mapping[str, Any]], triplets: Sequence[Mapping[str, Any]],
                   source: str, mined: Mapping[str, Sequence[str]] | None = None,
                   max_neg_per_pos: int = 3) -> list[dict]:
    """Exemples « difficiles » (E2) : pièges annotés, complétés par les négatifs extraits."""
    traps = defaultdict(list)
    for t in triplets:
        traps[(t["query_id"], t["pos"])].append((t["neg"], f"trap:{t['trap']}"))
    out = []
    for q in queries:
        rel = qrels.get(q["query_id"])
        if not rel:
            continue
        for pos in [u for u, r in rel.items() if r == 2]:
            negs = list(dict.fromkeys(traps.get((q["query_id"], pos), [])))
            for m in (mined or {}).get(q["query_id"], []):
                if len(negs) >= max_neg_per_pos:
                    break
                if rel.get(m, 0) == 0 and m not in {n for n, _ in negs}:
                    negs.append((m, "mined:e1"))
            for neg, origin in negs[:max_neg_per_pos]:
                assert rel.get(neg, 0) == 0, "un négatif ne peut pas être pertinent"
                out.append({"query_id": q["query_id"], "anchor": q["text"],
                            "positive": unit_text(units[pos]), "negative": unit_text(units[neg]),
                            "pos_id": pos, "neg_id": neg, "cluster": f"{source}:{q['cluster']}",
                            "source": source, "neg_origin": origin})
    return out


def random_negative_variant(examples: Sequence[Mapping[str, Any]],
                            pools: Mapping[str, Sequence[Mapping[str, Any]]],
                            qrels: Mapping[str, Mapping[str, int]], seed: int = 0) -> list[dict]:
    """E3 : remplace chaque négatif par une unité non pertinente tirée au hasard dans le split.

    ``pools[source]`` = unités candidates du split d'origine. Pour B-REAL, on ne tire que des
    unités d'**autres groupes** (sûres) ; pour B-SYN, n'importe quelle unité non pertinente.
    """
    rng = random.Random(seed)
    out = []
    for ex in examples:
        rel = qrels[ex["query_id"]]
        pool = pools[ex["source"]]
        while True:
            u = rng.choice(pool)
            if rel.get(u["unit_id"], 0) != 0 or u["unit_id"] == ex["pos_id"]:
                continue
            if ex["source"] == "breal" and f"breal:{u['project'].removeprefix('summre-')}" \
                    == ex["cluster"]:
                continue
            break
        out.append({**ex, "negative": unit_text(u), "neg_id": u["unit_id"],
                    "neg_origin": "random"})
    return out


def cluster_batches(examples: Sequence[Mapping[str, Any]], batch_size: int,
                    seed: int = 0) -> list[list[int]]:
    """Batchs sans deux exemples d'une même grappe ni d'un même positif (faux négatifs
    intra-batch). Les exemples restants qui ne trouvent pas de place forment des batchs plus
    petits plutôt que de violer la règle."""
    rng = random.Random(seed)
    order = list(range(len(examples)))
    rng.shuffle(order)
    batches: list[list[int]] = []
    open_batches: list[tuple[list[int], set, set]] = []
    for i in order:
        ex = examples[i]
        for b, clusters, positives in open_batches:
            if ex["cluster"] not in clusters and ex["positive"] not in positives:
                b.append(i)
                clusters.add(ex["cluster"])
                positives.add(ex["positive"])
                if len(b) == batch_size:
                    batches.append(b)
                    open_batches.remove((b, clusters, positives))
                break
        else:
            open_batches.append(([i], {ex["cluster"]}, {ex["positive"]}))
    batches += [b for b, _, _ in open_batches]
    rng.shuffle(batches)
    return batches
