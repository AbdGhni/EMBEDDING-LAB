# Rapport de relecture MLE complet : EL-009 (protocole) et EL-008 (splits)

> **Provenance** : rapport brut de l'agent `mle-reviewer` (ECC 2.2.3), lancé dans Claude Code sur le PC de l'étudiant le 2026-10-21, mandat `docs/mandates/EL-009-review.md`.
> L'état relu est le commit `088707a` de la branche `el-009-protocol`. Le rapport original écrit « el-009-protocole », c'est une coquille de l'agent.
> Les corrections apportées ensuite (commit `ea08e61`, protocole v1.1) ne sont pas prises en compte ici. Le résumé et les suites données figurent dans `docs/reviews/EL-009-mle-reviewer.md`.
> Texte reproduit sans modification de fond.

Relecture en lecture seule. Aucun fichier n'a été modifié.

## 0. Ce qui a été exécuté et ce qui ne l'a pas été

- **Lu** : le mandat, `docs/EXPERIMENT_PROTOCOL.md`, `docs/DATA_CARD.md`, `docs/DECISIONS.md` (D-008 à D-010), `src/embedding_lab/data/splits.py`, `scripts/make_splits.py`, `splits/summre_v1.json`, `src/embedding_lab/eval/metrics.py`, `src/embedding_lab/eval/test_access.py`, `tests/test_splits.py` et `tests/test_metrics.py`.
- **`CLAUDE.md`** : lu via le contexte injecté.
- **`docs/BRIEF_ORIGINAL.txt`** : non relu en entier, non vérifié.
- **pytest : NON exécuté.**
  - Commande : `python -m pytest tests/test_splits.py tests/test_metrics.py -q`.
  - Sortie exacte : `C:\Program Files\Python312\python.exe: No module named pytest`.
  - Il n'y a ni `.venv`, ni `uv` dans le PATH. Je n'ai rien installé.
  - Les tests sont donc **non vérifiés**. Je les ai seulement lus.
- **Données brutes absentes** : `data/` n'existe pas dans le clone. Je n'ai donc pas pu recalculer l'intersection des locuteurs à partir de `summre_meetings.jsonl`. Je n'ai pu contrôler que ce que le JSON versionné contient.
- **Vérifications faites** avec `python -I -c` en lecture seule :
  - inspection du JSON ;
  - appel direct de `paired_cluster_bootstrap` avec `sys.path.insert` et `dont_write_bytecode` ;
  - simulations de puissance.

## 1. Le découpage par composante empêche-t-il une même personne ou un même groupe d'être en train et en test ?

**Verdict : OK sur les groupes (vérifié). Locuteurs : OK conditionnel, non revérifié de façon indépendante.**

**Preuves**
- `splits/summre_v1.json`, champ `leakage` (extrait exact) :
  `'groups_in_several_splits': [], 'speakers_in_several_splits': []`
- Effectifs recalculés depuis `split_of` :
  - `Counter({'train': 178, 'val': 60, 'test': 45})`, conforme à la fiche des données.
  - Groupes par split : `{'test': 15, 'train': 60, 'val': 21}`, soit 96 groupes.
  - Intersections de groupes deux à deux : `{('test','train'): 0, ('test','val'): 0, ('train','val'): 0}`.
  - Réunions manuelles de test : 5 + 7 + 3 = 15, dont 5 de décision.
  - Cibles atteintes exactement.
  - `n_components` = 41.
- Code, `src/embedding_lab/data/splits.py:29-51` : l'union-find relie les groupes par locuteur commun.
  - `splits.py:44-47` : pour chaque locuteur, tous ses groupes sont fusionnés.
  - `splits.py:77-97` : l'affectation se fait par composante, donc groupes et locuteurs ne peuvent pas être séparés.
  - Les 3 réunions a/b/c d'un groupe restent ensemble.

**Réserves**
- **Contrôle tautologique** (risque faible).
  - `leakage_report` (`splits.py:108-137`) relit le même champ `speakers` que celui utilisé pour construire les composantes.
  - Il confirme la cohérence du code. Il ne prouve pas que `speakers` est complet.
  - Je n'ai pas pu vérifier ce champ, car `data/` est absent.
  - Si une réunion avait `speakers == []`, son groupe resterait isolé et pourrait partager une personne réelle sans que le rapport le détecte.
  - Correction : ajouter dans `make_splits.py` une assertion `all(m["speakers"] for m in meetings)` et consigner le nombre de réunions sans locuteur. Joindre au JSON un compte de locuteurs par split. Je recommande de lancer cette assertion sur le vrai fichier avant de geler le test.
