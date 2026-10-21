"""Générateur B-SYN : projets fictifs à trois réunions, pièges étiquetés par construction.

Pour chaque projet, trois « objets » suivent un scénario tiré au sort :

- budget : S1 proposé → validé ; S2 proposé → accord conditionnel → validé ;
  S3 proposé → validé → révisé (supersedes) ; S4 proposé → rejeté → autre montant validé ;
  S5 proposé → validé → annulé (supersedes) ;
- date de lancement : T1 proposée → confirmée ; T2 confirmée → reportée (supersedes) ;
  T3 proposée → exclue → autre date confirmée ; T4 confirmée → date contradictoire non résolue
  (contradicts) ;
- dossier : O1 question → engagement (answers) ; O2 demande à B sans réponse → engagement de C ;
  O3 engagement de A → réattribution à C (supersedes).

Les requêtes, leurs pertinences (0/1/2) et les triplets (requête, positif, piège, type de piège)
découlent du scénario : **aucun modèle n'intervient** dans le choix des pièges (protocole v1.1).

Exemple ::

    >>> data = generate_split("val", n_projects=2, seed=1)
    >>> sorted(data) == ['meetings', 'qrels', 'queries', 'relations', 'triplets', 'units']
    True
    >>> all(u["annotation"]["origin"] == "synthetic_generator" for u in data["units"])
    True
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from embedding_lab.synth.templates import (
    FILLERS,
    PEOPLE,
    PROJECT_WORDS,
    QUERIES,
    QUERY_FAMILIES_BY_SPLIT,
    RESERVED_PROJECTS,
    UNIT_FAMILIES_BY_SPLIT,
    UNITS,
)

SPLIT_YEAR = {"train": 2024, "val": 2025, "test": 2026}
SPLIT_AMOUNT_RESIDUE = {"train": 0, "val": 1, "test": 2}  # milliers ≡ r (mod 3)
MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
WEEKDAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

UNIT_META = {
    # kind: (type, status, objet)
    "b_prop": ("idea", "proposed", "budget"),
    "b_cond": ("decision", "conditional", "budget"),
    "b_valid": ("decision", "active", "budget"),
    "b_reject": ("decision", "rejected", "budget"),
    "b_new": ("decision", "active", "budget"),
    "b_cancel": ("decision", "cancelled", "budget"),
    "b_mention": ("risk", "open", "budget"),
    "d_prop": ("idea", "proposed", "launch"),
    "d_valid": ("decision", "active", "launch"),
    "d_postpone": ("decision", "active", "launch"),
    "d_neg": ("decision", "rejected", "launch"),
    "d_conflict": ("fact", "unknown", "launch"),
    "o_question": ("question", "open", "dossier"),
    "o_request": ("action", "open", "dossier"),
    "o_commit": ("commitment", "active", "dossier"),
    "o_reassign": ("commitment", "active", "dossier"),
}


def project_names(split: str) -> list[str]:
    names = [f"{w} {s}" for w in PROJECT_WORDS[split] for s in PROJECT_WORDS[f"{split}_suffix"]]
    assert not RESERVED_PROJECTS & set(names)
    return names


def fmt_amount(thousands: int, family: int) -> str:
    n = f"{thousands * 1000:,}".replace(",", " ")
    return (f"{n} euros", f"{thousands}k", f"{thousands} k€", f"{n} €")[family]


def fmt_date(d: date, family: int) -> str:
    base = f"{d.day} {MONTHS[d.month - 1]}"
    return f"{WEEKDAYS[d.weekday()]} {base}" if family == 3 else base


class _Project:
    def __init__(self, split: str, idx: int, name: str, rng: random.Random):
        self.split, self.idx, self.name, self.rng = split, idx, name, rng
        self.pid = f"bs-{split}-{idx:03d}"
        self.people = rng.sample(PEOPLE[split], 4)
        a, b, c, _ = self.people
        self.A, self.B, self.C = a, b, c
        y = SPLIT_YEAR[split]
        m1 = date(y, 1, 1) + timedelta(days=rng.randrange(0, 250))
        m2 = m1 + timedelta(days=rng.randrange(7, 15))
        m3 = m2 + timedelta(days=rng.randrange(7, 15))
        self.mdates = (m1, m2, m3)
        self.D1 = m3 + timedelta(days=rng.randrange(20, 60))
        self.D2 = self.D1 + timedelta(days=rng.randrange(14, 45))
        self.D3 = self.D1 + timedelta(days=rng.choice((-9, -5, 3, 6, 11)))
        self.DUE = m2 + timedelta(days=rng.randrange(5, 20))
        r = SPLIT_AMOUNT_RESIDUE[split]
        pool = [k for k in range(12, 300) if k % 3 == r]
        self.X, self.Y = rng.sample(pool, 2)
        self.story = {"budget": rng.choice(["S1", "S2", "S3", "S4", "S5"]),
                      "launch": rng.choice(["T1", "T2", "T3", "T4"]),
                      "dossier": rng.choice(["O1", "O2", "O3"])}
        self.items: list[tuple[int, str, str, dict]] = []  # (réunion, kind, locuteur, extras)

    def plan(self) -> None:
        add = self.items.append
        A, B, C = self.A, self.B, self.C
        rng = self.rng
        anyone = lambda: rng.choice(self.people)  # noqa: E731
        s = self.story["budget"]
        add((0, "b_prop", A, {"amount": "X"}))
        if rng.random() < 0.6:
            add((rng.choice((0, 1)), "b_mention", anyone(), {}))
        if s == "S1":
            add((1, "b_valid", B, {"amount": "X"}))
        elif s == "S2":
            add((1, "b_cond", B, {"amount": "X"}))
            add((2, "b_valid", C, {"amount": "X"}))
        elif s == "S3":
            add((1, "b_valid", B, {"amount": "X"}))
            add((2, "b_new", C, {"amount": "Y"}))
        elif s == "S4":
            add((1, "b_reject", B, {"amount": "X"}))
            add((2, "b_valid", C, {"amount": "Y"}))
        else:
            add((1, "b_valid", B, {"amount": "X"}))
            add((2, "b_cancel", C, {}))
        t = self.story["launch"]
        if t == "T1":
            add((0, "d_prop", anyone(), {"date": "D1"}))
            add((1, "d_valid", anyone(), {"date": "D1"}))
        elif t == "T2":
            add((0, "d_prop", anyone(), {"date": "D1"}))
            add((1, "d_valid", anyone(), {"date": "D1"}))
            add((2, "d_postpone", anyone(), {"date": "D2"}))
        elif t == "T3":
            add((0, "d_prop", anyone(), {"date": "D1"}))
            add((1, "d_neg", anyone(), {"date": "D1"}))
            add((2, "d_valid", anyone(), {"date": "D2"}))
        else:
            add((1, "d_valid", anyone(), {"date": "D1"}))
            add((2, "d_conflict", anyone(), {"date": "D3"}))
        o = self.story["dossier"]
        if o == "O1":
            add((0, "o_question", B, {}))
            add((1, "o_commit", A, {"owner": A}))
        elif o == "O2":
            add((0, "o_request", A, {"mentioned": [B]}))
            add((1, "o_commit", C, {"owner": C}))
        else:
            add((0, "o_commit", A, {"owner": A}))
            add((2, "o_reassign", B, {"owner": C, "mentioned": [A]}))


def _render(kind: str, family: int, p: _Project, extras: dict) -> tuple[str, dict]:
    vals = {"P": p.name, "A": p.A, "B": p.B, "C": p.C,
            "X": fmt_amount(p.X, family), "Y": fmt_amount(p.Y, family),
            "D1": fmt_date(p.D1, family), "D2": fmt_date(p.D2, family),
            "D3": fmt_date(p.D3, family), "DUE": fmt_date(p.DUE, family)}
    # un même patron sert à plusieurs étapes : « validé » porte {X} ou {D1} dans le texte,
    # mais la valeur réelle peut être Y (S4) ou D2 (T3).
    if extras.get("amount") == "Y" and "{Y}" not in UNITS[kind][family]:
        vals["X"] = vals["Y"]
    if extras.get("date") == "D2" and "{D2}" not in UNITS[kind][family]:
        vals["D1"] = vals["D2"]
    text = UNITS[kind][family].format(**vals)
    meta: dict[str, Any] = {}
    if "amount" in extras:
        meta["amount"] = vals[extras["amount"]]
    if "date" in extras:
        meta["event_date"] = getattr(p, extras["date"]).isoformat()
    if kind == "o_commit":
        meta["due_date"] = p.DUE.isoformat()
    meta["owner"] = extras.get("owner")
    meta["mentioned_people"] = extras.get("mentioned", [])
    return text, meta


def _build_project(p: _Project) -> dict[str, list]:
    rng = p.rng
    fams = UNIT_FAMILIES_BY_SPLIT[p.split]
    p.plan()
    meetings, units, by_kind = [], [], {}
    for k in range(3):
        sid = f"{p.pid}-m{k + 1}"
        title = f"Point projet {p.name}"
        filler_fam = FILLERS[rng.choice(fams)]
        lines: list[tuple[str, str, dict | None]] = []
        for _ in range(rng.randrange(2, 5)):
            lines.append((rng.choice(p.people), rng.choice(filler_fam), None))
        for _, kind, spk, extras in [it for it in p.items if it[0] == k]:
            fam = rng.choice(fams)
            text, meta = _render(kind, fam, p, extras)
            lines.insert(rng.randrange(1, len(lines) + 1),
                         (spk, text, {"kind": kind, "family": fam, **meta}))
        parts, pos = [], 0
        for spk, text, info in lines:
            prefix = f"{spk}: "
            start = pos + len(prefix)
            parts.append(prefix + text + "\n")
            pos += len(prefix) + len(text) + 1
            if info is None:
                continue
            kind = info["kind"]
            utype, status, obj = UNIT_META[kind]
            uid = f"u-{p.pid}-{len(units):02d}"
            unit = {
                "unit_id": uid, "source_id": sid, "source_date": p.mdates[k].isoformat(),
                "source_order": k, "project": p.name, "type": utype, "statement": text,
                "status": status, "assertion": "extracted", "speaker": spk,
                "owner": info["owner"], "mentioned_people": info["mentioned_people"],
                "due_date": info.get("due_date"), "event_date": info.get("event_date"),
                "amount": info.get("amount"),
                "evidence": {"text": text, "char_start": start, "char_end": start + len(text)},
                "retrieval_text": f"{title} — {spk} : {text}",
                "annotation": {"origin": "synthetic_generator", "annotator": "make_bsyn",
                               "reviewed": False,
                               "notes": f"kind={kind};family={info['family']};object={obj}"},
            }
            units.append(unit)
            by_kind.setdefault(kind, []).append(uid)
        meetings.append({"meeting_id": sid, "title": title, "project_id": p.pid,
                         "project": p.name,
                         "split": p.split, "source_date": p.mdates[k].isoformat(),
                         "source_order": k, "speakers": sorted({s for s, _, _ in lines}),
                         "text": "".join(parts)})
    return {"meetings": meetings, "units": units, "by_kind": by_kind}


def _relations(p: _Project, by: dict[str, list[str]], source_of: dict[str, str]) -> list[dict]:
    rels = []

    def rel(src: str, dst: str, r: str, why: str) -> None:
        frm = by[src][-1]
        rels.append({"from_id": frm, "to_id": by[dst][0], "relation": r,
                     "evidence_source_id": source_of[frm],
                     "justification": why, "origin": "synthetic_generator"})

    s, t, o = p.story["budget"], p.story["launch"], p.story["dossier"]
    if s == "S3":
        rel("b_new", "b_valid", "supersedes", "même projet, budget révisé explicitement")
    if s == "S5":
        rel("b_cancel", "b_valid", "supersedes", "même projet, budget annulé après validation")
    if t == "T2":
        rel("d_postpone", "d_valid", "supersedes", "même projet, report explicite du lancement")
    if t == "T4":
        rel("d_conflict", "d_valid", "contradicts", "date différente sans décision de report")
    if o == "O1":
        rel("o_commit", "o_question", "answers", "engagement qui répond à la question posée")
    if o == "O3":
        rel("o_reassign", "o_commit", "supersedes", "réattribution explicite du dossier")
    frm = by["b_prop"][0]
    rels.append({"from_id": frm, "to_id": by["o_commit"][0], "relation": "unrelated",
                 "evidence_source_id": source_of[frm], "justification": "objets différents",
                 "origin": "synthetic_generator"})
    return rels


def _queries(p: _Project, by: dict[str, list[str]], other_b_valid: str | None,
             rng: random.Random) -> tuple[list[dict], dict, list[dict]]:
    fams = QUERY_FAMILIES_BY_SPLIT[p.split]
    queries, qrels, triplets = [], {}, []
    s, t, o = p.story["budget"], p.story["launch"], p.story["dossier"]
    u = lambda k, i=0: by[k][i]  # noqa: E731

    def emit(qtype: str, fam: int, rel: dict[str, int], traps: list[tuple[str, str]],
             answerable: bool = True) -> None:
        qid = f"q-{p.pid}-{len(queries):02d}"
        queries.append({"query_id": qid, "project_id": p.pid, "cluster": p.pid,
                        "split": p.split, "type": qtype, "family": fam,
                        "text": QUERIES[qtype][fam].format(P=p.name), "answerable": answerable})
        if answerable:
            qrels[qid] = rel
            pos = [k for k, v in rel.items() if v == 2]
            for neg, trap in traps:
                assert rel.get(neg, 0) == 0
                triplets.extend({"query_id": qid, "pos": x, "neg": neg, "trap": trap} for x in pos)

    def budget_current() -> tuple[dict, list]:
        traps = [(u("b_prop"), "status")]
        if s == "S1":
            pos = u("b_valid")
        elif s == "S2":
            pos = u("b_valid")
            traps.append((u("b_cond"), "condition"))
        elif s == "S3":
            pos = u("b_new")
            traps.append((u("b_valid"), "superseded"))
        elif s == "S4":
            pos = u("b_valid")
            traps.append((u("b_reject"), "negation"))
        else:
            pos = u("b_cancel")
            traps.append((u("b_valid"), "superseded"))
        if "b_mention" in by:
            traps.append((u("b_mention"), "topic_only"))
        if other_b_valid:
            traps.append((other_b_valid, "topic_only"))
        return {pos: 2, **{n: 0 for n, _ in traps}}, traps

    def date_current() -> tuple[dict, list]:
        traps, rel = [], {}
        if t == "T1":
            rel[u("d_valid")] = 2
            traps.append((u("d_prop"), "status"))
        elif t == "T2":
            rel[u("d_postpone")] = 2
            traps += [(u("d_valid"), "superseded"), (u("d_prop"), "status")]
        elif t == "T3":
            rel[u("d_valid")] = 2
            traps += [(u("d_neg"), "negation"), (u("d_prop"), "status")]
        else:
            rel[u("d_valid")] = 2
            rel[u("d_conflict")] = 1  # conflit non résolu : à signaler, pas un piège
        return {**rel, **{n: 0 for n, _ in traps}}, traps

    def owner_current() -> tuple[dict, list]:
        if o == "O1":
            return ({u("o_commit"): 2, u("o_question"): 0}, [(u("o_question"), "topic_only")])
        if o == "O2":
            return ({u("o_commit"): 2, u("o_request"): 0}, [(u("o_request"), "person")])
        return ({u("o_reassign"): 2, u("o_commit"): 0}, [(u("o_commit"), "superseded")])

    def deadline() -> tuple[dict, list]:
        rel = {u("o_commit"): 2}
        if o == "O3":
            rel[u("o_reassign")] = 1
        date_unit = by.get("d_valid", by.get("d_postpone"))[0]
        traps = [(date_unit, "date")]
        if o == "O1":
            traps.append((u("o_question"), "topic_only"))
        if o == "O2":
            traps.append((u("o_request"), "person"))
        return {**rel, **{n: 0 for n, _ in traps}}, traps

    def budget_history() -> tuple[dict, list]:
        rel = {}
        for k in ("b_valid", "b_new", "b_cancel", "b_reject"):
            for x in by.get(k, []):
                rel[x] = 2
        for k in ("b_prop", "b_cond", "b_mention"):
            for x in by.get(k, []):
                rel[x] = 1
        return rel, []

    builders = {"q_budget_current": budget_current, "q_date_current": date_current,
                "q_owner_current": owner_current, "q_deadline": deadline,
                "q_budget_history": budget_history}
    for qtype, build in builders.items():
        chosen = [rng.choice(fams)]
        if len(fams) > 1 and qtype in ("q_budget_current", "q_date_current", "q_owner_current"):
            chosen = list(fams)
        for fam in chosen:
            rel, traps = build()
            emit(qtype, fam, rel, traps)
    if rng.random() < 0.5:
        emit("q_unanswerable", rng.choice(fams), {}, [], answerable=False)
    return queries, qrels, triplets


def generate_split(split: str, n_projects: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    names = project_names(split)
    if n_projects > len(names):
        raise ValueError(f"{split} : {n_projects} projets demandés, {len(names)} noms disponibles")
    names = rng.sample(names, n_projects)
    out: dict[str, Any] = {k: [] for k in ("meetings", "units", "relations", "queries",
                                           "triplets")}
    out["qrels"] = {}
    built = []
    for i, name in enumerate(names):
        p = _Project(split, i, name, random.Random(rng.random()))
        b = _build_project(p)
        built.append((p, b))
        out["meetings"] += b["meetings"]
        out["units"] += b["units"]
        source_of = {u["unit_id"]: u["source_id"] for u in b["units"]}
        out["relations"] += _relations(p, b["by_kind"], source_of)
    for i, (p, b) in enumerate(built):
        others = [bb["by_kind"]["b_valid"][0] for j, (_, bb) in enumerate(built)
                  if j != i and "b_valid" in bb["by_kind"]]
        other = p.rng.choice(others) if others else None
        q, qr, tr = _queries(p, b["by_kind"], other, p.rng)
        out["queries"] += q
        out["qrels"].update(qr)
        out["triplets"] += tr
    return out
