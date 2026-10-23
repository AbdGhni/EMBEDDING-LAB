from embedding_lab.train.data import build_examples, cluster_batches, random_negative_variant


def tiny():
    units = {f"u{i}": {"unit_id": f"u{i}", "project": f"summre-{900 + i % 3}",
                       "retrieval_text": f"texte {i}"} for i in range(12)}
    queries = [{"query_id": f"q{i}", "text": f"question {i}", "cluster": f"p{i % 3}"}
               for i in range(6)]
    qrels = {f"q{i}": {f"u{i}": 2, f"u{i + 6}": 0, f"u{(i + 1) % 6}": 1} for i in range(6)}
    triplets = [{"query_id": f"q{i}", "pos": f"u{i}", "neg": f"u{i + 6}", "trap": "status"}
                for i in range(6)]
    return units, queries, qrels, triplets


def test_negatives_never_relevant_and_mined_ones_filtered():
    units, queries, qrels, triplets = tiny()
    mined = {"q0": ["u1", "u7", "u8"]}  # u1 est pertinent (1) : ne doit jamais être pris
    ex = build_examples(queries, qrels, units, triplets, "bsyn", mined=mined)
    for e in ex:
        assert qrels[e["query_id"]].get(e["neg_id"], 0) == 0
    assert {e["neg_id"] for e in ex if e["query_id"] == "q0"} == {"u6", "u7", "u8"}


def test_random_variant_same_size_and_breal_negatives_from_other_groups():
    units, queries, qrels, triplets = tiny()
    ex = build_examples(queries, qrels, units, triplets, "breal")
    for e in ex:
        e["cluster"] = f"breal:{units[e['pos_id']]['project'].removeprefix('summre-')}"
    rnd = random_negative_variant(ex, {"breal": list(units.values())}, qrels, seed=1)
    assert len(rnd) == len(ex)
    for e in rnd:
        assert f"breal:{units[e['neg_id']]['project'].removeprefix('summre-')}" != e["cluster"]
        assert qrels[e["query_id"]].get(e["neg_id"], 0) == 0


def test_breal_queries_use_group_id_as_cluster():
    units, queries, qrels, triplets = tiny()
    breal_queries = [{"query_id": q["query_id"], "text": q["text"],
                      "group_id": units[f"u{i}"]["project"].removeprefix("summre-")}
                     for i, q in enumerate(queries)]
    ex = build_examples(breal_queries, qrels, units, triplets, "breal")
    assert ex and all(e["cluster"] == f"breal:{units[e['pos_id']]['project'][7:]}" for e in ex)
    rnd = random_negative_variant(ex, {"breal": list(units.values())}, qrels, seed=1)
    for e in rnd:
        assert f"breal:{units[e['neg_id']]['project'][7:]}" != e["cluster"]


def test_batches_never_mix_same_cluster_or_positive():
    ex = [{"cluster": f"c{i % 4}", "positive": f"p{i % 7}"} for i in range(40)]
    batches = cluster_batches(ex, batch_size=4, seed=0)
    assert sorted(i for b in batches for i in b) == list(range(40))
    for b in batches:
        assert len({ex[i]["cluster"] for i in b}) == len(b)
        assert len({ex[i]["positive"] for i in b}) == len(b)
