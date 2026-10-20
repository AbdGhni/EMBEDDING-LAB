"""Ingestion de SUMM-RE (texte seul) et reconstruction des réunions.

SUMM-RE stocke une ligne par **piste de locuteur** : chaque piste contient ses segments
horodatés. Pour obtenir une conversation lisible, on interclasse les segments de toutes
les pistes d'une réunion par heure de début, puis on fusionne les segments consécutifs
d'un même locuteur séparés de moins de ``merge_gap`` secondes en un **tour de parole**.

Le texte canonique d'une réunion est ``"<locuteur>: <texte>\\n"`` répété pour chaque tour.
Chaque tour garde ``char_start``/``char_end`` qui pointent sur **son texte seul** dans ce
texte canonique : ``meeting["text"][t["char_start"]:t["char_end"]] == t["text"]``. Ce sont
ces offsets que les unités annotées réutiliseront comme preuve.

Exemple ::

    >>> recs = [
    ...   {"meeting_id": "004c_PAPH", "speaker_id": "B", "official_split": "dev",
    ...    "segments": [{"start": 2.0, "end": 3.0, "text": "d'accord"}]},
    ...   {"meeting_id": "004c_PAPH", "speaker_id": "A", "official_split": "dev",
    ...    "segments": [{"start": 0.0, "end": 1.0, "text": "on part sur juin"},
    ...                 {"start": 1.2, "end": 1.8, "text": "ok"}]},
    ... ]
    >>> m = build_meetings(recs)[0]
    >>> print(m["text"], end="")
    A: on part sur juin ok
    B: d'accord
    >>> [t["turn_id"] for t in m["turns"]]
    ['004c_PAPH:t0000', '004c_PAPH:t0001']
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

REPO_ID = "linagora/SUMM-RE"
REVISION = "47cb4ec3437ef5497b6092b8c6d1e0b5b1d86dc0"
OFFICIAL_SPLITS = ("dev", "test", "train")
# Transcription manuelle pour dev/test, automatique (Whisper) pour train — fiche du dataset.
TRANSCRIPTION = {"dev": "manual", "test": "manual", "train": "asr"}


def group_id(meeting_id: str) -> str:
    """'004c_PAPH' -> '004' : numéro d'expérience (trois réunions a/b/c par expérience)."""
    return meeting_id.split("_", 1)[0][:-1]


def session_letter(meeting_id: str) -> str:
    """'004c_PAPH' -> 'c' : rang de la réunion dans l'expérience."""
    return meeting_id.split("_", 1)[0][-1]


_CODES = {
    "experiment_type": {"E": "experiment", "P": "pilot"},
    "meeting_type": {"R": "reporting", "D": "decision", "P": "planning"},
    "location": {"L": "LPL", "H": "H2C2", "Z": "zoom", "D": "home"},
}


def parse_meeting_code(meeting_id: str) -> dict:
    """'004c_PAPH' -> pilote, scénario A, réunion de planification, studio H2C2 (fiche SUMM-RE)."""
    code = meeting_id.split("_", 1)[1] if "_" in meeting_id else ""
    if len(code) != 4:
        return {"experiment_type": None, "scenario": None, "meeting_type": None, "location": None}
    return {
        "experiment_type": _CODES["experiment_type"].get(code[0]),
        "scenario": code[1],
        "meeting_type": _CODES["meeting_type"].get(code[2]),
        "location": _CODES["location"].get(code[3]),
    }


def build_meetings(records: Iterable[Mapping[str, Any]], merge_gap: float = 1.0) -> list[dict]:
    """Pistes de locuteurs -> réunions avec tours de parole interclassés et offsets."""
    by_meeting: dict[str, list[tuple[float, float, str, str]]] = defaultdict(list)
    meta: dict[str, dict] = {}
    for rec in records:
        mid = rec["meeting_id"]
        meta.setdefault(mid, {"official_split": rec["official_split"], "speakers": set()})
        meta[mid]["speakers"].add(rec["speaker_id"])
        for seg in rec["segments"]:
            text = " ".join((seg.get("text") or "").split())
            if text:
                by_meeting[mid].append((seg["start"], seg["end"], rec["speaker_id"], text))

    meetings = []
    for mid in sorted(by_meeting):
        segs = sorted(by_meeting[mid], key=lambda s: (s[0], s[2]))
        turns: list[dict] = []
        for start, end, spk, text in segs:
            last = turns[-1] if turns else None
            if last and last["speaker"] == spk and start - last["end"] <= merge_gap:
                last["text"] += " " + text
                last["end"] = max(last["end"], end)
                last["n_segments"] += 1
            else:
                turns.append({"speaker": spk, "start": start, "end": end, "text": text,
                              "n_segments": 1})
        parts, pos = [], 0
        for i, t in enumerate(turns):
            prefix = f"{t['speaker']}: "
            t["turn_id"] = f"{mid}:t{i:04d}"
            t["char_start"] = pos + len(prefix)
            t["char_end"] = t["char_start"] + len(t["text"])
            line = prefix + t["text"] + "\n"
            parts.append(line)
            pos += len(line)
        split = meta[mid]["official_split"]
        meetings.append({
            "meeting_id": mid,
            "group_id": group_id(mid),
            "session": session_letter(mid),
            "source_order": "abc".index(session_letter(mid)),
            **parse_meeting_code(mid),
            "official_split": split,
            "transcription": TRANSCRIPTION[split],
            "speakers": sorted(meta[mid]["speakers"]),
            "turns": turns,
            "text": "".join(parts),
        })
    return meetings


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_tracks(out_dir: Path, revision: str = REVISION) -> dict:
    """Télécharge les seules colonnes texte (une piste par ligne JSONL). Extra ``data`` requis."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem()
    root = f"datasets/{REPO_ID}@{revision}/data"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"repo_id": REPO_ID, "revision": revision,
                                "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "files": {}}
    for split in OFFICIAL_SPLITS:
        path = out_dir / f"tracks_{split}.jsonl"
        n = 0
        with open(path, "w", encoding="utf-8") as out:
            for remote in sorted(fs.glob(f"{root}/{split}/*.parquet")):
                with fs.open(remote, "rb", block_size=1 << 20) as f:
                    table = pq.ParquetFile(f).read(columns=["meeting_id", "speaker_id", "segments"])
                for row in table.to_pylist():
                    segs = [{"start": s["start"], "end": s["end"], "text": s["transcript"]}
                            for s in row["segments"] or []]
                    out.write(json.dumps({"meeting_id": row["meeting_id"],
                                          "speaker_id": row["speaker_id"],
                                          "official_split": split, "segments": segs},
                                         ensure_ascii=False) + "\n")
                    n += 1
        manifest["files"][path.name] = {"rows": n, "sha256": sha256_file(path)}
    manifest["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
