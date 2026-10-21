from embedding_lab.ingest.breal import assemble, contract_errors, task_text, validate_raw
from embedding_lab.ingest.summre import build_meetings


def meetings():
    recs = [
        {"meeting_id": "900a_EARL", "speaker_id": "001", "official_split": "dev",
         "segments": [{"start": 0, "end": 1, "text": "je propose qu' on parte sur le mois de juin"},
                      {"start": 5, "end": 6, "text": "bon c'est validé on part sur juin"}]},
        {"meeting_id": "900a_EARL", "speaker_id": "002", "official_split": "dev",
         "segments": [{"start": 2, "end": 3, "text": "moi je m'occupe de réserver la salle"}]},
        {"meeting_id": "900b_EADL", "speaker_id": "001", "official_split": "train",
         "segments": [{"start": 0, "end": 1, "text": "finalement on décale tout en septembre"}]},
    ]
    return {m["meeting_id"]: m for m in build_meetings(recs)}


def raw():
    return {"group_id": "900", "units": [
        {"key": "a-01", "meeting_id": "900a_EARL", "turn": "t0000",
         "evidence": "je propose qu' on parte sur le mois de juin", "type": "idea",
         "status": "proposed", "statement": "Proposition : juin."},
        {"key": "a-02", "meeting_id": "900a_EARL", "turn": "t0002",
         "evidence": "c'est validé on part sur juin", "type": "decision", "status": "active",
         "statement": "Décision : juin."},
        {"key": "a-03", "meeting_id": "900a_EARL", "turn": "t0001",
         "evidence": "je m'occupe de réserver la salle", "type": "commitment",
         "status": "active", "statement": "002 réserve la salle.", "owner": "002"},
        {"key": "b-01", "meeting_id": "900b_EADL", "turn": "t0000",
         "evidence": "on décale tout en septembre", "type": "decision", "status": "active",
         "statement": "Report en septembre."}],
        "relations": [{"from": "b-01", "to": "a-02", "relation": "supersedes",
                       "justification": "report explicite"}],
        "queries": [
            {"key": "q01", "about_meeting": "900a_EARL", "text": "quel mois a été retenu",
             "answerable": True, "qrels": {"b-01": 2, "a-02": 0, "a-01": 0},
             "traps": [{"unit": "a-02", "trap": "superseded"}, {"unit": "a-01", "trap": "status"}]},
            {"key": "q02", "about_meeting": "900a_EARL", "text": "quel traiteur est choisi",
             "answerable": False, "qrels": {}}]}


def test_task_text_lists_turns_and_marks_manual_meetings():
    txt = task_text("900", list(meetings().values()))
    assert "t0001 [002] moi je m'occupe de réserver la salle" in txt
    assert txt.count("QUESTIONS À ÉCRIRE") == 1  # seule 900a est manuelle


def test_valid_raw_assembles_into_valid_contracts():
    ms = meetings()
    assert validate_raw(raw(), ms) == []
    out = assemble(raw(), ms, "val", "test-annotator")
    assert contract_errors(out, ms) == []
    assert len(out["triplets"]) == 2 and out["qrels"]["q-sr-900-q01"]["u-sr-900-b-01"] == 2
    assert all(u["annotation"]["origin"] == "llm_provisional" for u in out["units"])


def test_rejects_paraphrased_evidence_and_wrong_meeting_letter():
    bad = raw()
    bad["units"][0]["evidence"] = "je propose de partir en juin"
    bad["units"][3]["key"] = "a-09"
    errs = validate_raw(bad, meetings())
    assert any("sous-chaîne exacte" in e for e in errs)
    assert any("lettre" in e for e in errs)


def test_rejects_queries_on_asr_meetings_and_copied_evidence():
    bad = raw()
    bad["queries"][0]["about_meeting"] = "900b_EADL"
    bad["queries"][1]["text"] = "x"
    bad["queries"].append({"key": "q03", "about_meeting": "900a_EARL",
                           "text": "on décale tout en septembre ou pas", "answerable": True,
                           "qrels": {"b-01": 2}})
    errs = validate_raw(bad, meetings())
    assert any("réunion manuelle" in e for e in errs)
    assert any("recopie" in e for e in errs)
