# Protocole expérimental

Version **1.7**, 2026-10-23. Toute modification ultérieure crée une version 1.x, journalisée avec sa raison. Les modifications faites après un premier accès au test sont signalées comme **post hoc**.

| Version | Date | Changement | Raison |
|---|---|---|---|
| 1.0 | 2026-10-21 | version initiale | — |
| 1.7 | 2026-10-23 | § 11 : composants de E4 précisés (RRF, rétrogradation des unités remplacées par R2, sans filtre de type ni reranker) | rédigé avant toute mesure de E4 : non post hoc. Le filtre de type dépend des intentions (EL-019) et le reranker cross-encoder est abandonné faute de temps ; les deux sont signalés comme non faits. |
| 1.6 | 2026-10-23 | § 10 : protocole du module de relations (EL-015) — tâche, classes, négatifs, modèles R0–R3, métriques, sélection sur val | rédigé avant toute mesure du module, sur val comme sur test : non post hoc. |
| 1.5 | 2026-10-23 | ajout de **E2S** (E2 sans les exemples B-REAL), ablation **diagnostique**, validation seulement, une graine ; jamais évaluée sur le test, n'entre dans aucune hypothèse ; grappes B-REAL des comparaisons = composantes de personnes (`eval/compare.py`), conformément au § 5 | décidée **après** lecture des résultats de validation E2/E3 (gain B-REAL identique pour E2 et E3, origine inconnue) : c'est une analyse exploratoire, signalée comme telle. Aucun accès au test : non post hoc vis-à-vis du test. |
| 1.4 | 2026-10-21 | B-REAL : portée de recherche = groupe d'expérience de la requête ; annotation des groupes val/test contenant une réunion manuelle (10 + 9 groupes) ; texte indexé B-REAL | 5 scénarios partagés par de nombreux groupes : une question posée sur tout le split aurait de vraies réponses non jugées dans d'autres groupes. Aucune annotation ni évaluation B-REAL faite : non post hoc. |
| 1.3 | 2026-10-21 | garde-fou B-REAL val, mêmes règles de batch E2/E3, même dtype et empreinte de configuration d'évaluation, moyenne par grappe en contrôle, limites ajoutées (identifiants de locuteurs, préentraînement d'e5, distracteurs ASR, prénoms communs) | points du rapport complet `docs/reviews/EL-009-mle-reviewer-full.md` absents du résumé. Aucun modèle évalué : non post hoc. |
| 1.2 | 2026-10-21 | texte indexé d'une unité B-SYN = titre de réunion + locuteur + extrait (`retrieval_text`) ; effectifs réels de B-SYN | sans contexte, une phrase comme « je me charge du dossier » ne dit ni le projet ni la personne : le piège « autre projet » était indiscernable. Aucun modèle évalué : non post hoc. |
| 1.1 | 2026-10-21 | taille de B-SYN fixée ; H3 descriptive ; origine des pièges du test définie ; test de permutation par grappes ; règles graines, H5 et sous-ensemble relu | relecture indépendante `mle-reviewer` (ECC 2.2.3), `docs/reviews/EL-009-mle-reviewer.md`. Aucun accès au test n'avait eu lieu : modification **non** post hoc. |

## 1. Question et hypothèses falsifiables

Question : un encodeur adapté par apprentissage contrastif avec négatifs difficiles retrouve-t-il mieux la preuve correcte qu'un encodeur générique et que BM25, en particulier face aux pièges de statut, de personne, de date et de négation ?

