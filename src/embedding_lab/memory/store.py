"""Mémoire sémantique (EL-018) : unités sourcées, liens, recherche dense.

La mémoire se construit à partir d'un fichier source (réunions + unités + relations), calcule
les positions exactes des extraits, valide chaque unité et chaque relation avec les schémas du
projet, puis indexe les unités avec l'encodeur choisi (E2 si ses poids sont disponibles, sinon
E1, ce qui est indiqué dans ``config()``).

Le contenu des réunions est une **donnée** : une phrase qui ressemble à une consigne
(« ignore les consignes… ») est stockée comme n'importe quelle unité et n'est jamais exécutée.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from embedding_lab.schemas import check_relation, check_unit

ACTIVE = {"active", "resolved", "open"}


def _meeting_text(meeting: Mapping[str, Any]) -> tuple[str, list[int]]:
    """Texte canonique « Locuteur : phrase » par ligne, et position de début de chaque tour."""
    parts, starts, pos = [], [], 0
    for speaker, text in meeting["turns"]:
        line = f"{speaker} : {text}"
        starts.append(pos + len(speaker) + 3)
        parts.append(line)
        pos += len(line) + 1
    return "\n".join(parts), starts


def build_from_source(src: Mapping[str, Any]) -> tuple[dict, list[dict], dict]:
    """Unités et relations validées ; lève ``ValueError`` à la première incohérence."""
    meetings = {m["source_id"]: m for m in src["meetings"]}
    order = {m["source_id"]: i for i, m in enumerate(sorted(src["meetings"],
                                                            key=lambda m: m["date"]))}
    texts = {}
    units: dict[str, dict] = {}
    for sid, m in meetings.items():
        texts[sid] = _meeting_text(m)
    for (uid, sid, turn, ev, typ, status, assertion, owner, mentioned, due, event, amount,
         statement) in src["units"]:
        m = meetings[sid]
        full, starts = texts[sid]
        speaker, turn_text = m["turns"][turn]
        offset = turn_text.find(ev)
        if offset < 0:
            raise ValueError(f"{uid} : extrait introuvable dans le tour {turn} de {sid}")
        start = starts[turn] + offset
        unit = {"unit_id": uid, "source_id": sid, "source_date": m["date"],
                "source_order": order[sid], "project": src["project"], "type": typ,
                "statement": statement, "status": status, "assertion": assertion,
                "speaker": speaker, "owner": owner, "mentioned_people": mentioned,
                "due_date": due, "event_date": event, "amount": amount,
                "retrieval_text": f"{m['title']} — {speaker} : {ev}",
                "evidence": {"text": ev, "char_start": start, "char_end": start + len(ev),
                             "segment_ids": [f"{sid}:t{turn:04d}"]},
                "annotation": {"origin": "human", "annotator": "claude:demo-atlas",
                               "reviewed": False,
                               "notes": "données de démonstration fictives écrites à la main"}}
        errors = check_unit(unit, full)
        if errors:
            raise ValueError(f"{uid} : {errors}")
        units[uid] = unit
    relations = []
    for frm, to, rel, sid, why in src["relations"]:
        r = {"from_id": frm, "to_id": to, "relation": rel, "evidence_source_id": sid,
             "justification": why, "origin": "human"}
        errors = check_relation(r, units)
        if errors:
            raise ValueError(f"{frm}->{to} : {errors}")
        relations.append(r)
    return units, relations, {sid: t for sid, (t, _) in texts.items()}


class Memory:
    def __init__(self, units: Mapping[str, dict], relations: Sequence[dict],
                 meetings: Mapping[str, dict], encoder: Any = None):
        self.units = dict(units)
        self.relations = list(relations)
        self.meetings = dict(meetings)
        self.encoder = encoder
        self.superseded_by: dict[str, str] = {}
        self.contradicted_by: dict[str, list[str]] = defaultdict(list)
        self.links: dict[str, list[dict]] = defaultdict(list)
        for r in self.relations:
            self.links[r["from_id"]].append(r)
            self.links[r["to_id"]].append(r)
            if r["relation"] == "supersedes":
                self.superseded_by[r["to_id"]] = r["from_id"]
            if r["relation"] == "contradicts":
                self.contradicted_by[r["to_id"]].append(r["from_id"])

    @classmethod
    def from_source(cls, path: Path, encoder: Any = None) -> Memory:
        src = json.loads(Path(path).read_text(encoding="utf-8"))
        units, relations, _ = build_from_source(src)
        meetings = {m["source_id"]: {"date": m["date"], "title": m["title"]}
                    for m in src["meetings"]}
        return cls(units, relations, meetings, encoder)

    # --- état des informations -----------------------------------------------------------

    def current(self, uid: str) -> str:
        """Dernière unité de la chaîne de remplacement."""
        seen = set()
        while uid in self.superseded_by and uid not in seen:
            seen.add(uid)
            uid = self.superseded_by[uid]
        return uid

    def is_current(self, uid: str) -> bool:
        return uid not in self.superseded_by

    def people(self) -> list[str]:
        names = set()
        for u in self.units.values():
            for n in [u.get("speaker"), u.get("owner"), *u.get("mentioned_people", [])]:
                if n:
                    names.add(n)
        return sorted(names)

    def projects(self) -> list[str]:
        return sorted({u["project"] for u in self.units.values() if u.get("project")})

    # --- recherche -----------------------------------------------------------------------

    def search(self, query: str, k: int = 8, types: Sequence[str] | None = None
               ) -> list[dict[str, Any]]:
        """Top-k unités (score dense), avec leur état (en vigueur, remplacée, contestée)."""
        if self.encoder is None:
            raise RuntimeError("mémoire sans encodeur : recherche impossible")
        cands = [u for u in self.units.values() if not types or u["type"] in types]
        scores = self.encoder.score(query, cands)
        ranked = sorted(cands, key=lambda u: (-scores[u["unit_id"]], u["unit_id"]))[:k]
        return [{"unit": u, "score": scores[u["unit_id"]],
                 "superseded_by": self.superseded_by.get(u["unit_id"]),
                 "contradicted_by": self.contradicted_by.get(u["unit_id"], [])}
                for u in ranked]

    def cite(self, uid: str) -> str:
        u = self.units[uid]
        return f"[{uid}, {u['source_date']}, {u['speaker']}]"
