"""Vérifie qu'une relecture IA couvre toutes les unités et tous les couples (question, unité).

Usage : python -I scripts/check_breal_review.py annotations/breal/review/ia/<meeting_id>.json
"""

import json
import sys
from pathlib import Path

VERDICTS = {"ok", "erreur", "douteux"}
QUALITY = {"ok", "ambiguë", "mal formulée", "recopie la preuve", "non répondable"}

rev = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
mid = rev["meeting_id"]
group = mid.split("_")[0][:-1]
raw = json.loads(Path(f"annotations/breal/raw/{group}.json").read_text(encoding="utf-8"))
keys = {u["key"] for u in raw["units"]}
mine = {u["key"] for u in raw["units"] if u["meeting_id"] == mid}
queries = [q for q in raw["queries"] if q["about_meeting"] == mid]
pairs = {(q["key"], k) for q in queries for k in q["qrels"]}
errs = []
got_units = {u["key"] for u in rev.get("units", [])}
if got_units != mine:
    errs.append(f"unités non jugées : {sorted(mine - got_units)} ; "
                f"inconnues : {sorted(got_units - mine)}")
got_pairs = {(j["query"], j["unit"]) for j in rev.get("query_judgments", [])}
if got_pairs != pairs:
    errs.append(f"couples non jugés : {sorted(pairs - got_pairs)[:10]} ; en trop : "
                f"{sorted(got_pairs - pairs)[:10]}")
for x in rev.get("units", []) + rev.get("query_judgments", []):
    if x.get("verdict") not in VERDICTS:
        errs.append(f"verdict invalide : {x}")
for m in rev.get("missing", []):
    if m.get("unit") not in keys or m.get("suggested_rel") not in (1, 2):
        errs.append(f"unité manquante invalide : {m}")
qk = {q["key"] for q in queries}
if {x["query"] for x in rev.get("query_quality", [])} != qk:
    errs.append("qualité non jugée pour toutes les questions")
if any(x.get("verdict") not in QUALITY for x in rev.get("query_quality", [])):
    errs.append("verdict de qualité invalide")
print(f"{len(got_units)} unités, {len(got_pairs)} couples, {len(rev.get('missing', []))} manques")
print("OK" if not errs else "\n".join(errs))
sys.exit(1 if errs else 0)
