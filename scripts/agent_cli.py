"""Interface en ligne de commande du mini-agent (démo).

Usage :
  uv run python -I scripts/agent_cli.py                         # boucle interactive, E1
  uv run python -I scripts/agent_cli.py --weights <E2>/best     # mémoire indexée avec E2
  uv run python -I scripts/agent_cli.py -q "Qui est responsable du budget ?"
  uv run python -I scripts/agent_cli.py --source demo/atlas/source.json   # un seul projet
  uv run python -I scripts/agent_cli.py --source <a.json> --source <b.json>   # plusieurs projets

Par défaut, deux projets fictifs sont chargés (Atlas, Cèdre) ; nommer le projet dans la demande.

Toutes les actions sont des propositions JSON (needs_confirmation=true, executed=false).
"""

import argparse
import json
from datetime import date
from pathlib import Path

from embedding_lab.agent.agent import intent_model
from embedding_lab.agent.workspace import Workspace
from embedding_lab.retrieval.dense import DenseRetriever


def show(out: dict) -> None:
    a = out["analysis"]
    if out.get("routed_project"):
        print(f"\n[projet {out['routed_project']}]", end="")
    print(f"\n[intention {a['intent']} ({a['confidence']}) · slots {a['slots']}"
          + (f" · échéance {a['deadline_resolved']}" if a["deadline_resolved"] else "") + "]")
    if out.get("markdown"):
        print(out["markdown"])
    elif out.get("answer"):
        print(out["answer"])
    for w in out.get("warnings", []):
        print("  ! " + w)
    if out.get("explanation"):
        print("  (" + out["explanation"] + ")")
    if out.get("justification"):
        print("Justification : " + out["justification"])
    if out.get("action"):
        print(json.dumps(out["action"], ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, action="append",
                    help="fichier source d'un projet (répétable) ; défaut : Atlas et Cèdre")
    ap.add_argument("--reference-date", default="2026-10-20")
    ap.add_argument("--intents", choices=["i2", "i2plus"], default="i2plus",
                    help="i2 : modèle retenu sur la validation ; i2plus : correction post hoc (EL-029)")
    ap.add_argument("--weights", type=Path)
    ap.add_argument("-q", "--query")
    args = ap.parse_args()
    e1 = DenseRetriever()
    if args.weights:
        from sentence_transformers import SentenceTransformer
        enc = DenseRetriever(model=SentenceTransformer(str(args.weights)),
                             weights=args.weights.parent.name)
    else:
        enc = e1
        print("Mémoire indexée avec E1 (encodeur initial) : passer --weights pour E2.")
    sources = args.source or [Path("demo/atlas/source.json"), Path("demo/cedre/source.json")]
    agent = Workspace.from_sources(sources, enc, intent_model(e1, args.intents),
                                   date.fromisoformat(args.reference_date))
    if args.query:
        show(agent.handle(args.query))
        return
    print(f"Mémoire — {agent.summary()}. Date de référence : {args.reference_date}. "
          "Ligne vide pour quitter.")
    while True:
        try:
            q = input("\n> ").strip()
        except EOFError:
            break
        if not q:
            break
        show(agent.handle(q))


if __name__ == "__main__":
    main()
