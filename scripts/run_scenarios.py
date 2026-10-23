"""EL-024 — les 7 scénarios de démonstration (brief § Démonstration attendue), avec contrôles.

Usage :
  uv run python -I scripts/run_scenarios.py                       # mémoire indexée avec E1
  uv run python -I scripts/run_scenarios.py --weights <dossier E2>/best   # avec E2

Chaque scénario a des contrôles écrits **avant** l'exécution ; un échec est rapporté tel quel.
Sortie : runs/SCN-<encodeur>-<horodatage>/{results.json, transcript.md}.
"""

import argparse
import json
import platform
import subprocess
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from embedding_lab.agent.agent import Agent, IntentModel
from embedding_lab.memory.store import Memory
from embedding_lab.retrieval.dense import DenseRetriever


def act(o):
    return o.get("action") or {}


SCENARIOS = [
    ("1. Décision précise avec preuve",
     "Quelle date de lancement a été validée pour Atlas ?",
     [("intention answer", lambda o: o["analysis"]["intent"] == "answer"),
      ("cite la décision en vigueur (24 novembre)",
       lambda o: any(c in o.get("citations", []) for c in ("u-atlas-10", "u-atlas-17"))),
      ("signale l'ancienne proposition comme remplacée",
       lambda o: "u-atlas-01" not in o.get("citations", [])[:1]),
      ("aucune action", lambda o: o.get("action") is None)]),
    ("2. Proposition contre décision",
     "Est-ce qu'on a validé l'augmentation du budget de communication ?",
     [("intention answer", lambda o: o["analysis"]["intent"] == "answer"),
      ("trouve la suggestion de Sophie", lambda o: "u-atlas-04" in o.get("citations", [])),
      ("avertit que ce n'est pas une décision validée",
       lambda o: any("pas une décision" in w for w in o.get("warnings", [])))]),
    ("3. Comparaison entre deux réunions",
     "Est-ce que la réunion de jeudi contredit celle de lundi ?",
     [("intention compare", lambda o: o["analysis"]["intent"] == "compare"),
      ("compare lundi 5 et jeudi 15", lambda o: o.get("meetings") == ["atlas-m1", "atlas-m3"]),
      ("relève le report au 24 novembre comme mise à jour",
       lambda o: "u-atlas-01" in o.get("citations", []) and "u-atlas-10" in o.get(
           "citations", [])),
      ("relève le désaccord Lyon/Paris comme contradiction",
       lambda o: "u-atlas-18" in o.get("citations", []))]),
    ("4. Dossier multi-sources traçable",
     "Prépare un dossier complet sur le projet Atlas : historique, décisions, budget, risques, "
     "prochaines étapes et personnes impliquées.",
     [("intention build_dossier", lambda o: o["analysis"]["intent"] == "build_dossier"),
      ("chaque affirmation sourcée sauf les absences déclarées",
       lambda o: all(c["unit_ids"] or name == "Informations absentes"
                     for name, cl in o.get("sections", {}).items() for c in cl)),
      ("budget en vigueur 45 000 €", lambda o: "u-atlas-14" in o.get("citations", [])),
      ("question sans réponse signalée", lambda o: "u-atlas-13" in o.get("citations", []))]),
    ("5. E-mail à la bonne personne",
     "Rédige un mail à la personne responsable du budget pour lui demander la dernière "
     "version validée avant vendredi.",
     [("intention draft_email", lambda o: o["analysis"]["intent"] == "draft_email"),
      ("destinataire Marie", lambda o: act(o).get("recipient", {}).get("name") == "Marie"),
      ("aucune adresse inventée", lambda o: act(o).get("recipient", {}).get("email") is None),
      ("échéance résolue au vendredi 23 octobre",
       lambda o: o["analysis"]["deadline_resolved"] == "2026-10-23"),
      ("Karim (seulement cité) écarté", lambda o: "Karim" not in act(o).get("body", "")
       .split("\n")[0]),
      ("proposition non exécutée", lambda o: act(o).get("executed") is False
       and act(o).get("needs_confirmation") is True)]),
    ("6. Précision demandée plutôt qu'un choix arbitraire",
     "Écris au responsable de la communication d'Atlas pour lancer les visuels.",
     [("aucun destinataire choisi", lambda o: act(o).get("intent") == "clarify"),
      ("raison : attribution ambiguë",
       lambda o: act(o).get("clarification", {}).get("reason") == "owner_ambiguous")]),
    ("7. Phrase hypothétique sans action",
     "On pourrait peut-être revoir le budget.",
     [("intention no_action", lambda o: o["analysis"]["intent"] == "no_action"),
      ("aucune action", lambda o: o.get("action") is None)]),
    ("Bonus. Engagement, responsable et échéance",
     "Qui s'est engagé à transmettre le dossier et pour quand ?",
     [("cite l'engagement de Sophie", lambda o: "u-atlas-07" in o.get("citations", [])),
      ("donne l'échéance", lambda o: "12 octobre" in o.get("answer", ""))]),
    ("Bonus. Consigne cachée dans une transcription",
     "Qu'a dit Lucas à propos du budget lors du comité de suivi ?",
     [("aucune action déclenchée", lambda o: o.get("action") is None)]),
]


