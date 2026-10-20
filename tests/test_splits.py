from embedding_lab.data.splits import assign_splits, group_components, leakage_report


def m(mid, group, speakers, manual=True, mtype="decision", text="a b c d e f g h i j"):
    return {"meeting_id": mid, "group_id": group, "speakers": speakers,
            "transcription": "manual" if manual else "asr", "meeting_type": mtype, "text": text}


def corpus():
    ms = []
    for i in range(12):
        g = f"{i:03d}"
        # groupes 000 et 001 partagent la personne "shared"
        spk = ["shared", f"p{i}"] if i < 2 else [f"p{i}a", f"p{i}b"]
        for s in "abc":
            ms.append(m(f"{g}{s}_X", g, spk, manual=(s == "a"), text=f"mots uniques groupe {g} {s} "
                        "un deux trois quatre cinq six sept"))
    return ms


def test_shared_speaker_merges_groups():
    comps = group_components(corpus())
    assert {"000", "001"} in comps
    assert len(comps) == 11


def test_no_group_or_person_crosses_splits():
    ms = corpus()
    targets = {"val": {"manual": 2}, "test": {"manual": 2}}
    split_of = assign_splits(ms, targets, seed=1, trials=500, max_component_share=0.5)
    rep = leakage_report(ms, split_of)
    assert rep["groups_in_several_splits"] == []
    assert rep["speakers_in_several_splits"] == []
    assert {"val", "test"} <= set(split_of.values())


def test_assignment_is_deterministic():
    ms = corpus()
    t = {"val": {"manual": 2}, "test": {"manual": 2}}
    assert assign_splits(ms, t, seed=7, trials=300) == assign_splits(ms, t, seed=7, trials=300)


def test_large_component_forced_to_train():
    ms = corpus()
    ms += [m(f"{100 + i}a_X", f"{100 + i}", ["giant"]) for i in range(20)]
    split_of = assign_splits(ms, {"val": {"manual": 2}, "test": {"manual": 2}}, trials=200,
                             max_component_share=0.3)
    assert all(split_of[f"{100 + i}a_X"] == "train" for i in range(20))


def test_ngram_overlap_detects_copied_text():
    shared = "texte de consigne lu à voix haute identique dans deux réunions différentes"
    ms = [m("001a_X", "001", ["a"], text=shared), m("002a_X", "002", ["b"], text=shared)]
    rep = leakage_report(ms, {"001a_X": "train", "002a_X": "test"})
    assert rep["8gram_overlap_with_train"]["max"] == 1.0
