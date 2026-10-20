from embedding_lab.ingest.summre import (
    build_meetings,
    group_id,
    parse_meeting_code,
    session_letter,
)


def rec(mid, spk, segs, split="dev"):
    return {"meeting_id": mid, "speaker_id": spk, "official_split": split,
            "segments": [{"start": s, "end": e, "text": t} for s, e, t in segs]}


def test_group_and_session_parsing():
    assert group_id("004c_PAPH") == "004"
    assert session_letter("004c_PAPH") == "c"
    assert group_id("101a_XYZ") == "101"


def test_meeting_code_parsing_follows_dataset_card():
    assert parse_meeting_code("001a_PARL") == {
        "experiment_type": "pilot", "scenario": "A",
        "meeting_type": "reporting", "location": "LPL"}
    assert parse_meeting_code("017a_EBRZ")["meeting_type"] == "reporting"
    assert parse_meeting_code("015b_EBDD")["meeting_type"] == "decision"


def test_interleaves_speakers_by_time():
    m = build_meetings([
        rec("001a_X", "A", [(0, 1, "bonjour"), (5, 6, "on valide")]),
        rec("001a_X", "B", [(2, 3, "salut"), (7, 8, "ok")]),
    ])[0]
    assert [t["speaker"] for t in m["turns"]] == ["A", "B", "A", "B"]


def test_merges_same_speaker_only_within_gap():
    segs = [(0, 1, "un"), (1.5, 2, "deux"), (10, 11, "trois")]
    m = build_meetings([rec("001a_X", "A", segs)], merge_gap=1.0)[0]
    assert [t["text"] for t in m["turns"]] == ["un deux", "trois"]
    assert m["turns"][0]["n_segments"] == 2


def test_offsets_point_to_turn_text():
    m = build_meetings([
        rec("002b_Y", "S1", [(0, 1, "on part   sur juin")]),
        rec("002b_Y", "S2", [(1.5, 2, "jeudi c'est férié")]),
    ])[0]
    for t in m["turns"]:
        assert m["text"][t["char_start"]:t["char_end"]] == t["text"]
    # espaces normalisés avant le calcul des offsets
    assert m["turns"][0]["text"] == "on part sur juin"


def test_drops_empty_segments_and_keeps_metadata():
    m = build_meetings([rec("003c_Z", "A", [(0, 1, "  "), (1, 2, "texte")], split="train")])[0]
    assert len(m["turns"]) == 1
    assert (m["transcription"], m["group_id"], m["session"]) == ("asr", "003", "c")


def test_turn_ids_are_stable_and_ordered():
    recs = [rec("004a_W", "A", [(0, 1, "a")]), rec("004a_W", "B", [(2, 3, "b")])]
    ids1 = [t["turn_id"] for t in build_meetings(recs)[0]["turns"]]
    ids2 = [t["turn_id"] for t in build_meetings(list(reversed(recs)))[0]["turns"]]
    assert ids1 == ids2 == ["004a_W:t0000", "004a_W:t0001"]