- **Hypothèse non confirmée** : les identifiants 001-212 désignent des personnes uniques (`DATA_CARD.md` § 2 ter et `DECISIONS.md` D-010 « Limite »).
  - Le risque est dans les deux sens. Si deux ids désignent la même personne, la fuite persiste.
  - Le protocole ne traite que le cas conservateur. Il faut donc écrire cette limite dans le protocole (§ 9), pas seulement dans D-010.
- **Test unitaire** `tests/test_splits.py:27-34` : il passe par le même code que ce qu'il contrôle. Il est correct, mais il ne remplace pas le contrôle sur les données réelles. Non exécuté.
- **Recouvrement de 8-grammes** : seulement test et val contre train (`splits.py:119-127`).
  - Médiane 0,0009 et maximum 0,0815 (`008a_EARH`), conformes à la fiche.
  - Il n'y a aucun contrôle contre les futures données synthétiques, qui sont l'autre source d'entraînement. Voir le point 2.

## 2. Une fuite reste-t-elle possible par d'autres voies ?

**Verdict : risque. Aucun bloquant avéré dans le code existant. Plusieurs trous dans le protocole.**

1. **Thèmes de scénario partagés** (risque moyen).
   - `splits/summre_v1.json`, `stats.test` : `scenario_A: 15, B: 12, D: 6, E: 12`. Ces scénarios figurent aussi en train (`A: 45, B: 52, D: 21, E: 48`).
   - Le test réel mesure donc en partie l'adaptation thématique, pas la discrimination des pièges. La fiche reconnaît ce point (`DATA_CARD.md` § 2 ter « Limite »).
   - Correction : toujours rapporter E3 (négatifs aléatoires) à côté d'E2 sur B-REAL, car c'est le seul contrôle thématique. Ajouter au protocole une phrase interdisant d'attribuer un gain B-REAL aux pièges.
2. **Étiquettes d'entraînement et de test produites par le même annotateur** (risque élevé).
   - Protocole § 2 : B-REAL est « pré-annotation par Claude (`llm_provisional`), échantillon relu par l'étudiant ».
   - Protocole § 6 : l'entraînement utilise « unités B-REAL train ».
   - E2 peut apprendre les conventions d'étiquetage de Claude, puis être évalué sur des qrels issus du même Claude. Le gain B-REAL est alors gonflé, et E1 et BM25 sont désavantagés.
   - Correction :
     - (a) décider le sous-ensemble de test relu à la main avant toute mesure et rapporter les résultats séparément sur ce sous-ensemble, avec le taux d'accord LLM/humain ;
     - (b) ne pas utiliser de qrels LLM de B-REAL pour sélectionner quoi que ce soit ;
     - (c) pour H3, qui est un garde-fou, l'effet est plutôt favorable à E2. Il faut le signaler explicitement.
3. **Négatifs difficiles : outil de minage non défini** (risque élevé pour H2).
   - Protocole § 3 et § 6 : on parle de « triplets annotés » et de « négatifs difficiles », mais on ne dit ni qui les mine ni avec quel modèle.
   - Si les négatifs difficiles de test sont minés avec E1 (ou BM25), ils sont, par construction, des cas où E1 échoue. E2 gagne alors facilement sur H2, sans que ce soit un fait général.
   - À l'inverse, si E2 est entraîné sur des négatifs minés par E1 sur le train, c'est légitime. Mais dans ce cas le test des triplets de piège doit venir des types de pièges annotés par construction du générateur, pas d'un minage sur E1.
   - Correction : ajouter au § 3 ou § 6 « les négatifs difficiles du test sont définis par construction (type de piège du générateur ou annotation), jamais minés avec E1, E2 ou BM25 », et l'inscrire dans le manifeste.
4. **Pièges d'entraînement et de test issus du même générateur et de la même typologie** (risque moyen).
   - Protocole § 2 : « familles de patrons, noms de projets, personnes et plages de dates disjoints », mais les huit types de pièges (§ 3) sont les mêmes en train et en test.
   - Le protocole reconnaît lui-même un « seul auteur (Claude) », donc un biais de style commun. Un gain H1/H2 sur B-SYN mesure donc surtout l'apprentissage de la structure du générateur.
   - Correction : ajouter un contrôle de recouvrement n-grammes entre B-SYN train et B-SYN test, et entre B-SYN et les réunions SUMM-RE de test. Le `leakage_report` actuel ne couvre pas ce cas. Il faut aussi un ablation « patrons totalement hors distribution » en test (au moins une famille de formulation jamais vue).
