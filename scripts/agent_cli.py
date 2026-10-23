"""Interface en ligne de commande du mini-agent (démo).

Usage :
  uv run python -I scripts/agent_cli.py                         # boucle interactive, E1
  uv run python -I scripts/agent_cli.py --weights <E2>/best     # mémoire indexée avec E2
  uv run python -I scripts/agent_cli.py -q "Qui est responsable du budget ?"
  uv run python -I scripts/agent_cli.py --source <autre source.json> --reference-date 2026-10-20

Toutes les actions sont des propositions JSON (needs_confirmation=true, executed=false).
"""

import argparse
import json
from datetime import date
from pathlib import Path

from embedding_lab.agent.agent import Agent, IntentModel
from embedding_lab.memory.store import Memory
from embedding_lab.retrieval.dense import DenseRetriever


def show(out: dict) -> None:
    a = out["analysis"]
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
    ap.add_argument("--source", type=Path, default=Path("demo/atlas/source.json"))
    ap.add_argument("--reference-date", default="2026-10-20")
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
    agent = Agent(Memory.from_source(args.source, encoder=enc), IntentModel(e1),
                  date.fromisoformat(args.reference_date))
    if args.query:
        show(agent.handle(args.query))
        return
    print(f"Mémoire : {len(agent.memory.units)} unités, {len(agent.memory.relations)} liens. "
          f"Date de référence : {args.reference_date}. Ligne vide pour quitter.")
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
