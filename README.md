# EMBEDDING LAB — De la mémoire sémantique à l'agent intelligent

Projet individuel de trois semaines (ECE Paris, mentor : Martial Roberge). Sujet officiel : [`docs/BRIEF_ORIGINAL.txt`](docs/BRIEF_ORIGINAL.txt).

**En une phrase** : un encodeur de phrases fine-tuné par apprentissage contrastif pour retrouver, dans des réunions en français, *ce qui a été décidé* (et pas seulement *ce dont on a parlé*), utilisé par un petit agent qui répond avec ses sources, construit des dossiers et prépare des actions **uniquement simulées**.

## Le problème

Une recherche vectorielle classique rapproche « le budget est proposé », « le budget est validé » et « le budget est annulé » : même sujet, mêmes mots. Pour un assistant, ce sont trois informations opposées. Le projet mesure si un encodeur entraîné sur des exemples piégés (proposition contre décision, ancienne contre nouvelle version, personne citée contre personne responsable) fait mieux, puis construit un agent qui s'appuie dessus sans jamais inventer une décision, un destinataire ou une adresse.

## Résultats principaux (test, évalué une seule fois)

nDCG@10 (qualité du classement des 10 premiers résultats, de 0 à 1) ; scores fine-tunés = moyenne de 3 graines.

| Système | B-SYN (synthétique contrôlé) | B-REAL (réunions orales réelles) |
|---|---|---|
| E0 — BM25 (lexical) | 0,548 | 0,207 |
| E1 — e5-small pré-entraîné | 0,841 | 0,333 |
| **E2 — e5-small fine-tuné, négatifs difficiles** | **0,903** | **0,563** |
| E3 — e5-small fine-tuné, négatifs aléatoires | 0,898 | 0,564 |
| E4 — E2 + rétrogradation des informations remplacées | 0,900 | 0,539 |

- **H1 et H2 confirmées** : E2 > E1 sur B-SYN (+0,062 nDCG@10) et sur les pièges (+0,070), p corrigé (Holm) = 0,0002.
- **Oral réel** : +0,229 nDCG@10, gain dans les 7 groupes de personnes du test. Une ablation montre que ce gain vient des exemples réels annotés, pas des données synthétiques.
- **Négatifs difficiles** : même classement global que des négatifs aléatoires, mais l'encodeur préfère bien plus souvent la décision qui en remplace une autre (54 % contre 15 %).
- **Ce qui ne marche pas** : l'hybride BM25 + dense n'apporte rien ; reconnaître une information remplacée reste difficile (une fois sur deux) ; pour les intentions, le modèle choisi en validation est battu par de simples règles sur le test.
- **Relations** entre unités (remplace, contredit, répond à…) : macro-F1 0,608. **Agent** : 8 scénarios de démonstration sur 9 réussis.

Analyse complète : [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md). Détail de chaque expérience : [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md).

## Architecture

```
réunions (texte)          demande de l'utilisateur
      │                            │
      ▼                            ▼
unités sémantiques        intention + paramètres            src/embedding_lab/intents/
(décision, engagement,    (answer, compare, build_dossier,
 question, risque…)        draft_email, create_task,
 + relations               schedule_event, clarify, no_action)
      │                            │
      ▼                            ▼
mémoire indexée ───────► recherche dense (encodeur E2)      src/embedding_lab/memory/, retrieval/
                                   │
                                   ▼
                    état de l'information : remplacée,       src/embedding_lab/relations/
                    contestée, en vigueur
                                   │
                                   ▼
                    dates relatives, responsable explicite    src/embedding_lab/resolution/
                    (une mention ≠ une responsabilité)
                                   │
                                   ▼
          réponse sourcée │ comparaison │ dossier │ brouillon     src/embedding_lab/agent/
          d'e-mail, tâche, événement │ question de précision     src/embedding_lab/tools/
          │ rien (phrase hypothétique)
```

Toutes les actions sont des propositions JSON validées par schéma (`needs_confirmation: true`, `executed: false`). Les réponses sont extractives : chaque affirmation cite l'unité et l'extrait dont elle vient. Aucun modèle de langue ne rédige les réponses.