5. **Sélection du checkpoint et hyperparamètres** : OK sur le principe. Le § 6 impose val seulement (B-SYN val, au plus 4 configurations).
   - Trou : le choix de la graine finale n'est pas défini quand il y en a 3 (13, 42, 1234). Le choix « de la meilleure sur le test » serait un biais.
   - Correction : écrire « la graine/le run rapporté est choisi sur val, ou on rapporte les trois ».
   - Trou : le critère de sélection est le nDCG sur B-SYN val seulement, alors que H3 porte sur B-REAL. Un checkpoint qui sur-apprend B-SYN peut dégrader B-REAL. Il faut ajouter B-REAL val (11 réunions manuelles) comme garde-fou dans le critère, ou au moins le journaliser à chaque évaluation.
6. **Seuils** : § 7 règle 5 « fixés sur val ou dev ». OK. Pour PAWS-X, c'est cohérent (dev/test).
7. **Journal d'accès au test non contraignant** (risque moyen).
   - `src/embedding_lab/eval/test_access.py` : `log_test_access` écrit un journal si on l'appelle. Rien n'oblige les fonctions de chargement du test à l'appeler.
   - Le test `tests/test_metrics.py:75-81` ne vérifie que le motif non vide et un fuseau +01:00/+02:00. Il ne vérifie pas que le chargement des requêtes de test passe par ce journal.
   - Correction : faire du chargeur des fichiers de test l'unique chemin de lecture et y appeler `log_test_access`, avec un test qui échoue si le chargeur est appelé sans enregistrement. Vérifier que `runs/TEST_ACCESS.log` est versionné ou au moins empreinté.
8. **Contamination par préentraînement de `multilingual-e5-small`** : non vérifié. Les données de préentraînement du modèle ne sont pas auditées, donc la présence de SUMM-RE (CC BY-SA, public) n'est pas exclue. Cela affecte E1 et E2 de la même façon, mais doit figurer dans les limites (§ 9).

## 3. H1 à H5 sont-elles réfutables avec les effectifs ? Le bootstrap est-il correct ?

### 3a. Implémentation du bootstrap : OK, avec trois réserves

**Preuves** (`src/embedding_lab/eval/metrics.py`)
- **Rééchantillonnage par grappe** : `metrics.py:104-107` regroupe les différences par `cluster_of[q]`. `metrics.py:113` fait `rng.choices(clusters, k=len(clusters))`, soit un tirage avec remise de grappes entières. C'est correct.
- **Appariement E1/E2** : `metrics.py:102-103` impose le même ensemble de requêtes. `metrics.py:106` calcule `a[q] - b[q]` avant tout rééchantillonnage, donc les deux systèmes partagent les mêmes tirages. C'est correct.
- **Graine et déterminisme** : `random.Random(seed)` avec `seed=0` (`metrics.py:110`).
  - Deux appels consécutifs avec les mêmes entrées donnent un résultat identique.
  - Sortie observée : `True {'diff': -0.0525, 'ci_low': -0.1728, 'ci_high': 0.0655, 'n_queries': 60, 'n_clusters': 12}`.
- **Nombre d'itérations** : défaut `n_resamples=10_000` (`metrics.py:92`), conforme au § 4.
- **Calcul de l'IC** : percentile.
  - Borne basse : indice `floor(0.025·10000)` = 250.
  - Borne haute : `ceil(0.975·10000) - 1` = 9749, bornée par `min(...)`.
  - C'est cohérent (`metrics.py:116-117`).
- **Grappes triées** (`metrics.py:107`) : bon pour la reproductibilité.

**Réserves**
1. **Liberté à petit nombre de grappes** (risque moyen).
   - Le bootstrap percentile est anti-conservateur quand il y a peu de grappes.
   - Simulation avec K = 12 grappes de 10 requêtes, effet vrai nul, 200 essais : la borne basse de l'IC dépasse 0 dans **4 %** des cas. C'est un peu plus que les 2,5 % attendus d'un seul côté. Avec K = 60, on obtient 3 %.
   - Correction : pour B-REAL (K probablement ≤ 15), rapporter aussi un test de permutation par signe au niveau de la grappe, ou un bootstrap t (studentisé). Garder le percentile comme IC principal si le protocole le dit, mais signaler la limite.
