"""I0 — règles à mots-clés écrites a priori, et extraction de slots par règles.

L'ordre des tests compte : on écarte d'abord les hypothèses (`no_action`), puis les demandes
d'action sans cible (`clarify`), puis les actions et enfin les questions.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Any

HEDGES = ("peut-être", "peut etre", "éventuellement", "sans doute", "à voir", "à la limite",
          "je pense que", "j'ai l'impression", "me semble", "me paraît", "ce serait",
          "si ça se trouve", "on verra", "je me dis", "il faudrait")
IMPERATIVE_START = ("envoie", "transmets", "préviens", "relance", "dis-lui", "écris",
                    "fais", "occupe", "règle", "rappelle-lui", "mets", "programme", "crée",
                    "fais suivre")
DEICTIC = ("ça", "le ", "lui", "leur", "les", "-le", "-la", "-les", "-lui", "-leur",
           "qui de droit", "bonne personne", "personne concernée", "qui il faut",
           "dont on a parlé", "responsable.")
EMAIL = ("mail", "e-mail", "courriel", "écris", "écrire", "rédige un message", "relance pour",
         "envoie un message", "envoie à")
TASK = ("tâche", "liste de", "action", "assigne", "rappel pour", "à faire", "suivi d")
EVENT = ("réunion", "point ", "visio", "créneau", "rendez-vous", "invitation", "planifie",
         "programme une", "bloque", "cale ", "organise")
DOSSIER = ("dossier", "synthèse", "récapitulatif", "rapport", "document", "mémo",
           "état des lieux", "note de synthèse", "compile")
COMPARE = ("changé", "change", "évolué", "évolution", "contredit", "contradiction",
           "compare", "comparaison", "différence", "diffère", "revu", "annule", "modifié",
           "bougé", "changements")


def _norm(text: str) -> str:
    return " " + text.lower().replace("’", "'") + " "


def classify(text: str) -> str:
    t = _norm(text)
    stripped = t.strip()
    if any(h in t for h in HEDGES):
        return "no_action"
    words = len(stripped.split())
    if words <= 6 and stripped.startswith(IMPERATIVE_START) and any(d in t for d in DEICTIC) \
            and not re.search(r"\b[A-ZÉ][a-zéèêëîïôûç]+", text[1:]):
        return "clarify"
    if any(k in t for k in DOSSIER) and not t.strip().startswith(("est-ce", "qui")):
        return "build_dossier"
    if any(k in t for k in EMAIL) and "?" not in t:
        return "draft_email"
    if any(k in t for k in TASK) and "?" not in t:
        return "create_task"
    if any(k in t for k in EVENT) and "?" not in t:
        return "schedule_event"
    if any(k in t for k in COMPARE):
        return "compare"
    return "answer"


# --- slots ------------------------------------------------------------------------------

DAYS = r"(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)"
MONTHS = (r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|"
          r"octobre|novembre|décembre|decembre)")
DATE_RE = re.compile(
    rf"\b(?:le \d{{1,2}}(?:er)? {MONTHS}|{DAYS}(?: prochain)?|après-demain|demain|"
    rf"la semaine prochaine|cette semaine|la fin de (?:la )?semaine|la fin du mois)\b",
    re.IGNORECASE)


def _fold(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def find_name(text: str, names: Iterable[str]) -> str | None:
    """Premier nom connu présent comme mot entier (insensible aux accents et à la casse)."""
    ft = _fold(text)
    hits = []
    for n in names:
        m = re.search(rf"(?<![a-z]){re.escape(_fold(n))}(?![a-z])", ft)
        if m:
            hits.append((m.start(), n))
    return min(hits)[1] if hits else None


def extract_slots(text: str, persons: Iterable[str], projects: Iterable[str]
                  ) -> dict[str, Any]:
    """>>> extract_slots("Prépare un point vendredi avec Inès sur Orion.", ["Inès"], ["Orion"])
    {'person': 'Inès', 'project': 'Orion', 'deadline': 'vendredi'}
    """
    m = DATE_RE.search(text)
    return {"person": find_name(text, persons), "project": find_name(text, projects),
            "deadline": m.group(0).lower() if m else None}
