import pytest

from embedding_lab.eval.compare import compare, component_of_groups, mean_over_seeds


def test_mean_over_seeds_rejects_mismatched_items():
    with pytest.raises(ValueError):
        mean_over_seeds([{"q1": 1.0}, {"q2": 1.0}])


def test_compare_counts_components_not_groups():
    of = component_of_groups([{"001", "002"}, {"003"}])
    cluster_of = {"q1": of["001"], "q2": of["002"], "q3": of["003"]}
    a = {"q1": 1.0, "q2": 1.0, "q3": 0.5}
    b = {"q1": 0.0, "q2": 0.0, "q3": 0.0}
    res = compare(a, b, cluster_of, n_resamples=200)
    assert res["n_clusters"] == 2
    assert res["permutation"]["method"] == "exact"
    assert res["bootstrap"]["diff"] == pytest.approx(2.5 / 3)
