# État courant

Mis à jour : session S12, 2026-10-23 (midi)

## Git

- `main` @ `825fa57` — poussé.
- `el-001-cadrage` @ `b8f8a78` — poussé, PR à ouvrir depuis GitHub (le CLI `gh` n'est pas authentifié dans la VM).
- `el-003-datasets` @ `4e19a61` — poussé.
- `el-005-006-env-schemas` @ `50f0837` — poussé, CI verte.
- `el-007-ingest` @ `0d471ab` — poussé.
- `el-008-splits` @ `cd2fb38` — poussé.
- `el-009-protocol` @ `76e2533` — poussé (rapport complet de relecture).
- `el-007c-bsyn` @ `15f0b16` — poussé (fusion de `76e2533`).
- `el-007b-breal` @ `43874fd` — poussé.
- `el-010-eval-bm25` — basé sur `el-007b-breal`, voir son dernier commit (contient aussi les relectures IA, le test B-REAL v2 et E1). Branches empilées : 001 → 003 → 005-006 → 007 → 008 → 009 → 007c → 007b → 010.
- `el-012-013-training` — basé sur `el-010-eval-bm25` ; annotations train B-REAL, données d'entraînement versionnées, notebook Colab. Branche de travail courante.
- Dépôt renommé `AbdGhni/EMBEDDING-LAB` ; remote mis à jour.

## Tickets

- EL-001, EL-002 : validés.
- EL-003 : exécuté non validé (licence XNLI non vérifiée).
- EL-004 : validé (D-008).
- EL-005 : validé (CI verte Ubuntu + Windows).
- EL-007 : validé (ingestion SUMM-RE, 283 réunions, empreintes).
- EL-007b : exécuté non validé — val (10 groupes, 78 requêtes) ; test **v2** (104 requêtes, 302 triplets), relecture IA puis relecture humaine ciblée des 43 désaccords (v2 confirmée) ; **train : 38/38 groupes** (4 135 unités, 325 requêtes répondables, 1 174 triplets), non relu.
- EL-012 : exécuté non validé — `data/train/` : E2 7 343 exemples (B-SYN 6 222 + B-REAL 1 121, SHA-256 `1cd42b9a…`), E3 7 343 (`dfefa76c…`) ; empreintes attendues `splits/data_sha256.json`.
- EL-013 / EL-014 : exécutés non validés — E2 et E3 × 3 graines sur Colab (val seulement) ; comparaison `runs/CMP-val-2026-10-23T1256`. E2 val : B-SYN 0,890, B-REAL 0,511 (E1 : 0,752 / 0,293) ; E2 ≈ E3 en nDCG@10, E2 > E3 sur les pièges B-SYN. Poids sur le Drive de l'étudiant.
- EL-010 : exécuté non validé — point d'entrée commun + BM25 ; val mesuré.
- EL-011 : exécuté non validé — e5-small sur val (B-SYN nDCG@10 0,752, B-REAL 0,293).
- EL-008 : validé (`splits/summre_v1.json`, SHA-256 `d6992f5d…`).
- EL-009 : validé (protocole **v1.4**, voir JOURNAL pour les empreintes ; v1.1 `4dc2ec3a…` après relecture `mle-reviewer` ; test SUMM-RE `ddd19567…` ; sous-ensemble relu `7cc1bec7…`) ; qrels à figer à leur création.
- EL-007c : validé (B-SYN 240/32/48 projets, test figé par empreintes).
- EL-006 : exécuté non validé (guide à relire).
- Autres : prévus.

## Décisions clés

Français (D-004), Colab pour l'entraînement (D-005), pas d'échéance fixe (D-006), assistance IA documentée (D-007).

## Environnement

- VM cloud Linux, Python 3.13, CPU seulement. Venv de travail temporaire hors dépôt (pyarrow, huggingface_hub).
- Projet : `uv sync --locked --extra dev` ; 77 tests verts. Extra `ml` installé (torch 2.14.1+cpu, sentence-transformers 6.2.0).

## Données locales (hors Git, dans la VM)

- `data/raw/summre/` + `manifest.json` ; `data/processed/summre_meetings.jsonl` (SHA-256 `05a46a7f…`). Régénérables par `uv run python -I scripts/fetch_summre.py`.
- `data/bsyn/` (manifeste `050f8e7d…`), régénérable à l'identique par `uv run python -I scripts/make_bsyn.py`.
- `data/breal/` (tâches + benchmark assemblé), régénérable par `prepare_breal_tasks.py` puis `assemble_breal.py`.

## Runs

`E0-bm25-val-2026-10-22T1127`, `E0r-random-val-2026-10-22T1127`, `E1-e5-small-val-2026-10-22T1130` (val uniquement ; voir `docs/EXPERIMENTS.md`). Diagnostics et tests de fumée : `DIAG-e2-cpu-…`, `DIAG-e2-cuda-…`, `SMOKE-E2-…`. Entraînements : `E2-e5s-s*-bs64-…`, `E3-e5s-s*-bs64-…` ; comparaison `CMP-val-2026-10-23T1256`. Aucun accès au test (`runs/TEST_ACCESS.log` absent).

## Blocages

- ECC 2.2.3 installé sur le PC, invocable seulement là-bas (relectures déléguées via `docs/mandates/`).

## Prochaine action

Décision à prendre par l'étudiant : (a) ablation « B-SYN seul » (une graine, val) pour savoir d'où vient le gain sur B-REAL, ou (b) figer E2/E3 tels quels. Ensuite : EL-015 (relations), E4 (hybride), puis évaluation **unique** du test avec les configurations figées (journal `TEST_ACCESS.log`).
