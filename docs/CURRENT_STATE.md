# État courant

Mis à jour : session S02, 2026-10-20 (soir)

## Git

- `main` @ `825fa57` — poussé.
- `el-001-cadrage` @ `b8f8a78` — poussé, PR à ouvrir depuis GitHub (le CLI `gh` n'est pas authentifié dans la VM).
- `el-003-datasets` — basé sur `el-001-cadrage`, voir son dernier commit.

## Tickets

- EL-001, EL-002 : validés.
- EL-003 : exécuté non validé (licence XNLI non vérifiée).
- EL-004 : en attente de validation de D-008 (SUMM-RE re-splitté par groupe + synthétique + PAWS-X fr).
- Autres : prévus.

## Décisions clés

Français (D-004), Colab pour l'entraînement (D-005), pas d'échéance fixe (D-006), assistance IA documentée (D-007).

## Environnement

- VM cloud Linux, Python 3.13, CPU seulement. Venv de travail temporaire hors dépôt (pyarrow, huggingface_hub).
- Environnement du projet pas encore créé (EL-005).

## Runs

Aucun.

## Blocages

- Validation de D-008 par l'étudiant.
- ECC non vérifiable depuis la VM.

## Prochaine action

EL-005 (pyproject + CI) et EL-006 (schémas unités/relations/intentions + guide d'annotation).