## Données

| Jeu | Contenu | Pourquoi |
|---|---|---|
| **SUMM-RE** (Linagora, CC BY-SA 4.0) | 283 réunions orales en français | seule source réelle française de réunions de décision trouvée |
| **B-SYN** | projets synthétiques à 3 réunions, avec pièges construits | cas difficiles contrôlés ; personnes, projets, dates et gabarits disjoints entre train, val et test |
| **B-REAL** | unités, relations et requêtes annotées sur SUMM-RE (annotateur IA, relecture humaine ciblée) | mesurer sur de l'oral réel |
| **Intentions** | 1 764 requêtes générées + 80 écrites à la main | classer les demandes |
| **Atlas** | projet entièrement fictif (3 réunions) | démonstration |

Le découpage train / val / test se fait par **groupes de personnes** : deux groupes de réunions qui partagent un participant vont dans le même split. Les splits officiels de SUMM-RE mélangeaient les mêmes groupes entre train et test (fuite). Détails, licences et limites : [`docs/DATA_CARD.md`](docs/DATA_CARD.md).

## Méthode en bref

- Encodeur : `intfloat/multilingual-e5-small` (révision figée).
- Fine-tuning : perte contrastive *Multiple Negatives Ranking Loss* (InfoNCE) avec un négatif difficile par exemple (même sujet, mais mauvais statut, mauvaise personne, ancienne version…), 7 343 exemples, Google Colab (T4), environ 2 minutes par entraînement, 3 graines.
- Évaluation : un seul point d'entrée pour tous les systèmes, test figé et évalué une seule fois (chaque accès est consigné dans `runs/TEST_ACCESS.log`), tests statistiques par grappes (projets, groupes de personnes).
- Protocole écrit avant les mesures : [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md).

## Installation

