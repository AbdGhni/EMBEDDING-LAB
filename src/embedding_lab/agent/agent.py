"""Mini-agent (EL-022) : étapes explicites, sorties extractives et sourcées.

Demande → intention + slots (I2 + règles) → recherche dense dans la mémoire → état des
informations (remplacements, contradictions) → résolution des dates et des personnes →
opération : réponse, comparaison, dossier, brouillon d'e-mail, tâche, événement,
clarification, ou rien (hypothèse).

Aucune phrase n'est générée par un modèle de langue : les réponses citent les extraits des
sources (gabarits). Toute action passe par ``tools.simulated`` (jamais exécutée).
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

from embedding_lab.intents.rules import extract_slots
from embedding_lab.memory.store import Memory
from embedding_lab.resolution.dates import resolve
from embedding_lab.resolution.recipients import named_person, person_for_schema, responsible_for
from embedding_lab.tools import simulated

TOPICS = ["budget", "dossier", "communication", "facture", "traiteur", "lancement", "salle",
          "lieu", "planning", "contrat", "devis", "recrutement", "programme"]
WEEKDAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
             "septembre", "octobre", "novembre", "décembre"]


def fr_date(iso: str | None) -> str:
    if not iso:
        return "date inconnue"
    d = date.fromisoformat(iso)
    return f"{WEEKDAYS[d.weekday()]} {d.day} {FR_MONTHS[d.month - 1]} {d.year}"


def find_topic(text: str) -> str | None:
    t = text.lower()
    hits = [(t.find(k), k) for k in TOPICS if k in t]
    return min(hits)[1] if hits else None


class IntentModel:
    """I2 : régression logistique (C = 10, choisi sur I-SYN val) sur e5-small gelé."""

    def __init__(self, encoder: Any, train_path: Path = Path("data/intents/train.jsonl"),
                 C: float = 10.0):
        from sklearn.linear_model import LogisticRegression

        rows = [json.loads(line) for line in train_path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
        self.encoder = encoder
        X = encoder._encode(["query: " + r["text"] for r in rows])
        self.model = LogisticRegression(C=C, max_iter=3000, random_state=0)
        self.model.fit(X, [r["intent"] for r in rows])

    def predict(self, text: str) -> tuple[str, float]:
        p = self.model.predict_proba(self.encoder._encode(["query: " + text]))[0]
        i = int(p.argmax())
        return str(self.model.classes_[i]), float(p[i])


class Agent:
    def __init__(self, memory: Memory, intent_model: IntentModel, reference_date: date):
        self.memory, self.intents, self.ref = memory, intent_model, reference_date

    # --- étape 1 : intention et paramètres ------------------------------------------------

    def analyse(self, request: str) -> dict[str, Any]:
        intent, conf = self.intents.predict(request)
        slots = extract_slots(request, self.memory.people(), self.memory.projects())
        slots["topic"] = find_topic(request)
        due = resolve(slots["deadline"], self.ref)
        return {"intent": intent, "confidence": round(conf, 3), "slots": slots,
                "deadline_resolved": due.isoformat() if due else None}

    def handle(self, request: str) -> dict[str, Any]:
        a = self.analyse(request)
        op = {"answer": self.answer, "compare": self.compare,
              "build_dossier": self.build_dossier, "draft_email": self.draft_email,
              "create_task": self.create_task, "schedule_event": self.schedule_event,
              "clarify": self.clarify, "no_action": self.no_action}[a["intent"]]
        out = op(request, a)
        return {"request": request, "reference_date": self.ref.isoformat(), "analysis": a,
                **out}

    # --- opérations -----------------------------------------------------------------------

    def _line(self, uid: str) -> str:
        u = self.memory.units[uid]
        state = ""
        if u["unit_id"] in self.memory.superseded_by:
            state = f" (remplacé par {self.memory.superseded_by[uid]})"
        elif u["status"] in ("proposed", "conditional"):
            label = "proposé, non validé" if u["status"] == "proposed" else "conditionnel"
            state = f" (statut : {label})"
        return (f"{u['statement']}{state} — « {u['evidence']['text']} » "
                f"{self.memory.cite(uid)}")

    def answer(self, request: str, a: Mapping[str, Any]) -> dict[str, Any]:
        hits = self.memory.search(request, k=5)
        top = hits[0]["unit"]["unit_id"]
        # une question retrouvée n'est pas une réponse : suivre la relation « answers »
        answered = [r["from_id"] for r in self.memory.links.get(top, [])
                    if r["relation"] == "answers" and r["to_id"] == top]
        asked = top if answered else None
        top = answered[0] if answered else top
        current = self.memory.current(top)
        lines, cited, warnings = [], [current], []
        if asked:
            lines.append("Question posée : " + self._line(asked))
            cited.append(asked)
        lines.append(self._line(current))
        if current != top:
            lines.append("Historique : " + self._line(top))
            cited.append(top)
        u = self.memory.units[current]
        if u["status"] in ("proposed", "conditional"):
            warnings.append("l'information la plus proche n'est pas une décision validée")
        for c in self.memory.contradicted_by.get(current, []):
            warnings.append(f"contestée par {c} : « {self.memory.units[c]['evidence']['text']} »"
                            " — désaccord non tranché dans les sources")
            cited.append(c)
        if u.get("owner"):
            lines.append(f"Responsable : {u['owner']}"
                         + (f", échéance {fr_date(u['due_date'])}" if u.get("due_date") else ""))
        return {"operation": "answer", "answer": "\n".join(lines), "citations": cited,
                "warnings": warnings, "retrieved": [h["unit"]["unit_id"] for h in hits],
                "action": None}

    def compare(self, request: str, a: Mapping[str, Any]) -> dict[str, Any]:
        """Compare l'état des informations entre deux réunions : pour chaque unité de la
        réunion ancienne, on suit les remplacements datés au plus tard de la réunion récente ;
        les contradictions apparues entre les deux sont listées à part."""
        m = self.memory
        t = request.lower()
        meetings = sorted(m.meetings.items(), key=lambda kv: kv[1]["date"])
        picked = []
        for _pos, d in sorted((t.find(name), i) for i, name in enumerate(WEEKDAYS)
                              if name in t):
            same_day = [sid for sid, meta in meetings
                        if date.fromisoformat(meta["date"]).weekday() == d
                        and date.fromisoformat(meta["date"]) <= self.ref]
            if same_day and same_day[-1] not in picked:
                picked.append(same_day[-1])
        if len(picked) < 2:
            picked = [meetings[0][0], meetings[-1][0]]
        early, late = sorted(picked[:2], key=lambda sid: m.meetings[sid]["date"])
        d_early, d_late = m.meetings[early]["date"], m.meetings[late]["date"]
        topic = a["slots"].get("topic")
        changes, conflicts, cited = [], [], []
        for u in sorted((u for u in m.units.values() if u["source_id"] == early),
                        key=lambda u: u["evidence"]["char_start"]):
            uid, final = u["unit_id"], u["unit_id"]
            while final in m.superseded_by and \
                    m.units[m.superseded_by[final]]["source_date"] <= d_late:
                final = m.superseded_by[final]
            if final == uid or (topic and topic not in (u["statement"] + m.units[final]
                                                        ["statement"]).lower()):
                continue
            new = m.units[final]
            changes.append(f"Mise à jour : « {u['evidence']['text']} » {m.cite(uid)} est "
                           f"remplacé par « {new['evidence']['text']} » {m.cite(final)}")
            cited += [uid, final]
        for r in m.relations:
            if r["relation"] != "contradicts":
                continue
            new, old = m.units[r["from_id"]], m.units[r["to_id"]]
            if not (d_early <= new["source_date"] <= d_late):
                continue
            conflicts.append(f"Contradiction non tranchée : « {new['evidence']['text']} » "
                             f"{m.cite(new['unit_id'])} s'oppose à « {old['evidence']['text']} »"
                             f" {m.cite(old['unit_id'])}")
            cited += [old["unit_id"], new["unit_id"]]
        text = "\n".join(changes + conflicts) or "Aucun changement ni contradiction relevé."
        note = ("Une mise à jour remplace explicitement l'information précédente (relation "
                "supersedes) : ce n'est pas une contradiction. Une contradiction oppose deux "
                "affirmations sans qu'aucune décision ne tranche.")
        return {"operation": "compare", "answer": text, "explanation": note,
                "meetings": [early, late], "citations": cited, "action": None}

    def build_dossier(self, request: str, a: Mapping[str, Any]) -> dict[str, Any]:
        m = self.memory
        project = a["slots"].get("project") or (m.projects()[0] if m.projects() else None)
        units = sorted((u for u in m.units.values() if u.get("project") == project),
                       key=lambda u: (u["source_date"] or "", u["evidence"]["char_start"]))
        sections: dict[str, list[dict[str, Any]]] = {k: [] for k in (
            "Chronologie", "Décisions en vigueur", "Décisions remplacées", "Budget", "Risques",
            "Prochaines étapes et responsables", "Personnes impliquées", "Points ouverts",
            "Informations absentes")}

        def claim(section: str, text: str, ids: list[str]) -> None:
            sections[section].append({"text": text, "unit_ids": ids})

        for sid, meta in sorted(m.meetings.items(), key=lambda kv: kv[1]["date"]):
            ids = [u["unit_id"] for u in units if u["source_id"] == sid]
            claim("Chronologie", f"{fr_date(meta['date'])} — {meta['title']} "
                  f"({len(ids)} unités)", ids)
        # doublons : une décision reprise (« supports ») par une décision plus récente est
        # fusionnée avec elle, la ligne cite les deux
        confirmed_by = {r["to_id"]: r["from_id"] for r in m.relations
                        if r["relation"] == "supports"
                        and m.units[r["from_id"]]["type"] == "decision"
                        and m.units[r["to_id"]]["type"] == "decision"}
        for u in units:
            uid = u["unit_id"]
            if u["type"] == "decision":
                if uid in confirmed_by and m.is_current(uid):
                    continue
                if m.is_current(uid) and u["status"] == "active":
                    earlier = [k for k, v in confirmed_by.items() if v == uid]
                    note = " (contestée, voir points ouverts)" if m.contradicted_by.get(uid) \
                        else ""
                    claim("Décisions en vigueur", u["statement"] + note
                          + (f" — confirmée, reprend {', '.join(earlier)}" if earlier else ""),
                          [*earlier, uid])
                elif not m.is_current(uid):
                    claim("Décisions remplacées", f"{u['statement']} → remplacé par "
                          f"{m.superseded_by[uid]}", [uid, m.superseded_by[uid]])
            if u.get("amount"):
                state = ("remplacé" if not m.is_current(uid)
                         else "contrainte" if u["type"] == "fact"
                         else "en vigueur" if u["status"] == "active" else u["status"])
                claim("Budget", f"{u['amount']} ({state}) : {u['statement']}", [uid])
            if u["type"] == "risk":
                claim("Risques", u["statement"], [uid])
            if u["type"] in ("commitment", "action") and u["status"] != "proposed":
                due = f", échéance {fr_date(u['due_date'])}" if u.get("due_date") else ""
                if u.get("due_date") and u["due_date"] < self.ref.isoformat():
                    due += " (passée, état d'avancement non renseigné)"
                claim("Prochaines étapes et responsables",
                      f"{u['owner'] or 'responsable non désigné'} : {u['statement']}{due}", [uid])
            if u["type"] == "question" and u["status"] == "open":
                claim("Points ouverts", f"Question sans réponse : {u['statement']}", [uid])
            for c in m.contradicted_by.get(uid, []):
                claim("Points ouverts", f"Désaccord non tranché : {u['statement']} / "
                      f"{m.units[c]['statement']}", [uid, c])
            if u["type"] in ("commitment", "action") and u["status"] == "proposed":
                claim("Points ouverts", f"Attribution non tranchée : {u['statement']}", [uid])
        owners = sorted({u["owner"] for u in units if u.get("owner")})
        cited = sorted({p for u in units for p in u.get("mentioned_people", [])} - set(owners))
        for o in owners:
            claim("Personnes impliquées", f"{o} — responsable d'au moins un sujet",
                  [u["unit_id"] for u in units if u.get("owner") == o])
        for c in cited:
            claim("Personnes impliquées", f"{c} — cité(e) sans responsabilité attribuée",
                  [u["unit_id"] for u in units if c in u.get("mentioned_people", [])])
        sections["Informations absentes"].append(
            {"text": "Adresses e-mail : aucune dans les sources (non inventées).", "unit_ids": []})
        if not any("traiteur" in u["statement"].lower() and u.get("owner") for u in units):
            sections["Informations absentes"].append(
                {"text": "Prestataire traiteur : ni choix ni responsable dans les sources.",
                 "unit_ids": []})
        md = [f"# Dossier — projet {project}",
              f"Établi le {fr_date(self.ref.isoformat())} à partir de {len(m.meetings)} "
              "réunions. Chaque ligne cite ses unités sources.", ""]
        for name, claims in sections.items():
            md.append(f"## {name}")
            md += [f"- {c['text']} " + (f"[{', '.join(c['unit_ids'])}]" if c["unit_ids"]
                                         else "[aucune source]") for c in claims]
            if not claims:
                md.append("- (rien dans les sources)")
            md.append("")
        cited_ids = sorted({i for cl in sections.values() for c in cl for i in c["unit_ids"]})
        return {"operation": "build_dossier", "project": project, "sections": sections,
                "markdown": "\n".join(md), "citations": cited_ids, "action": None}

    def _person(self, a: Mapping[str, Any]) -> dict[str, Any] | None:
        if a["slots"].get("person"):
            return named_person(self.memory, a["slots"]["person"])
        if a["slots"].get("topic"):
            return responsible_for(self.memory, a["slots"]["topic"])
        return None

    def draft_email(self, request: str, a: Mapping[str, Any]) -> dict[str, Any]:
        person = self._person(a)
        ref = self.ref.isoformat()
        if person is None or person["resolution_status"] in ("ambiguous", "not_found"):
            reason = "owner_ambiguous" if person and person["resolution_status"] == "ambiguous" \
                else "owner_missing"
            q = ("À qui dois-je écrire ? " + (person["justification"] if person else
                                               "la demande ne désigne ni personne ni sujet."))
            return {"operation": "clarify", "action": simulated.clarify(
                reason, q, person["evidence_unit_ids"] if person else [], ref),
                "justification": person["justification"] if person else None}
        topic = a["slots"].get("topic") or "suivi"
        project = a["slots"].get("project") or (self.memory.projects() or [""])[0]
        m = re.search(r"(?:demander|obtenir|avoir|récupérer|transmettre)\s+(.+?)"
                      r"(?:\s+(?:avant|d'ici|pour)\b.*)?[.?!]?$", request, re.IGNORECASE)
        obj = m.group(1).strip() if m else f"les dernières informations sur le {topic}"
        obj = re.sub(r"^(?:lui|leur)\s+demander\s+", "", obj)
        if topic not in obj.lower():
            obj += {"communication": " de la communication", "facture": " des factures",
                    "salle": " de la salle"}.get(topic, f" du {topic}")
        due = a["deadline_resolved"]
        when = f" avant le {fr_date(due)}" if due else ""
        context, sources = [], list(person["evidence_unit_ids"])
        hits = self.memory.search(f"{topic} {project} décision validée", k=3,
                                  types=["decision"])
        for h in hits:
            uid = self.memory.current(h["unit"]["unit_id"])
            u = self.memory.units[uid]
            if topic in u["statement"].lower() and u["status"] == "active":
                context.append(f"Pour mémoire : {u['statement']} ({fr_date(u['source_date'])}).")
                sources.append(uid)
                break
        body = (f"Bonjour {person['name']},\n\nPourrais-tu me transmettre {obj}{when} ?\n\n"
                + (context[0] + "\n\n" if context else "") + "Merci.")
        contract = simulated.email_create_draft(
            person_for_schema(person), f"Projet {project} — {topic}", body,
            sorted(set(sources)), ref,
            clarification={"needed": True, "reason": "email_missing",
                           "question": f"Je n'ai pas l'adresse de {person['name']} dans les "
                                       "sources : peux-tu la confirmer avant tout envoi ?"})
        return {"operation": "draft_email", "action": contract,
                "justification": person["justification"]}

    def create_task(self, request: str, a: Mapping[str, Any]) -> dict[str, Any]:
        person = self._person(a)
        ref = self.ref.isoformat()
        if person is None or person["resolution_status"] in ("ambiguous", "not_found"):
            return self.clarify(request, a)
        title = re.sub(r"^(?:prépare|crée|ajoute|mets)\s+(?:une\s+)?(?:tâche|action)\s*"
                       r"(?:pour\s+\w+\s*)?:?\s*", "", request, flags=re.IGNORECASE).strip(" .")
        contract = simulated.tasks_create_draft(
            title or request, person_for_schema(person), a["deadline_resolved"],
            person["evidence_unit_ids"], ref,
            clarification={"needed": True, "reason": "email_missing",
                           "question": f"Confirmer l'attribution à {person['name']} ?"})
        return {"operation": "create_task", "action": contract,
                "justification": person["justification"]}

    def schedule_event(self, request: str, a: Mapping[str, Any]) -> dict[str, Any]:
        ref = self.ref.isoformat()
        start = a["deadline_resolved"]
        clar = None if start else {"needed": True, "reason": "date_ambiguous",
                                   "question": "Pour quelle date dois-je proposer le point ?"}
        project = a["slots"].get("project") or (self.memory.projects() or [""])[0]
        hits = self.memory.search(request, k=3)
        contract = simulated.calendar_create_draft(
            f"Point {project}" + (f" — {a['slots']['topic']}" if a["slots"].get("topic") else ""),
            f"{start}T10:00:00" if start else None, [h["unit"]["unit_id"] for h in hits], ref,
            clarification=clar)
        return {"operation": "schedule_event", "action": contract,
                "note": "heure par défaut 10:00, à confirmer" if start else None}

    def clarify(self, request: str, a: Mapping[str, Any]) -> dict[str, Any]:
        q = ("Je ne peux pas identifier la personne ni l'objet de la demande. À qui faut-il "
             "s'adresser, et à propos de quel sujet ?")
        return {"operation": "clarify",
                "action": simulated.clarify("insufficient_context", q, [], self.ref.isoformat())}

    def no_action(self, request: str, a: Mapping[str, Any]) -> dict[str, Any]:
        return {"operation": "no_action", "action": None,
                "answer": "Phrase hypothétique ou avis : aucune action n'est créée. Dis-moi "
                          "explicitement ce que tu veux que je prépare."}