| ID | Hypothèse | Statut | Règle de décision |
|---|---|---|---|
| H1 | E2 (fine-tuné) > E1 (initial) sur B-SYN test, nDCG@10 | confirmatoire | confirmée si différence > 0 **et** p < 0,05 (test de permutation apparié par grappes, bilatéral, correction de Holm sur H1–H2) ; l'IC bootstrap est rapporté à côté |
| H2 | Gain sur les pièges : précision par paires E2 > E1 sur B-SYN test | confirmatoire | même règle que H1 |
| H3 | Effet de E2 sur données réelles (B-REAL test) | **descriptive** | on rapporte la différence nDCG@10, son IC et la p-valeur exacte, **sans verdict** : 7 grappes seulement (p minimale atteignable 2/128), puissance insuffisante pour un test de non-dégradation |
| H4 | À budget égal, négatifs difficiles > négatifs aléatoires (E3) sur les pièges de B-SYN test | secondaire | différence, IC et p rapportés, sans correction |
| H5 | Hybride ≥ meilleur système seul (E4) | secondaire | le « meilleur système seul » est désigné **sur val**, puis comparé sur test |

H3 à H5 et E5 à E7 sont présentés comme indicatifs. Les sous-ensembles relus à la main sont rapportés séparément.

## 2. Benchmarks

| ID | Contenu | Rôle | Construction |
|---|---|---|---|
| **B-SYN** | Projets fictifs français multi-réunions (3 réunions par projet) avec dates, montants, responsables, propositions, validations, annulations, réattributions | principal (H1, H2, H4) | générateur à graine fixe ; **240 projets train, 32 val, 48 test**, environ 8 requêtes par projet (≈ 384 requêtes de test, 48 grappes) ; familles de patrons, noms de projets, personnes et plages de dates **disjoints** entre train, val et test |
| **B-REAL** | Unités extraites des réunions SUMM-RE (`splits/summre_v1.json`) + requêtes en langage naturel | validité externe (H3) | pré-annotation par des sous-agents Claude (`llm_provisional`, mandat `docs/mandates/EL-007b-annotation.md`), échantillon relu par l'étudiant ; groupes val/test contenant une réunion manuelle (10 et 9 groupes) ; requêtes uniquement sur les réunions manuelles |
| **B-PAWS** | PAWS-X fr (dev pour le seuil, test pour la mesure) | robustesse aux reformulations adversariales | données officielles, sans modification |

Les requêtes de B-SYN test sont écrites avec des familles de formulations **distinctes** de celles du train. Limite : un seul auteur (Claude) écrit toutes les familles, donc un biais de style commun est possible ; B-REAL sert de contrôle.

**Origine des pièges d'évaluation.** Dans B-SYN val et test, les négatifs difficiles sont définis **par construction** (le générateur sait quelle unité est une proposition, une annulation, la mauvaise personne…). Dans B-REAL, ils sont définis **par annotation**. Ils ne sont jamais extraits à l'aide d'un modèle évalué (E1, E2, BM25) : sinon les pièges seraient choisis pour piéger E1, et le gain de E2 serait acquis d'avance.

**Sous-ensemble relu.** Cinq réunions manuelles de B-REAL test sont tirées **avant** toute annotation (`splits/summre_v1_test_human_review.txt`, graine 20261021) : 019a_EARD, 036c_EAPH, 047c_EDPH, 069b_EEDL, 097c_EBPH. L'étudiant relit leurs annotations ; les résultats sur ce sous-ensemble sont rapportés à part de ceux du reste du test (annoté par Claude seul).

### Unités de recherche et corpus de recherche

- Unité de recherche (« document ») : une unité sémantique (`unit.schema.json`) représentée par `retrieval_text` si présent, sinon `evidence.text`. Pour B-SYN : `Point projet <nom> — <locuteur> : <extrait>`. Pour B-REAL : `Réunion <rang>/3 (<type>) — locuteur <id> : <extrait>` ; E5 teste l'ajout du tour précédent.
- Corpus de recherche d'une requête : pour B-SYN, **toutes** les unités du split (les autres projets servent de distracteurs, le nom de projet figure dans le texte indexé) ; pour B-REAL, **les unités du groupe d'expérience de la requête** (réunions a/b/c, manuelles et ASR), car les scénarios sont partagés entre groupes et les unités d'autres groupes ne sont pas jugées.
- Pertinence graduée : 2 = preuve directe et en vigueur ; 1 = utile mais incomplète ou historique (ex. décision remplacée pour une question « historique ») ; 0 = non pertinente, y compris les pièges.
- Requêtes multi-positives autorisées. Les requêtes **sans réponse** sont exclues des métriques de recherche et mesurées séparément (abstention).

