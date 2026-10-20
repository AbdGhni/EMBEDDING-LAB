# Routage des agents et capacités

Dernière vérification : 2026-10-20T21:45+02:00 (Europe/Paris).

## Constat d'environnement

| Élément | Constat | Comment vérifié |
|---|---|---|
| Session de travail actuelle | VM cloud Linux, Python 3.13.16, Git 2.43, 2 vCPU, 7,8 Gio RAM, **pas de GPU** | `uname`, `nproc`, `free`, `nvidia-smi` absent |
| Modèle orchestrateur | Opus 5.5 (`claude-opus-5-5`) | déclaré par l'environnement d'exécution |
| Modèle des sous-agents | **non vérifié** (hérite de l'orchestrateur sauf surcharge) | description de l'outil Agent |
| Plugin ECC (affaan-m/ECC) | **absent de cette VM** | aucun fichier ECC dans `~/.claude/plugins` |
| ECC sur le PC Windows | **non vérifié** : PC relié mais aucun dossier partagé, pas de shell distant | `get_device_info` |
| Accès GitHub | push sur `AbdGhni/embedding-lab` fonctionnel ; `gh` CLI non authentifié (pas d'ouverture de PR en ligne de commande) | push réussi de `main` ; `gh auth status` |

Conséquence : tant qu'ECC n'est pas visible, aucune délégation n'est attribuée à un agent ECC. Si tu travailles depuis Claude Code sous Windows avec ECC, ce document devra être complété là-bas avec les noms exacts listés par l'installation.

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
| — | — | — | aucune délégation à ce jour | — |
