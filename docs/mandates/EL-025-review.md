# Mandat de relecture indépendante — EL-025 (à lancer sur le PC, ECC 2.2.3)

Dépôt : `AbdGhni/EMBEDDING-LAB`, branche `el-019-intents`. Le test a déjà été évalué une fois : **ne relancer aucune évaluation sur le test** ; signaler les problèmes, ne pas corriger le code.

## 1. `mle-reviewer`

Lire `docs/EXPERIMENT_PROTOCOL.md` (v1.8), `docs/EXPERIMENTS.md`, `docs/FINAL_REPORT.md`, `src/embedding_lab/train/`, `src/embedding_lab/eval/`, `scripts/final_analysis.py`, `runs/CMP-test-2026-10-23T1450/final.json`, `runs/TEST_ACCESS.log`. Vérifier :
- fuites possibles entre train, val et test (splits, négatifs, données B-REAL) ;
- que les conclusions du rapport (H1–H5, relations, intentions) suivent les règles du protocole et ne vont pas au-delà des chiffres ;
- que les écarts déclarés (E2S décidée après la val, correction de l'agent après le premier passage des scénarios, I2 battu par les règles sur le test) sont correctement présentés ;
- les statistiques (permutation par grappes, Holm, bootstrap).

## 2. `security-reviewer`

Lire `src/embedding_lab/tools/`, `src/embedding_lab/agent/`, `src/embedding_lab/schemas/`, `tests/test_agent_parts.py`. Vérifier : aucune exécution réelle possible, aucune adresse inventée, contenu des transcriptions traité comme donnée (consigne cachée `u-atlas-20`), absence de secrets dans le dépôt.

## 3. `python-reviewer`

Lire `src/embedding_lab/` et `scripts/`. Signaler les bogues probables, les erreurs silencieuses et les incohérences entre code et documentation.

## Retour attendu

Pour chaque relecteur : liste des problèmes (fichier, ligne, gravité), sans correction. Copier le rapport dans `docs/reviews/EL-025-<relecteur>.md` puis le pousser, ou le coller dans la conversation.
