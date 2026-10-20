# Décisions

Format : ID · date · décision · justification · alternatives · statut.

## D-001 · 2026-10-20 · Initialisation de `main` par un commit minimal

- **Décision** : le dépôt distant étant vide, un premier commit sur `main` contient seulement `README.md`, `.gitignore` et la copie fidèle du sujet. Le travail suivant passe par des branches `el-xxx-*`.
- **Justification** : une branche de base est nécessaire pour ouvrir des PR ; rien n'est écrasé.
- **Statut** : appliquée (commit `825fa57`).

## D-002 · 2026-10-20 · Agent déterministe, sorties extractives par défaut

- **Décision** : pipeline Python modulaire explicite ; réponses et dossiers produits par gabarits extractifs ; un LLM de reformulation reste une extension facultative.
- **Justification** : le sujet exige d'évaluer séparément retrieval, relations et routage ; un LLM ne doit pas masquer les erreurs du moteur.
- **Statut** : proposée, à valider par l'étudiant.

## D-003 · 2026-10-20 · Entraînement hors de la VM cloud

- **Décision** : la VM cloud (2 vCPU, sans GPU) sert au code, aux tests et aux baselines légères ; le fine-tuning E2/E3 s'exécutera sur une machine dotée d'un GPU, à déterminer.
- **Statut** : en attente des caractéristiques du PC et de l'autorisation éventuelle d'un service gratuit/payant.

## Questions ouvertes (EL-002)

1. Échéance exacte et temps disponible par semaine.
2. Langue cible des données : français, anglais, ou bilingue.
3. GPU disponible sur ton PC (modèle, VRAM) ; autorisation d'utiliser Colab/Kaggle gratuits ; budget éventuel pour du calcul payant.
4. Règles de l'école sur l'usage de l'IA dans le projet individuel.
