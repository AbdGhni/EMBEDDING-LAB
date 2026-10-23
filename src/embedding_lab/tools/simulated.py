"""Outils **simulés** (EL-023) : ils construisent une proposition, ils n'exécutent rien.

Aucune bibliothèque réseau n'est importée dans ce paquet (vérifié par un test). Chaque contrat
est validé par ``schemas/action.schema.json`` : ``needs_confirmation`` vaut toujours ``true``
et ``executed`` toujours ``false``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from embedding_lab.schemas import check_action


def _finish(contract: dict[str, Any]) -> dict[str, Any]:
    contract["needs_confirmation"] = True
    contract["executed"] = False
    errors = check_action(contract)
    if errors:
        raise ValueError(f"contrat d'action invalide : {errors}")
    return contract


def _clar(clarification: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(clarification) if clarification else {"needed": False}


def email_create_draft(recipient: Mapping[str, Any], subject: str, body: str,
                       source_unit_ids: Sequence[str], reference_date: str,
                       clarification: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _finish({"intent": "draft_email", "tool_candidate": "email.create_draft",
                    "recipient": dict(recipient), "subject": subject, "body": body,
                    "reference_date": reference_date, "source_unit_ids": list(source_unit_ids),
                    "clarification": _clar(clarification)})


def tasks_create_draft(title: str, assignee: Mapping[str, Any] | None, due_date: str | None,
                       source_unit_ids: Sequence[str], reference_date: str,
                       clarification: Mapping[str, Any] | None = None) -> dict[str, Any]:
    c = {"intent": "create_task", "tool_candidate": "tasks.create_draft", "title": title,
         "due_date": due_date, "reference_date": reference_date,
         "source_unit_ids": list(source_unit_ids), "clarification": _clar(clarification)}
    if assignee:
        c["assignee"] = dict(assignee)
    return _finish(c)


def calendar_create_draft(title: str, start: str | None, source_unit_ids: Sequence[str],
                          reference_date: str, clarification: Mapping[str, Any] | None = None
                          ) -> dict[str, Any]:
    return _finish({"intent": "schedule_event", "tool_candidate": "calendar.create_draft",
                    "title": title, "start": start, "reference_date": reference_date,
                    "source_unit_ids": list(source_unit_ids),
                    "clarification": _clar(clarification)})


def clarify(reason: str, question: str, source_unit_ids: Sequence[str], reference_date: str
            ) -> dict[str, Any]:
    return _finish({"intent": "clarify", "tool_candidate": "none",
                    "reference_date": reference_date, "source_unit_ids": list(source_unit_ids),
                    "clarification": {"needed": True, "reason": reason, "question": question}})