## 3. Métriques

| Métrique | Définition | Dénominateur |
|---|---|---|
| **nDCG@10 (principale)** | gain 2^rel − 1, remise log2(rang + 1), normalisé par le DCG idéal | requêtes du split ayant ≥ 1 unité de pertinence ≥ 1 |
| Recall@{1, 5, 10} | proportion des unités pertinentes (rel ≥ 1) dans les K premiers | idem |
| MRR@10 | 1 / rang de la première unité de rel ≥ 1 (0 si absente du top 10) | idem |
| Précision par paires sur pièges | proportion de triplets (requête, positif, négatif difficile) où score(positif) > score(négatif) ; ex æquo = 0,5 | triplets annotés du split, ventilés par type de piège |
| B-PAWS | précision et AP de la classification paraphrase / non-paraphrase par cosinus, seuil fixé sur dev | paires du test PAWS-X fr |

Types de pièges : `status` (proposition / validation / rejet / annulation), `condition`, `negation`, `person` (mauvaise personne, mauvais rôle, simple mention), `date`, `amount`, `superseded`, `topic_only`.

Les métriques des modules aval (relations, intentions, destinataires, dossiers, système) suivent la matrice M-03 à M-07 de `REQUIREMENTS_MATRIX.md` ; leurs protocoles détaillés seront ajoutés en version 1.x avant leur première évaluation.

## 4. Statistiques

- Différences appariées (même requêtes, mêmes corpus).
- **Décision** : test de permutation apparié par grappes (inversion des signes grappe par grappe ; énumération exacte jusqu'à 16 grappes, 10 000 tirages Monte-Carlo au-delà, graine 0). Implémentation : `paired_cluster_permutation_test`.
- **Estimation** : IC 95 % par bootstrap par grappes (projet pour B-SYN, composante de personnes pour B-REAL), 10 000 tirages, graine 0. La relecture a montré qu'avec peu de grappes cet intervalle est trop étroit (environ 4 % d'erreur de chaque côté au lieu de 2,5 % pour 12 grappes) : il sert à estimer, pas à décider.
- Grappes de B-REAL test : 8 composantes, dont 7 contiennent des réunions manuelles.
- Graines d'entraînement : 3 graines (13, 42, 1234) si le budget Colab le permet. Le test confirmatoire utilise, pour chaque requête, la **moyenne des scores sur les 3 graines** ; les résultats de chaque graine sont aussi rapportés. **Aucune graine n'est sélectionnée.** Avec 1 seule graine, la variance d'entraînement n'est pas prise en compte, et c'est signalé comme limite.
- Les effectifs (requêtes, grappes, triplets) sont toujours rapportés.
- La moyenne sur requêtes donne plus de poids aux grappes riches en requêtes ; une moyenne **par grappe** (moyenne des moyennes) est calculée en contrôle et rapportée si elle diverge.

## 5. Expériences

Encodeur de référence : `intfloat/multilingual-e5-small`, révision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, licence MIT, 12 couches, dimension 384, pooling moyen, normalisation L2, 512 tokens maximum. Préfixes obligatoires selon la fiche du modèle : `query: ` pour les requêtes, `passage: ` pour les unités. Longueur max utilisée : 128 tokens (unités courtes ; 6 mots par tour en médiane), vérifiée par la mesure de troncature.

