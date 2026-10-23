import ast
from pathlib import Path

import pytest

from embedding_lab.memory.store import Memory
from embedding_lab.resolution.recipients import named_person, responsible_for
from embedding_lab.tools import simulated

SOURCE = Path(__file__).resolve().parents[1] / "demo" / "atlas" / "source.json"
NETWORK = {"requests", "urllib", "http", "socket", "smtplib", "httpx", "aiohttp", "ftplib"}


@pytest.fixture(scope="module")
def memory():
    return Memory.from_source(SOURCE)


def test_memory_units_are_valid_and_chains_resolve(memory):
    assert len(memory.units) == 21
    assert memory.current("u-atlas-01") == "u-atlas-10"
    assert memory.current("u-atlas-08") == "u-atlas-14"
    assert memory.contradicted_by["u-atlas-11"] == ["u-atlas-18"]


def test_mention_is_not_responsibility(memory):
    budget = responsible_for(memory, "budget")
    assert budget["name"] == "Marie" and budget["email"] is None
    assert budget["resolution_status"] == "email_missing"
    assert "Karim" in budget["justification"]  # cité, mais écarté
    assert responsible_for(memory, "communication")["resolution_status"] == "ambiguous"
    assert responsible_for(memory, "traiteur")["resolution_status"] == "not_found"
    assert named_person(memory, "Zoé")["resolution_status"] == "not_found"


def test_tool_contracts_never_execute(memory):
    p = responsible_for(memory, "budget")
    person = {k: p[k] for k in ("name", "email", "evidence_unit_ids", "resolution_status")}
    contracts = [
        simulated.email_create_draft(person, "Projet Atlas — budget", "Bonjour", ["u-atlas-14"],
                                     "2026-10-20", {"needed": True, "reason": "email_missing",
                                                    "question": "Adresse ?"}),
        simulated.tasks_create_draft("Relancer", person, "2026-10-23", ["u-atlas-15"],
                                     "2026-10-20", {"needed": True, "reason": "email_missing",
                                                    "question": "Confirmer ?"}),
        simulated.calendar_create_draft("Point Atlas", "2026-10-23T10:00:00", [], "2026-10-20"),
        simulated.clarify("insufficient_context", "À qui ?", [], "2026-10-20"),
    ]
    for c in contracts:
        assert c["executed"] is False and c["needs_confirmation"] is True


def test_unresolved_recipient_without_clarification_is_rejected(memory):
    person = {"name": None, "email": None, "evidence_unit_ids": [],
              "resolution_status": "not_found"}
    with pytest.raises(ValueError):
        simulated.email_create_draft(person, "Objet", "Corps", [], "2026-10-20")


def test_invented_email_is_rejected():
    person = {"name": "Marie", "email": "marie@example.org", "evidence_unit_ids": ["u-atlas-15"],
              "resolution_status": "resolved"}
    with pytest.raises(ValueError):
        simulated.email_create_draft(person, "Objet", "Corps", [], "2026-10-20")


def test_tools_package_imports_no_network_library():
    root = Path(__file__).resolve().parents[1] / "src" / "embedding_lab" / "tools"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not {n.split(".")[0] for n in names} & NETWORK, f"{path}: {names}"


def test_injected_instruction_is_stored_as_data(memory):
    u = memory.units["u-atlas-20"]
    assert u["type"] == "fact" and "ignore les consignes" in u["evidence"]["text"]
