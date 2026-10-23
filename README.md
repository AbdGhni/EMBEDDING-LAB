# EMBEDDING LAB — De la mémoire sémantique à l'agent intelligent

Projet individuel de trois semaines (mentor référent : Martial Roberge).

Objectif : entraîner et évaluer un modèle d'embeddings spécialisé (apprentissage contrastif, hard negatives) capable de distinguer proposition, décision, annulation, responsabilité et simple mention, puis l'utiliser dans un mini-agent déterministe qui répond avec preuves, construit des dossiers sourcés et prépare des actions **uniquement simulées** (aucun e-mail envoyé, aucune tâche ni événement créé).

Sujet officiel : [`docs/BRIEF_ORIGINAL.txt`](docs/BRIEF_ORIGINAL.txt).

## État

Fine-tuning contrastif (E2, E3), relations, intentions, mémoire, agent et scénarios de démonstration réalisés et mesurés **sur validation**. Les mesures finales sur le test n'ont pas encore été faites. Résultats : [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) ; état détaillé : [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md).

## Démonstration

```bash
uv sync --locked --extra dev --extra ml
uv run python -I scripts/run_scenarios.py                    # 7 scénarios + 2 bonus, contrôles automatiques
uv run python -I scripts/agent_cli.py                        # boucle interactive
uv run python -I scripts/agent_cli.py -q "Qui est responsable du budget ?"
```

Par défaut, la mémoire est indexée avec l'encodeur initial (E1). Pour utiliser l'encodeur fine-tuné (E2), télécharger un dossier `E2-…/best` depuis le Drive de l'étudiant et ajouter `--weights <dossier>/best`. La mémoire de démonstration (`demo/atlas/source.json`) est un projet **fictif** ; aucune adresse e-mail n'existe dans les sources, donc l'agent n'en propose jamais. Toutes les actions sont des propositions JSON (`needs_confirmation: true`, `executed: false`).

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

Voir `docs/EXPERIMENTS.md` et `docs/EXPERIMENT_PROTOCOL.md` § 9 à 12 : annotations B-REAL provisoires (IA), test non encore mesuré, données d'intentions synthétiques ou écrites par l'IA, mémoire de démonstration écrite à la main.
