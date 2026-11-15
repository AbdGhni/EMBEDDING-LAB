# Relecture indépendante EL-025 — mle-reviewer

- **Relecteur** : mle-reviewer (agent Claude, relecture MLE)
- **Date** : 2026-11-15
- **État relu** : `56a7442` (branche locale `el-025-review` = `origin/el-019-intents`)
- **Périmètre** : mandat `docs/mandates/EL-025-review.md`, section 1. Fichiers lus :
  - `docs/EXPERIMENT_PROTOCOL.md` (v1.8), `docs/EXPERIMENTS.md`, `docs/FINAL_REPORT.md`, `docs/JOURNAL.md` (S12 à S18), `docs/CURRENT_STATE.md` ;
  - `src/embedding_lab/train/` (`contrastive.py`, `data.py`), `src/embedding_lab/eval/` (`metrics.py`, `compare.py`, `harness.py`, `test_access.py`) ;
  - `scripts/final_analysis.py`, `scripts/build_training_data.py`, `src/embedding_lab/intents/rules.py` ;
  - `runs/CMP-test-2026-10-23T1450/final.json`, `runs/TEST_ACCESS.log`, `metrics_*`, `manifest.json` et `config.json` des runs de test, `R-test` et `I-test` ;
  - `splits/summre_v1.json`, `splits/data_sha256.json`, `data/train/*`.
- **Contraintes respectées** :
  - Lecture seule : aucun fichier modifié, créé ou supprimé dans le dépôt, aucune opération git qui écrit.
  - Aucun script du projet, aucun entraînement, aucune évaluation, pas de pytest, aucun import du paquet.
  - Seulement `git log/show/diff`, lecture, grep, et du Python autonome (`python -I`) qui lit des JSON de `runs/`, `splits/` et `data/train/`, ou qui simule une statistique.
  - Aucune donnée brute de test lue (`data/bsyn` et `data/breal` sont de toute façon absents de cette extraction). Le contenu des données est traité comme non fiable.

## 1. Ce qui est vérifié et ce qui est supposé

**Vérifié directement**
- Les splits SUMM-RE : aucun groupe d'expérience dans plusieurs splits (calculé depuis `split_of`).
- Les 38 groupes B-REAL de `data/train/e2_hard.jsonl` sont tous du split train.
- Les exemples d'entraînement sont 100 % B-SYN `bs-train` ou B-REAL train. Les négatifs sont soit des pièges du générateur, soit des négatifs extraits par E1 sur B-SYN train, soit des unités jugées 0 de B-REAL train.
- Chaque exécution de test apparaît une seule fois dans `TEST_ACCESS.log`. Les `run_id` sont uniques, il n'y a pas de seconde passe d'un même (système, graine).
- Le commit de test `d30c44b` précède le premier accès (14:32:56 contre 14:33:33). Les manifestes de test indiquent `git_dirty: false`.
- Entre `d30c44b` et `HEAD`, seul `scripts/final_analysis.py` change dans `src/` et `scripts/`. Le protocole et `EXPERIMENTS.md` ne sont pas modifiés par un diff de code, mais voir F-08.
- Les 15 empreintes de poids (E2, E3, E4) des configs de test correspondent aux `train_summary.json`.
- Les configurations d'évaluation E1, E2 et E3 sont identiques (dtype fp32, longueur 128, préfixes, batch 64). Seul le champ `weights` diffère. Les effectifs sont 384 requêtes / 48 grappes / 622 triplets pour B-SYN et 104 / 9 groupes (7 composantes) / 302 pour B-REAL.
- Je n'ai pas relancé `final_analysis.py`. Les moyennes et `final.json` sont recoupés sur les `metrics_*.json` par run : E4-dem `superseded` B-SYN 0,573 / 0,622 / 0,659, soit 0,62 ; E2 0,512 / 0,585 / 0,524, soit 0,54 ; E3 0,171 / 0,122 / 0,171, soit 0,15.
- Le code statistique (`metrics.py:99-176`, `final_analysis.py:38-49`, `compare.py`) est lu en entier. Résultat détaillé en §3.
- Toutes les valeurs de H1 à H5, des relations et des intentions citées dans `FINAL_REPORT.md` sont retrouvées dans `final.json`, `R-test` et `I-test`.

