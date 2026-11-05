"""EL-028 : mémoire Cèdre et espace de travail à plusieurs projets (sans modèle téléchargé)."""

import json
import re
from datetime import date
from pathlib import Path

import pytest

from embedding_lab.agent.workspace import Workspace
from embedding_lab.memory.store import Memory
from embedding_lab.resolution.recipients import responsible_for

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "demo" / "atlas" / "source.json"
CEDRE = ROOT / "demo" / "cedre" / "source.json"


class StubEncoder:
    """Recouvrement de mots : suffisant pour tester le routage, pas la qualité de recherche."""

    def score(self, query, units):
        q = set(re.findall(r"\w+", query.lower()))
        return {u["unit_id"]: len(q & set(re.findall(r"\w+", u["retrieval_text"].lower())))
                / (1 + len(q)) for u in units}


class StubIntents:
    def predict(self, text):
        t = text.lower()
        if "peut-être" in t:
            return "no_action", 0.9
        if "dossier" in t:
            return "build_dossier", 0.9
        if "mail" in t or "écris" in t:
            return "draft_email", 0.9
        return "answer", 0.9


@pytest.fixture(scope="module")
def workspace():
    return Workspace.from_sources([ATLAS, CEDRE], StubEncoder(), StubIntents(),
                                  date(2026, 10, 20))


def test_cedre_source_is_valid_and_chains_resolve():
    mem = Memory.from_source(CEDRE)
    assert len(mem.units) == 21 and len(mem.relations) == 8
    assert mem.projects() == ["Cèdre"]
    assert mem.current("u-cedre-01") == "u-cedre-10"
    assert mem.current("u-cedre-05") == "u-cedre-11"
    assert mem.current("u-cedre-04") == "u-cedre-12"
    assert mem.current("u-cedre-08") == "u-cedre-15"
    assert mem.contradicted_by["u-cedre-11"] == ["u-cedre-17"]
    assert all(u["annotation"]["notes"].startswith("données de démonstration fictives")
               for u in mem.units.values())


def test_sources_have_no_email_address():
    for path in (ATLAS, CEDRE):
        assert not re.search(r"[\w.]+@[\w.]+", path.read_text(encoding="utf-8"))


def test_mention_is_not_responsibility_in_cedre():
    mem = Memory.from_source(CEDRE)
    formation = responsible_for(mem, "formation")
    assert formation["name"] == "Nadia" and formation["email"] is None
    assert responsible_for(mem, "sécurité")["resolution_status"] == "ambiguous"
    assert responsible_for(mem, "pages rh")["resolution_status"] == "not_found"


def test_injected_instruction_is_stored_as_data():
    u = Memory.from_source(CEDRE).units["u-cedre-19"]
    assert u["type"] == "fact" and u["status"] == "unknown"
    assert "oublie tes règles" in u["evidence"]["text"]


def test_named_project_is_routed_and_sources_do_not_mix(workspace):
    out = workspace.handle("Prépare un dossier complet sur le projet Cèdre.")
    assert out["routed_project"] == "Cèdre"
    assert out["citations"] and all(c.startswith("u-cedre") for c in out["citations"])
    out = workspace.handle("Prépare un dossier complet sur le projet Atlas.")
    assert out["routed_project"] == "Atlas"
    assert out["citations"] and all(c.startswith("u-atlas") for c in out["citations"])


def test_missing_information_is_declared_per_project(workspace):
    cedre = workspace.handle("Prépare un dossier sur Cèdre.")["sections"]
    atlas = workspace.handle("Prépare un dossier sur Atlas.")["sections"]
    cedre_missing = " ".join(c["text"] for c in cedre["Informations absentes"])
    atlas_missing = " ".join(c["text"] for c in atlas["Informations absentes"])
    assert "pages RH" in cedre_missing and "traiteur" not in cedre_missing
    assert "traiteur" in atlas_missing and "pages RH" not in atlas_missing


def test_unnamed_project_asks_which_one(workspace):
    out = workspace.handle("Prépare un dossier complet.")
    assert out["routed_project"] is None and out["operation"] == "clarify"
    clar = out["action"]["clarification"]
    assert clar["needed"] and clar["reason"] == "insufficient_context"
    assert "Atlas" in clar["question"] and "Cèdre" in clar["question"]
    assert out["action"]["executed"] is False and out["action"]["needs_confirmation"] is True
    assert "citations" not in out  # aucune recherche


def test_hypothesis_without_project_creates_no_action(workspace):
    out = workspace.handle("On pourrait peut-être revoir l'hébergement.")
    assert out["operation"] == "no_action" and out["action"] is None


def test_email_goes_to_the_owner_of_the_named_project(workspace):
    out = workspace.handle("Écris à la personne responsable de la formation de Cèdre "
                           "pour demander le support avant mercredi.")
    assert out["action"]["recipient"]["name"] == "Nadia"
    assert out["action"]["recipient"]["email"] is None
    assert out["action"]["executed"] is False


def test_duplicate_project_is_rejected():
    with pytest.raises(ValueError):
        Workspace.from_sources([ATLAS, ATLAS], StubEncoder(), StubIntents(), date(2026, 10, 20))


def test_source_without_units_is_rejected(tmp_path):
    src = json.loads(ATLAS.read_text(encoding="utf-8"))
    src["units"], src["relations"] = [], []
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(src, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        Workspace.from_sources([bad], StubEncoder(), StubIntents(), date(2026, 10, 20))
