"""Résolution des destinataires (EL-021).

Règles (brief : « une mention d'une personne dans une réunion ne suffit pas à en faire le
responsable ») :
- seule une attribution **explicite** compte : champ ``owner`` d'un engagement, d'une action ou
  d'une décision, dans une unité ``extracted`` ;
- une unité remplacée, rejetée, annulée ou simplement proposée ne désigne personne ;
- parmi les attributions valides sur le sujet, la plus récente l'emporte ; si deux personnes
  différentes restent candidates à la même date → ``ambiguous`` ;
- aucune adresse e-mail n'est jamais produite : l'annuaire de démonstration n'en contient pas,
  donc une personne identifiée a le statut ``email_missing``.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

from embedding_lab.memory.store import Memory

RESPONSIBLE_TYPES = {"commitment", "action", "decision"}
INVALID_STATUS = {"rejected", "cancelled", "superseded", "proposed"}
# variantes de sujets (racines simples) ; les sujets inconnus sont cherchés tels quels
TOPIC_VARIANTS = {"budget": ["budget"], "dossier": ["dossier"], "communication": ["communication"],
                  "facture": ["facture"], "lieu": ["salle", "lieu"], "traiteur": ["traiteur"],
                  "lancement": ["lancement"]}


def _fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def mentions_topic(unit: Mapping[str, Any], topic: str) -> bool:
    text = _fold(unit["statement"] + " " + unit["evidence"]["text"])
    return any(_fold(v) in text for v in TOPIC_VARIANTS.get(topic, [topic]))


def responsible_for(memory: Memory, topic: str) -> dict[str, Any]:
    """Personne explicitement responsable de ``topic``, avec preuves et justification."""
    valid, mentions = [], []
    for u in memory.units.values():
        if not mentions_topic(u, topic):
            continue
        if u.get("mentioned_people"):
            mentions.append(u)
        if (u["type"] in RESPONSIBLE_TYPES and u.get("owner") and u["assertion"] == "extracted"
                and u["status"] not in INVALID_STATUS and memory.is_current(u["unit_id"])):
            valid.append(u)
    if not valid:
        cited = sorted({p for u in mentions for p in u["mentioned_people"]})
        open_choice = [u for u in mentions if u["type"] in RESPONSIBLE_TYPES
                       and u["status"] == "proposed" and len(u["mentioned_people"]) > 1]
        if open_choice:
            names = sorted({p for u in open_choice for p in u["mentioned_people"]})
            return {"name": None, "email": None,
                    "evidence_unit_ids": [u["unit_id"] for u in open_choice],
                    "resolution_status": "ambiguous",
                    "justification": f"attribution non tranchée pour « {topic} » entre "
                                     f"{', '.join(names)}"}
        return {"name": None, "email": None, "evidence_unit_ids": [u["unit_id"] for u in mentions],
                "resolution_status": "not_found",
                "justification": (f"aucune attribution explicite pour « {topic} »"
                                  + (f" ; personnes seulement citées : {', '.join(cited)}"
                                     if cited else ""))}
    valid.sort(key=lambda u: (u["source_date"] or "", u["evidence"]["char_start"]), reverse=True)
    latest_date = valid[0]["source_date"]
    latest_owners = sorted({u["owner"] for u in valid if u["source_date"] == latest_date})
    if len(latest_owners) > 1:
        return {"name": None, "email": None,
                "evidence_unit_ids": [u["unit_id"] for u in valid
                                      if u["source_date"] == latest_date],
                "resolution_status": "ambiguous",
                "justification": f"plusieurs responsables au {latest_date} : "
                                 f"{', '.join(latest_owners)}"}
    name = latest_owners[0]
    ev = [u["unit_id"] for u in valid if u["owner"] == name]
    others = sorted({u["owner"] for u in valid} - {name})
    just = (f"{name} est désigné(e) explicitement ({', '.join(ev)}), attribution la plus "
            f"récente : {latest_date}")
    if others:
        just += f" ; attributions plus anciennes à {', '.join(others)} ignorées"
    cited = sorted({p for u in mentions for p in u["mentioned_people"]} - {name})
    if cited:
        just += f" ; {', '.join(cited)} seulement cité(e)s, non responsables"
    return {"name": name, "email": None, "evidence_unit_ids": ev,
            "resolution_status": "email_missing", "justification": just}


def named_person(memory: Memory, name: str) -> dict[str, Any]:
    """Personne nommée dans la demande : vérifiée dans la mémoire, jamais d'adresse inventée."""
    ev = [u["unit_id"] for u in memory.units.values()
          if name in {u.get("owner"), u.get("speaker"), *u.get("mentioned_people", [])}]
    if not ev:
        return {"name": name, "email": None, "evidence_unit_ids": [],
                "resolution_status": "not_found",
                "justification": f"{name} n'apparaît dans aucune source"}
    return {"name": name, "email": None, "evidence_unit_ids": ev[:5],
            "resolution_status": "email_missing",
            "justification": f"{name} est nommé(e) dans la demande et présent(e) dans les sources"}


def person_for_schema(p: Mapping[str, Any]) -> dict[str, Any]:
    keys: Sequence[str] = ("name", "email", "evidence_unit_ids", "resolution_status")
    return {k: p[k] for k in keys}