Prérequis : Python ≥ 3.10 et [uv](https://docs.astral.sh/uv/). Fonctionne sous Linux, macOS et Windows (PowerShell).

```bash
git clone https://github.com/AbdGhni/EMBEDDING-LAB.git
cd EMBEDDING-LAB
uv sync --locked --extra dev            # socle + tests
uv run pytest                           # 94 tests
uv sync --locked --extra dev --extra ml # + torch, sentence-transformers (démo, entraînement)
```

## Démonstration

```bash
uv run python -I scripts/run_scenarios.py              # 7 scénarios du brief + 2 bonus, contrôles automatiques
uv run python -I scripts/agent_cli.py                  # boucle interactive
uv run python -I scripts/agent_cli.py -q "Rédige un mail à la personne responsable du budget pour lui demander la dernière version validée avant vendredi."
```

Par défaut, la mémoire est indexée avec l'encodeur initial (E1). Pour l'encodeur fine-tuné, télécharger un dossier `E2-…/best` (≈ 470 Mo, hors Git) et ajouter `--weights <dossier>/best`. Script de démonstration de 5 à 10 minutes : [`docs/DEMO.md`](docs/DEMO.md).

Exemple de sortie (brouillon d'e-mail, jamais envoyé) :

```json
{
 "intent": "draft_email",
 "tool_candidate": "email.create_draft",
 "recipient": {"name": "Marie", "email": null,
               "evidence_unit_ids": ["u-atlas-15", "u-atlas-02"],
               "resolution_status": "email_missing"},
 "subject": "Projet Atlas — budget",
 "body": "Bonjour Marie,\n\nPourrais-tu me transmettre la dernière version validée du budget avant le vendredi 23 octobre 2026 ?\n\nPour mémoire : La direction a validé le budget à 45 000 euros. (jeudi 15 octobre 2026).\n\nMerci.",
 "clarification": {"needed": true, "reason": "email_missing",
                   "question": "Je n'ai pas l'adresse de Marie dans les sources : peux-tu la confirmer avant tout envoi ?"},
 "needs_confirmation": true,
 "executed": false
}
```

Marie est choisie parce qu'elle s'est explicitement engagée sur le budget ; Karim, seulement cité à propos du budget, est écarté. Son adresse n'existe pas dans les sources : elle reste vide.

## Reproduire

| Étape | Commande |
|---|---|
| Télécharger SUMM-RE (texte seul) | `uv run python -I scripts/fetch_summre.py` |
| Splits par groupes de personnes | `uv run python -I scripts/make_splits.py` |
| Générer B-SYN | `uv run python -I scripts/make_bsyn.py` |
| Assembler B-REAL depuis les annotations | `uv run python -I scripts/prepare_breal_tasks.py val test train` puis `uv run python -I scripts/assemble_breal.py --splits train val test` |
| Vérifier que les données sont identiques à la référence | `uv run python -I scripts/verify_data.py` |
| Baselines (BM25, e5-small) | `uv run python -I scripts/run_eval.py --system bm25 --split val` |
| Fine-tuning E2 / E3 | `notebooks/colab_e2_e3.ipynb` (Colab, GPU) |
| Relations, intentions | `scripts/train_relations.py`, `scripts/train_intents.py` |
| Comparaisons statistiques | `scripts/compare_runs.py`, `scripts/final_analysis.py` |

Chaque exécution écrit un dossier `runs/<id>/` (configuration, commit Git, empreintes des données, métriques par requête).

## Organisation du dépôt

```
src/embedding_lab/   code (ingestion, splits, B-SYN, évaluation, retrieval, entraînement,
                     relations, intentions, mémoire, résolution, agent, outils simulés, schémas)
scripts/             points d'entrée en ligne de commande
notebooks/           entraînement sur Colab
annotations/         annotations B-REAL et jeu d'intentions écrit à la main (versionnés)
data/                données générées (en partie hors Git), exemples d'entraînement
demo/atlas/          mémoire de démonstration fictive
runs/                tous les résultats, journal d'accès au test
splits/              splits figés et empreintes
docs/                rapport, protocole, expériences, données, décisions, journal
tests/               tests automatiques
```

## Documents

| Document | Contenu |
|---|---|
| [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md) | rapport final : résultats, analyse, limites, coûts |
| [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) | chaque expérience, avec ses chiffres et sa lecture |
| [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md) | hypothèses, métriques, règles d'accès au test (écrit avant les mesures) |
| [`docs/DATA_CARD.md`](docs/DATA_CARD.md) | sources, licences, splits, annotation, limites |
| [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) | fiche de l'encodeur fine-tuné |
| [`docs/LEARNING_GUIDE.md`](docs/LEARNING_GUIDE.md) | explications des notions utilisées, avec questions de compréhension |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | décisions de conception et leurs raisons |
| [`docs/JOURNAL.md`](docs/JOURNAL.md) | journal horodaté de toutes les sessions |
| [`docs/AGENT_ROUTING.md`](docs/AGENT_ROUTING.md) | ce qui a été fait avec quels outils d'IA |

## Usage de l'IA

Le code, la documentation et les annotations B-REAL ont été produits avec Claude (Claude Code). J'ai fixé les choix de départ (langue française, calcul sur Colab), validé les décisions proposées à chaque étape et relu les points litigieux des annotations du test. Tout est tracé dans [`docs/JOURNAL.md`](docs/JOURNAL.md) et [`docs/AGENT_ROUTING.md`](docs/AGENT_ROUTING.md). Les annotations faites par l'IA sont marquées comme provisoires ; aucun accord inter-annotateurs humain n'est revendiqué.

## Limites

- Annotations B-REAL produites par une IA, la même pour train, val et test : une partie du gain sur l'oral peut venir de son style de questions.
- B-SYN, les intentions et la démonstration sont générés ou écrits par l'auteur du système.
- Test B-REAL : 7 groupes de personnes seulement, d'où des intervalles larges.
- Une seule taille de modèle ; pas de reranker cross-encoder ni de filtre par type d'unité.
- La démonstration repose sur une mémoire de 21 unités : elle teste l'enchaînement de l'agent, pas la qualité de la recherche.

## Licences

Code : à préciser. Données dérivées de SUMM-RE (annotations B-REAL, exemples d'entraînement) : CC BY-SA 4.0, attribution à Linagora. Encodeur de base : MIT.