**Supposé ou non vérifiable ici**
- Les empreintes SHA-256 des données de test par rapport à `splits/data_sha256.json`. Les valeurs de `JOURNAL.md` y sont identiques pour B-SYN et pour B-REAL v2, mais les fichiers `data/bsyn` et `data/breal` ne sont pas présents ; je n'ai pas pu les recalculer.
- Les locuteurs partagés entre splits et les 8-grammes. Je reprends le rapport de fuite de `splits/summre_v1.json` (0 groupe et 0 locuteur partagé), sans accès à `data/processed`.
- Le recouvrement de thèmes entre requêtes de train et de test B-REAL (F-11). Je n'ai pas lu les requêtes de test, par contrainte.
- La véracité du premier passage de scénarios (7/9), dont le run a été supprimé (F-01).
- Les 3 poids E2 et E3 sont sur le Drive de l'étudiant, hors dépôt : seule l'empreinte est contrôlable.

## 2. Problèmes

| ID | Fichier:ligne | Gravité | Constat (résumé) |
|---|---|---|---|
| F-01 | `docs/EXPERIMENTS.md:193-208`, `docs/FINAL_REPORT.md:50`, `docs/JOURNAL.md:421-422` | MOYENNE | Scénarios de l'agent : corrections après un premier passage non conservé, présentées comme résultat de test |
| F-02 | `docs/FINAL_REPORT.md:49,58`, `src/embedding_lab/intents/rules.py:1-45` | MOYENNE | Règles I0 non indépendantes des gabarits de test ; biais d'auteur mentionné seulement pour I-MAN |
| F-03 | `docs/FINAL_REPORT.md:48,57`, `docs/EXPERIMENTS.md:256` | MOYENNE | R2 est battu sur B-SYN test ; affirmation « prédit trop de remplacements » contredite sur ce jeu |
| F-04 | `docs/FINAL_REPORT.md:45,54`, `docs/EXPERIMENTS.md:232,249` | MOYENNE | H3 (7 grappes) : IC bootstrap sans mise en garde, et lecture « résultat principal » plus forte que « descriptive » |
| F-11 | `docs/EXPERIMENT_PROTOCOL.md:124`, `docs/FINAL_REPORT.md:65` | MOYENNE | Chevauchement de thèmes B-REAL train/test non quantifié, et mêmes annotateur, même mandat |
| F-05 | `docs/EXPERIMENTS.md:125,249`, `docs/FINAL_REPORT.md:54` | BASSE | E2S : formulation causale (« montre ») sur val, une graine, nombre de pas différent, reprise pour le test |
| F-06 | `docs/FINAL_REPORT.md:47`, `docs/EXPERIMENTS.md:222-234` | BASSE | « H5 non soutenue » : pas de règle de décision au protocole ; E4-dem n'est pas un hybride lexical/dense ; E4-rrf-dem mesuré sur le test mais non rapporté |
| F-07 | `docs/EXPERIMENTS.md:245` | BASSE | « Le classement des systèmes est le même » faux pour E2 / E3 |
| F-08 | `docs/EXPERIMENTS.md:5`, `docs/CURRENT_STATE.md:3-30` | BASSE | Documents périmés et contradictoires |
| F-09 | `runs/TEST_ACCESS.log:8-9,39` | BASSE | Journal « append-only » fusionné hors ordre ; motif identique pour 38 accès |
| F-10 | `metrics.py:99-176`, `final_analysis.py:84-92` | BASSE / INFO | Plancher des p-valeurs Monte-Carlo, graine identique, indépendance des grappes B-SYN, comparaisons exploratoires non corrigées |
| F-12 | `docs/EXPERIMENT_PROTOCOL.md:37,50`, `docs/FINAL_REPORT.md:60-67` | BASSE | B-PAWS et abstention promis au protocole, jamais faits ni listés comme non faits |
| F-13 | `docs/FINAL_REPORT.md:43-44,56`, `docs/EXPERIMENTS.md:236-243` | INFO | Le gain H2 est concentré sur `superseded` et `negation` ; le « statut » reste marginal |
| F-14 | `docs/FINAL_REPORT.md:46`, `docs/EXPERIMENTS.md:250` | INFO | La quasi-totalité du gain H1 s'obtient aussi avec des négatifs aléatoires |
| F-15 | `src/embedding_lab/train/`, `splits/summre_v1.json` | INFO | Contrôles de fuite passés (liste exhaustive) |

Aucun problème CRITIQUE ni HAUT n'a été trouvé dans ce qui est vérifiable.

### F-01 — MOYENNE — Scénarios de l'agent : jeu de développement présenté dans les « résultats sur le test »
- **Constat.**
  - Le journal (`JOURNAL.md:421`) indique un premier passage à 7/9, avec le « code non commité, run supprimé ».
  - Il y a eu deux séries de corrections après ce passage : le suivi de la relation `answers` (annoncé dans `EXPERIMENTS.md:206`) **et** la présentation du dossier (doublons, décisions contestées, objet du mail).
  - La seconde série est le commit `e64ace0` (14:21:50, `agent.py` +22/−3). Elle n'est pas mentionnée dans `EXPERIMENTS.md`, qui range ces comportements dans « Réussis ».
  - `FINAL_REPORT.md:50` donne « 8 scénarios sur 9 réussis » dans la section « Résultats sur le test », sans préciser que les 9 scénarios ont servi à régler l'agent.
