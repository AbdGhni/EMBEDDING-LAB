# Préparation du point avec Martial Roberge (jeudi 5 novembre 2026, proposé)

État vérifié le 2026-10-30 : `main` = `el-019-intents` = `56a7442`, poussé ; 94 tests verts, ruff propre ; clone neuf + `uv sync --locked --extra dev --extra ml` + `scripts/run_scenarios.py` (E1) : 8 scénarios sur 9 réussis (`runs/SCN-E1-2026-10-30T1138`), comme le 23 octobre. Le scénario 2 échoue (voir §3).

## 1. Trame du point (20 à 25 minutes)

1. **Problème et question** (2 min) : un encodeur qui aide un agent à savoir ce qui a été décidé, par qui, et ce qui est encore valable. Une proximité vectorielle ne prouve pas la compatibilité logique.
2. **Données et splits** (3 min) : SUMM-RE, découpage par groupes de personnes (les splits officiels partagent 30 groupes entre train et test), B-SYN et B-REAL, annotateur IA unique déclaré.
3. **Méthode** (3 min) : e5-small, perte contrastive MNRL, négatif difficile explicite contre négatifs aléatoires, 3 graines, test gelé évalué une seule fois.
4. **Résultats** (4 min) : nDCG@10 B-REAL 0,333 → 0,563 ; B-SYN 0,841 → 0,903 ; décision à jour 0,54 contre 0,15 avec négatifs aléatoires ; H5 (hybride) non soutenue ; ablation E2S : le gain réel vient des exemples réels.
5. **Démo** (6 min) : `docs/DEMO.md`, questions 1, 3, 4, 5, 6, 7 puis l'échec connu (question 2).
6. **Limites et suite** (4 min) : voir §3 et §4.
7. **Questions** : `docs/LEARNING_GUIDE.md`, fin de document (10 questions probables).

## 2. Ce que j'ai à montrer, par exigence du sujet

| Démo attendue par le sujet | État |
|---|---|
| Décision précise avec preuve | OK (scénario 1) |
| Question ambiguë opposant proposition et décision | **Échec** (scénario 2) |
| Comparaison de deux réunions | OK (3) |
| Dossier multi-sources traçable | OK (4) |
| E-mail à la bonne personne, justifié | OK (5) |
| Précision demandée plutôt qu'un choix arbitraire | OK (6) |
| Phrase hypothétique sans action | OK (7) |
| « Charger plusieurs conversations », démo « reproductible sur plusieurs conversations » | **Partiel** : une seule mémoire de démonstration (Atlas, 3 réunions) |

## 3. Écarts que Martial peut relever

1. **Le scénario 2 est un cas demandé par le sujet.** L'échec vient du classifieur d'intentions (« augmentation » lu comme `compare`). Il n'a pas été corrigé pour ne pas régler le système sur la démo. Pour une démo « valide », il faut le corriger proprement, avec un résultat étiqueté **post hoc**, vérifié sur des requêtes qui ne servent ni à l'entraînement ni à la démo.
2. **Une seule mémoire de démonstration.** Le sujet attend plusieurs conversations. À faire : une seconde mémoire (autre projet fictif ou réunions SUMM-RE réelles) chargeable par `agent_cli.py`.
3. **Pas de reranker ni de filtre temporel ou par type**, alors que la semaine 2 du sujet demande de les étudier. Écart déclaré dans le rapport.
4. **M-05 (destinataires) et M-06 (dossiers) non mesurées** sur un jeu dédié ; seulement des contrôles de scénarios.
5. **Relectures indépendantes (ECC)** non faites : `docs/mandates/EL-025-review.md`, à lancer sur le PC.
6. **Poids E2** uniquement sur le Drive de l'étudiant ; la démo avec l'encodeur fine-tuné n'a pas été rejouée sur une machine propre (rejouée sur la VM le 23 octobre : `runs/SCN-E2-*`). Cette vérification est à faire sur le PC avant le point.

## 4. Prochaines étapes proposées (par priorité)

| # | Étape | Pourquoi | Effort | Décision à prendre |
|---|---|---|---|---|
| 1 | Rejouer la démo sur le PC avec les poids E2 (`docs/DEMO.md`) | démo prouvée sur la machine de l'étudiant | 30 min | aucune |
| 2 | Lancer les trois relectures ECC (mandat prêt) et corriger ce qui est signalé | exigence du protocole, regard indépendant | 1 à 2 h | aucune |
| 3 | Écrire 40 à 60 requêtes d'intentions soi-même (troisième jeu, indépendant de Claude), puis évaluer I0, I1, I2 dessus | seul jeu non écrit par l'auteur du système ; départage les règles et I2 | 1 à 2 h | oui, voir ci-dessous |
| 4 | Corriger les intentions (règles + I2 en secours, ou I0 seul) et rejouer les 9 scénarios, étiqueté post hoc | rend le scénario 2 réussi sans tricher | 2 h | choisir la stratégie |
| 5 | Deuxième mémoire de démonstration (plusieurs conversations) | exigence du sujet | 2 à 3 h | fictif ou SUMM-RE réel |
| 6 | Mesures M-05 / M-06 sur un petit jeu dédié (destinataires, couverture des dossiers) | métriques du sujet manquantes | 3 h | taille du jeu |
| 7 | Reranking ou filtre temporel (étude courte) | semaine 2 du sujet | 3 à 4 h | à demander au mentor |
| 8 | Relecture humaine d'un échantillon des annotations B-REAL train/val | réduit le risque d'annotateur IA unique | variable | à demander au mentor |

## 5. Questions à poser à Martial

1. Pour la démo, préfère-t-il voir un seul échec expliqué (scénario 2) ou un système corrigé et marqué post hoc ?
2. Faut-il une seconde mémoire de démonstration fictive ou des réunions SUMM-RE réelles ?
3. Le reranking est-il attendu pour la validation ou reste-t-il optionnel ?
4. Quel niveau de relecture humaine des annotations B-REAL juge-t-il suffisant ?
5. Le rendu final : date, format du rapport et de la démonstration.

## 6. Règles à garder pendant la préparation

- Le test a été évalué une seule fois (23 octobre) ; aucune nouvelle évaluation du test. Toute amélioration est mesurée sur de nouvelles données et marquée post hoc.
- Ne rien annoncer sans run ou fichier : citer `docs/EXPERIMENTS.md` et `docs/FINAL_REPORT.md`.
- Dire clairement ce qui a été produit par Claude (code, annotations) et ce que l'étudiant a décidé et contrôlé.