| ID | Comparaison | Seule variable | Mesures |
|---|---|---|---|
| E0 | BM25 (`rank-bm25`, k1 = 1,5, b = 0,75 ; minuscules, `_` → espace, jetons `w_N`/`sil` retirés) | — | toutes |
| E1 | e5-small sans adaptation | — | toutes |
| E2 | e5-small fine-tuné, négatifs difficiles | poids de l'encodeur | toutes, + courbes |
| E3 | E2 avec négatifs aléatoires du même split à la place des négatifs difficiles | origine des négatifs (même nombre de pas, même taille de batch, même graine) | sous-ensemble pièges |
| E2S | E2 entraîné sur les seuls exemples B-SYN (6 222) | présence des données réelles à l'entraînement (le nombre de pas diffère aussi) | val seulement, diagnostique |
| E4 | BM25 / dense / fusion RRF (k = 60) ; filtres type / statut ; reranking cross-encoder si le temps le permet. Le meilleur système seul (pour H5) est désigné sur val | composant ajouté | B-SYN, B-REAL |
| E5 | unité seule vs unité + tour précédent | texte encodé | B-REAL (conditionnel) |
| E6 | e5-small vs `intfloat/multilingual-e5-base` (révision `d128750597153bb5987e10b1c3493a34e5a4502a`) | taille du modèle | B-SYN, B-REAL (conditionnel) |
| E7 | fenêtres fixes de 64 mots vs tours vs unités | granularité | B-REAL, chemin brut (conditionnel) |

Le benchmark E1/E2 est **isolé** : même corpus, mêmes requêtes, même découpage, aucun reranker ni filtre. Cette isolation sera garantie par **un seul point d'entrée d'évaluation** commun à tous les systèmes (EL-010), qui ne diffère que par la fonction de score ou le chemin des poids. Chaque `metrics_*.json` contient l'empreinte de la configuration d'évaluation (longueur max, préfixes, dtype, taille de batch, empreintes du corpus et des qrels) ; E1 et E2 sont évalués dans le **même dtype** (fp32), et un test échoue si leurs configurations diffèrent autrement que par les poids.

## 6. Entraînement (E2, E3)

