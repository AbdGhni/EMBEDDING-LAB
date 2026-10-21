# Routage des agents et capacités

Dernière vérification : 2026-10-20T21:45+02:00 (Europe/Paris).

## Constat d'environnement

| Élément | Constat | Comment vérifié |
|---|---|---|
| Session de travail actuelle | VM cloud Linux, Python 3.13.16, Git 2.43, 2 vCPU, 7,8 Gio RAM, **pas de GPU** | `uname`, `nproc`, `free`, `nvidia-smi` absent |
| Modèle orchestrateur | Opus 5.5 (`claude-opus-5-5`) | déclaré par l'environnement d'exécution |
| Modèle des sous-agents | **non vérifié** (hérite de l'orchestrateur sauf surcharge) | description de l'outil Agent |
| Plugin ECC (affaan-m/ECC) | **absent de cette VM** | aucun fichier ECC dans `~/.claude/plugins` |
| ECC sur le PC Windows | **installé, version 2.2.3** ; invocable seulement depuis Claude Code sur le PC | listing PowerShell de l'étudiant (2026-10-21) |
| Accès GitHub | push sur `AbdGhni/embedding-lab` fonctionnel ; `gh` CLI non authentifié (pas d'ouverture de PR en ligne de commande) | push réussi de `main` ; `gh auth status` |

Mise à jour 2026-10-21T15:07+02:00 : session ouverte depuis le PC. Le PC est joignable, mais aucun dossier n'est partagé et le dossier `~/.claude` (où vivent les plugins) est un dossier Claude protégé, invisible depuis cette session cloud. ECC reste **non vérifié**.

Conséquence : tant qu'ECC n'est pas visible, aucune délégation n'est attribuée à un agent ECC. Si tu travailles depuis Claude Code sous Windows avec ECC, ce document devra être complété là-bas avec les noms exacts listés par l'installation.

## ECC sur le PC (vérifié le 2026-10-21T15:12+02:00)

Preuve : listing PowerShell fourni par l'étudiant (`C:\Users\abdul\.claude\plugins\cache\ecc\ecc\2.2.3`) et lecture des définitions d'agents à la source amont (`affaan-m/ECC`, fichier `VERSION` = 2.2.3, commit `90606c8`).

**ECC n'est invocable que dans Claude Code sur le PC**, pas depuis cette session cloud. Une délégation ECC signifie donc : l'étudiant lance l'agent sur sa machine avec le mandat écrit dans `docs/mandates/`, puis colle ou commite le rapport. Aucun rapport ECC n'est inventé ici.

| Agent ECC 2.2.3 | Description (source) | Outils déclarés | Modèle déclaré | Usage prévu | Exclusion |
|---|---|---|---|---|---|
| `mle-reviewer` | revue ML : contrats de données, reproductibilité, évaluation offline | Read, Grep, Glob, Bash | sonnet (déclaré, effectif non vérifié) | protocole, splits, fuites, runs E2/E3, rapport final | ne pas l'utiliser pour du style de code |
| `rag-pipeline-reviewer` | revue RAG : qualité du retrieval, chunking, embeddings, couverture d'évaluation | Read, Grep, Glob, Bash | sonnet (déclaré) | E0/E1/E4, B-REAL, mémoire et retrieval de l'agent | pas d'avis sur l'entraînement |
| `python-reviewer` | revue Python (idiomes, typage, sécurité) | Read, Grep, Glob, Bash | sonnet (déclaré) | revue des lots de code avant fusion | — |
| `security-reviewer` | secrets, injections, OWASP | Read, Grep, Glob, Bash | sonnet (déclaré) | outils simulés, injection dans les transcriptions (C-07) | — |
| `silent-failure-hunter` | erreurs avalées, replis silencieux | Read, Grep, Glob, Bash | sonnet (déclaré) | pipeline de données et d'évaluation | — |
| `planner` | planification | Read, Grep, Glob | opus (déclaré) | non utilisé : le plan existe déjà | — |
| `tdd-guide` | écriture des tests d'abord | Read, Write, Edit, Bash, Grep | sonnet (déclaré) | non utilisé : il écrit dans le dépôt, risque de modifications concurrentes | — |

Règle : les agents de revue ECC servent de **relecteur distinct de l'auteur** (l'orchestrateur), comme exigé pour les jalons scientifiques.

## Capacités réellement disponibles dans cette session

| Capacité | Provenance | Usage prévu | Exclusions | Modèle |
|---|---|---|---|---|
| Orchestrateur (cette conversation) | Claude, session cloud | intégration, code, explications, décisions | — | Opus 5.5 |
| `Plan` (agent) | intégré à l'environnement | plans d'implémentation de modules (S3) | pas d'édition de fichiers | non vérifié |
| `Explore` (agent) | intégré | recherche dans un code devenu volumineux | inutile tant que le dépôt est petit | non vérifié |
| `general-purpose` (agent) | intégré | relecture indépendante des résultats et des fuites de données | jamais l'auteur du travail relu | non vérifié |
| skill `engineering:code-review` | plugin engineering | revue de code avant fusion | — | — |
| skill `engineering:testing-strategy` | plugin engineering | conception des tests (EL-005, EL-023) | — | — |
| skill `engineering:debug` | plugin engineering | dépannage structuré | — | — |
| skill `data:statistical-analysis` | plugin data | intervalles de confiance, tests appariés (bootstrap par groupe) | — | — |
| skill `data:validate-data` | plugin data | contrôle des splits et des analyses | — | — |

Aucun spécialiste ML dédié n'est disponible : l'orchestrateur assume la revue scientifique en s'appuyant sur les sources primaires (articles, documentation des modèles et des bibliothèques), et une relecture par un agent distinct est demandée pour les jalons E2/E3 et le rapport final.

## Règles de délégation

- Au plus trois sous-agents simultanés, uniquement sur des tâches indépendantes et des fichiers disjoints.
- Chaque mandat précise : objectif, contexte minimal, fichiers autorisés, livrable, critères d'acceptation, dépendances.
- Chaque délégation est inscrite dans `JOURNAL.md` avec son motif et le résultat réellement reçu.
- Aucune délégation pour un changement trivial.

## Journal des délégations

| Date | Ticket | Agent | Mandat | Résultat |
|---|---|---|---|---|
| 2026-10-21 | EL-008/EL-009 | `mle-reviewer` (ECC, PC de l'étudiant) | `docs/mandates/EL-009-review.md` | en attente d'exécution par l'étudiant |
