import json

import pytest

from embedding_lab.eval.harness import config_fingerprint, load_benchmark, run_benchmark
from embedding_lab.retrieval.baselines import RandomRetriever
from embedding_lab.retrieval.bm25 import BM25Retriever


def write_bench(root, name="bsyn", split="val"):
    base = root / ("data/bsyn" if name == "bsyn" else "data/breal") / split
    base.mkdir(parents=True)
    units = [
        {"unit_id": "u-1", "project": "summre-900", "retrieval_text": "le budget est validé"},
        {"unit_id": "u-2", "project": "summre-900", "retrieval_text": "le budget est proposé"},
        {"unit_id": "u-3", "project": "summre-901", "retrieval_text": "la date de lancement"},
    ]
    queries = [{"query_id": "q1", "text": "budget validé", "answerable": True,
                "cluster": "p1", "group_id": "900"},
               {"query_id": "q2", "text": "rien", "answerable": False, "cluster": "p1",
                "group_id": "900"}]
    (base / "units.jsonl").write_text("".join(json.dumps(u) + "\n" for u in units))
    (base / "queries.jsonl").write_text("".join(json.dumps(q) + "\n" for q in queries))
    (base / "qrels.json").write_text(json.dumps({"q1": {"u-1": 2, "u-2": 0}}))
    (base / "triplets.jsonl").write_text(
        json.dumps({"query_id": "q1", "pos": "u-1", "neg": "u-2", "trap": "status"}) + "\n")
    return root


def test_test_split_requires_reason_and_is_logged(tmp_path):
    root = write_bench(tmp_path, split="test")
    with pytest.raises(PermissionError):
        load_benchmark("bsyn", "test", root=root)
    load_benchmark("bsyn", "test", test_reason="essai", run_id="r", root=root)
    assert (root / "runs/TEST_ACCESS.log").read_text().count("\n") == 1


def test_unanswerable_queries_excluded_and_triplets_scored(tmp_path):
    bench = load_benchmark("bsyn", "val", root=write_bench(tmp_path))
    res = run_benchmark(BM25Retriever(), bench)
    assert res["n_queries"] == 1
    assert res["summary"]["ndcg@10"] == pytest.approx(1.0)
    assert res["summary"]["pairwise_by_trap"]["status"]["n"] == 1


def test_breal_scope_is_the_query_group(tmp_path):
    bench = load_benchmark("breal", "val", root=write_bench(tmp_path, name="breal"))
    assert {u["unit_id"] for u in bench["scopes"][bench["scope_of"]["q1"]]} == {"u-1", "u-2"}


def test_fingerprint_changes_only_with_system_config(tmp_path):
    bench = load_benchmark("bsyn", "val", root=write_bench(tmp_path))
    a = config_fingerprint(BM25Retriever().config(), bench)
    assert a == config_fingerprint(BM25Retriever().config(), bench)
    assert a != config_fingerprint(BM25Retriever(k1=1.2).config(), bench)


def test_random_baseline_is_deterministic(tmp_path):
    bench = load_benchmark("bsyn", "val", root=write_bench(tmp_path))
    assert run_benchmark(RandomRetriever(), bench)["per_query"] == \
        run_benchmark(RandomRetriever(), bench)["per_query"]
