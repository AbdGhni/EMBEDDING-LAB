# Tickets

Charges en demi-journées (½j) estimées. « Fin » = critère de fin vérifiable.

| ID | Titre | Dépend de | Charge | Livrable | Fin | Statut |
|---|---|---|---|---|---|---|
| EL-001 | Cadrage, audit environnement, documents de suivi | — | 1 | matrice, roadmap, tickets, routing, journal, état | documents poussés sur une branche | en cours |
| EL-002 | Réponses aux questions bloquantes (échéance, temps, langue, calcul) | EL-001 | ½ | décisions dans DECISIONS.md | réponses de l'étudiant enregistrées | bloqué (attente étudiant) |
| EL-003 | Revue des datasets candidats (sources officielles, licences) | EL-001 | 2 | tableau comparatif dans DATA_CARD.md | licence et redistribution vérifiées pour chaque candidat retenu | prévu |
| EL-004 | Choix du corpus principal + évaluation complémentaire | EL-002, EL-003 | ½ | décision D-xxx | choix justifié | prévu |
| EL-005 | Environnement reproductible (pyproject, verrou, CI légère) | EL-002 | 1 | `pyproject.toml`, lock, CI | installation propre Windows + Linux | prévu |
| EL-006 | Schéma des unités/relations/intentions + guide d'annotation | EL-001 | 1 | `docs/ANNOTATION_GUIDE.md`, schémas JSON | exemples valides et invalides testés | prévu |
| EL-007 | Corpus v0 : ingestion, unités sourcées avec offsets | EL-004, EL-006 | 2 | `data/` (hors Git) + script d'acquisition | empreintes enregistrées | prévu |
| EL-008 | Splits par groupe + détection de doublons / fuites | EL-007 | 1 | script de split, rapport de fuites | 0 groupe partagé entre splits | prévu |
| EL-009 | Protocole expérimental puis gel du test | EL-008 | 1 | `EXPERIMENT_PROTOCOL.md` | empreinte du test gelé dans le journal | prévu |
| EL-010 | E0 : BM25 | EL-009 | ½ | `runs/E0-*` | métriques sur val et test | prévu |
| EL-011 | E1 : encodeur pré-entraîné | EL-009 | 1 | `runs/E1-*` | métriques + révision du modèle | prévu |
| EL-012 | Paires/triplets + mining de hard negatives (train uniquement) | EL-008 | 2 | jeu d'entraînement + inspection faux négatifs | aucun négatif issu de val/test | prévu |
| EL-013 | E2 : fine-tuning contrastif | EL-011, EL-012 | 2 | checkpoint, logs, commande | checkpoint choisi sur validation | prévu |
| EL-014 | E3 : ablation hard vs simples | EL-013 | 1 | `runs/E3-*` | budget égal documenté | prévu |
| EL-015 | Classifieur de relations | EL-007 | 2 | `relations/` + métriques | macro-F1 et matrice de confusion | prévu |
| EL-016 | E4 : hybride, filtres, reranking | EL-013 | 1 | `runs/E4-*` | composants isolés | prévu |
| EL-017 | Analyse d'erreurs S2 + relecture indépendante | EL-014, EL-016 | 1 | EXPERIMENTS.md | relecture tracée | prévu |
| EL-018 | Mémoire indexée (unités + liens) | EL-013, EL-015 | 1 | `memory/` | requêtes retournent unités + preuves | prévu |
| EL-019 | Intentions + slots | EL-006 | 2 | `intents/` | macro-F1 sur test d'intentions | prévu |
| EL-020 | Temporalité (date de référence injectable) + identités | EL-018 | 1 | `resolution/` | tests dates relatives et homonymes | prévu |
| EL-021 | Destinataires + clarification | EL-020 | 1 | `resolution/recipients.py` | métriques M-05 | prévu |
| EL-022 | Réponses et dossiers sourcés (gabarits extractifs) | EL-018 | 2 | `agent/` | taux d'affirmations non étayées mesuré | prévu |
| EL-023 | Outils simulés + schémas JSON | EL-019 | 1 | `tools/`, `schemas/` | CI : executed=false toujours | prévu |
| EL-024 | Évaluation de bout en bout + 7 scénarios | EL-021–023 | 2 | logs de scénarios | 7/7 exécutés, résultats rapportés honnêtement | prévu |
| EL-025 | Rapport final + MODEL_CARD | EL-024 | 2 | FINAL_REPORT.md | relecture indépendante | prévu |
| EL-026 | Installation propre + script de démo 5–10 min | EL-024 | 1 | DEMO.md | démo rejouée sur environnement neuf | prévu |

Total ≈ 34 demi-journées pour ~30 disponibles sur 15 jours : la marge est négative si E5–E7 s'ajoutent. Ces expériences secondaires restent donc **conditionnelles**.
