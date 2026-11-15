"""EL-029 : jeux post hoc d'intentions (validité et absence de recouvrement)."""

import json
from pathlib import Path

import numpy as np

from embedding_lab.agent.agent import POST_TRAIN, IntentModel
from embedding_lab.intents.data import INTENTS

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "annotations" / "intents" / "post_control_v1.jsonl"


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def texts(path):
    return {r["text"].strip().lower() for r in rows(path)}


def test_post_hoc_files_are_valid_and_labelled():
    for path in (ROOT / POST_TRAIN, CONTROL):
        data = rows(path)
        assert all(r["intent"] in INTENTS for r in data)
        assert all(r["origin"] == "claude_written_post_hoc" for r in data)
        assert len({r["id"] for r in data}) == len(data)


def test_control_has_eight_requests_per_class():
    counts = {k: 0 for k in INTENTS}
    for r in rows(CONTROL):
        counts[r["intent"]] += 1
    assert set(counts.values()) == {8}


def test_control_is_disjoint_from_every_training_and_evaluation_text():
    control = texts(CONTROL)
    others = [ROOT / POST_TRAIN, ROOT / "data/intents/train.jsonl", ROOT / "data/intents/val.jsonl",
              ROOT / "data/intents/test.jsonl", ROOT / "annotations/intents/test_manual_v1.jsonl"]
    for path in others:
        assert not control & texts(path), path.name


def test_control_does_not_reuse_demo_requests():
    demo = (ROOT / "scripts" / "run_scenarios.py").read_text(encoding="utf-8").lower()
    for text in texts(CONTROL):
        assert text not in demo


class BagEncoder:
    def __init__(self):
        self.sizes = []

    def _encode(self, queries):
        self.sizes.append(len(queries))
        out = np.zeros((len(queries), 64))
        for i, q in enumerate(queries):
            for w in q.lower().split():
                out[i, hash(w) % 64] += 1
        return out


def test_extra_training_rows_are_used():
    n_base = len(rows(ROOT / "data/intents/train.jsonl"))
    n_post = len(rows(ROOT / POST_TRAIN))
    enc_base, enc_plus = BagEncoder(), BagEncoder()
    IntentModel(enc_base)
    plus = IntentModel(enc_plus, extra_train=(ROOT / POST_TRAIN,))
    assert enc_base.sizes[0] == n_base and enc_plus.sizes[0] == n_base + n_post
    assert plus.predict("Est-ce qu'on a validé le devis ?")[0] in INTENTS