- **Preuve.**
  - `git log -- scripts/run_scenarios.py` : un seul commit (`3e7edee`, 14:20:59), postérieur au premier passage. L'affirmation « contrôles écrits avant la première exécution » (`EXPERIMENTS.md:195`) n'est donc pas vérifiable.
  - Les contrôles n'ont pas changé entre `3e7edee` et `e64ace0` (diff vide) : c'est positif.
  - Le seul run du premier passage (7/9) a été supprimé. `CLAUDE.md` n'autorise l'annonce que de ce qui a un log vérifiable.
- **Conséquence.**
  - 8/9 est un score de développement, pas une mesure indépendante. Le fait que E1 et E2 donnent le même résultat montre surtout la petitesse de la mémoire (21 unités, déjà relevée).
  - La divulgation existe (le journal et un paragraphe de `EXPERIMENTS.md`) mais elle est partielle, et le rapport final l'omet.
- **Recommandation.** Dans `FINAL_REPORT.md` et `EXPERIMENTS.md`, sortir l'agent de « Résultats sur le test », écrire « 7/9 au premier passage, run non conservé, deux séries de corrections ensuite, 8/9 = score de développement », et citer `e64ace0`. L'échec de la classification d'intention du scénario 2 ne doit pas être corrigé : c'est déjà le choix retenu.

### F-02 — MOYENNE — Règles I0 : non indépendantes du jeu de test I-SYN
- **Constat.**
  - Le générateur I-SYN (4 familles, dont la famille 3 pour le test), les règles I0 et I-MAN sont dans le **même commit** `eadb349` (14:12:36). Il n'existe aucune trace montrant que les règles ont été écrites sans connaître les gabarits de la famille de test, que l'auteur a sous les yeux dans `intents/data.py`.
  - Les listes de mots (`rules.py:16-34`) contiennent des termes calibrés sur ces gabarits (« rappel pour », « relance pour », « dont on a parlé », « responsable. »).
  - Le rapport ne parle de biais d'auteur que pour I-MAN (`FINAL_REPORT.md:58`, `EXPERIMENTS.md:268`).
- **Preuve.**
  - I0 : 0,817 en val (famille 2) puis 0,948 en test (famille 3). I2 : 0,895 puis 0,817.
  - L'inversion indique que les règles dépendent surtout de la difficulté propre des familles, non de la généralisation. Les règles n'ont pas de « split » au sens d'un entraînement.
- **Conséquence.**
  - Le score I0 sur I-SYN test n'est pas une mesure hors-échantillon.
  - Sur I-MAN, l'écart I0 / I2 est indistinguable : IC 95 % [0,840 ; 0,968] contre [0,774 ; 0,931], avec 80 exemples et un seul auteur (`I-test`).
  - La phrase « les règles gagnent sur le test » (`FINAL_REPORT.md:58`) n'est solide que sur I-SYN, et seulement avec cette réserve.
  - La métrique de sécurité « action à tort » sur I-MAN est de 0,10 pour I2 (2 hypothèses classées `create_task`) contre 0,033 pour I0 ; sur I-SYN, I2 est meilleur (0,044 contre 0,050).
  - Les IC de I-SYN sont des bootstraps par exemple sur des gabarits : trop étroits (limite signalée au protocole § 12).
- **Recommandation.** Ajouter la réserve sur la connaissance des gabarits de test, ne pas écrire « font mieux » pour I-MAN, et confirmer sur le troisième jeu écrit par l'étudiant (déjà prévu). Le traitement du verdict « I2 reste le modèle officiel, I0 le bat » est correct et conforme au protocole.

### F-03 — MOYENNE — Relations : R2 retenu est battu sur B-SYN test
- **Constat.**
  - R2 est sélectionné sur B-REAL val (conforme au protocole). Il alimente la rétrogradation de E4-dem et l'agent.
  - Sur B-SYN test (`R-test`) : R2 0,890 contre R1 1,000 (R2 − R1 = −0,110 [−0,145 ; −0,078]) et R3 0,936. Sur B-SYN val, R2 était à 0,966.
  - Pour `supersedes`, R2 a une précision de 1,0 et un rappel de 0,39 sur B-SYN test.
  - Le rapport donne uniquement le chiffre B-REAL et dit « B-SYN trivial pour R1 ». Il ne signale pas la chute de R2.
