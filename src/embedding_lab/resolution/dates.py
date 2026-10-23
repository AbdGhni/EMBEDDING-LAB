"""Résolution des échéances relatives (EL-020). La date de référence est **injectée** : aucun
appel à l'horloge, pour que les résultats soient reproductibles.

Convention : un jour de la semaine désigne sa **prochaine** occurrence strictement après la
date de référence (« vendredi » un mardi = le vendredi de la même semaine ; « vendredi » un
vendredi = le vendredi suivant). Une expression non reconnue renvoie ``None`` : l'appelant
demande alors une précision au lieu de deviner.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
          "septembre", "octobre", "novembre", "décembre"]
_FOLD = {"fevrier": "février", "aout": "août", "decembre": "décembre"}


def next_weekday(ref: date, weekday: int) -> date:
    delta = (weekday - ref.weekday()) % 7 or 7
    return ref + timedelta(days=delta)


def resolve(expr: str | None, ref: date) -> date | None:
    """>>> ref = date(2026, 10, 20)  # mardi
    >>> resolve("avant vendredi", ref), resolve("demain", ref), resolve("le 3 novembre", ref)
    (datetime.date(2026, 10, 23), datetime.date(2026, 10, 21), datetime.date(2026, 11, 3))
    >>> resolve("lundi prochain", ref), resolve("la fin du mois", ref), resolve("bientôt", ref)
    (datetime.date(2026, 10, 26), datetime.date(2026, 10, 31), None)
    """
    if not expr:
        return None
    t = expr.lower().strip()
    if "après-demain" in t:
        return ref + timedelta(days=2)
    if "demain" in t:
        return ref + timedelta(days=1)
    if "aujourd'hui" in t:
        return ref
    m = re.search(r"\b(\d{1,2})(?:er)? (\w+)(?: (\d{4}))?", t)
    if m:
        month = _FOLD.get(m.group(2), m.group(2))
        if month in MONTHS:
            year = int(m.group(3)) if m.group(3) else ref.year
            d = date(year, MONTHS.index(month) + 1, int(m.group(1)))
            if not m.group(3) and d < ref:
                d = date(year + 1, d.month, d.day)
            return d
    for i, day in enumerate(DAYS):
        if re.search(rf"\b{day}\b", t):
            d = next_weekday(ref, i)
            if "prochain" in t and d - ref < timedelta(days=7) and d.weekday() > ref.weekday():
                d += timedelta(days=7)
            return d
    if "semaine prochaine" in t:
        return next_weekday(ref, 0)
    if "fin de semaine" in t or "fin de la semaine" in t:
        return next_weekday(ref, 4) if ref.weekday() < 4 else ref
    if "fin du mois" in t or "fin octobre" in t:
        return date(ref.year, ref.month, calendar.monthrange(ref.year, ref.month)[1])
    return None
