# Journal (append-only)

Règles : heures réellement observées, fuseau Europe/Paris en ISO 8601 ; « non enregistré » si inconnu ; les erreurs anciennes ne sont jamais effacées, seules des corrections sont ajoutées.

---

## 2026-10-20 · Session S01 · EL-001 Cadrage

- **Début** : 2026-10-20T21:41+02:00 (heure du message de lancement) · **Fin** : 2026-10-20T21:50+02:00 environ (estimation, non chronométrée)
- **Branche** : `el-001-cadrage` (base `main` @ `825fa57`)
- **Exigences couvertes** : L-01 (amorce), C-08 (préparation), matrice complète
- **Agent / capacité** : orchestrateur seul (Opus 5.5). Aucune délégation : travail de cadrage séquentiel, ECC absent de la VM.

### Actions

1. Audit de l'environnement cloud : Linux x86_64, Python 3.13.16, Git 2.43.0, 2 vCPU, 7,8 Gio RAM, pas de GPU, ~30 Go libres. Accès réseau à huggingface.co, pypi.org et groups.inf.ed.ac.uk (HTTP 200).
2. Dépôt `AbdGhni/embedding-lab` : distant **vide** (aucune référence). Aucun AGENTS.md / CLAUDE.md / README préexistant.
3. ECC : absent de la VM. PC Windows relié à la session, aucun dossier partagé : ECC non vérifiable.
4. `gh` CLI : jeton invalide → PR non ouvrable en ligne de commande ; push Git fonctionnel.
5. Copie fidèle du sujet : lignes 354–665 du prompt fourni → `docs/BRIEF_ORIGINAL.txt`, 311 lignes, SHA-256 `3120508a626d4eb5748423236f4772a527f71f40135088c4a7d39001948aca52`.
6. Commit initial sur `main` (`825fa57`) poussé : README, .gitignore, BRIEF.
7. Création sur `el-001-cadrage` : REQUIREMENTS_MATRIX, ROADMAP, TICKETS, AGENT_ROUTING, DECISIONS, LEARNING_GUIDE (leçon 1), JOURNAL, CURRENT_STATE, CLAUDE.md.

### Résultats et limites

- Aucun code, donnée, entraînement ni métrique à ce stade.
- Les valeurs de cosinus de la leçon 1 sont illustratives, non mesurées.
- Estimation de charge (34 ½j) supérieure à la capacité estimée (30 ½j) : E5–E7 conditionnels.

### Suite

