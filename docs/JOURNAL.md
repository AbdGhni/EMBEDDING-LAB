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