- **Preuve.** `runs/R-test-2026-10-23T1434/metrics_test.json`, clés `R2|bsyn` (`supersedes` rappel 0,3902, `macro_f1` 0,8904) et `R1|bsyn` (`macro_f1` 1,0).
- **Conséquence.**
  - L'explication de `FINAL_REPORT.md:57` (« prédit trop de remplacements ») vient de B-REAL val. Sur B-SYN test, R2 en prédit trop peu. Le biais dépend donc du jeu et du seuil 0,5 fixé a priori.
  - L'effet net de la rétrogradation sur `superseded` B-SYN (+0,08, soit 0,54 → 0,62) vient de la précision, pas du rappel.
  - R2 − R1 sur B-REAL (+0,034 [+0,013 ; +0,081]) repose sur 7 grappes : il est à lire comme descriptif (§ 10 du protocole le dit).
- **Recommandation.** Rapporter R1/R2/R3 sur B-SYN test, nuancer la phrase de `FINAL_REPORT.md:57`, et ne pas présenter R2 comme « meilleur » sans préciser que c'est sur B-REAL.

### F-04 — MOYENNE — H3 : intervalle trop optimiste et lecture au-delà de « descriptive »
- **Constat.**
  - H3 est déclarée descriptive, sans verdict (`protocole:25`). Le rapport la présente en conformité : `FINAL_REPORT.md:45` donne +0,229 [+0,152 ; +0,296], p = 0,016 « minimum atteignable » (vérifié : `final.json` `p_value` 0,015625, `method: exact`, `n_clusters: 7`).
  - L'IC bootstrap n'est pas accompagné de la mise en garde que le protocole formule en § 4 (intervalle trop étroit avec peu de grappes).
  - `EXPERIMENTS.md:249` appelle « résultat principal » le gain de +0,23 sur l'oral réel, et `FINAL_REPORT.md:54` « gain net et reproductible, surtout sur l'oral réel ».
- **Preuve (calcul).**
  - Simulation autonome du bootstrap percentile (même procédé, grappes de poids égal, effet nul, normale) : couverture ≈ 0,88 pour 7 grappes, ≈ 0,90 pour 12, ≈ 0,93 pour 48.
  - La simulation est indicative et simplifiée (grappes de même taille). Elle suggère que l'estimation du protocole (« ~4 % par côté pour 12 grappes ») est elle-même optimiste.
  - Les p-valeurs de permutation n'ont pas ce défaut : le test exact est valide à 7 grappes.
  - E2 − E3 sur B-REAL vaut −0,002 [−0,034 ; +0,021] : le gain est identique avec des négatifs aléatoires, il ne vient donc pas des pièges. L'ablation E2S l'attribue aux exemples réels d'entraînement.
- **Conséquence.**
  - L'IC de H3 ne peut pas se lire comme un 95 % fiable.
  - Le gain B-REAL est aussi compatible avec une adaptation au style des questions de l'annotateur IA et aux thèmes partagés (F-11). Le rapport le dit en §6 mais pas à côté du chiffre.
- **Recommandation.** Écrire à côté de H3 : « 7 grappes ; IC indicatif (couverture réelle probablement < 95 %) ; effet identique avec négatifs aléatoires ; compatible avec adaptation au style de l'annotateur et aux thèmes ». Retirer « résultat principal » pour B-REAL. Le fait « gain dans les 7 composantes » est établi : p = 2/128 impose le même signe partout.

### F-11 — MOYENNE — Chevauchement de thèmes B-REAL train/test
- **Constat.**
  - Seulement 5 scénarios existent dans tout SUMM-RE ; les mêmes thèmes se retrouvent en train et en test (`DATA_CARD.md:77`, `protocole:124`). Les groupes et les locuteurs sont, eux, bien disjoints.
  - Les requêtes de train comme de test ont été écrites par la même IA avec le même mandat.
  - E2 est entraîné sur 1 121 exemples B-REAL de train (322 requêtes uniques) et évalué sur le test de ces mêmes scénarios.
  - La déclaration existe, mais l'ampleur n'est pas mesurée.
- **Preuve.**
  - Les 322 anchors B-REAL de `e2_hard.jsonl` sont des textes tous distincts (aucun doublon exact), donc ce n'est pas une fuite par duplication.
  - Rien ne dit si les questions de test sont proches (même sujet, mêmes mots) de celles du train. Cela n'a pas été mesuré, et je n'ai pas pu le faire sans lire les requêtes de test.
- **Conséquence.**
  - Le gain B-REAL (E2 +0,23, E3 identique) mesure l'adaptation au corpus SUMM-RE, pas la généralisation à des réunions d'un autre type.
  - Les faux négatifs in-batch entre groupes (thèmes proches) sont possibles mais ne touchent pas la validité de l'évaluation. La règle de batch (`data.py:107-132`) utilise la grappe `group_id` (pas la composante de personnes) pour B-REAL.
