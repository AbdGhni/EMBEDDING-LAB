import pytest

from embedding_lab.schemas import check_relation, check_unit
from embedding_lab.synth.bsyn import generate_split, project_names
from embedding_lab.synth.templates import (
    PEOPLE,
    QUERY_FAMILIES_BY_SPLIT,
    RESERVED_PROJECTS,
    UNIT_FAMILIES_BY_SPLIT,
)

SPLITS = ("train", "val", "test")


@pytest.fixture(scope="module")
def val():
    return generate_split("val", 8, seed=3)


def test_entity_pools_and_families_are_disjoint():
    for i, a in enumerate(SPLITS):
        for b in SPLITS[i + 1:]:
            assert not set(PEOPLE[a]) & set(PEOPLE[b])
            assert not set(project_names(a)) & set(project_names(b))
            assert not set(UNIT_FAMILIES_BY_SPLIT[a]) & set(UNIT_FAMILIES_BY_SPLIT[b])
            assert not set(QUERY_FAMILIES_BY_SPLIT[a]) & set(QUERY_FAMILIES_BY_SPLIT[b])
    assert all(not RESERVED_PROJECTS & set(project_names(s)) for s in SPLITS)


def test_generation_is_deterministic():
    assert generate_split("val", 3, seed=5) == generate_split("val", 3, seed=5)


def test_all_contracts_valid(val):
    texts = {m["meeting_id"]: m["text"] for m in val["meetings"]}
    index = {u["unit_id"]: u for u in val["units"]}
    assert all(check_unit(u, texts[u["source_id"]]) == [] for u in val["units"])
    assert all(check_relation(r, index) == [] for r in val["relations"])


def test_traps_are_never_relevant_and_belong_to_split(val):
    index = {u["unit_id"]: u for u in val["units"]}
    for t in val["triplets"]:
        assert val["qrels"][t["query_id"]][t["pos"]] == 2
        assert val["qrels"][t["query_id"]].get(t["neg"], 0) == 0
        assert t["neg"] in index and t["pos"] in index


def test_current_budget_answer_matches_story(val):
    index = {u["unit_id"]: u for u in val["units"]}
    for q in val["queries"]:
        if q["type"] != "q_budget_current":
            continue
        pos = [index[u] for u, r in val["qrels"][q["query_id"]].items() if r == 2]
        assert len(pos) == 1
        assert pos[0]["status"] in ("active", "cancelled")
        assert pos[0]["project"] in q["text"]


def test_rendered_values_match_metadata(val):
    for u in val["units"]:
        if u["amount"]:
            assert u["amount"] in u["evidence"]["text"]


def test_unanswerable_queries_have_no_qrels(val):
    for q in val["queries"]:
        assert (q["query_id"] in val["qrels"]) == q["answerable"]
