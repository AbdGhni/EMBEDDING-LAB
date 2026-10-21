"""B-REAL : préparation des tâches d'annotation SUMM-RE, validation et assemblage.

Une tâche = un groupe d'expérience (réunions a/b/c). L'annotateur (sous-agent Claude,
annotation **provisoire**) produit un fichier brut ``annotations/breal/raw/<groupe>.json`` ;
ce module vérifie chaque extrait contre la transcription puis construit unités, relations,
requêtes, pertinences et triplets au format du projet.

Portée de recherche B-REAL (protocole v1.4) : les unités du groupe de la requête.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from embedding_lab.schemas import check_relation, check_unit

TYPE_FR = {"reporting": "compte rendu", "decision": "décision", "planning": "planification"}
TRAPS = {"status", "condition", "negation", "person", "date", "amount", "superseded",
         "topic_only"}
RELATIONS = {"supports", "contradicts", "supersedes", "creates_action", "answers", "unrelated"}
_PLACEHOLDER = re.compile(r"\bw_\d+\b|\bsil\b")
_KEY = re.compile(r"^[a-c]-\d{2,3}$")


def task_text(group: str, meetings: Sequence[Mapping[str, Any]]) -> str:
    """Transcription lisible d'un groupe : une ligne par tour, ``tNNNN [locuteur] texte``."""
    out = [f"# Groupe d'expérience {group}", ""]
    for m in sorted(meetings, key=lambda m: m["source_order"]):
        out.append(f"## Réunion {m['meeting_id']} — lettre {m['session']} "
                   f"(rang {m['source_order'] + 1}/3), type : {TYPE_FR[m['meeting_type']]}, "
                   f"transcription : {m['transcription']}"
                   + (" — QUESTIONS À ÉCRIRE SUR CETTE RÉUNION" if m["transcription"] == "manual"
                      else " — pas de questions, unités seulement"))
        out.append("")
        for t in m["turns"]:
            out.append(f"{t['turn_id'].split(':')[1]} [{t['speaker']}] {t['text']}")
        out.append("")
    return "\n".join(out) + "\n"


