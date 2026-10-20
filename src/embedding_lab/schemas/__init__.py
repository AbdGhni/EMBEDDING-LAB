"""Validation des contrats JSON : schéma structurel + invariants sémantiques.

Le schéma JSON vérifie la forme. Les fonctions ``check_*`` vérifient ce qu'un schéma
ne peut pas exprimer : offsets cohérents avec la transcription, sens des relations,
destinataire issu de l'annuaire de démo, clarification obligatoire quand la
résolution échoue.

Exemple ::

    >>> errs = validate("action", {"intent": "clarify", "tool_candidate": "none",
    ...     "source_unit_ids": [], "clarification": {"needed": False},
    ...     "needs_confirmation": True, "executed": False})
    >>> bool(errs)   # clarify impose clarification.needed = true
    True
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import date
from functools import cache
from importlib import resources
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_NAMES = ("unit", "relation", "action")
_FORMAT_CHECKER = FormatChecker()


@cache
def load_schema(name: str) -> dict:
    if name not in SCHEMA_NAMES:
        raise ValueError(f"schéma inconnu : {name}")
    text = resources.files(__package__).joinpath(f"{name}.schema.json").read_text("utf-8")
    schema = json.loads(text)
    Draft202012Validator.check_schema(schema)
    return schema


def validate(name: str, obj: Mapping[str, Any]) -> list[str]:
    """Erreurs structurelles (liste vide = valide)."""
    validator = Draft202012Validator(load_schema(name), format_checker=_FORMAT_CHECKER)
    return sorted(
        f"{'/'.join(map(str, e.absolute_path)) or '<racine>'}: {e.message}"
        for e in validator.iter_errors(obj)
    )


def check_unit(unit: Mapping[str, Any], source_text: str | None = None) -> list[str]:
    """Schéma + invariants d'une unité. ``source_text`` = transcription brute de la source."""
    errors = validate("unit", unit)
    if errors:
        return errors
    ev = unit["evidence"]
    if ev["char_end"] <= ev["char_start"]:
        errors.append("evidence: char_end doit être > char_start")
    elif source_text is not None and source_text[ev["char_start"]:ev["char_end"]] != ev["text"]:
        errors.append("evidence: l'extrait ne correspond pas aux offsets dans la source")
    owner = unit.get("owner")
    if owner and owner in unit.get("mentioned_people", []):
        errors.append("owner ne peut pas figurer aussi dans mentioned_people")
    return errors


def check_relation(
    rel: Mapping[str, Any], units: Mapping[str, Mapping[str, Any]] | None = None
) -> list[str]:
    """Schéma + invariants. ``units`` = index unit_id -> unité, si disponible."""
    errors = validate("relation", rel)
    if errors:
        return errors
    if rel["from_id"] == rel["to_id"]:
        errors.append("une unité ne peut pas être en relation avec elle-même")
    if units is not None:
        for key in ("from_id", "to_id"):
            if rel[key] not in units:
                errors.append(f"{key} inconnu : {rel[key]}")
        if errors:
            return errors
        src, dst = units[rel["from_id"]], units[rel["to_id"]]
        if rel["relation"] == "supersedes":
            if date.fromisoformat(src["source_date"]) < date.fromisoformat(dst["source_date"]):
                errors.append("supersedes : l'unité qui remplace doit être au moins aussi récente")
            if src.get("project") != dst.get("project"):
                errors.append("supersedes : les deux unités doivent concerner le même projet")
        if rel["relation"] == "answers" and dst["type"] != "question":
            errors.append("answers : to_id doit être une question")
    return errors


def check_action(
    action: Mapping[str, Any],
    units: Mapping[str, Mapping[str, Any]] | None = None,
    directory: Mapping[str, str] | None = None,
) -> list[str]:
    """Schéma + invariants. ``directory`` = annuaire fictif nom -> e-mail de la démo."""
    errors = validate("action", action)
    if errors:
        return errors
    people = [action[k] for k in ("recipient", "assignee") if k in action]
    for person in people:
        email = person["email"]
        if email is not None and (directory is None or directory.get(person["name"]) != email):
            errors.append("e-mail absent de l'annuaire de démo : adresse inventée interdite")
        if person["resolution_status"] != "resolved" and not action["clarification"]["needed"]:
            errors.append("destinataire non résolu : une clarification est obligatoire")
    if units is not None:
        cited: Iterable[str] = list(action["source_unit_ids"]) + [
            uid for p in people for uid in p["evidence_unit_ids"]
        ]
        errors += [f"unité citée inconnue : {uid}" for uid in cited if uid not in units]
    return errors
