"""Invariants des contrats : on teste les risques réels (action exécutée, adresse
inventée, offsets faux, relation mal orientée), pas la recopie du schéma."""

import copy

import pytest

from embedding_lab.schemas import (
    SCHEMA_NAMES,
    check_action,
    check_relation,
    check_unit,
    load_schema,
)

SOURCE = "bon alors on confirme le report au 22 novembre pour atlas"


def make_unit(**over):
    u = {
        "unit_id": "u-014",
        "source_id": "meeting-03",
        "source_date": "2026-10-12",
        "project": "Atlas",
        "type": "decision",
        "statement": "Le lancement du projet Atlas est reporté au 22 novembre.",
        "status": "active",
        "assertion": "extracted",
        "speaker": "Marie",
        "owner": None,
        "mentioned_people": [],
        "event_date": "2026-11-22",
        "evidence": {
            "text": "on confirme le report au 22 novembre",
            "char_start": 10,
            "char_end": 46,
        },
        "annotation": {"origin": "human", "annotator": "test", "reviewed": True},
    }
    u.update(over)
    return u


def make_email(**over):
    """Exemple du sujet (brouillon à Marie, adresse inconnue)."""
    a = {
        "intent": "draft_email",
        "tool_candidate": "email.create_draft",
        "recipient": {
            "name": "Marie",
            "email": None,
            "evidence_unit_ids": ["u-011"],
            "resolution_status": "email_missing",
        },
        "subject": "Projet Atlas — version validée du budget",
        "body": "Bonjour Marie,\n\nPourrais-tu me transmettre la dernière version validée "
        "du budget du projet Atlas avant vendredi ?\n\nMerci.",
        "reference_date": "2026-10-20",
        "source_unit_ids": ["u-011", "u-014"],
        "clarification": {
            "needed": True,
            "reason": "email_missing",
            "question": "Je n'ai pas l'adresse de Marie : peux-tu la confirmer ?",
        },
        "needs_confirmation": True,
        "executed": False,
    }
    a.update(over)
    return a


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schemas_are_valid_json_schema(name):
    load_schema(name)


def test_unit_valid_with_matching_offsets():
    assert check_unit(make_unit(), SOURCE) == []


def test_unit_offsets_must_match_source():
    u = make_unit()
    u["evidence"]["char_start"] += 1
    assert any("offsets" in e for e in check_unit(u, SOURCE))


def test_unit_rejects_unknown_type():
    assert check_unit(make_unit(type="rumeur"))


def test_owner_cannot_be_mere_mention():
    u = make_unit(owner="Karim", mentioned_people=["Karim"])
    assert check_unit(u)


def test_brief_email_example_is_valid():
    assert check_action(make_email()) == []


@pytest.mark.parametrize("field,value", [("executed", True), ("needs_confirmation", False)])
def test_action_can_never_be_executed_or_auto_confirmed(field, value):
    assert check_action(make_email(**{field: value}))


def test_invented_email_rejected():
    a = make_email()
    a["recipient"] = dict(a["recipient"], email="marie@atlas.fr", resolution_status="resolved")
    a["clarification"] = {"needed": False}
    assert any("inventée" in e for e in check_action(a, directory={}))
    assert check_action(a, directory={"Marie": "marie@atlas.fr"}) == []


def test_unresolved_recipient_requires_clarification():
    a = make_email(clarification={"needed": False})
    assert check_action(a)


def test_ambiguous_recipient_cannot_carry_email():
    a = make_email()
    a["recipient"] = {"name": None, "email": "x@y.fr", "evidence_unit_ids": [],
                      "resolution_status": "ambiguous"}
    assert check_action(a)


def test_clarify_intent_requires_question():
    a = {"intent": "clarify", "tool_candidate": "none", "source_unit_ids": [],
         "clarification": {"needed": True, "reason": "insufficient_context"},
         "needs_confirmation": True, "executed": False}
    assert check_action(a)
    a["clarification"]["question"] = "À qui faut-il envoyer quoi exactement ?"
    assert check_action(a) == []


def test_action_cites_only_existing_units():
    assert check_action(make_email(), units={"u-011": {}})  # u-014 manquant


def test_supersedes_direction_and_project():
    old = make_unit(unit_id="u-006", source_date="2026-10-05")
    new = make_unit()
    units = {"u-006": old, "u-014": new}
    rel = {"from_id": "u-014", "to_id": "u-006", "relation": "supersedes",
           "evidence_source_id": "meeting-03", "justification": "même projet, report confirmé",
           "origin": "human"}
    assert check_relation(rel, units) == []
    reversed_rel = dict(rel, from_id="u-006", to_id="u-014")
    assert check_relation(reversed_rel, units)
    other = copy.deepcopy(units)
    other["u-006"]["project"] = "Orion"
    assert check_relation(rel, other)


def test_supersedes_uses_order_when_dates_unknown():
    old = make_unit(unit_id="u-006", source_date=None, source_order=0)
    new = make_unit(source_date=None, source_order=2)
    rel = {"from_id": "u-014", "to_id": "u-006", "relation": "supersedes",
           "evidence_source_id": "004c", "justification": "réunion c revient sur a",
           "origin": "human"}
    assert check_relation(rel, {"u-006": old, "u-014": new}) == []
    undated = {"u-006": make_unit(unit_id="u-006", source_date=None),
               "u-014": make_unit(source_date=None)}
    assert any("invérifiable" in e for e in check_relation(rel, undated))


def test_answers_must_target_a_question():
    units = {"u-1": make_unit(unit_id="u-1", type="answer"), "u-2": make_unit(unit_id="u-2")}
    rel = {"from_id": "u-1", "to_id": "u-2", "relation": "answers",
           "evidence_source_id": "m", "justification": "j", "origin": "human"}
    assert check_relation(rel, units)
