"""Espace de travail à plusieurs projets (EL-028).

Chaque projet garde sa propre mémoire : la recherche, les comparaisons, les dossiers et la
résolution des destinataires ne mélangent donc jamais deux projets. Le projet est repéré par
son nom dans la demande ; s'il y a plusieurs projets et que la demande n'en nomme aucun, l'agent
demande lequel au lieu de choisir (sauf pour une phrase hypothétique, qui ne déclenche rien).

Les sources sont des données : un projet n'est chargé que depuis un fichier source explicite.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from embedding_lab.agent.agent import Agent, IntentModel
from embedding_lab.intents.rules import find_name
from embedding_lab.memory.store import Memory
from embedding_lab.tools import simulated


class Workspace:
    def __init__(self, memories: Mapping[str, Memory], intent_model: IntentModel,
                 reference_date: date):
        if not memories:
            raise ValueError("espace de travail vide")
        self.agents = {name: Agent(mem, intent_model, reference_date)
                       for name, mem in memories.items()}
        self.intents, self.ref = intent_model, reference_date

    @classmethod
    def from_sources(cls, paths: Sequence[Path], encoder: Any, intent_model: IntentModel,
                     reference_date: date) -> Workspace:
        memories: dict[str, Memory] = {}
        for p in paths:
            mem = Memory.from_source(Path(p), encoder=encoder)
            projects = mem.projects()
            if len(projects) != 1:
                raise ValueError(f"{p} : un fichier source doit décrire un seul projet")
            if projects[0] in memories:
                raise ValueError(f"projet en double : {projects[0]}")
            memories[projects[0]] = mem
        return cls(memories, intent_model, reference_date)

    @property
    def projects(self) -> list[str]:
        return sorted(self.agents)

    def summary(self) -> str:
        parts = [f"{p} : {len(a.memory.units)} unités, {len(a.memory.relations)} liens, "
                 f"{len(a.memory.meetings)} réunions" for p, a in sorted(self.agents.items())]
        return " | ".join(parts)

    def handle(self, request: str) -> dict[str, Any]:
        project = find_name(request, self.agents)
        if project is None and len(self.agents) == 1:
            project = next(iter(self.agents))
        if project is not None:
            out = self.agents[project].handle(request)
            return {**out, "routed_project": project}
        first = next(iter(self.agents.values()))
        analysis = first.analyse(request)
        if analysis["intent"] == "no_action":
            return {**first.handle(request), "routed_project": None}
        names = ", ".join(self.projects)
        question = f"Sur quel projet porte la demande ({names}) ?"
        return {"request": request, "reference_date": self.ref.isoformat(),
                "analysis": analysis, "operation": "clarify", "routed_project": None,
                "action": simulated.clarify("insufficient_context", question, [],
                                            self.ref.isoformat()),
                "explanation": "plusieurs projets sont chargés et la demande n'en nomme aucun ; "
                               "aucune recherche n'a été faite pour ne pas mélanger les sources"}
