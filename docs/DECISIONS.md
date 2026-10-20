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

Réponses de l'étudiant reçues le 2026-10-20T22:01+02:00 → D-004 à D-007.

## D-004 · 2026-10-20 · Données en français

- **Décision** : corpus, requêtes et démo en français ; identifiants de code en anglais.
- **Conséquence** : AMI, ICSI, QMSum et MeetingBank sont écartés comme corpus principal ; un encodeur multilingue est nécessaire.
- **Statut** : validée par l'étudiant.

## D-005 · 2026-10-20 · Calcul d'entraînement sur Google Colab

- **Décision** : E2/E3 (et l'éventuel cross-encoder) s'exécutent sur Google Colab ; la VM cloud sert au code, aux tests et aux baselines.
- **Conséquences** : notebooks fins qui appellent le paquet du dépôt ; commit et révision du modèle enregistrés dans chaque run ; checkpoints sauvegardés sur le Drive de l'étudiant, avec empreinte dans `runs/<id>/manifest.json`. GPU et durée de session Colab non garantis : runs courts et reprenables.
- **Remplace** : D-003 (en attente) → appliquée sous cette forme.
- **Statut** : validée par l'étudiant. Type de GPU obtenu : à relever au premier run.

## D-006 · 2026-10-20 · Échéance « le plus vite possible »

- **Décision** : pas de date imposée ; on garde le plan en 15 jours comme borne haute et on enchaîne les tickets sans attente. Les expériences E5–E7 restent conditionnelles.
- **Statut** : validée.

## D-007 · 2026-10-20 · Usage de l'IA

- **Constat** : l'étudiant indique qu'aucune règle de l'école ne restreint l'assistance IA.
- **Décision** : l'assistance reste documentée honnêtement (journal, routage). Les annotations produites par LLM sont marquées provisoires ; seul l'étudiant peut valider l'échantillon de contrôle manuel.
- **Statut** : appliquée.

## D-008 · 2026-10-20 · Corpus principal SUMM-RE, re-split par groupe d'expérience

- **Décision proposée** : SUMM-RE (FR, CC BY-SA 4.0, révision `47cb4ec`) comme corpus réel ; test = réunions transcrites à la main, groupes d'expérience entiers non vus ; entraînement = synthétique contrôlé + groupes d'entraînement SUMM-RE ; PAWS-X fr en complément.
- **Justification** : seul candidat français vérifié qui contient de vraies réunions de décision et de planification. Les splits officiels partagent 30 groupes d'expérience entre train et test (fuite).
- **Alternatives** : FREDSum (débats, peu d'actions) ; benchmark 100 % synthétique (refusé : il mesurerait la reconnaissance de nos propres patrons).
- **Statut** : validée le 2026-10-20T22:42+02:00 (réponse « Faut le mieux », interprétée comme acceptation de l'option recommandée ; à corriger si ce n'était pas l'intention).
