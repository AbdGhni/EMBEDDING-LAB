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
