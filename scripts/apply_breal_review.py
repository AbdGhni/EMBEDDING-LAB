"""EL-007b — applique les corrections des relectures (IA ou humaine) aux annotations brutes.

Règle d'arbitrage (orchestrateur) : on applique les verdicts « erreur » qui portent une
correction explicite et vérifiable (statut ou type valide, extrait copié exactement du tour,
pertinence suggérée) et les unités manquantes ; les verdicts « douteux » ne changent rien.
Chaque modification est consignée dans annotations/breal/review/<source>/adjudication.json.

Usage : uv run python -I scripts/apply_breal_review.py --source ia
"""

import argparse
import json
from pathlib import Path

from embedding_lab.ingest.breal import load_meetings, validate_raw

TYPES = {"decision", "action", "commitment", "question", "answer", "fact", "risk", "idea"}
STATUSES = {"proposed", "conditional", "active", "rejected", "cancelled", "open", "resolved",
            "unknown"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="ia")
    args = ap.parse_args()
    meetings = load_meetings(Path("data/processed/summre_meetings.jsonl"))
    log = []
    for rev_path in sorted(Path(f"annotations/breal/review/{args.source}").glob("*_*.json")):
        rev = json.loads(rev_path.read_text(encoding="utf-8"))
        mid = rev["meeting_id"]
        group = mid.split("_")[0][:-1]
        raw_path = Path(f"annotations/breal/raw/{group}.json")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        units = {u["key"]: u for u in raw["units"]}
        queries = {q["key"]: q for q in raw["queries"]}
        turns = {t["turn_id"].split(":")[1]: t["text"] for t in meetings[mid]["turns"]}

        def note(kind, key, before, after, why, applied=True, mid=mid):
            log.append({"meeting": mid, "kind": kind, "key": key, "before": before,
                        "after": after, "reason": why, "applied": applied})

        for x in rev["units"]:
            if x["verdict"] != "erreur":
                continue
            u, field, corr = units[x["key"]], x.get("field"), x.get("correction")
            ok = ((field == "status" and corr in STATUSES)
                  or (field == "type" and corr in TYPES)
                  or (field == "evidence" and isinstance(corr, str) and len(corr.split()) >= 3
                      and corr in turns[u["turn"]]))
            before = u.get(field) if field != "evidence" else u["evidence"]
            if ok:
                u[field] = corr
            note(f"unit.{field}", x["key"], before, corr, x.get("comment", ""), ok)
        for j in rev["query_judgments"]:
            if j["verdict"] != "erreur" or j.get("suggested_rel") not in (0, 1, 2):
                continue
            q = queries[j["query"]]
            before = q["qrels"].get(j["unit"])
            q["qrels"][j["unit"]] = j["suggested_rel"]
            if j["suggested_rel"] > 0:
                q["traps"] = [t for t in q.get("traps", []) if t["unit"] != j["unit"]]
            note("qrel", f"{j['query']}/{j['unit']}", before, j["suggested_rel"],
                 j.get("comment", ""))
        for m in rev.get("missing", []):
            q = queries[m["query"]]
            before = q["qrels"].get(m["unit"])
            q["qrels"][m["unit"]] = m["suggested_rel"]
            q["traps"] = [t for t in q.get("traps", []) if t["unit"] != m["unit"]]
            note("qrel.missing", f"{m['query']}/{m['unit']}", before, m["suggested_rel"],
                 m.get("comment", ""))
        for qk, q in list(queries.items()):
            if q.get("answerable", True) and not any(v == 2 for v in q["qrels"].values()):
                # plus aucune réponse directe après relecture : question invalide, retirée
                raw["queries"] = [x for x in raw["queries"] if x["key"] != qk]
                note("query.removed", qk, q["text"], None,
                     "aucune unité de pertinence 2 après relecture (question non tranchable)")
        group_meetings = {k: v for k, v in meetings.items() if v["group_id"] == group}
        errs = validate_raw(raw, group_meetings)
        if errs:
            raise SystemExit(f"{group} invalide après corrections : {errs[:5]}")
        raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    out = Path(f"annotations/breal/review/{args.source}/adjudication.json")
    out.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{sum(e['applied'] for e in log)} corrections appliquées, "
          f"{sum(not e['applied'] for e in log)} refusées (non vérifiables)")
    for e in log:
        if not e["applied"]:
            print("refusée :", e["meeting"], e["key"], e["kind"])


if __name__ == "__main__":
    main()
