# Mandat de relecture — EL-008 / EL-009

**Agent** : `mle-reviewer` (ECC 2.2.3), lancé par l'étudiant dans Claude Code sur son PC, à la racine d'un clone de `AbdGhni/embedding-lab` sur la branche `el-009-protocol`.
**Auteur relu** : l'orchestrateur (session Claude cloud). Le relecteur ne modifie aucun fichier.

## Objectif

Vérifier, preuves à l'appui, que le protocole et les splits permettent une comparaison honnête E1 (encodeur initial) / E2 (encodeur fine-tuné), sans fuite.

## Fichiers à lire

`docs/EXPERIMENT_PROTOCOL.md`, `docs/DATA_CARD.md`, `docs/DECISIONS.md` (D-008 à D-010), `src/embedding_lab/data/splits.py`, `scripts/make_splits.py`, `splits/summre_v1.json`, `src/embedding_lab/eval/metrics.py`, `tests/test_splits.py`, `tests/test_metrics.py`.

## Questions précises

1. Le découpage par composante de locuteurs empêche-t-il qu'une même personne ou un même groupe soit en train et en test ? Vérifier dans `splits/summre_v1.json` (champ `leakage`) et dans le code.
2. Une fuite reste-t-elle possible par d'autres voies : négatifs difficiles, données synthétiques, sélection du checkpoint, seuils ?
3. Les hypothèses H1–H5 sont-elles réellement réfutables avec les effectifs prévus (45 réunions de test, dont 15 manuelles) ? Le bootstrap par grappes est-il correctement implémenté ?
4. Le benchmark E1/E2 est-il bien isolé (aucun autre composant ne change) ?
5. Qu'est-ce qui, dans ce protocole, pourrait produire un gain illusoire ?

## Livrable

Un rapport en français avec, pour chaque point : verdict (OK / risque / bloquant), preuve (fichier et ligne ou extrait), correction proposée. Ne pas approuver sur le style seul.

## Critères d'acceptation

Chaque verdict cite une preuve vérifiable. Le rapport est enregistré par l'étudiant dans `docs/reviews/EL-009-mle-reviewer.md` (ou collé dans la conversation).