EL-002 (réponses de l'étudiant), puis EL-003 (revue des datasets et licences).

### Correction S01

L'heure de fin estimée « 21:50 » était inexacte : l'horloge relevée au moment du push donnait 2026-10-20T21:44:59+02:00.

---

## 2026-10-20 · Session S02 · EL-002, EL-003 (+ préparation EL-004)

- **Début** : 2026-10-20T22:01+02:00 (heure du message de l'étudiant) · **Fin** : voir l'horodatage du commit de cette entrée
- **Branche** : `el-003-datasets` (base `el-001-cadrage` @ `b8f8a78`)
- **Exigences couvertes** : L-02 (amorce), C-03 (détection de fuite), C-04
- **Agent / capacité** : orchestrateur seul ; WebSearch/WebFetch pour les sources officielles. Pas de délégation : la recherche est séquentielle, chaque résultat oriente le suivant.

### Actions

1. Réponses de l'étudiant enregistrées : échéance « le plus vite possible », données en français, Colab pour l'entraînement, aucune règle IA (D-004 à D-007).
2. Vérification des licences et caractéristiques sur les sources officielles : SUMM-RE (fiche HF), FREDSum (GitHub linto-ai), PAWS-X (fiche HF), XNLI (page NYU : licence non indiquée), AMI (page Édimbourg : CC BY 4.0).
3. SUMM-RE : schéma lu (`pyarrow`, lecture de colonnes par HTTP, révision `47cb4ec`), sans télécharger l'audio. Inventaire : 283 réunions, 938 pistes de locuteurs, ~5,8 M caractères.
4. **Constat de fuite** : 30 groupes d'expérience partagés entre train et test officiels, 27 entre train et dev.
5. Ajout de `scripts/inspect_summre.py` et `docs/DATA_CARD.md` ; proposition D-008.

### Résultats et limites

- Licence XNLI non vérifiée : son usage est suspendu.
- L'hypothèse « mêmes participants au sein d'un groupe d'expérience » reste à confirmer dans l'article SUMM-RE.
- Aucune donnée n'est stockée dans le dépôt.

### Suite

Validation de D-008 par l'étudiant, puis EL-005 (environnement) et EL-006 (schéma et guide d'annotation), qui peuvent avancer en parallèle.

---

## 2026-10-20 · Session S03 · EL-004, EL-005, EL-006

- **Début** : 2026-10-20T22:42+02:00 (message de l'étudiant) · **Fin** : voir l'horodatage du commit
- **Branche** : `el-005-006-env-schemas` (base `el-003-datasets` @ `4e19a61`)
- **Exigences couvertes** : L-01, L-08 (amorce), C-01, C-02, D-08 (rôle vs mention), D-10
- **Agent / capacité** : orchestrateur seul. EL-005 et EL-006 sont indépendants, mais trop petits pour justifier une délégation.

### Actions

1. D-008 marquée validée (réponse « Faut le mieux » interprétée comme acceptation ; à corriger sinon).
2. `pyproject.toml` (socle léger + extras `data`, `ml`, `dev`), `uv.lock` (88 paquets résolus), CI GitHub Actions (Ubuntu + Windows, Python 3.10 et 3.12 ; lint et tests, sans entraînement).
3. Schémas JSON `unit`, `relation`, `action` + module `embedding_lab.schemas` : validation structurelle et invariants sémantiques (offsets ↔ source, sens et projet de `supersedes`, cible de `answers`, adresse obligatoirement issue de l'annuaire de démo, clarification obligatoire si le destinataire n'est pas résolu, `executed` toujours `false`).
4. `docs/ANNOTATION_GUIDE.md` v0.1.

### Résultats

- `pytest` : 17 tests verts (local, puis copie propre installée avec `uv sync --locked`).
- `ruff` : aucune erreur après correction (une importation inutilisée, un `if` imbriqué, une ligne trop longue).
- Le contrôle d'offsets a détecté une erreur dans ma propre donnée de test (début 9 au lieu de 10) : corrigée.

### Limites

- CI pas encore observée sur GitHub, Windows non testé.
- Le format `date-time` n'est pas vérifié par jsonschema sans dépendance supplémentaire ; `date` et `email` le sont.
- Le guide d'annotation n'a pas encore été relu par l'étudiant.

### Suite

EL-007 : ingestion de SUMM-RE (texte seul, révision figée), reconstruction des tours de parole, empreintes.

---

## 2026-10-20 · Session S04 · EL-005 (validation), EL-007

- **Début** : 2026-10-20T23:40+02:00 (message « Go ») · **Fin** : voir l'horodatage du commit
- **Branche** : `el-007-ingest` (base `el-005-006-env-schemas` @ `50f0837`)
- **Exigences couvertes** : L-02, C-03 (préparation), D-06
- **Agent / capacité** : orchestrateur seul.

### Actions et résultats

1. CI GitHub du commit `50f0837` : succès sur les 4 jobs (Ubuntu/Windows × Python 3.10/3.12) → EL-005 validé.
2. Module `embedding_lab.ingest.summre` : interclassement des pistes par heure de début, fusion des segments d'un même locuteur séparés de 1 s au plus, texte canonique `locuteur: texte` avec offsets par tour, métadonnées de réunion décodées depuis l'identifiant (ordre a/b/c, type R/D/P, lieu — confirmé dans la fiche SUMM-RE).
3. Schéma `unit` : `source_date` peut valoir null (SUMM-RE n'a pas de dates calendaires, on n'en invente pas) ; ajout de `source_order`. `supersedes` est vérifié par date, sinon par rang, sinon refusé comme invérifiable.
4. Acquisition réelle : 938 pistes en 4 min 47 s (23:42:06 → 23:46:53), puis reconstruction de 283 réunions et 100 651 tours ; 0 erreur d'offset (détail et empreintes dans DATA_CARD § 2 bis).
5. Constat : aucun groupe d'expérience n'est entièrement transcrit à la main (57 mixtes, 39 tout-ASR).
6. 27 tests verts (dont doctests) ; `scripts/inspect_summre.py` supprimé (remplacé par `fetch_summre.py`).

### Correction

EL-007 ne couvrait pas l'extraction des unités : la pré-annotation devient un ticket séparé, EL-007b.

### Suite

EL-008 : split par groupe d'expérience (stratifié par type de réunion et part de transcription manuelle), contrôle des quasi-doublons, puis gel des identifiants du test.

---

## 2026-10-20/21 · Session S05 · EL-008

- **Début** : 2026-10-20T23:57+02:00 (message « Fonce ») · **Fin** : voir l'horodatage du commit
- **Branche** : `el-008-splits` (base `el-007-ingest` @ `0d471ab`)
- **Exigences couvertes** : C-03, L-02
- **Agent / capacité** : orchestrateur seul.

### Actions et résultats

1. Analyse : 5 scénarios (A–E) partagés par de nombreux groupes ; 91 groupes sur 96 suivent la séquence reporting / planification / décision.
2. **Deuxième fuite détectée** : 80 identifiants de locuteurs sur 212 apparaissent dans plusieurs groupes. Union-find → 41 composantes, dont une de 27 groupes.
3. `embedding_lab.data.splits` : composantes, affectation par tirages à graine fixe, rapport de fuites (groupes, locuteurs, recouvrement de 8-grammes). 6 nouveaux tests ; 33 tests verts.
4. `scripts/make_splits.py` → `splits/summre_v1.json` (SHA-256 `d6992f5d…`) : train 178, val 60, test 45 réunions ; cibles manuelles atteintes exactement (val 11 dont 4 décision, test 15 dont 5 décision).
5. Rapport : 0 groupe et 0 locuteur partagés ; recouvrement de 8-grammes ≤ 8,2 %, expliqué par des répétitions et des jetons `w_N`/`sil` (0,54 % des tours ASR, 0,12 % des tours manuels).

### Limites

- Identifiants de locuteurs traités comme des personnes : hypothèse prudente, non confirmée par la fiche.
- Thèmes de scénario partagés entre train et test.

### Suite

EL-009 : protocole expérimental puis gel du test. EL-007b (pré-annotation des unités) et la génération des données synthétiques peuvent avancer en parallèle.

---

## 2026-10-21 · Session S06 · EL-009

- **Début** : 2026-10-21T15:07+02:00 (message « go », session depuis le PC) · **Fin** : voir l'horodatage du commit
- **Branche** : `el-009-protocol` (base `el-008-splits` @ `cd2fb38`)
- **Exigences couvertes** : M-01, M-02, C-08, X-E0 à X-E7 (planification)
- **Agent / capacité** : orchestrateur seul ; sources primaires : fiche du modèle e5 à révision figée.

### Actions et résultats

1. PC : joignable, aucun dossier partagé ; `~/.claude` protégé → ECC non vérifiable (AGENT_ROUTING mis à jour).
2. Vérifié sur la fiche du modèle à révision figée : `intfloat/multilingual-e5-small` @ `614241f6…`, MIT, 12 couches, dim. 384, pooling moyen, préfixes « query: » / « passage: » obligatoires, 512 tokens max. `multilingual-e5-base` @ `d1287505…`, MIT.
3. `docs/EXPERIMENT_PROTOCOL.md` v1.0 (SHA-256 `1c595028aaa5c2ea5358eb8d5472a0e14b86850dbc17375f301bfd1f3dc4e5ce`) : H1–H5, B-SYN / B-REAL / B-PAWS, métrique principale nDCG@10, bootstrap par grappes, règles d'entraînement et d'accès au test.
4. **Gel du périmètre du test SUMM-RE** : `splits/summre_v1_test_meetings.txt`, 45 réunions, SHA-256 `ddd195673ac7a4f9be368df8b3513ef763b33909657afd659b31268557e2ded8`.
5. `eval/metrics.py` (nDCG, MRR, Recall, précision par paires, bootstrap par grappes) et `eval/test_access.py` (journal obligatoire). 44 tests verts.
6. Dépendance `tzdata` ajoutée pour Windows (zoneinfo), verrou régénéré.

### Erreur corrigée

L'exemple du doctest de nDCG annonçait 0,6045 (mon calcul manuel) ; la valeur exacte est 0,659. Le test unitaire, écrit à partir de la formule, était juste.

### Limites

- Les requêtes et pertinences de test n'existent pas encore : elles seront figées à leur création (EL-007b, EL-007c), avant toute évaluation.
- Ticket manquant ajouté : EL-007c (générateur B-SYN).

### Suite

EL-007c (générateur B-SYN) puis EL-007b (annotation B-REAL), puis E0 et E1.

### Complément S06 (2026-10-21T15:12+02:00)

- ECC vérifié : version 2.2.3 installée sur le PC (listing PowerShell de l'étudiant), définitions d'agents lues à la source amont (`affaan-m/ECC` @ `90606c8`, VERSION 2.2.3).
- ECC n'est pas invocable depuis la session cloud. Première délégation préparée : relecture indépendante du protocole et des splits par `mle-reviewer`, mandat `docs/mandates/EL-009-review.md`, à exécuter par l'étudiant. Statut : en attente.

---

## 2026-10-21 · Session S06 suite · Relecture EL-009 et protocole v1.1

- **Début** : 2026-10-21T15:22+02:00 (rapport transmis par l'étudiant) · **Fin** : voir l'horodatage du commit
- **Branche** : `el-009-protocol`
- **Agent / capacité** : `mle-reviewer` (ECC 2.2.3, exécuté par l'étudiant sur son PC, 3 min 25 s) comme relecteur ; orchestrateur pour la vérification et les corrections.

### Résultats de la relecture

0 bloquant dans le code des splits ; 3 corrections de protocole exigées avant gel ; 8 risques de gain illusoire. Détail et suites : `docs/reviews/EL-009-mle-reviewer.md`.

### Vérifications de l'orchestrateur

- 0 réunion sans locuteur dans les vraies données.
- B-REAL test : 8 composantes, dont **7** avec réunions manuelles (moins que les 12–15 de la simulation du relecteur) → H3 descriptive.

### Corrections

1. Code : refus des réunions sans locuteur ; refus des classements avec doublons ; `pairwise_win` (score par triplet) ; `paired_cluster_permutation_test` (exact jusqu'à 16 grappes). 49 tests verts.
2. Splits régénérés : empreinte inchangée `d6992f5d…`.
3. Sous-ensemble de relecture humaine tiré avant annotation : `splits/summre_v1_test_human_review.txt` (SHA-256 `7cc1bec7385708dca4a1144a977b1fb37e8b7bcfc191f4d381425fc71ac0c77b`).
4. Protocole v1.1 (SHA-256 `4dc2ec3a40950bfcce29a1394e77f36620a0b3aad53846a4fd980db35be97571`) : B-SYN 240/32/48 projets ; H3 descriptive ; pièges du test par construction ou annotation ; décision par permutation ; graines moyennées sans sélection ; comparateur H5 désigné sur val ; accès au test et isolation E1/E2 imposés par un point d'entrée commun (EL-010). Aucun accès au test n'avait eu lieu : changement non post hoc.

### Suite

EL-007c : générateur B-SYN selon le protocole v1.1.

---

## 2026-10-21 · Session S07 · EL-007c (B-SYN)

- **Début** : 2026-10-21T15:30+02:00 · **Fin** : voir l'horodatage du commit
- **Branche** : `el-007c-bsyn` (base `el-009-protocol` @ `ea08e61` ; le commit `76e2533` de l'étudiant, qui ajoute le rapport complet de relecture, n'est pas encore poussé)
- **Exigences couvertes** : D-02 à D-08, D-11, D-12 (cas difficiles construits), X-E1/E2/E3 (préparation)
- **Agent / capacité** : orchestrateur seul.

### Actions et résultats

1. Générateur `embedding_lab.synth` (patrons, scénarios, pièges par construction) + `scripts/make_bsyn.py` + 8 tests. 57 tests verts.
2. Bugs trouvés pendant la mise au point (sur le projet `bs-test-000`, voir DATA_CARD § 2 quater) : montant et date non substitués dans les phrases « validé » des scénarios S4/T3 ; accord « est déchargé ». Corrigés ; contrôle automatique ajouté (le montant des métadonnées doit apparaître dans le texte).
3. Défaut de conception corrigé : sans titre de réunion ni locuteur, le piège « autre projet » était indiscernable → `retrieval_text` ; protocole v1.2.
4. Génération : 320 projets, 2 529 unités, 2 638 requêtes, 3 961 triplets ; 0 contrat invalide ; 0 entité partagée ; 4-grammes test/train : unités 0 %, requêtes 1,8 %. Deuxième génération identique à l'octet près.

### Gel du test B-SYN (avant toute évaluation)

| Fichier | SHA-256 |
|---|---|
| `data/bsyn/test/queries.jsonl` | `7c669b293e017b569bc65d8a0015a3ab350776a74cf8b554ceff2fe319dd7c8e` |
| `data/bsyn/test/qrels.json` | `ecb0e5b06ef155ec39cefecd0e48e0d0af9b5cebecf2ac8de7189cb6bcac76e6` |
| `data/bsyn/test/triplets.jsonl` | `c48ba6a7c986b1071c58918fa82f648b90a70b0d3a292136d2e3eddc529cb37f` |
| `data/bsyn/test/units.jsonl` | `596ddafe559641e45a48c954c0bc1945e8a08119e76a07b5a8ddb912db7d9eff` |
| `data/bsyn/manifest.json` | `050f8e7d43861a0e81a968339b4816fd81bb25165cbf24f3e093448c3dcd7dae` |

### Suite

EL-007b (B-REAL : unités et requêtes SUMM-RE) puis EL-010 (point d'entrée commun d'évaluation + BM25).

### Correction S07

Le commit `15d31d0` contenait par erreur `data/bsyn/` (absent de `.gitignore`), en contradiction avec DATA_CARD. Les fichiers sont retirés du suivi par un nouveau commit (sans réécriture de l'historique : ils restent visibles dans `15d31d0`). Aucun risque de licence, ce sont des données fictives générées par notre code. `.gitignore` complété.

---

## 2026-10-21 · Session S07 suite · Rapport complet de relecture, protocole v1.3

- **Début** : 2026-10-21T15:40+02:00 · **Fin** : voir l'horodatage du commit
- **Branche** : `el-007c-bsyn` ; fusion de `el-009-protocol` @ `76e2533` (rapport complet poussé par l'étudiant) → commit de fusion `a6f0eec`.
- Dépôt renommé côté GitHub en `AbdGhni/EMBEDDING-LAB` : remote mis à jour dans la VM.

### Actions

1. Lecture intégrale de `docs/reviews/EL-009-mle-reviewer-full.md` (rapport sur l'état `088707a`).
2. Mesure demandée : 4-grammes des unités B-SYN train présents dans SUMM-RE test = 19 / 5 321 (0,36 %), dont des prénoms communs.
3. Protocole v1.3 (non post hoc) : garde-fou B-REAL val, règles de batch identiques E2/E3, dtype et empreinte de configuration d'évaluation, moyenne par grappe en contrôle, quatre limites ajoutées. Suites tracées dans `docs/reviews/EL-009-mle-reviewer.md`.

### Non vérifié

Tests sur le PC de l'étudiant (uv absent) ; la CI GitHub sous Windows reste la preuve d'exécution.

---

## 2026-10-21 · Session S08 · EL-007b (B-REAL), lancement

- **Début** : 2026-10-21T15:45+02:00 (message « go ») · **Fin** : en cours
- **Branche** : `el-007b-breal` (base `el-007c-bsyn` @ `15f0b16`)
- **Agent / capacité** : orchestrateur (outillage, contrôle qualité) ; sous-agents `general-purpose` (Claude, modèle effectif non vérifié) pour l'annotation, au plus 3 en parallèle, une tâche = un groupe, mandat `docs/mandates/EL-007b-annotation.md`. Motif : 19 groupes (~1,35 M caractères) à lire intégralement, tâches indépendantes et fichiers de sortie disjoints.

### Actions

1. Périmètre : groupes val (10) et test (9) contenant au moins une réunion manuelle : 57 réunions. Portée de recherche B-REAL = groupe (protocole v1.4).
2. Outillage : `ingest/breal.py` (tâche, validation, assemblage), `scripts/prepare_breal_tasks.py`, `scripts/check_breal_raw.py`, 4 tests (61 au total).
3. **Pilote** sur le groupe val 015 (6 min 53 s) : 101 unités, 28 relations, 8 requêtes, validateur OK. Contrôle par l'orchestrateur des 8 requêtes et de leurs pertinences : cohérentes ; q03 repose sur un accord hésitant (marqué `inferred`).
4. Huit remarques du pilote sur les consignes → mandat v2 et guide v0.2 : pas de statut `superseded` dans les unités, `supersedes` possible vers une proposition explicitement écartée, `creates_action` depuis une idée retenue, format de `owner` et `speaker_names`, champ `amount`, réponses possibles dans une autre réunion du groupe, pas de pièges pour les questions sans réponse. Validateur renforcé en conséquence.
5. Pilote relancé pour mettre 015 au format v2 ; annotation des groupes val 008 et 014 lancée.

### Avancement S08 (2026-10-21, jusqu'à 21:40+02:00)

- Val terminé : 10 groupes annotés et validés (008, 014, 015, 021, 025, 027, 051, 053, 093, 101). Assemblage `scripts/assemble_breal.py` : 1 255 unités, 89 requêtes dont 78 répondables, 262 triplets à piège.
- Écarts acceptés : 014 a 8 questions répondables (7 au plus prévues) ; plusieurs groupes dépassent 40 unités par réunion avant la consigne de plafond (008, 014, 015, 021).
- Données sensibles : plusieurs annotateurs ont volontairement écarté des informations de santé ou personnelles ; consigne ajoutée aux mandats suivants.
- **Interruption** : les tâches test 019, 024 et 033 ont été arrêtées vers 17 h par la limite d'usage de la session (HTTP 429, réinitialisation à 20 h). Reprises à 21:40 depuis leur contexte sauvegardé.

---

## 2026-10-21 · Session S08 fin · EL-007b : B-REAL complet et gel du test

- **Fin** : voir l'horodatage du commit
- **Agent / capacité** : 19 tâches d'annotation par sous-agents (pilote compris), contrôle de chaque fichier par l'orchestrateur (`check_breal_raw.py`) ; aucun fichier rejeté au contrôle final.

### Résultats

- Val : 10 groupes, 1 255 unités, 78 requêtes répondables, 262 triplets.
- Test : 9 groupes, 975 unités, 105 requêtes répondables (15 sans réponse), 303 triplets ; 7 grappes.
- Classeur de relecture (5 réunions tirées au sort, 197 unités, 35 requêtes répondables, 187 lignes de jugement) : `annotations/breal/review/relecture_v1.xlsx`.

### Gel du test B-REAL (avant toute évaluation)

| Fichier | SHA-256 |
|---|---|
| `data/breal/test/queries.jsonl` | `e099ccc2332a10172da8ed718d79af2c01a5e57abeb8189516a312030d7b0cb7` |
| `data/breal/test/qrels.json` | `7fe031a8ede3b1d4298b9294e9fb460699c9ff8a7388e9e0237e563dfb956a29` |
| `data/breal/test/triplets.jsonl` | `401a2b23ada81c39ae84d963636b76aa8cf4f9d36e8f5270348b566e8dc4de25` |
| `data/breal/test/units.jsonl` | `0f9dc0d7faf6f266b0ed0be979d39f46ede5d12a86751914549629baa80383b0` |

Les empreintes des 9 fichiers bruts de test sont dans `data/breal/manifest.json` (champ `raw_sha256`). Si la relecture humaine corrige des annotations de test, la version corrigée sera figée comme **v2**, avec ses propres empreintes, toujours avant toute évaluation ; la v1 reste consignée ici.

### Suite

Relecture par l'étudiant ; en parallèle, EL-010 (point d'entrée d'évaluation commun + BM25) sur val.

---

## 2026-10-22 · Session S09 · Relecture IA du sous-ensemble (lancement) et EL-010

- **Début** : 2026-10-22T11:24+02:00 (message « vas-y, fait aussi de ton côté la relecture ») · **Fin** : voir l'horodatage du commit
- **Branches** : `el-007b-breal` (mandat de relecture IA, `43874fd`) puis `el-010-eval-bm25`.
- **Agent / capacité** : relecteurs `general-purpose` **neufs** (aucun n'a produit l'annotation relue), une tâche par réunion, mandat `docs/mandates/EL-007b-relecture-ia.md`. Ce n'est pas une relecture humaine : étiquetée « relecture IA ». Orchestrateur pour EL-010.

### EL-010

1. `eval/harness.py` : point d'entrée unique ; refus du test sans motif (journal `runs/TEST_ACCESS.log`) ; portée de recherche B-SYN = split, B-REAL = groupe ; triplets notés avec les mêmes scores que le classement ; empreinte de configuration ; moyenne par grappe en contrôle ; manifeste (commit, état, versions, horaires).
2. `retrieval/bm25.py` (k1 = 1,5, b = 0,75, tokenisation SUMM-RE) et plancher `retrieval/baselines.py`. 6 tests ; 67 au total.
3. **Incident de provenance** : les deux premiers runs (11:27) indiquaient `git_dirty: false` alors que le code n'était pas commité (fichiers non suivis ignorés). Détection corrigée, code commité (`17606d0`), runs supprimés puis relancés avec les mêmes chiffres.
4. Résultats sur **val uniquement** : voir `docs/EXPERIMENTS.md`. BM25 : B-SYN nDCG@10 0,517, B-REAL 0,206 ; précision par paires proche du hasard sur les pièges `status` et `superseded`.

### Relecture IA du sous-ensemble et gel du test B-REAL v2 (S09, 2026-10-22)

- 5 relecteurs IA neufs, un par réunion du sous-ensemble ; tous les fichiers passent `check_breal_review.py`.
- **Écart de méthode** : entre 11:35 et 11:40 environ, 4 relecteurs ont tourné en même temps (036c, 047c, 069b, 097c), au-delà de la limite de 3 sous-agents simultanés fixée par le prompt. Tâches indépendantes, fichiers de sortie distincts : aucun conflit, mais la règle n'a pas été respectée.
- Accord avec l'annotation : unités 92,4 % (182/197), couples 86,3 % (157/182), 5 réponses oubliées. Biais dominant : pertinence 1 attribuée à des unités qui ne répondent pas.
- Arbitrage mécanique (erreurs explicites appliquées, douteux ignorés) : 27 corrections, 0 refusée ; 047c q12 retirée (plus aucune réponse directe).
- Classeur humain v2 avec colonnes « Avis IA » : `annotations/breal/review/relecture_v2.xlsx` (la v1 reste dans le dépôt).

| Test B-REAL v2 | SHA-256 |
|---|---|
| `data/breal/test/queries.jsonl` | `875f4de32c98f0301cc4bdfd29919d96f9e56499adb2ac54cf8dcc2e9fdf26fe` |
| `data/breal/test/qrels.json` | `66787fffe9eae9334c09e2c5aed08e417f8dab4504ceefabeff19a6c2b6178d0` |
| `data/breal/test/triplets.jsonl` | `08a52eb90565f042cb4cb525c42dfb18a6431fcfb345bc677bf1b5ba25775035` |
| `data/breal/test/units.jsonl` | `6206d6788df75f4ff9262c806ccc2882a750c3d034a7161a09f7b5e02e809093` |

Aucun accès au test à ce jour (`runs/TEST_ACCESS.log` absent).

---

## 2026-10-22 · Session S10 · Relecture humaine ciblée, annotation du train B-REAL

- **Début** : 2026-10-22T13:19+02:00 (message de l'étudiant avec le classeur rempli) · **Fin** : voir l'horodatage du commit
- **Branche** : `el-010-eval-bm25`

### Relecture humaine (étudiant)

- Fichier reçu archivé : `annotations/breal/review/humain/relecture_v2_etudiant.xlsx` (SHA-256 `41878b8b…ee75b7`).
- Portée réelle : les **43 lignes signalées par la relecture IA** (15 unités, 28 couples question–unité), toutes marquées « oui », sans commentaire. Les 182 unités et 153 couples jugés « ok » par l'IA n'ont pas été examinés.
- Lecture : sur ces points litigieux, l'étudiant confirme les corrections appliquées (lignes « erreur ») et l'annotation d'origine (lignes « douteux »). Aucune modification du test : la **v2 reste la version de référence**.
- Anomalies : une ligne « erreur » non remplie (047c q09/c-16, déjà corrigée en v2) ; un « oui » sur une ligne « ok » voisine (019a q05/a-17), probablement un décalage d'une ligne.
- À écrire dans le rapport : relecture humaine **ciblée** des désaccords, pas une relecture exhaustive ni un accord inter-annotateurs.

### Train B-REAL

Décision de l'étudiant (« oui vas-y ») : annoter les 38 groupes d'entraînement contenant une réunion manuelle (112 réunions), même mandat v2, 3 sous-agents simultanés au plus.

- Avancement au 2026-10-22T22:48+02:00 : 14/38 groupes validés et poussés (004 006 007 011 012 013 016 017 018 020 032 034 035 037).
- Interruption : les sous-agents de 039, 040 et 043 ont été arrêtés par la limite de session de l'API (HTTP 429, levée à 18:10 Europe/Paris) avant d'écrire leur fichier ; repris par message à 22:48 sur leur transcription sauvegardée.
- Reprise après la seconde limite d'usage (levée à 01:50) : 081, 084, 088 repris par message, puis 100 et 102.
- Fin de l'annotation du train : **38/38 groupes** validés (`check_breal_raw.py` OK), recomptés par script (unités, relations, requêtes, aucune relation vers une unité absente) et poussés un par un. Deux comptes rendus d'annotateurs contenaient des chiffres faux (044 : relation fantôme annoncée, 039 : identifiant de réunion mal recopié) ; fichiers vérifiés corrects. Consigne ajoutée à partir de 049 : recompter depuis le JSON final.
- Assemblage `assemble_breal.py --splits train` : 112 réunions, 4 135 unités, 372 requêtes (325 répondables), 1 174 triplets, qrels SHA-256 `51ee18c7…`. Val et test réassemblés à part : identiques octet pour octet aux versions figées.

## S11 · EL-012 · données d'entraînement avec B-REAL

- **Heure** : 2026-10-23T02:14+02:00 (fin de la passe ; début ≈ 02:00, réception du compte rendu 102)
- Bogue trouvé : `build_examples` lisait `q["cluster"]`, absent des requêtes B-REAL (`group_id`). Le test unitaire ne le voyait pas car sa fixture donnait un champ `cluster` aux deux sources. Correction (`query_cluster`, même définition que le harnais) + test de régression avec des requêtes au format B-REAL ; 73 tests verts.
- `build_training_data.py` : E2 7 343 exemples (B-SYN 6 222 + B-REAL 1 121 ; 278 grappes), SHA-256 `1cd42b9a…` ; E3 `dfefa76c…`. La part B-SYN est identique ligne à ligne à la version B-SYN seule. B-REAL : 471 des 475 couples positifs de pertinence 2 ont au moins un piège ; pas de minage e5 pour B-REAL (les unités non jugées du même groupe pourraient être de faux négatifs).
- Empreintes attendues : `splits/data_sha256.json` (27 fichiers).
- Test de fumée CPU (3 étapes, batch 8) sur les nouvelles données : étape 0 = E1 exactement (B-SYN 0,752 / B-REAL 0,293), chaîne complète OK. Les valeurs après 3 étapes ne sont pas un résultat.

## S12 · EL-013 / EL-014 · entraînements E2 et E3 sur Colab

- **Heure** : 11:52 (demande « fait le toi depuis chrome ») → 2026-10-23T12:57+02:00
- Pilotage de Colab dans le Chrome de l'étudiant (extension Claude in Chrome), notebook ouvert depuis GitHub (branche `el-012-013-training`, commit `50e4fbc`). GPU Tesla T4 15 Go.
- Autorisation Google Drive : accord de l'étudiant demandé et obtenu (12:2x) ; la fenêtre d'autorisation Google s'ouvrant hors de l'onglet piloté, l'étudiant l'a validée lui-même. Premier essai de montage expiré (« mount failed »), second réussi.
- Régénération des données sur Colab : `verify_data.py` → « OK : données identiques ». Diagnostic CUDA : `overfit_ok: true`, 0,32 s/étape au batch 64.
- 6 runs (E2/E3 × graines 13/42/1234) entre 12:34 et 12:50 ; la sauvegarde sur Drive (~1 min par checkpoint) domine la durée. Cellule ajoutée à la main dans la session Colab (non enregistrée dans le dépôt) pour copier `runs_e2_e3.zip` sur le Drive ; zip récupéré par le connecteur Google Drive, SHA-256 `a986ebe9…` identique à celui calculé dans Colab.
- Manifestes : commit `50e4fbc`, `git_dirty: false`. Aucun `TEST_ACCESS.log`.
- Nouveau : `eval/compare.py` + `scripts/compare_runs.py` (moyenne des graines par requête ; grappes B-REAL = composantes de personnes comme le prévoit le protocole, alors que le harnais regroupe par groupe pour son indicateur de contrôle — écart relevé, sans effet sur les métriques par requête). 77 tests verts.
- Résultats de validation et lecture : `docs/EXPERIMENTS.md` (E2 et E3). Point saillant : E2 ≈ E3 en nDCG@10, mais E2 ≫ E3 sur les pièges « superseded » de B-SYN (0,88 contre 0,32).

## S13 · EL-013 · ablation E2S (B-SYN seul)

- **Heure** : 13:01 (« vasy ») → 13:12
- Variante `e2s` (exemples B-SYN seuls, identiques octet pour octet à la version d'hier `23596325…`), section ajoutée au notebook, protocole v1.5 (ablation déclarée exploratoire, décidée après lecture de la validation). Commit `569b83c`.
- Colab : la mise à jour du dépôt a d'abord échoué (runs non suivis de la session précédente) ; anciens runs déplacés dans `/content/runs_session1` de la session Colab, puis `verify_data.py` OK et entraînement (84 s).
- Zip récupéré via le connecteur Google Drive, SHA-256 `cdd99416…` identique à Colab. Manifeste : commit `569b83c`, propre.
- Résultat (val) : E2S B-REAL 0,307 contre 0,293 (E1) et 0,507 (E2) → le gain réel vient des données B-REAL d'entraînement. Détails : `docs/EXPERIMENTS.md`.

## S14 · EL-015 · module de relations

- **Heure** : 13:13 (« vasy continue ») → 13:25
- Branche `el-015-relations` (depuis `el-012-013-training`). Protocole v1.6 (§ 10) écrit et commité **avant** toute mesure (`3d55b95`), puis précisé avant mesure (R1 = table des types ; statuts exclus des variables car `resolved` découle de la relation ; classes pondérées) dans `3c30c0b`.
- Code : `relations/{pairs,features,models,metrics}.py`, `scripts/train_relations.py`, tests (83 verts).
- Run `R-val-2026-10-23T1316` (4 min CPU) : R2 meilleur (B-REAL val macro-F1 0,648) ; R3 (plongements gelés) moins bon que R2 ; B-SYN trivial (R1 = 1,0). Lecture dans `docs/EXPERIMENTS.md`.