- **Recommandation.** Après coup, et marqué comme exploratoire (`protocole § 7.4`) : mesurer la similarité maximale entre chaque requête de test B-REAL et les requêtes de train, et rapporter le gain par tranche de similarité.

### F-05 — BASSE — E2S : déclaration correcte, mais formulation causale forte
- **Constat.**
  - La déclaration est correcte. L'ablation est décidée après la lecture des résultats E2/E3 (val du 12:57, commit `569b83c` à 13:04, run à 13:05) ; elle est inscrite en v1.5 et dans `EXPERIMENTS.md:115` comme exploratoire ; elle n'est jamais évaluée sur le test (absente de `TEST_ACCESS.log`) et n'entre dans aucune hypothèse.
  - En revanche : E2S = 1 graine (13), val seulement, et le nombre de pas diffère (296 contre 350 ; meilleur point à l'étape 200 contre 350). `EXPERIMENTS.md:125` conclut « le gain ... vient des exemples B-REAL d'entraînement », et `EXPERIMENTS.md:249` / `FINAL_REPORT.md:54` écrivent « l'ablation montre » à propos du test.
- **Preuve.** `runs/CMP-val-2026-10-23T1310/comparison.json` : E2S − E1 sur B-REAL +0,015 [−0,038 ; +0,064], p = 0,625 ; E2(s13) − E2S +0,200 [+0,107 ; +0,306], p = 0,0156. Chiffres identiques à ceux du rapport.
- **Conséquence.**
  - Le gain B-REAL n'était déjà que de 0,29 à 0,50 dès l'étape 100 pour E2 (donc pas dû au nombre de pas) : l'inférence tient, mais c'est une indication, non une démonstration.
  - La conclusion « ce que le générateur enseigne ne se transfère pas à l'oral réel » est cohérente avec le chiffre, mais mesurée sur val.
- **Recommandation.** Remplacer « montre » par « indique (val, 1 graine) » dans les documents qui en parlent à propos du test.

### F-06 — BASSE — H5 : verdict non défini par le protocole
- **Constat.**
  - Le protocole classe H5 comme secondaire et dit « différence, IC et p rapportés » ; il ne définit aucun verdict. Le rapport écrit « non soutenue ».
  - Les chiffres (B-SYN −0,003 [−0,010 ; +0,003], p = 0,62 ; B-REAL −0,024 [−0,063 ; +0,016], p = 0,34) montrent une absence d'écart détectable, non une infériorité ; la non-infériorité n'est pas démontrée non plus à 7 grappes.
  - Le « hybride retenu » est E4-dem (E2 + rétrogradation), pas un hybride lexical / dense. Le vrai hybride E4-rrf est significativement pire : −0,114 [−0,145 ; −0,084] sur B-SYN et −0,185 [−0,256 ; −0,114] sur B-REAL. Le rapport le dit en §5.4 et dans les tableaux.
  - Les 3 graines de **E4-rrf-dem** ont été évaluées sur le test (`TEST_ACCESS.log:15-16,23-24,31-32` ; nDCG@10 B-SYN 0,770, B-REAL 0,385) mais n'apparaissent ni dans `final_analysis.py` (`SYSTEMS`) ni dans les tableaux de test.
- **Recommandation.** Écrire « H5 : pas de gain détecté (hybride retenu sur val = E2 + rétrogradation) » et ajouter E4-rrf-dem (0,770 / 0,385) au tableau de test. Le choix du « meilleur hybride sur val » est conforme à la règle fixée avant mesure (E4-dem : 0,665 contre 0,542 et 0,492, calcul recoupé sur `EXPERIMENTS.md:166-169`).

### F-07 — BASSE — Sous-ensemble B-REAL relu : « même classement » inexact
- **Constat.** `EXPERIMENTS.md:245` : « Le classement des systèmes est le même dans les deux parties ».
- **Preuve** (`final.json`, `breal_reviewed_subset`) :
  - relu, 34 requêtes : E0 0,276, E1 0,409, E2 0,590, E3 0,613 ;
  - reste, 70 requêtes : E0 0,173, E1 0,297, E2 0,549, E3 0,541.
  - E3 dépasse E2 dans le sous-ensemble relu, et l'inverse dans le reste. L'écart E2 − E1 est de +0,18 en relu contre +0,25 ailleurs.
- **Conséquence.** Les deux parties s'accordent sur « E2 ≈ E3 > E1 > E0 », mais pas sur l'ordre exact E2 / E3. Aucune conséquence pour les hypothèses ; un défaut d'énoncé. En outre, la relecture humaine n'a porté que sur 43 points litigieux (déjà dit).

### F-08 — BASSE — Documents périmés
- `docs/EXPERIMENTS.md:5` affirme « Aucune mesure sur un split de test à ce stade (`runs/TEST_ACCESS.log` absent) », ce qui contredit la section de test des lignes 210-270 et le journal.
- `docs/CURRENT_STATE.md:3` est daté « session S17, 15 h » ; il liste `main @ 825fa57` puis `main @ 6856536`, et indique « I-SYN test et I-MAN ... à mesurer » alors qu'ils l'ont été. C'est une violation de la consigne de reprise (`CLAUDE.md`).
- Le tableau de versions du protocole est dans un ordre incohérent (1.0, 1.8, 1.7, 1.6, 1.5 ...), sans conséquence sur le contenu.

### F-09 — BASSE — Journal d'accès au test
- **Constat.**
  - Les entrées Colab (lignes 9-38) ont été fusionnées après coup : la ligne 8 (14:38:20) précède la ligne 9 (14:33:33). Le journal n'est donc ni ordonné ni scellé, et la preuve d'ordre repose sur les horodatages internes.
  - Le motif « évaluation finale unique » est répété pour 38 accès à des systèmes différents (chacun mesuré une fois, ce qui est correct, mais le mot « unique » est ambigu).
  - La contrainte « imposée par le code » (`protocole § 7.3`) ne vaut que pour le chemin `load_benchmark`. `final_analysis.py` lit les requêtes de test par un autre chemin, mais il journalise lui-même (ligne 39).
- **Preuve.** `TEST_ACCESS.log` : 38 lignes de runs distincts + 1 ligne d'analyse. Pas de doublon de `run_id`. `d30c44b` précède le premier accès.
- **Recommandation.** Indiquer dans le journal une ligne de fusion datée et l'empreinte du zip Colab (déjà dans `JOURNAL.md:428`) ; reformuler le motif.

### F-10 — BASSE / INFO — Statistiques (implémentation et usage)
Voir §3 pour la vérification détaillée. Points mineurs :
- **Plancher Monte-Carlo.** Avec 48 grappes et 10 000 tirages, la p-valeur minimale est 1/10 001 = 9,999e-5 (`min_attainable_p`). Les p-valeurs de H1, H2 et H4 sont toutes à ce plancher. « p Holm 0,0002 » vaut 2 fois le plancher : il faut écrire « < 1e-4 (plancher MC) ». Le choix (exact ≤ 16 grappes, MC au-delà, graine 0) est cohérent avec le protocole § 4.
- **Même graine pour tous les tests.** Les mêmes tirages de signes servent à toutes les comparaisons à 48 grappes : les p-valeurs sont corrélées, sans effet sur la validité.
- **Indépendance des grappes B-SYN.** Les requêtes de projets différents partagent le même corpus de distracteurs : l'échangeabilité au niveau des projets est approximative. Même remarque pour B-REAL, dont les composantes partagent des thèmes. Risque faible.
- **Graines d'entraînement hors inférence.** Les p-valeurs conditionnent sur 3 modèles entraînés, dont l'écart-type est ≤ 0,009 (recoupé : E2 B-SYN 0,0034 ; E3 0,0072 ; E4-dem B-REAL 0,0083). C'est négligeable face à l'effet de 0,062, mais le protocole le signale déjà.
- **Comparaisons exploratoires.** `other_comparisons` (24 comparaisons dans `final_analysis.py:89-92`) n'est pas corrigé pour comparaisons multiples ; le rapport n'en cite qu'une poignée et ne les présente pas comme confirmatoires.

### F-12 — BASSE — Éléments promis par le protocole, ni faits ni listés
- B-PAWS (`protocole:37`) : aucun code ni run (`git grep paws` ne trouve que de la documentation).
- Abstention sur les requêtes sans réponse (`protocole:50`) : 15 requêtes de test sont exclues des métriques de recherche et leur mesure séparée n'existe nulle part.
- `FINAL_REPORT.md:66` liste E5-E7, le reranker et le filtre de type comme non faits, mais ni B-PAWS ni l'abstention. Le report est donc incomplet par rapport au protocole.

### F-13 — INFO — Où se loge le gain de H2
- Décomposition par type de piège sur B-SYN test (n par type : `superseded` 82, `status` 172, `negation` 52, `condition` 18, `date` 48, `topic_only` 196). Contribution à Δ = +0,0697 (E1 → E2) :

| Piège | E1 → E2 | Contribution (points sur 622) |
|---|---|---|
| `superseded` | 0,293 → 0,54 | ≈ 20 |
| `negation` | 0,808 → 1,0 | ≈ 10 |
| `status` | 0,855 → 0,89 | ≈ 6 |
| `topic_only` | 0,954 → 0,97 | ≈ 4 |
| `condition`, `date` | — | ≈ 3 |

- Le total (≈ 43 sur 622) reproduit les +0,070 de H2.
- Le « statut », piège censé être central, ne gagne que +0,035 sur le test. Sur le val, E1 était à 0,24 sur `status` ; sur le test, il est à 0,855.
- Cela montre que la difficulté relative des familles varie beaucoup entre val et test. Les chiffres de val ne se comparent pas à ceux du test, et le récit « E1 sous le hasard sur le statut » ne vaut pas sur le test.
- `FINAL_REPORT.md:43-44` est exact. Le rapport ne montre que 4 types sur 7 (omet `negation`).

### F-14 — INFO — H1 et négatifs difficiles
- E3 − E1 sur B-SYN nDCG@10 = +0,057 [+0,035 ; +0,078], contre E2 − E1 = +0,062. E2 − E3 = +0,005 [−0,007 ; +0,017], p = 0,42.
- H1 ne prouve donc pas l'intérêt des négatifs difficiles ; seul H4 (sur les paires, +0,064) le fait. Le rapport le dit (`FINAL_REPORT.md:46,55`).
- E3 est pire qu'E1 sur `superseded` (0,15 contre 0,29), ce que le rapport ne mentionne pas. C'est cohérent avec « négatifs aléatoires = apprend à ignorer la nuance ».

### F-15 — INFO — Fuites : ce qui a été contrôlé et passe
- **Splits.** Unité de découpage = composante de groupes liés par un locuteur (`data/splits.py`). 60 / 21 / 15 groupes, 0 groupe partagé (recalculé). Les 38 groupes B-REAL de train utilisés en entraînement sont tous du split train.
- **Négatifs.** `build_examples` (`train/data.py:52-78`) n'accepte que des négatifs jugés 0 pour la requête (assertion à la ligne 73) ; pour B-REAL, jamais d'unité non jugée. `random_negative_variant` (`data.py:81-104`) tire dans le pool du split train et exclut le groupe d'origine pour B-REAL.
- **Extraction des négatifs.** `mine_with_e1` n'est appelé que sur `data/bsyn/train` (`scripts/build_training_data.py:62-64`) ; aucun négatif ne vient de val ou de test.
- **Sélection.** Le checkpoint est choisi sur B-SYN val (`contrastive.py:133-170`) ; B-REAL val sert de garde-fou ; le test n'est jamais lu pendant l'entraînement. Une seule configuration d'hyperparamètres a été essayée (le protocole en autorise 4) : pas de risque de sur-ajustement de la validation par le réglage.
- **E2 contre E3.** Mêmes exemples, mêmes ancres, mêmes positifs, même règle de batch (`cluster_batches`, graine identique), seule la colonne `negative` change.
- **Pièges de test.** Définis par construction (B-SYN) ou par annotation (B-REAL), jamais extraits avec E1 / E2 / BM25 (protocole § 2). Les corrections de B-REAL test v1 → v2 (27, après relecture IA du sous-ensemble) ont eu lieu avant toute évaluation (`JOURNAL.md:331-346`).
- **Limites déclarées, non des fuites.** Même générateur et mêmes types de pièges en train et test (`protocole § 9`) ; le test B-SYN mesure surtout la discrimination des constructions de l'auteur.

## 3. Statistiques : vérification point par point

- **Permutation par grappes** (`metrics.py:133-176`). Correcte.
  - Statistique = somme pondérée des différences par grappe, avec inversion de signe par grappe.
  - Bilatérale par `abs`, énumération exacte jusqu'à 16 grappes (2^7 = 128 pour H3, p min = 2/128 = 0,015625 vérifié), Monte-Carlo au-delà avec la statistique observée ajoutée à la distribution (correction +1).
  - Les clés de triplets `t%05d` de `final_analysis.py:67` coïncident avec celles du harnais (`harness.py:97-104`).
  - La grappe B-REAL est bien la composante de personnes dans l'analyse (7), alors que le harnais utilise le groupe pour son indicateur de contrôle (9 groupes) ; c'est documenté (`compare.py:8-12`).
- **Holm** (`final_analysis.py:38-49`). Correct pour m = 2 : la p ajustée de H1 et de H2 est 2 × 9,999e-5 = 0,00019998 (`final.json`, `holm_H1_H2`). Appliqué seulement à H1-H2, comme au protocole ; H3-H5 hors correction, conformément au protocole.
- **Bootstrap par grappes** (`metrics.py:99-130`). Correct (percentile, indices 250 et 9749 sur 10 000, grappes rééchantillonnées en bloc). Trop étroit à peu de grappes : voir F-04.
- **Règle de H1 / H2.** Δ > 0 et p < 0,05 (Holm) : remplie (+0,0615 / +0,0697, p Holm 0,0002). Le rapport la restitue correctement.
- **Moyenne des graines.** nDCG par requête moyenné sur 3 graines avant comparaison (`compare.py:24-34`) ; aucune graine sélectionnée, conformément au protocole. Pour E1 et E0 (déterministes), une seule exécution.

## 4. Synthèse

- **Fuites** : je n'en trouve aucune dans le périmètre vérifiable. Splits, négatifs d'entraînement et données d'entraînement sont conformes. Les risques résiduels sont déclarés mais non quantifiés (thèmes partagés, annotateur IA unique, générateur commun).
- **Conclusions du rapport** : H1 et H2 respectent exactement la règle du protocole. H3 est correctement présentée comme descriptive, mais deux phrases la dépassent (F-04). H4 est correcte. H5 est étiquetée « non soutenue » sans règle de décision (F-06). Les chiffres relations et intentions correspondent aux runs ; deux omissions ou affirmations incomplètes (F-02, F-03).
- **Écarts déclarés** :
  - E2S est correctement déclarée (post-val, exploratoire, jamais testée), avec une formulation un peu forte (F-05).
  - La correction de l'agent n'est présentée qu'à moitié : une seule des deux séries de corrections est citée, le 7/9 initial et la suppression du run sont absents des documents de résultats, et l'agent est rangé dans « Résultats sur le test » (F-01).
  - I2 battu par I0 sur le test est rapporté honnêtement et le choix de ne pas changer de modèle est correct, mais la mesure n'est pas indépendante (F-02).
- **Statistiques** : implémentation correcte et usage conforme. Réserves sur l'IC de H3 et le plancher MC (F-04, F-10).
- **Omissions** : E4-rrf-dem (test mesuré non rapporté), B-PAWS et abstention (F-06, F-12). Documents périmés (F-08).

Recommandations par priorité :
1. Reformuler l'agent (F-01) et ajouter une réserve sur I0 (F-02).
2. Rapporter R1/R2/R3 sur B-SYN test et nuancer le biais de R2 (F-03).
3. Ajouter à H3 la réserve sur l'IC et sur le style d'annotateur, et mesurer a posteriori la proximité des requêtes de test aux requêtes de train (F-04, F-11).
4. Corriger les formulations (F-05, F-06, F-07), la documentation périmée (F-08), et lister les éléments non faits (F-12).

## 5. Verdict

**Decision : APPROVE WITH WARNINGS**

**Primary risks : weak eval** (jeu de développement présenté comme test pour l'agent, règles I0 non indépendantes, B-REAL à 7 grappes et thèmes partagés), **other** (omissions de reporting et documents périmés). Pas de fuite de données identifiée, pas de risque de serving, pas de fuite de secrets dans le périmètre lu.

**Tests run** : aucun test ni script du projet (interdits par le mandat). Vérifications autonomes en Python (`python -I`) :
- recalcul des moyennes par graine, des contributions par type de piège et des p / Holm à partir des JSON de `runs/` ;
- contrôle des empreintes de poids entre `train_summary.json` et les configs de test (15 sur 15 concordent) ;
- contrôle des splits et de la provenance des exemples d'entraînement ;
- simulation de couverture du bootstrap (≈ 0,88 pour 7 grappes) ;
- lecture de `git log` et `git diff --stat` entre `d30c44b` et `HEAD`.

Fichiers cités (chemins absolus) : `C:\Users\abdul\embedding-lab\docs\EXPERIMENT_PROTOCOL.md`, `C:\Users\abdul\embedding-lab\docs\EXPERIMENTS.md`, `C:\Users\abdul\embedding-lab\docs\FINAL_REPORT.md`, `C:\Users\abdul\embedding-lab\docs\JOURNAL.md`, `C:\Users\abdul\embedding-lab\docs\CURRENT_STATE.md`, `C:\Users\abdul\embedding-lab\scripts\final_analysis.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\eval\metrics.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\eval\compare.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\eval\harness.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\train\data.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\train\contrastive.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\intents\rules.py`, `C:\Users\abdul\embedding-lab\runs\CMP-test-2026-10-23T1450\final.json`, `C:\Users\abdul\embedding-lab\runs\TEST_ACCESS.log`, `C:\Users\abdul\embedding-lab\runs\R-test-2026-10-23T1434\metrics_test.json`, `C:\Users\abdul\embedding-lab\runs\I-test-2026-10-23T1438\metrics_test.json`, `C:\Users\abdul\embedding-lab\runs\CMP-val-2026-10-23T1310\comparison.json`, `C:\Users\abdul\embedding-lab\splits\summre_v1.json`.