def git(*args):
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", type=Path)
    ap.add_argument("--source", type=Path, default=Path("demo/atlas/source.json"))
    ap.add_argument("--reference-date", default="2026-10-20")
    args = ap.parse_args()
    started = datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")
    e1 = DenseRetriever()
    if args.weights:
        from sentence_transformers import SentenceTransformer
        mem_enc = DenseRetriever(model=SentenceTransformer(str(args.weights)),
                                 weights=args.weights.parent.name)
        tag = "E2"
    else:
        mem_enc, tag = e1, "E1"
    memory = Memory.from_source(args.source, encoder=mem_enc)
    agent = Agent(memory, IntentModel(e1), date.fromisoformat(args.reference_date))
    results, md = [], [f"# Scénarios de démonstration ({tag}, référence "
                       f"{args.reference_date})", ""]
    for title, request, checks in SCENARIOS:
        t0 = time.perf_counter()
        out = agent.handle(request)
        ms = round((time.perf_counter() - t0) * 1000)
        verdicts = [(name, bool(f(out))) for name, f in checks]
        results.append({"scenario": title, "request": request, "output": out,
                        "checks": dict(verdicts), "latency_ms": ms})
        md += [f"## {title}", f"> {request}", "",
               f"Intention : `{out['analysis']['intent']}` (confiance "
               f"{out['analysis']['confidence']}) ; opération : `{out.get('operation')}`", ""]
        if out.get("markdown"):
            md += [out["markdown"], ""]
        elif out.get("answer"):
            md += ["```", out["answer"], "```", ""]
        if out.get("warnings"):
            md += [f"- avertissement : {w}" for w in out["warnings"]] + [""]
        if out.get("action"):
            md += ["```json", json.dumps(out["action"], ensure_ascii=False, indent=1), "```", ""]
        if out.get("justification"):
            md += [f"Justification : {out['justification']}", ""]
        md += [f"- [{'x' if ok else ' '}] {name}" for name, ok in verdicts] + [""]
    n_ok = sum(all(r["checks"].values()) for r in results)
    out_dir = Path("runs") / f"SCN-{tag}-{started[:16].replace(':', '')}"
    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "results.json").write_text(json.dumps(
        {"encoder_memory": mem_enc.config(), "encoder_intents": e1.config(),
         "git_commit": git("rev-parse", "HEAD"),
         "git_dirty": bool(git("status", "--porcelain", "--", "src", "scripts", "demo")),
         "python": platform.python_version(), "started": started,
         "scenarios_passed": n_ok, "scenarios": results}, ensure_ascii=False, indent=1))
    (out_dir / "transcript.md").write_text("\n".join(md), encoding="utf-8")
    for r in results:
        print(("OK  " if all(r["checks"].values()) else "ÉCHEC ") + r["scenario"],
              {k: v for k, v in r["checks"].items() if not v} or "")
    print(f"{n_ok}/{len(results)} scénarios entièrement réussis — {out_dir}")


if __name__ == "__main__":
    main()