2. **Pas de métrique par triplet pour H2** (risque moyen).
   - `pairwise_accuracy` (`metrics.py:59-63`) renvoie un scalaire. Le bootstrap attend un score par requête (`a`, `b`).
   - Il n'y a aucune fonction qui produit un score par triplet (1 / 0,5 / 0), ni de `cluster_of` pour les triplets. H2 et H4 ne sont donc pas encore calculables avec le code. Non vérifié ailleurs.
   - Correction : ajouter `pairwise_scores(...)` par triplet, avec l'identifiant de grappe. Ajouter un test bootstrap sur des triplets.
3. **`evaluate_run` et classements dupliqués** (risque faible).
   - `dcg_at_k` (`metrics.py:35`) compte une unité deux fois si elle apparaît deux fois dans `ranking`. Le nDCG pourrait dépasser 1.
   - `recall_at_k` utilise `set`, donc pas le même comportement.
   - Aucun test ne couvre les doublons.
   - Correction : valider l'absence de doublons dans `ranking`. Vérifier aussi que `ranking` est borné au corpus du split.
- **Tests de bootstrap** : `tests/test_metrics.py:58-67` n'utilise que 500 rééchantillons et ne teste pas l'appariement ni la graine. Les 30 requêtes en 10 grappes détectent un gain énorme (0,8 contre 0,5). Ce n'est pas un test de calibration. Non exécuté.

### 3b. Puissance (ordre de grandeur, hypothèses explicites)

**Hypothèses de ma simulation (non issues des données, ce sont les miennes)**
- 10 requêtes par grappe.
- Écart-type par requête de 0,30.
- Hétérogénéité d'effet entre grappes de 0,05.
- Test unilatéral : borne basse de l'IC > 0 pour H1.
- Seed de simulation fixée à 5, 200 essais par cellule, 1 000 rééchantillons.
- Ce sont des ordres de grandeur, pas des mesures.

**Résultats**

| K grappes | P(rejet H0) si effet 0,05 | si effet 0,10 | si effet 0,15 | P(borne ≥ −0,02) si effet 0 |
|---|---|---|---|---|
| 12 | 0,41 | 0,91 | 1,00 | 0,14 |
| 15 | 0,46 | 0,94 | 0,995 | 0,165 |
| 30 | 0,705 | 1,00 | 1,00 | 0,22 |
| 60 | 0,95 | 1,00 | 1,00 | 0,34 |

**Interprétation**
- Les grappes de B-REAL test sont au plus 15 groupes (`groups.test` : `['019','024','033','036','038','047','048','069','090','091','096','097','098','099','104']`). Les composantes sont encore moins nombreuses, car certaines relient plusieurs groupes. Je n'ai pas pu compter les composantes du test (données brutes absentes) : **non vérifié**.
- L'effet minimal détectable à 80 % de puissance est donc de l'ordre de **0,07 à 0,09 nDCG@10** pour K = 12-15. Il est inférieur à 0,05 seulement à partir d'environ 30-60 grappes.
- **Effet de seuil sur les requêtes** : les requêtes de B-REAL ne portent que sur les 15 réunions manuelles, donc sur moins de 15 groupes. Ajouter des requêtes dans une grappe fait peu baisser l'incertitude.

**Verdict par hypothèse**

- **H1 (B-SYN) : risque, non quantifiable.**
  - Le § 2 dit « projets de graine test (définis à la génération) » mais ne fixe pas leur nombre.
  - Le nombre de grappes de B-SYN est donc libre, et la réfutabilité en dépend.
  - Correction : fixer avant génération un nombre minimal de projets de test (≥ 40) et de requêtes par projet, et inscrire dans le protocole la puissance visée avec l'effet minimal d'intérêt.
- **H2 : risque.** Même problème que H1, avec en plus l'absence de score par triplet (point 3a-2) et de définition du minage (point 2.3). Et le critère « IC contient 0 » est sans effet minimal.
- **H3 (non-infériorité à −0,02) : bloquant pour sa formulation, pas pour le projet.**
  - Avec K ≈ 12-15, la demi-largeur typique de l'IC est de l'ordre de 0,05-0,06.
  - Si l'effet vrai est 0 (aucune dégradation), la règle « réfutée si borne basse < −0,02 » déclare H3 réfutée dans plus de 80 % des cas (14-17 % de réussite dans ma simulation).
  - L'hypothèse ne peut quasiment pas être confirmée avec ces effectifs, même si le modèle ne dégrade rien.
  - Correction : soit élargir la marge à un niveau compatible avec la précision (≈ −0,06 à −0,08, à justifier comme un choix produit), soit reformuler H3 comme « on estime l'écart avec son IC, sans verdict binaire », soit augmenter le nombre de grappes (impossible : le test est figé à 15 groupes ; on pourrait ajouter val manuelles dans une évaluation exploratoire séparée, sans toucher au test).
  - La marge de −0,02 n'est justifiée nulle part dans le protocole (« magic constant »).
