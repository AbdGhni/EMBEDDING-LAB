# Fiche du modèle — E2 (e5-small fine-tuné, EMBEDDING LAB)

- **Base** : `intfloat/multilingual-e5-small`, révision `614241f622f53c4eeff9890bdc4f31cfecc418b3` (licence MIT), 384 dimensions.
- **Variantes** : 3 graines (13, 42, 1234) ; runs `E2-e5s-s{13,42,1234}-bs64-lr2e-05-2026-10-23T12xx`. Poids sur le Drive de l'étudiant (`MyDrive/embedding_lab_checkpoints/<run>/best`), empreinte SHA-256 dans `runs/<run>/train_summary.json`. Non publiés dans Git.
- **Usage prévu** : recherche d'unités de réunion en français (décisions, engagements, questions…) à partir d'une question, dans une mémoire d'agent. Entrées : « query: … » et « passage: … », 128 jetons au plus, normalisation L2, cosinus.
- **Usage non prévu** : décider seul qu'une information est valide, contradictoire ou remplacée (utiliser un module de relations) ; autres langues ou domaines sans nouvelle évaluation.
- **Entraînement** : MNRL avec négatif difficile explicite, 7 343 exemples (B-SYN train 6 222, B-REAL train 1 121), lr 2e-5, batch 64, ≤ 3 epochs, sélection sur B-SYN val. Données B-REAL dérivées de SUMM-RE (CC BY-SA 4.0) : les exemples d'entraînement (`data/train/`) sont diffusés sous la même licence.
- **Évaluation (test, moyenne des 3 graines)** : B-SYN nDCG@10 0,903 (E1 : 0,841) ; B-REAL nDCG@10 0,563 (E1 : 0,333) ; préférence pour la décision à jour sur B-SYN 0,54 (E1 : 0,29). Détails : `docs/EXPERIMENTS.md`.
- **Limites** : annotations d'entraînement et de test produites par une IA ; gain sur l'oral réel dépendant des exemples réels d'entraînement (ablation E2S) ; reconnaît mal l'information remplacée une fois sur deux ; corpus de préentraînement d'e5 non audité.
- **Risques** : une recherche plus convaincante peut donner une fausse assurance ; l'agent du projet cite toujours ses sources et ne fait que proposer des actions.
