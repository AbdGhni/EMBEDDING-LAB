# Tickets

Charges en demi-journées (½j) estimées. « Fin » = critère de fin vérifiable.

| ID | Titre | Dépend de | Charge | Livrable | Fin | Statut |
|---|---|---|---|---|---|---|
| EL-001 | Cadrage, audit environnement, documents de suivi | — | 1 | matrice, roadmap, tickets, routing, journal, état | documents poussés sur une branche | validé |
| EL-002 | Réponses aux questions bloquantes (échéance, temps, langue, calcul) | EL-001 | ½ | décisions dans DECISIONS.md | réponses de l'étudiant enregistrées | validé |
| EL-003 | Revue des datasets candidats (sources officielles, licences) | EL-001 | 2 | tableau comparatif dans DATA_CARD.md | licence et redistribution vérifiées pour chaque candidat retenu | exécuté non validé (XNLI : licence non vérifiée) |
| EL-004 | Choix du corpus principal + évaluation complémentaire | EL-002, EL-003 | ½ | décision D-008 | choix justifié et validé par l'étudiant | validé |
| EL-005 | Environnement reproductible (pyproject, verrou, CI légère) | EL-002 | 1 | `pyproject.toml`, lock, CI | installation propre Windows + Linux | validé (CI verte : Ubuntu et Windows, Python 3.10 et 3.12) |
| EL-006 | Schéma des unités/relations/intentions + guide d'annotation | EL-001 | 1 | `docs/ANNOTATION_GUIDE.md`, schémas JSON | exemples valides et invalides testés | exécuté non validé (17 tests verts ; guide à relire par l'étudiant) |
| EL-007 | Corpus v0 : ingestion SUMM-RE, texte canonique et tours avec offsets | EL-004, EL-006 | 1 | `data/` (hors Git) + `scripts/fetch_summre.py` | empreintes enregistrées, 0 erreur d'offset | validé |
| EL-007b | B-REAL : pré-annotation des unités et requêtes SUMM-RE (LLM provisoire) + échantillon de contrôle à relire par l'étudiant | EL-007, EL-008, EL-009 | 2 | unités et qrels JSONL validés par `check_unit` | 100 % des unités valides ; qrels test figés (SHA-256) ; échantillon de relecture préparé | exécuté non validé (val 10 + test 9 + train 38 groupes ; test v2 figé, relecture humaine ciblée faite ; train non relu) |
| EL-007c | B-SYN : générateur de projets synthétiques (familles de patrons, entités et dates disjointes par split) | EL-006, EL-009 | 2 | `scripts/make_bsyn.py`, données hors Git | 0 entité, patron ou projet partagé entre splits ; qrels test figés | validé (empreintes test dans JOURNAL, régénération identique) |
| EL-008 | Splits par composante de personnes + détection de doublons / fuites | EL-007 | 1 | `scripts/make_splits.py`, `splits/summre_v1.json` | 0 groupe et 0 locuteur partagés entre splits | validé |
| EL-009 | Protocole expérimental puis gel du test | EL-008 | 1 | `EXPERIMENT_PROTOCOL.md` v1.0, `eval/metrics.py`, `splits/summre_v1_test_meetings.txt` | protocole et périmètre du test figés avec empreintes ; qrels figés à leur création (EL-007b/c) | validé (protocole v1.1 après relecture `mle-reviewer` ; périmètre figé) |
| EL-010 | Point d'entrée commun d'évaluation (refus du test sans journal, même code pour tous les systèmes) + E0 : BM25 | EL-007b, EL-007c | ½ | `eval/harness.py`, `runs/E0-*` | métriques sur val et test | exécuté non validé (val mesuré ; test après relecture B-REAL) |
| EL-011 | E1 : encodeur pré-entraîné | EL-007b, EL-007c | 1 | `runs/E1-*` | métriques + révision du modèle | exécuté non validé (val) |
| EL-012 | Paires/triplets + mining de hard negatives (train uniquement) | EL-007b, EL-007c, EL-008 | 2 | jeu d'entraînement + inspection faux négatifs | aucun négatif issu de val/test | exécuté non validé (`data/train/`, 7 343 exemples ; négatifs tirés du train uniquement) |
| EL-013 | E2 : fine-tuning contrastif | EL-011, EL-012 | 2 | checkpoint, logs, commande | checkpoint choisi sur validation | exécuté non validé (3 graines, val ; `docs/EXPERIMENTS.md`) |
| EL-014 | E3 : ablation hard vs simples | EL-013 | 1 | `runs/E3-*` | budget égal documenté | exécuté non validé (3 graines, val) |
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
