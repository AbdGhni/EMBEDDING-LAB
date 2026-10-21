import math

import pytest

from embedding_lab.eval.metrics import (
    evaluate_run,
    mean_metric,
    mrr_at_k,
    ndcg_at_k,
    paired_cluster_bootstrap,
    pairwise_accuracy,
    recall_at_k,
)
from embedding_lab.eval.test_access import log_test_access


def test_ndcg_hand_computed():
    # DCG = 3/log2(3) + 1/log2(4) ; IDCG = 3/log2(2) + 1/log2(3)
    qrels = {"a": 2, "b": 1}
    expected = (3 / math.log2(3) + 1 / 2) / (3 + 1 / math.log2(3))
    assert ndcg_at_k(["x", "a", "b"], qrels, 10) == pytest.approx(expected)


def test_perfect_and_empty_rankings():
    qrels = {"a": 2, "b": 1}
    assert ndcg_at_k(["a", "b"], qrels) == pytest.approx(1.0)
    assert ndcg_at_k([], qrels) == 0.0
    assert mrr_at_k([], qrels) == 0.0


def test_trap_ranked_first_is_penalised():
    # le piège (pertinence 0) passe devant la vraie décision
    qrels = {"decision": 2, "proposition": 0}
    assert ndcg_at_k(["proposition", "decision"], qrels) < ndcg_at_k(["decision"], qrels)


def test_multi_positive_recall():
    qrels = {"a": 2, "b": 1, "c": 0}
    assert recall_at_k(["a", "c", "b"], qrels, 2) == 0.5
    assert recall_at_k(["a", "c", "b"], qrels, 3) == 1.0


def test_unanswerable_query_must_be_excluded():
    with pytest.raises(ValueError):
        ndcg_at_k(["a"], {"a": 0})


def test_missing_ranking_scores_zero():
    per_q = evaluate_run({}, {"q1": {"a": 2}})
    assert per_q["q1"]["ndcg@10"] == 0.0
    assert mean_metric(per_q, "recall@10") == 0.0


def test_pairwise_accuracy_counts_ties_as_half():
    assert pairwise_accuracy([(0.9, 0.1), (0.2, 0.8), (0.5, 0.5)]) == pytest.approx(0.5)


def test_cluster_bootstrap_detects_clear_gain_and_no_gain():
    clusters = {f"q{i}": f"p{i // 3}" for i in range(30)}
    better = {q: 0.8 for q in clusters}
    worse = {q: 0.5 for q in clusters}
    res = paired_cluster_bootstrap(better, worse, clusters, n_resamples=500)
    assert res["ci_low"] > 0 and res["n_clusters"] == 10
    noisy = {q: (0.6 if i % 2 else 0.4) for i, q in enumerate(clusters)}
    same = {q: 0.5 for q in clusters}
    res2 = paired_cluster_bootstrap(noisy, same, clusters, n_resamples=500)
    assert res2["ci_low"] <= 0 <= res2["ci_high"]


def test_bootstrap_requires_same_queries():
    with pytest.raises(ValueError):
        paired_cluster_bootstrap({"q1": 1.0}, {"q2": 1.0}, {"q1": "a", "q2": "a"})


def test_test_access_requires_reason(tmp_path):
    log = tmp_path / "TEST_ACCESS.log"
    with pytest.raises(PermissionError):
        log_test_access("E1-x", " ", "B-SYN", log)
    entry = log_test_access("E1-x", "évaluation finale", "B-SYN", log)
    assert entry["time"].endswith("+02:00") or entry["time"].endswith("+01:00")
    assert log.read_text(encoding="utf-8").count("\n") == 1