- **H4 : risque.**
  - Même difficulté, avec en plus la sous-population de pièges, plus petite.
  - Le test de H4 compare E2 et E3 à graine identique : la variance entre graines d'entraînement n'entre pas dans l'IC bootstrap (le § 4 la « rapporte à côté », sans l'intégrer).
  - Un seul entraînement par bras signifie que l'IC ne mesure que la variance d'échantillonnage du test, pas la variance d'entraînement. Un gain faible serait trompeur.
- **H5 : risque.**
  - Le critère « réfutée si différence négative avec IC excluant 0 » est asymétrique. L'hypothèse n'est réfutée que si l'hybride est significativement pire.
  - Avec peu de grappes, ce cas est rare : la non-réfutation vient du manque de puissance, pas d'une preuve.
  - « Meilleur des deux seuls » est choisi sur le test lui-même, ce qui est une sélection post hoc.
  - Correction : désigner à l'avance, sur val, le meilleur des deux comparateurs, et ajouter une marge de non-infériorité.
- **Comparaisons multiples** : le § 1 limite les confirmatoires à H1 et H2. Cela fait deux tests sans correction. Il faut dire lequel est primaire (H1) ou corriger (Holm) pour H2.

## 4. Le benchmark E1/E2 est-il isolé ?

**Verdict : OK sur le principe, risque sur l'exécution.**

**Preuves**
- Protocole § 5 : « Le benchmark E1/E2 est isolé : même corpus, mêmes requêtes, même découpage, aucun reranker ni filtre. »
- Même modèle de base à révision figée (`614241f6...`), mêmes préfixes `query: ` / `passage: `, même longueur max de 128 tokens, pooling et normalisation identiques.

