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