- Perte : Multiple Negatives Ranking Loss (InfoNCE avec négatifs du batch) + un négatif difficile explicite par exemple ; échelle (inverse de la température) 20.
- Faux négatifs : un batch ne contient jamais deux exemples du même projet ni deux exemples partageant un positif (règle identique pour E2 et E3, afin que seule l'origine des négatifs diffère) ; les négatifs difficiles candidats sont filtrés s'ils sont annotés pertinents pour la requête.
- Données : uniquement B-SYN train + unités B-REAL train (réunions du split train, manuelles ou ASR). **Aucune donnée de val ou de test**, ni comme ancre, ni comme positif, ni comme négatif.
- Négatifs difficiles **d'entraînement** : pièges étiquetés par le générateur, complétés par des négatifs extraits avec E1 **sur le train uniquement**. E3 remplace ces négatifs par des négatifs aléatoires.
- Sélection du checkpoint : nDCG@10 sur **B-SYN val**, évalué toutes les 100 étapes ; nDCG@10 sur **B-REAL val** est journalisé à chaque évaluation comme garde-fou (une chute signale une sur-spécialisation sur le générateur et est rapportée) ; arrêt anticipé après 3 évaluations sans amélioration ; au plus 3 epochs. Hyperparamètres de départ : lr 2e-5, warmup 10 %, batch 64, précision mixte si GPU.
- Recherche d'hyperparamètres : au plus 4 configurations, sur val uniquement.
- Avant le run complet : test des dimensions, vérification de la perte sur un batch connu, sur-apprentissage volontaire d'un mini-lot (la perte doit tendre vers 0), mesure du temps par étape et de la mémoire. Ces diagnostics sont journalisés comme tels.
- Chaque run produit `runs/<run_id>/` : `config.yaml`, `manifest.json` (commit, état dirty, versions, révision du modèle, empreintes des données, matériel, début/fin), `train_log.jsonl`, `metrics_val.json`, et `metrics_test.json` après l'évaluation finale seulement.

Échec reconnaissable : perte qui ne baisse pas, nDCG val inférieur à E1 dès les premières évaluations, effondrement (tous les cosinus proches de 1), ou gain sur B-SYN avec chute sur B-REAL (sur-spécialisation sur nos patrons).

## 7. Règles d'accès au test

1. Le **périmètre** du test est figé : réunions listées dans `splits/summre_v1.json` (`test`) et, pour B-SYN, les projets de graine test (définis à la génération).
2. Les requêtes et pertinences de test sont figées **dès leur création**, avant toute évaluation : leur SHA-256 est inscrit dans `JOURNAL.md`.
3. Le test n'est évalué qu'avec une configuration finale choisie sur val. Chaque accès est consigné dans `runs/TEST_ACCESS.log` (horodatage, run, motif). L'obligation sera **imposée par le code** : le point d'entrée commun d'évaluation (EL-010) refusera le split test sans écriture préalable dans ce journal.
4. L'analyse d'erreurs sur le test est autorisée **après** les mesures finales, et ne sert pas à modifier le système. Si une modification est faite ensuite, le nouveau résultat est étiqueté post hoc ; un nouveau holdout est créé si les données le permettent.
5. Les seuils (abstention, classification, PAWS) sont fixés sur val ou dev.

## 8. Budget

- Calcul : Google Colab gratuit (GPU non garanti). Estimation à confirmer par le diagnostic : e5-small, ~20 000 triplets, 128 tokens, batch 64 → environ 300 étapes par epoch, quelques minutes par epoch sur T4. Budget plafond : 3 h de GPU pour l'ensemble E2 + E3 + E6.
- Si aucun GPU n'est disponible : E2 sur CPU avec un sous-échantillon, signalé, et E6 abandonné.
- Inférence : mesurée sur la VM (2 vCPU) pour la latence système.

## 9. Ce que ce protocole ne permet pas de conclure

- Un gain sur B-SYN montre une meilleure discrimination des pièges **sur nos propres constructions** : même générateur et mêmes types de pièges en train et en test, seuls les patrons, entités et dates changent. H1 ne démontre donc pas une généralisation au-delà du générateur ; seul B-REAL renseigne sur l'oral réel.
- Les thèmes de scénario SUMM-RE sont partagés entre train et test : E3 est toujours rapporté à côté de E2, et un gain sur B-REAL n'est jamais attribué aux pièges seuls.
- Les identifiants de locuteurs SUMM-RE sont supposés désigner des personnes uniques. Si deux identifiants désignaient la même personne, une fuite de personne resterait possible ; ce cas n'est pas contrôlable.
- Le corpus de préentraînement d'e5 n'est pas audité : la présence de SUMM-RE (public) n'est pas exclue. L'effet touche E1 et E2 de la même façon.
- Le corpus de recherche de B-REAL contient aussi les unités des réunions ASR du split (distracteurs plus bruités) : cela change le niveau absolu des scores, pas la comparaison appariée.
- Quelques prénoms du pool d'entraînement B-SYN (ex. Julie, Lucas, Camille) apparaissent dans les transcriptions SUMM-RE de test ; recouvrement global des 4-grammes B-SYN train / SUMM-RE test : 0,36 %.
- Les annotations de B-REAL sont provisoires tant que l'étudiant ne les a pas relues ; les résultats B-REAL sont étiquetés selon la part relue.
- La similarité ne prouve ni la validation ni la contradiction : ces relations sont évaluées par le module de relations, séparément.

## 10. Module de relations (EL-015)

**Tâche.** Pour un couple d'unités d'un même projet (B-SYN) ou d'un même groupe d'expérience (B-REAL), prédire la relation entre l'unité **la plus récente** X et l'unité **la plus ancienne** Y (ordre : rang de réunion, puis tour, puis position). Classes : `supersedes` (X remplace Y), `contradicts`, `answers` (X répond à la question Y), `supports`, `creates_action` (Y crée l'action X), `none`. Le sens est fixé par l'ordre chronologique : le module ne peut pas prédire qu'une unité ancienne remplace une plus récente (C-06).

**Couples.** Positifs : relations annotées (B-REAL : annotateur IA, provisoire ; B-SYN : générateur). Les rares relations annotées « à rebours » (`supports` ou `contradicts` d'une unité ancienne vers une récente) sont remises dans le sens chronologique, sans changer de classe. Négatifs `none` : B-SYN, couples `unrelated` du générateur ; B-REAL, **un** couple non relié par positif, tiré dans le même groupe, de préférence dans la même réunion ou la réunion voisine (graine 0). Limite : un couple non annoté n'est pas sûrement sans relation (bruit d'étiquette sur `none`).

**Modèles.**
- R0 : classe majoritaire du train.
- R1 : table des types : classe la plus fréquente du train pour chaque triplet (type de X, type de Y, même réunion), repli sur (type X, type Y) puis sur la classe majoritaire. Pas d'autre apprentissage.
- R2 : régression logistique multinomiale (variables standardisées, classes pondérées « balanced ») sur des variables structurelles : types des deux unités et leur couple, même réunion, écart de rang, écart de tours, même locuteur, recouvrement lexical, présence de nombres, indices lexicaux de changement ou de négation dans X (liste fixée a priori). Les **statuts** ne sont pas utilisés : dans l'annotation, le statut d'une question (« resolved ») découle de la relation elle-même.
- R3 : R2 + plongements e5-small (E1) **gelés** des deux extraits (`passage: ` + texte de l'extrait ; `[x, y, x·y, |x − y|]`).
Le seul hyperparamètre (C de la régression, grille 0,01 à 100) est choisi sur **val** (macro-F1 B-REAL). Entraînement : B-REAL train + B-SYN train.

**Métriques (M-03).** Principale : macro-F1 sur les 6 classes, B-REAL test. Secondaires : macro-F1 sur les 5 classes de relation seules (couples positifs, sans `none`), P/R par classe, matrice de confusion, et les mêmes mesures sur B-SYN test (4 classes). IC 95 % par bootstrap par grappes (composantes de personnes pour B-REAL, projets pour B-SYN), 10 000 tirages, graine 0. Comparaison R3 − R0 et R3 − R1 descriptive (pas d'hypothèse confirmatoire).

**Ce que cela ne permet pas de conclure.** Les étiquettes B-REAL viennent du même annotateur IA en train et en test ; le module apprend aussi son style. Les types d'unités utilisés comme variables sont ceux de l'annotation : en usage réel, ils viendraient d'un extracteur, avec ses propres erreurs.

## 11. E4 — hybride et rétrogradation (EL-016)

Systèmes, tous évalués par le harnais commun, dense = **E2** (3 graines, scores moyennés par requête comme au § 4) :
- **E4-rrf** : fusion RRF de BM25 (E0) et E2, k = 60, poids égaux, sur toute la portée de recherche.
- **E4-dem** : E2 puis rétrogradation des unités remplacées : parmi les 20 premières, pour chaque couple d'unités du même projet (B-SYN) ou du même groupe (B-REAL), R2 (§ 10, C = 0,1, entraîné sur les trains) estime la probabilité que la plus récente remplace la plus ancienne ; si elle est ≥ 0,5 (seuil fixé a priori) et que l'ancienne est classée au-dessus, l'ancienne est placée juste sous sa remplaçante. Les rangs au-delà de 20 ne bougent pas.
- **E4-rrf-dem** : E4-rrf puis la même rétrogradation.
- Contrôle : **E0-dem** (BM25 + rétrogradation), pour voir si la rétrogradation seule suffit.

Non faits, déclarés : filtre par type d'unité (il suppose de connaître l'intention de la question, EL-019) ; reranker cross-encoder (temps).

« Meilleur système seul » pour H5 : celui de E0 et E2 qui a le meilleur nDCG@10 B-SYN val (E2, voir EXPERIMENTS). Le système hybride retenu pour le test est celui des trois E4 qui a le meilleur nDCG@10 moyen sur B-SYN val et B-REAL val ; en cas d'écart < 0,005, le plus simple.
