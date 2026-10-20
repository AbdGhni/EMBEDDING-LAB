# EMBEDDING LAB — De la mémoire sémantique à l'agent intelligent

Projet individuel de trois semaines (mentor référent : Martial Roberge).

Objectif : entraîner et évaluer un modèle d'embeddings spécialisé (apprentissage contrastif, hard negatives) capable de distinguer proposition, décision, annulation, responsabilité et simple mention, puis l'utiliser dans un mini-agent déterministe qui répond avec preuves, construit des dossiers sourcés et prépare des actions **uniquement simulées** (aucun e-mail envoyé, aucune tâche ni événement créé).

Sujet officiel : [`docs/BRIEF_ORIGINAL.txt`](docs/BRIEF_ORIGINAL.txt).

## État

Phase de cadrage (semaine 1, jour 1). Aucun code exécutable, aucune donnée, aucun modèle entraîné à ce stade. Voir [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md).

## Documents de suivi

| Document | Rôle |
|---|---|
| `docs/REQUIREMENTS_MATRIX.md` | Traçabilité exigence → module → test → preuve → statut |
| `docs/ROADMAP.md` | Plan sur trois semaines, jalons, marges |
| `docs/TICKETS.md` | Tickets EL-xxx, dépendances, critères de fin |
| `docs/AGENT_ROUTING.md` | Capacités d'assistance réellement disponibles et règles de délégation |
| `docs/LEARNING_GUIDE.md` | Cours progressif et questions de compréhension |
| `docs/JOURNAL.md` | Historique horodaté append-only |
| `docs/CURRENT_STATE.md` | État fiable pour reprendre une session |

## Installation

Prérequis : Python ≥ 3.10 et [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --extra dev          # socle + tests (Linux, macOS, Windows/PowerShell)
uv sync --locked --extra dev --extra data   # + acquisition SUMM-RE (texte seul)
uv run pytest
```

L'extra `ml` (torch, sentence-transformers) est destiné à Colab ou à une machine avec GPU.

## Limites

Projet en cours ; aucune métrique n'est encore disponible.
