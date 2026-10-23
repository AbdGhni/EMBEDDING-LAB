# Résultats expérimentaux

Toutes les mesures passent par `embedding_lab.eval.harness` (point d'entrée unique). Chaque ligne renvoie à un dossier `runs/<run_id>/` (configuration, manifeste avec commit et empreintes, métriques, scores par requête, gains par triplet).

**Aucune mesure sur un split de test à ce stade** (`runs/TEST_ACCESS.log` absent).

## E0 — BM25 et plancher aléatoire (validation)

Runs : `E0-bm25-val-2026-10-22T1127`, `E0r-random-val-2026-10-22T1127` (commit `17606d0`, propre).

| Benchmark (val) | Système | nDCG@10 | MRR@10 | R@1 | R@10 | Précision par paires | Requêtes / grappes / triplets |
|---|---|---|---|---|---|---|---|
| B-SYN | aléatoire | 0,018 | 0,028 | 0,004 | 0,034 | 0,545 | 160 / 32 / 235 |
| B-SYN | BM25 | **0,517** | 0,523 | 0,292 | 0,560 | 0,723 | 160 / 32 / 235 |
| B-REAL | aléatoire | 0,047 | 0,053 | 0,000 | 0,080 | 0,428 | 78 / 10 / 262 |
| B-REAL | BM25 | **0,206** | 0,355 | 0,069 | 0,284 | 0,479 | 78 / 10 / 262 |

Précision par paires de BM25, par type de piège (n entre parenthèses) :

| Piège | B-SYN val | B-REAL val |
|---|---|---|
| status | 0,48 (54) | 0,42 (31) |
| superseded | 0,44 (25) | 0,49 (45) |
| negation | 0,77 (22) | 0,63 (8) |
| person | 0,75 (16) | 0,47 (52) |
| date | 1,00 (32) | 0,33 (12) |
| condition | 1,00 (6) | — |
| amount | — | 0,58 (12) |
| topic_only | 0,83 (80) | 0,49 (102) |

### Lecture

- BM25 est **au hasard (≈ 0,5) sur les pièges de statut et de remplacement** : une proposition et une décision sur le même objet partagent presque tous leurs mots. C'est précisément le défaut que le fine-tuning doit corriger (H2).
- Sur B-SYN, BM25 gagne sur `topic_only` et `date` grâce au nom de projet et au type de phrase : ces pièges sont faciles lexicalement dans notre générateur, ce qui confirme la limite déclarée de B-SYN.
- Sur B-REAL, BM25 reste faible (nDCG@10 = 0,21) : requêtes reformulées, oral bruité, vocabulaire peu partagé entre question et preuve. La précision par paires y est inférieure à 0,5 : les pièges réels partagent souvent davantage de mots avec la question que la vraie réponse.
- Le plancher aléatoire de B-REAL (0,43) s'écarte de 0,5 : ses 262 triplets ne sont pas indépendants (un même positif apparaît dans plusieurs triplets). C'est du bruit d'échantillonnage, pas un signal.
- Ces chiffres de validation servent de repère ; ils ne sont pas les résultats confirmatoires (test, protocole § 7).

## E1 — e5-small sans adaptation (validation)

Run : `E1-e5-small-val-2026-10-22T1130` (commit `1720d6b`, propre). `intfloat/multilingual-e5-small` @ `614241f6…`, fp32, CPU (2 vCPU), 128 tokens (0 passage tronqué), préfixes « query: » / « passage: ». Durée totale : 44 s pour les deux benchmarks.

| Benchmark (val) | Système | nDCG@10 | MRR@10 | R@1 | R@10 | Précision par paires |
|---|---|---|---|---|---|---|
| B-SYN | BM25 | 0,517 | 0,523 | 0,292 | 0,560 | 0,723 |
| B-SYN | e5-small | **0,752** | 0,712 | 0,335 | **0,969** | 0,600 |
| B-REAL | BM25 | 0,206 | 0,355 | 0,069 | 0,284 | 0,479 |
| B-REAL | e5-small | **0,293** | 0,466 | 0,138 | 0,335 | 0,588 |

Précision par paires d'e5-small, par type de piège :

| Piège | B-SYN val | B-REAL val |
|---|---|---|
| status | **0,24** (54) | 0,42 (31) |
| superseded | **0,04** (25) | 0,49 (45) |
| negation | 0,73 (22) | 0,75 (8) |
| person | 0,50 (16) | 0,62 (52) |
| date | 1,00 (32) | 0,33 (12) |
| condition | 0,83 (6) | — |
| amount | — | 0,75 (12) |
| topic_only | 0,83 (80) | 0,67 (102) |

### Lecture

- L'encodeur générique retrouve le bon **sujet** (R@10 = 0,97 sur B-SYN), mais classe mal **l'état** de l'information : R@1 = 0,34.
- Sur B-SYN, il est **nettement en dessous du hasard** sur `status` (0,24) et `superseded` (0,04) : il préfère systématiquement la proposition à la validation, et l'ancienne décision à celle qui la remplace. Explication probable, à vérifier sur des exemples : la formulation de la question (« quelle date a été retenue », « quel budget validé ») ressemble davantage aux phrases d'annonce initiales qu'aux phrases de correction (« finalement… au lieu de… »).
- Sur B-REAL, e5 améliore BM25 (nDCG@10 0,29 contre 0,21) mais reste au hasard sur `status` et `superseded`.
- Conséquence pour E2 : le gain attendu se situe d'abord dans le **réordonnancement** des candidats (R@1, pièges), pas dans le rappel.
- Ce sont des mesures de validation, sans intervalle de confiance : elles orientent la conception de E2 et ne valident aucune hypothèse.

## E2 et E3 — fine-tuning contrastif (validation)

Runs (Colab, Tesla T4, commit `50e4fbc`, propre ; exemples `1cd42b9a…` pour E2, `dfefa76c…` pour E3 ; 7 343 exemples, batch 64, lr 2e-5, ≤ 3 epochs, 348–350 étapes, ~2 min d'entraînement par run) :
`E2-e5s-s{13,42,1234}-bs64-lr2e-05-2026-10-23T12xx`, `E3-e5s-s{13,42,1234}-…`. Poids sur le Drive de l'étudiant (`MyDrive/embedding_lab_checkpoints/<run_id>/best`, empreinte dans `train_summary.json`). Diagnostic GPU : `DIAG-e2-cuda-2026-10-23T1234` (perte initiale 1,50 contre 2,77 au hasard, sur-apprentissage d'un mini-lot OK, 0,32 s/étape).

Comparaison : `runs/CMP-val-2026-10-23T1256/comparison.json` (`scripts/compare_runs.py`). Scores moyennés **requête par requête sur les 3 graines**, aucune graine choisie. Grappes : 32 projets (B-SYN), 7 composantes de personnes (B-REAL ; p minimale atteignable 2/128 = 0,016).

| Système (val) | B-SYN nDCG@10 | B-SYN R@1 | B-SYN paires | B-REAL nDCG@10 | B-REAL R@1 | B-REAL paires |
|---|---|---|---|---|---|---|
| E0 BM25 | 0,517 | 0,292 | 0,723 | 0,206 | 0,069 | 0,479 |
| E1 e5-small | 0,752 | 0,335 | 0,600 | 0,293 | 0,138 | 0,588 |
| E2 (négatifs difficiles) | **0,890** (é.-t. graines 0,012) | **0,587** | **0,864** | 0,511 (0,007) | 0,174 | **0,751** |
| E3 (négatifs aléatoires) | 0,893 (0,003) | 0,535 | 0,803 | 0,517 (0,004) | 0,173 | 0,723 |

| Différence (val) | Mesure | B-SYN Δ [IC 95 %] p | B-REAL Δ [IC 95 %] p |
|---|---|---|---|
| E2 − E1 | nDCG@10 | +0,138 [+0,108 ; +0,169] p < 0,001 | +0,219 [+0,171 ; +0,280] p = 0,016 |
| E2 − E1 | paires | +0,264 [+0,222 ; +0,307] p < 0,001 | +0,163 [+0,051 ; +0,251] p = 0,094 |
| E2 − E3 | nDCG@10 | −0,003 [−0,025 ; +0,021] p = 0,81 | −0,006 [−0,029 ; +0,014] p = 0,63 |
| E2 − E3 | paires | +0,061 [+0,023 ; +0,103] p = 0,006 | +0,028 [−0,007 ; +0,055] p = 0,25 |

Précision par paires par type de piège (moyenne des 3 graines) :

| Piège | E1 B-SYN | E2 B-SYN | E3 B-SYN | E1 B-REAL | E2 B-REAL | E3 B-REAL |
|---|---|---|---|---|---|---|
| superseded | 0,04 | **0,88** | 0,32 | 0,49 | 0,73 | 0,70 |
| status | 0,24 | 0,59 | 0,52 | 0,42 | 0,68 | 0,56 |
| person | 0,50 | 0,96 | 1,00 | 0,62 | 0,75 | 0,71 |
| negation | 0,73 | 0,98 | 0,98 | 0,75 | 0,83 | 0,83 |
| topic_only | 0,83 | 0,94 | 0,96 | 0,67 | 0,81 | 0,80 |
| date | 1,00 | 1,00 | 1,00 | 0,33 | 0,39 | 0,42 |
| condition / amount | 0,83 | 0,78 | 0,94 | 0,75 | 0,83 | 0,92 |

### Lecture

- **Le fine-tuning marche, et fort** : sur la validation, E2 dépasse E1 de +0,14 nDCG@10 sur B-SYN et de +0,22 sur B-REAL ; R@1 sur B-SYN passe de 0,34 à 0,59. Les trois graines sont proches (écart-type ≤ 0,012).
- **Les négatifs difficiles ne changent pas le classement global** (E2 ≈ E3 en nDCG@10 sur les deux benchmarks), **mais ils changent ce qui est appris sur les pièges** : sur B-SYN, la préférence pour la décision qui remplace l'ancienne passe de 0,04 (E1) à 0,88 avec E2, contre 0,32 avec E3. C'est l'effet visé ; il est net sur B-SYN (p = 0,006 sur l'ensemble des paires), plus faible et non significatif sur B-REAL (+0,03, 7 grappes).
- **Le gain sur B-REAL est acquis très tôt** (≈ 0,50 dès l'étape 100, puis plateau) et il est identique pour E2 et E3. Il ne vient donc pas des pièges. Hypothèses concurrentes, non départagées à ce stade : adaptation au format des passages (« Réunion r/3 — locuteur id : … ») et à l'oral, style des questions écrites par le même annotateur IA en train et en val, thèmes de scénario SUMM-RE partagés entre splits (limite déclarée au protocole). Une ablation « B-SYN seul » (une graine, val seulement) permettrait d'isoler l'apport des données réelles.
- **Garde-fou B-REAL** : aucune chute de B-REAL val pendant l'entraînement (0,50–0,52 de l'étape 100 à la fin) ; pas de sur-spécialisation visible sur le générateur.
- **Entraînement court** : plusieurs runs ont leur meilleur point à la dernière étape (plafond de 3 epochs du protocole). Le plafond n'est pas relevé : le modifier après avoir vu la validation serait du réglage, à décider explicitement.
- Ce sont des mesures de **validation**. Les hypothèses H1–H4 se jugent sur le test (protocole § 7), une seule fois, avec ces configurations figées.
