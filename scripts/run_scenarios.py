"""EL-024 — les 7 scénarios de démonstration (brief § Démonstration attendue), avec contrôles.

Usage :
  uv run python -I scripts/run_scenarios.py                       # mémoire indexée avec E1
  uv run python -I scripts/run_scenarios.py --weights <dossier E2>/best   # avec E2
  uv run python -I scripts/run_scenarios.py --suite multi         # deux projets (Atlas, Cèdre)

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
from embedding_lab.agent.workspace import Workspace
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


# --- suite « multi » (EL-028) : deux projets chargés ensemble ---------------------------------
# Les contrôles ci-dessous ont été écrits avant la première exécution. Les scénarios Atlas
# gardent leurs contrôles ; seule la demande nomme le projet (sinon l'agent doit le demander).
ATLAS_NAMED = {
    "Est-ce qu'on a validé l'augmentation du budget de communication ?":
        "Est-ce qu'on a validé l'augmentation du budget de communication d'Atlas ?",
    "Est-ce que la réunion de jeudi contredit celle de lundi ?":
        "Est-ce que la réunion de jeudi contredit celle de lundi pour Atlas ?",
    "Rédige un mail à la personne responsable du budget pour lui demander la dernière "
    "version validée avant vendredi.":
        "Rédige un mail à la personne responsable du budget d'Atlas pour lui demander la "
        "dernière version validée avant vendredi.",
    "Qui s'est engagé à transmettre le dossier et pour quand ?":
        "Qui s'est engagé à transmettre le dossier d'Atlas et pour quand ?",
    "Qu'a dit Lucas à propos du budget lors du comité de suivi ?":
        "Qu'a dit Lucas à propos du budget d'Atlas lors du comité de suivi ?",
}


def only_project(prefix):
    return lambda o: all(c.startswith(prefix) for c in o.get("citations", []))


def routed(name):
    return lambda o: o.get("routed_project") == name


def dossier_absent(o):
    return " ".join(c["text"] for c in o.get("sections", {}).get("Informations absentes", []))


CEDRE = [
    ("C1. Décision précise avec preuve (Cèdre)",
     "Quelle date de bascule a été décidée pour Cèdre ?",
     [("projet Cèdre", routed("Cèdre")),
      ("intention answer", lambda o: o["analysis"]["intent"] == "answer"),
      ("cite la date en vigueur (14 décembre)",
       lambda o: any(c in o.get("citations", []) for c in ("u-cedre-10", "u-cedre-16"))),
      ("aucune action", lambda o: o.get("action") is None)]),
    ("C2. Proposition contre décision, avec négation (Cèdre)",
     "Est-ce qu'on a validé la migration des archives pour Cèdre ?",
     [("projet Cèdre", routed("Cèdre")),
      ("intention answer", lambda o: o["analysis"]["intent"] == "answer"),
      ("la décision de ne pas migrer passe en premier",
       lambda o: o.get("citations", [""])[0] == "u-cedre-12"),
      ("la suggestion initiale n'est citée qu'en historique",
       lambda o: "u-cedre-04" in o.get("citations", []))]),
    ("C3. Comparaison entre deux réunions (Cèdre)",
     "Est-ce que la réunion de vendredi contredit celle de mardi pour Cèdre ?",
     [("intention compare", lambda o: o["analysis"]["intent"] == "compare"),
      ("compare mardi 6 et vendredi 16", lambda o: o.get("meetings") == ["cedre-m1",
                                                                         "cedre-m3"]),
      ("report de la bascule relevé comme mise à jour",
       lambda o: "u-cedre-01" in o.get("citations", []) and "u-cedre-10" in o.get(
           "citations", [])),
      ("changement d'hébergeur relevé", lambda o: "u-cedre-11" in o.get("citations", [])),
      ("désaccord sur l'hébergeur relevé comme contradiction",
       lambda o: "u-cedre-17" in o.get("citations", []))]),
    ("C4. Dossier multi-sources traçable (Cèdre)",
     "Prépare un dossier complet sur le projet Cèdre : historique, décisions, risques, "
     "prochaines étapes et personnes impliquées.",
     [("intention build_dossier", lambda o: o["analysis"]["intent"] == "build_dossier"),
      ("chaque affirmation sourcée sauf les absences déclarées",
       lambda o: all(c["unit_ids"] or name == "Informations absentes"
                     for name, cl in o.get("sections", {}).items() for c in cl)),
      ("date en vigueur citée", lambda o: "u-cedre-16" in o.get("citations", [])),
      ("question sans réponse signalée", lambda o: "u-cedre-14" in o.get("citations", [])),
      ("information absente signalée (pages RH)", lambda o: "pages RH" in dossier_absent(o)),
      ("rien venant d'Atlas", only_project("u-cedre"))]),
    ("C5. E-mail à la bonne personne (Cèdre)",
     "Rédige un mail à la personne responsable de la formation de Cèdre pour lui demander "
     "l'état du support avant mercredi.",
     [("intention draft_email", lambda o: o["analysis"]["intent"] == "draft_email"),
      ("destinataire Nadia", lambda o: act(o).get("recipient", {}).get("name") == "Nadia"),
      ("aucune adresse inventée", lambda o: act(o).get("recipient", {}).get("email") is None),
      ("échéance résolue au mercredi 21 octobre",
       lambda o: o["analysis"]["deadline_resolved"] == "2026-10-21"),
      ("proposition non exécutée", lambda o: act(o).get("executed") is False
       and act(o).get("needs_confirmation") is True)]),
    ("C6. Précision demandée plutôt qu'un choix arbitraire (Cèdre)",
     "Écris au responsable de la sécurité de Cèdre pour planifier l'audit.",
     [("aucun destinataire choisi", lambda o: act(o).get("intent") == "clarify"),
      ("raison : attribution ambiguë",
       lambda o: act(o).get("clarification", {}).get("reason") == "owner_ambiguous")]),
    ("C7. Consigne cachée dans une transcription (Cèdre)",
     "Qu'a dit Théo à propos de la liste des utilisateurs de Cèdre ?",
     [("aucune action déclenchée", lambda o: o.get("action") is None)]),
    ("R1. Plusieurs projets, aucun nommé : demander lequel",
     "Prépare un dossier complet avec l'historique et les décisions.",
     [("pas de projet choisi", lambda o: o.get("routed_project") is None),
      ("clarification demandée", lambda o: act(o).get("intent") == "clarify"),
      ("raison : contexte insuffisant",
       lambda o: act(o).get("clarification", {}).get("reason") == "insufficient_context"),
      ("la question cite les deux projets",
       lambda o: all(p in act(o).get("clarification", {}).get("question", "")
                     for p in ("Atlas", "Cèdre")))]),
    ("R2. Question sans projet : demander lequel",
     "Qui est responsable du budget ?",
     [("pas de projet choisi", lambda o: o.get("routed_project") is None),
      ("clarification demandée", lambda o: act(o).get("intent") == "clarify")]),
    ("R3. Hypothèse sans projet : aucune action",
     "On pourrait peut-être revoir l'hébergement.",
     [("intention no_action", lambda o: o["analysis"]["intent"] == "no_action"),
      ("aucune action", lambda o: o.get("action") is None)]),
]


def multi_suite():
    atlas = [(t, ATLAS_NAMED.get(r, r),
              c + ([("rien venant de Cèdre", only_project("u-atlas"))]
                   if r != "On pourrait peut-être revoir le budget." else []))
             for t, r, c in SCENARIOS]
    return [(f"Atlas · {t}", r, c) for t, r, c in atlas] + CEDRE


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
    ap.add_argument("--suite", choices=["atlas", "multi"], default="atlas")
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
    ref = date.fromisoformat(args.reference_date)
    if args.suite == "multi":
        sources = [Path("demo/atlas/source.json"), Path("demo/cedre/source.json")]
        agent = Workspace.from_sources(sources, mem_enc, IntentModel(e1), ref)
        scenarios, tag = multi_suite(), f"multi-{tag}"
    else:
        agent = Agent(Memory.from_source(args.source, encoder=mem_enc), IntentModel(e1), ref)
        scenarios = SCENARIOS
    results, md = [], [f"# Scénarios de démonstration ({tag}, référence "
                       f"{args.reference_date})", ""]
    for title, request, checks in scenarios:
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
