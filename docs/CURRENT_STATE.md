# État courant

Mis à jour : session S09, 2026-10-22 (midi)

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
- Dépôt renommé `AbdGhni/EMBEDDING-LAB` ; remote mis à jour.

## Tickets

- EL-001, EL-002 : validés.
- EL-003 : exécuté non validé (licence XNLI non vérifiée).
- EL-004 : validé (D-008).
- EL-005 : validé (CI verte Ubuntu + Windows).
- EL-007 : validé (ingestion SUMM-RE, 283 réunions, empreintes).
- EL-007b : exécuté non validé — val (10 groupes, 78 requêtes) ; test **v2** (104 requêtes, 302 triplets) après relecture IA du sous-ensemble ; relecture humaine en attente (`annotations/breal/review/relecture_v2.xlsx`).
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
- Projet : `uv sync --locked --extra dev` ; 67 tests verts. Extra `ml` installé (torch 2.14.1+cpu, sentence-transformers 6.2.0).

## Données locales (hors Git, dans la VM)

- `data/raw/summre/` + `manifest.json` ; `data/processed/summre_meetings.jsonl` (SHA-256 `05a46a7f…`). Régénérables par `uv run python -I scripts/fetch_summre.py`.
- `data/bsyn/` (manifeste `050f8e7d…`), régénérable à l'identique par `uv run python -I scripts/make_bsyn.py`.
- `data/breal/` (tâches + benchmark assemblé), régénérable par `prepare_breal_tasks.py` puis `assemble_breal.py`.

## Runs

`E0-bm25-val-2026-10-22T1127`, `E0r-random-val-2026-10-22T1127`, `E1-e5-small-val-2026-10-22T1130` (val uniquement ; voir `docs/EXPERIMENTS.md`).

## Blocages

- ECC 2.2.3 installé sur le PC, invocable seulement là-bas (relectures déléguées via `docs/mandates/`).

## Prochaine action

EL-012 : paires et triplets d'entraînement (B-SYN train + B-REAL train à annoter ou non : décision à prendre), puis EL-013 : notebook Colab du fine-tuning E2 avec diagnostics. Pas de mesure sur le test avant la fin de E2/E3.