def validate_raw(raw: Mapping[str, Any], meetings: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Erreurs de forme et de contenu d'une annotation brute (liste vide = acceptable)."""
    errs: list[str] = []
    units = raw.get("units", [])
    keys = [u.get("key") for u in units]
    if len(set(keys)) != len(keys):
        errs.append("clés d'unités dupliquées")
    known = set(keys)
    letter_of = {mid: m["session"] for mid, m in meetings.items()}
    for u in units:
        k = u.get("key", "?")
        if not isinstance(k, str) or not _KEY.match(k):
            errs.append(f"{k}: clé invalide (attendu a-01, b-12…)")
        m = meetings.get(u.get("meeting_id"))
        if m is None:
            errs.append(f"{k}: réunion inconnue {u.get('meeting_id')}")
            continue
        if isinstance(k, str) and k[:1] != letter_of[m["meeting_id"]]:
            errs.append(f"{k}: la lettre de la clé doit être celle de la réunion")
        turn = next((t for t in m["turns"] if t["turn_id"].endswith(":" + str(u.get("turn")))),
                    None)
        if turn is None:
            errs.append(f"{k}: tour inconnu {u.get('turn')}")
            continue
        if u.get("status") == "superseded":
            errs.append(f"{k}: statut superseded interdit (utiliser une relation supersedes)")
        ev = u.get("evidence", "")
        if not ev or ev not in turn["text"]:
            errs.append(f"{k}: l'extrait n'est pas une sous-chaîne exacte du tour {u.get('turn')}")
        elif len(ev.split()) < 3:
            errs.append(f"{k}: extrait trop court (< 3 mots)")
        elif _PLACEHOLDER.search(ev):
            errs.append(f"{k}: extrait contenant des jetons w_N/sil")
    for r in raw.get("relations", []):
        if r.get("from") not in known or r.get("to") not in known:
            errs.append(f"relation {r}: clé inconnue")
        if r.get("relation") not in RELATIONS:
            errs.append(f"relation {r}: type inconnu")
        if not r.get("justification"):
            errs.append(f"relation {r}: justification manquante")
    manual = {mid for mid, m in meetings.items() if m["transcription"] == "manual"}
    for q in raw.get("queries", []):
        qk = q.get("key", "?")
        if q.get("about_meeting") not in manual:
            errs.append(f"{qk}: about_meeting doit être une réunion manuelle")
        if not q.get("text"):
            errs.append(f"{qk}: texte vide")
        qrels = q.get("qrels", {})
        if any(k not in known for k in qrels):
            errs.append(f"{qk}: qrels sur une clé inconnue")
        if any(v not in (0, 1, 2) for v in qrels.values()):
            errs.append(f"{qk}: pertinence hors {{0,1,2}}")
        if q.get("answerable", True):
            if not any(v == 2 for v in qrels.values()):
                errs.append(f"{qk}: requête répondable sans unité de pertinence 2")
        elif any(v >= 1 for v in qrels.values()):
            errs.append(f"{qk}: requête sans réponse mais avec unité pertinente")
        for t in q.get("traps", []):
            if not q.get("answerable", True):
                errs.append(f"{qk}: pas de pièges pour une question sans réponse")
            if t.get("trap") not in TRAPS:
                errs.append(f"{qk}: type de piège inconnu {t.get('trap')}")
            if qrels.get(t.get("unit"), 0) != 0 or t.get("unit") not in known:
                errs.append(f"{qk}: un piège doit être une unité connue jugée 0")
        ev_words = {k: set(re.findall(r"\w+", u["evidence"].lower())) for k, u in
                    ((u["key"], u) for u in units if u.get("evidence"))}
        qw = re.findall(r"\w+", q.get("text", "").lower())
        grams = {tuple(qw[i:i + 5]) for i in range(len(qw) - 4)}
        for k, v in qrels.items():
            if v == 2 and k in ev_words:
                ew = re.findall(r"\w+", next(u for u in units if u["key"] == k)["evidence"].lower())
                if grams & {tuple(ew[i:i + 5]) for i in range(len(ew) - 4)}:
                    errs.append(f"{qk}: la requête recopie 5 mots consécutifs de la preuve {k}")
    return errs


def assemble(raw: Mapping[str, Any], meetings: Mapping[str, Mapping[str, Any]],
             split: str, annotator: str) -> dict[str, Any]:
    """Annotation brute validée -> contrats du projet (unités, relations, requêtes…)."""
    group = raw["group_id"]
    uid = {u["key"]: f"u-sr-{group}-{u['key']}" for u in raw["units"]}
    units = []
    for u in raw["units"]:
        m = meetings[u["meeting_id"]]
        turn = next(t for t in m["turns"] if t["turn_id"].endswith(":" + u["turn"]))
        start = turn["char_start"] + turn["text"].index(u["evidence"])
        units.append({
            "unit_id": uid[u["key"]], "source_id": m["meeting_id"], "source_date": None,
            "source_order": m["source_order"], "project": f"summre-{group}",
            "type": u["type"], "statement": u["statement"], "status": u["status"],
            "assertion": u.get("assertion", "extracted"), "speaker": turn["speaker"],
            "owner": u.get("owner"), "mentioned_people": u.get("mentioned_people", []),
            "due_date": None, "event_date": None, "amount": u.get("amount"),
            "evidence": {"text": u["evidence"], "char_start": start,
                         "char_end": start + len(u["evidence"]),
                         "segment_ids": [turn["turn_id"]]},
            "retrieval_text": (f"Réunion {m['source_order'] + 1}/3 "
                               f"({TYPE_FR[m['meeting_type']]}) — locuteur {turn['speaker']} : "
                               f"{u['evidence']}"),
            "annotation": {"origin": "llm_provisional", "annotator": annotator,
                           "reviewed": False, "notes": u.get("notes") or None},
        })
    index = {u["unit_id"]: u for u in units}
    relations = [{"from_id": uid[r["from"]], "to_id": uid[r["to"]], "relation": r["relation"],
                  "evidence_source_id": index[uid[r["from"]]]["source_id"],
                  "justification": r["justification"], "origin": "llm_provisional"}
                 for r in raw.get("relations", [])]
    queries, qrels, triplets = [], {}, []
    for q in raw.get("queries", []):
        qid = f"q-sr-{group}-{q['key']}"
        queries.append({"query_id": qid, "project_id": f"summre-{group}", "group_id": group,
                        "split": split, "about_meeting": q["about_meeting"], "type": "real",
                        "text": q["text"], "answerable": bool(q.get("answerable", True))})
        if q.get("answerable", True):
            qrels[qid] = {uid[k]: v for k, v in q["qrels"].items()}
            pos = [uid[k] for k, v in q["qrels"].items() if v == 2]
            triplets += [{"query_id": qid, "pos": p, "neg": uid[t["unit"]], "trap": t["trap"]}
                         for t in q.get("traps", []) for p in pos]
    return {"units": units, "relations": relations, "queries": queries, "qrels": qrels,
            "triplets": triplets}


def contract_errors(assembled: Mapping[str, Any],
                    meetings: Mapping[str, Mapping[str, Any]]) -> list[str]:
    index = {u["unit_id"]: u for u in assembled["units"]}
    errs = [f"{u['unit_id']}: {e}" for u in assembled["units"]
            for e in check_unit(u, meetings[u["source_id"]]["text"])]
    errs += [f"relation: {e}" for r in assembled["relations"] for e in check_relation(r, index)]
    return errs


def load_meetings(path: Path) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        return {m["meeting_id"]: m for m in (json.loads(line) for line in f if line.strip())}
