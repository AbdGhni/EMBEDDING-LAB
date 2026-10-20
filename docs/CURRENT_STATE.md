# État courant

Mis à jour : session S04, 2026-10-20 (23 h 50)

## Git

- `main` @ `825fa57` — poussé.
- `el-001-cadrage` @ `b8f8a78` — poussé, PR à ouvrir depuis GitHub (le CLI `gh` n'est pas authentifié dans la VM).
- `el-003-datasets` @ `4e19a61` — poussé.
- `el-005-006-env-schemas` @ `50f0837` — poussé, CI verte.
- `el-007-ingest` — basé sur `el-005-006-env-schemas`, voir son dernier commit. Branches empilées : fusionner dans l'ordre 001 → 003 → 005-006 → 007.

## Tickets

- EL-001, EL-002 : validés.
- EL-003 : exécuté non validé (licence XNLI non vérifiée).
- EL-004 : validé (D-008).
- EL-005 : validé (CI verte Ubuntu + Windows).
- EL-007 : validé (ingestion SUMM-RE, 283 réunions, empreintes).
- EL-007b : prévu (pré-annotation des unités).
- EL-006 : exécuté non validé (guide à relire).
- Autres : prévus.

## Décisions clés

Français (D-004), Colab pour l'entraînement (D-005), pas d'échéance fixe (D-006), assistance IA documentée (D-007).

## Environnement

- VM cloud Linux, Python 3.13, CPU seulement. Venv de travail temporaire hors dépôt (pyarrow, huggingface_hub).
- Projet : `uv sync --locked --extra dev` ; 17 tests verts.

## Données locales (hors Git, dans la VM)

- `data/raw/summre/` + `manifest.json` ; `data/processed/summre_meetings.jsonl` (SHA-256 `05a46a7f…`). Régénérables par `uv run python -I scripts/fetch_summre.py`.

## Runs

Aucun.

## Blocages

- ECC non vérifiable depuis la VM.

## Prochaine action

EL-008 : split par groupe d'expérience (stratifié par type de réunion et part de manuel), quasi-doublons, gel des identifiants du test.
