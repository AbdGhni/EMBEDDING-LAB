from embedding_lab.relations.features import structural
from embedding_lab.relations.metrics import bootstrap_macro_f1, report
from embedding_lab.relations.pairs import build_pairs, order_key


def unit(uid, order, turn, typ="idea", speaker="s1", project="summre-900", text="on garde le lieu"):
    return {"unit_id": uid, "source_order": order, "source_id": f"900{'abc'[order]}_X",
            "evidence": {"segment_ids": [f"900{'abc'[order]}_X:t{turn:04d}"], "char_start": 0,
                         "text": text},
            "type": typ, "speaker": speaker, "project": project}


def test_pairs_are_oriented_recent_first_and_none_never_linked():
    units = {u["unit_id"]: u for u in [
        unit("u1", 0, 3), unit("u2", 1, 1, "decision"), unit("u3", 1, 5), unit("u4", 2, 2)]}
    # relation annotée « à rebours » : l'ancienne vers la récente
    rels = [{"from_id": "u1", "to_id": "u2", "relation": "supports"},
            {"from_id": "u4", "to_id": "u3", "relation": "supersedes"}]
    pairs = build_pairs(rels, units)
    pos = [p for p in pairs if p["label"] != "none"]
    for p in pairs:
        assert order_key(units[p["x"]]) > order_key(units[p["y"]])
    assert {(p["x"], p["y"], p["label"]) for p in pos} == {("u2", "u1", "supports"),
                                                           ("u4", "u3", "supersedes")}
    linked = {frozenset((r["from_id"], r["to_id"])) for r in rels}
    nones = [p for p in pairs if p["label"] == "none"]
    assert len(nones) == 2
    assert all(frozenset((p["x"], p["y"])) not in linked for p in nones)


def test_structural_ignores_status():
    a, b = unit("u1", 1, 1, "answer"), unit("u2", 0, 1, "question")
    a2 = {**a, "status": "resolved"}
    assert structural(a, b) == structural(a2, b)


def test_report_and_bootstrap():
    gold = ["supersedes", "none", "answers", "none"]
    pred = ["supersedes", "none", "none", "none"]
    labels = ("supersedes", "answers", "none")
    rep = report(gold, pred, labels)
    assert rep["per_class"]["answers"]["recall"] == 0.0
    assert rep["macro_f1_relations_only"] == 0.5
    ci = bootstrap_macro_f1(gold, pred, ["g1", "g1", "g2", "g2"], labels, n_resamples=100)
    assert ci["n_clusters"] == 2 and ci["ci_low"] <= ci["value"] <= ci["ci_high"]


def test_demote_moves_replaced_unit_below_its_replacement():
    from embedding_lab.retrieval.hybrid import demote

    units = {"old": unit("old", 0, 1, "decision"), "new": unit("new", 2, 1, "decision"),
             "other": {**unit("other", 1, 1), "project": "summre-901"}}
    scores = {"old": 0.9, "other": 0.8, "new": 0.7}
    out, applied = demote(scores, units, lambda x, y: 1.0 if x["unit_id"] == "new" else 0.0)
    order = sorted(out, key=lambda u: -out[u])
    assert applied == [("new", "old")]
    assert order == ["other", "new", "old"]