**Réserves**
- **Rien n'oblige E1 et E2 à partager la même configuration d'évaluation dans le code** : aucun module d'évaluation encodeur n'est présent dans `src/embedding_lab/eval/` (seuls `metrics.py` et `test_access.py`, d'après le listing du dossier). Non vérifié pour l'avenir.
  - Correction : écrire un seul chemin d'encodage et de classement, paramétré uniquement par le chemin des poids. Journaliser dans chaque `metrics_*.json` l'empreinte de la configuration d'évaluation (longueur max, préfixes, dtype, taille de batch, empreinte du corpus et des qrels). Ajouter un test qui échoue si E1 et E2 diffèrent par autre chose que les poids.
- **Précision mixte** : l'entraînement se fait en fp16 « si GPU » (§ 6). L'évaluation doit utiliser le même dtype pour E1 et E2, sinon un écart de numérique se mélange au gain.
- **Tuning asymétrique** : E2 bénéficie d'un choix sur val et de jusqu'à 4 configurations, E1 non (longueur max, préfixes). C'est la norme, mais il faut le dire dans les limites.
- **E2 et E3** : l'isolation « origine des négatifs » est bien formulée (§ 5, même nombre de pas, même batch, même graine). Mais le filtre des faux négatifs (§ 6) et la règle « jamais deux exemples du même projet dans un batch » s'appliquent-ils aux deux ? À spécifier : la composition des batchs est une deuxième variable si elle diffère.
- **BM25 (E0)** : la tokenisation (§ 5) est fixée avec retrait de `w_N`/`sil` : bon. Il faut ajouter l'état du corpus (statistiques idf calculées sur le corpus du split, comme pour les autres).

## 5. Qu'est-ce qui pourrait produire un gain illusoire ?

**Verdict : risque élevé, aucun bloquant de code. Classement par gravité.**

1. **Même annotateur pour l'entraînement et pour les qrels du test B-REAL** (point 2.2).
2. **Négatifs difficiles de test minés ou définis par rapport à E1** (point 2.3) : gain H2 artificiel.
3. **Générateur unique, Claude, pour train et test de B-SYN**, avec la même typologie de pièges (§ 2 : « biais de style commun possible »). H1 peut ne mesurer que la reconnaissance de nos patrons. La fiche des données le dit elle-même (`DATA_CARD.md` § 3, « Limite connue » et D-008 : un benchmark 100 % synthétique « mesurerait la reconnaissance de nos propres patrons »). Or H1 est précisément mesuré sur B-SYN, hypothèse « principale ». La conclusion de H1 doit donc être formulée dans le protocole comme limitée au générateur, ce que le § 9 fait déjà. Je recommande de ne pas présenter H1 comme un résultat de généralisation.
4. **Thèmes de scénario partagés** (point 2.1), avec en plus le fait qu'il n'y a que 5 scénarios pour tout le corpus.
5. **Puissance insuffisante** : avec 12-15 grappes, les petits gains sont du bruit. La sélection post hoc d'une graine ou d'une configuration fait apparaître des gains qui ne se répliquent pas (points 2.5 et 3b).
6. **Variance d'entraînement ignorée** : une seule graine possible « si le budget Colab le permet » (§ 4). Un IC bootstrap étroit avec un seul entraînement donne une fausse précision.
7. **Corpus de recherche de B-REAL** : le § 2 dit « toutes réunions du split », ASR comprises, mais les requêtes ne portent que sur des unités manuelles. Les distracteurs ASR (texte plus bruité) rendent la tâche plus facile ou plus difficile de façon systématique. Cela touche E1 et E2 de la même façon, mais change l'interprétation absolue.
8. **Qrels graduées et pièges notés 0** : le nDCG punit un piège classé premier. C'est voulu. Mais si les pièges de B-SYN sont plus faciles à repérer que ce qu'un annotateur marque en B-REAL, les deux benchmarks ne sont pas comparables entre eux.
9. **Moyennes sur requêtes** : le bootstrap pondère par le nombre de requêtes par grappe (`metrics.py:109`, moyenne sur la liste concaténée). Une grappe très riche en requêtes domine. À documenter ou à contrôler par un second calcul à moyenne de grappe.
10. **Journal d'accès au test non appliqué** (point 2.7).

## Synthèse

### Bloquants
Aucun bloquant sur les splits eux-mêmes : les groupes sont disjoints, vérifié dans `splits/summre_v1.json`. Avant de geler le test, je recommande de traiter les points suivants comme **conditions de gel**. Ils sont bloquants pour la validité des conclusions, pas pour le code existant.

1. **Nombre de projets de test de B-SYN non fixé** (§ 2) : H1 n'est pas démontrablement réfutable. Fixer le nombre minimal de projets, de requêtes et la puissance visée avant la génération.
2. **H3 mal formulée** (§ 1, marge de −0,02) : avec K ≈ 12-15 grappes elle ne peut presque jamais être confirmée (14-17 % de réussite à effet nul dans ma simulation). Revoir la marge ou la nature du verdict.
3. **Définition du minage des négatifs difficiles de test absente** (§ 3, § 6) : risque de gain H2 circulaire avec E1. À écrire avant de produire les triplets de test.

### Risques
1. Étiquettes LLM identiques pour train et test de B-REAL (`EXPERIMENT_PROTOCOL.md` § 2 et § 6).
2. Contrôle de fuite des locuteurs tautologique et non revérifié sur les données brutes ; `speakers` vide possible (`splits.py:108-137`). Données absentes, non vérifié.
3. Pas de contrôle de recouvrement de n-grammes entre B-SYN, ni entre B-SYN et SUMM-RE test.
4. Thèmes de scénario partagés entre train et test (`stats` du JSON).
5. Bootstrap percentile légèrement anti-conservateur à petit K (4 % observé pour 2,5 % nominal à K = 12).
6. Pas de métrique par triplet ni de grappe pour H2 et H4 (`metrics.py:59-63`).
7. Doublons de `ranking` non contrôlés dans le nDCG (`metrics.py:35`).
8. Choix de la graine finale et critère de sélection du checkpoint non couplés à B-REAL val.
9. H5 : « meilleur des deux » choisi sur le test, critère asymétrique, pas de marge.
10. Variance entre graines non intégrée dans les IC ; une seule graine possible.
11. Journal d'accès au test sans mécanisme contraignant (`test_access.py`, `tests/test_metrics.py:75-81`).
12. Isolation E1/E2 à garantir par un chemin d'évaluation unique et une empreinte de configuration.
13. Deux hypothèses confirmatoires sans correction multiple.
14. pytest non exécuté (module absent), donc l'état des tests est **non vérifié**.
15. Contamination éventuelle du préentraînement d'e5 par SUMM-RE : non vérifié.
