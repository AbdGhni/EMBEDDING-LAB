# État courant

Mis à jour : session S03, 2026-10-20 (soir)

## Git

- `main` @ `825fa57` — poussé.
- `el-001-cadrage` @ `b8f8a78` — poussé, PR à ouvrir depuis GitHub (le CLI `gh` n'est pas authentifié dans la VM).
- `el-003-datasets` @ `4e19a61` — poussé.
- `el-005-006-env-schemas` — basé sur `el-003-datasets`, voir son dernier commit. Branches empilées : fusionner dans l'ordre 001 → 003 → 005-006.

## Tickets

- EL-001, EL-002 : validés.
- EL-003 : exécuté non validé (licence XNLI non vérifiée).
- EL-004 : validé (D-008).
- EL-005 : exécuté non validé (CI GitHub et Windows non observés).
- EL-006 : exécuté non validé (guide à relire).
- Autres : prévus.

## Décisions clés

Français (D-004), Colab pour l'entraînement (D-005), pas d'échéance fixe (D-006), assistance IA documentée (D-007).

## Environnement

- VM cloud Linux, Python 3.13, CPU seulement. Venv de travail temporaire hors dépôt (pyarrow, huggingface_hub).
- Projet : `uv sync --locked --extra dev` ; 17 tests verts.

## Runs

Aucun.

## Blocages

- ECC non vérifiable depuis la VM.

## Prochaine action

EL-007 : `scripts/fetch_summre.py` → `data/raw/summre/` (texte seul, révision `47cb4ec`), tours de parole interclassés, empreintes SHA-256.
