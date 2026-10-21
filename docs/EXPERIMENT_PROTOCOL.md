# Protocole expérimental

Version **1.0**, figée le 2026-10-21. Toute modification ultérieure crée une version 1.x, journalisée avec sa raison. Les modifications faites après un premier accès au test sont signalées comme **post hoc**.

## 1. Question et hypothèses falsifiables

Question : un encodeur adapté par apprentissage contrastif avec négatifs difficiles retrouve-t-il mieux la preuve correcte qu'un encodeur générique et que BM25, en particulier face aux pièges de statut, de personne, de date et de négation ?

| ID | Hypothèse | Réfutée si |
|---|---|---|
| H1 | E2 (fine-tuné) > E1 (initial) sur B-SYN test, métrique principale | IC 95 % de la différence nDCG@10 (E2 − E1) contient 0 ou est négatif |
| H2 | Le gain de H1 se concentre sur les pièges : précision par paires sur négatifs difficiles E2 > E1 | IC 95 % de la différence contient 0 |
| H3 | E2 ne dégrade pas la recherche sur données réelles : nDCG@10 (E2 − E1) sur B-REAL test ≥ −0,02 | borne inférieure de l'IC 95 % < −0,02 |
| H4 | À budget égal, des négatifs difficiles > des négatifs simples (E3) sur le sous-ensemble pièges | IC 95 % de la différence contient 0 |
| H5 | Hybride (BM25 + dense) ≥ meilleur des deux seuls (E4) | différence négative avec IC excluant 0 |

H1 et H2 sont les hypothèses confirmatoires. H3 à H5 et E5 à E7 sont secondaires : leurs résultats sont rapportés sans correction pour comparaisons multiples et présentés comme indicatifs.

## 2. Benchmarks

| ID | Contenu | Rôle | Construction |
|---|---|---|---|
| **B-SYN** | Projets fictifs français multi-réunions (3 réunions par projet) avec dates, montants, responsables, propositions, validations, annulations, réattributions | principal (H1, H2, H4) | générateur à graine fixe ; familles de patrons, noms de projets, personnes et plages de dates **disjoints** entre train, val et test |
| **B-REAL** | Unités extraites des réunions SUMM-RE (`splits/summre_v1.json`) + requêtes en langage naturel | validité externe (H3) | pré-annotation par Claude (`llm_provisional`), échantillon relu par l'étudiant ; uniquement réunions manuelles pour val/test |
| **B-PAWS** | PAWS-X fr (dev pour le seuil, test pour la mesure) | robustesse aux reformulations adversariales | données officielles, sans modification |

Les requêtes de B-SYN test sont écrites avec des familles de formulations **distinctes** de celles du train. Limite : un seul auteur (Claude) écrit toutes les familles, donc un biais de style commun est possible ; B-REAL sert de contrôle.

### Unités de recherche et corpus de recherche

- Unité de recherche (« document ») : une unité sémantique (`unit.schema.json`) représentée par `evidence.text`, éventuellement avec contexte (E5).
- Corpus de recherche d'une requête : **toutes** les unités du split concerné (tous projets confondus pour B-SYN, toutes réunions du split pour B-REAL). Les autres projets servent donc de distracteurs.
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
- IC 95 % par **bootstrap par grappes** : on rééchantillonne des grappes (projet pour B-SYN, composante de personnes pour B-REAL) avec remise, 10 000 tirages, graine 0. Les requêtes d'une même grappe ne sont pas traitées comme indépendantes.
- Graines d'entraînement : 3 graines (13, 42, 1234) pour E1 → E2 si le budget Colab le permet ; sinon 1, et la limite est signalée. La variance entre graines est rapportée à côté de l'IC bootstrap.
- Les effectifs (requêtes, grappes, triplets) sont toujours rapportés.

## 5. Expériences

Encodeur de référence : `intfloat/multilingual-e5-small`, révision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, licence MIT, 12 couches, dimension 384, pooling moyen, normalisation L2, 512 tokens maximum. Préfixes obligatoires selon la fiche du modèle : `query: ` pour les requêtes, `passage: ` pour les unités. Longueur max utilisée : 128 tokens (unités courtes ; 6 mots par tour en médiane), vérifiée par la mesure de troncature.

| ID | Comparaison | Seule variable | Mesures |
|---|---|---|---|
| E0 | BM25 (`rank-bm25`, k1 = 1,5, b = 0,75 ; minuscules, `_` → espace, jetons `w_N`/`sil` retirés) | — | toutes |
| E1 | e5-small sans adaptation | — | toutes |
| E2 | e5-small fine-tuné, négatifs difficiles | poids de l'encodeur | toutes, + courbes |
| E3 | E2 avec négatifs aléatoires du même split à la place des négatifs difficiles | origine des négatifs (même nombre de pas, même taille de batch, même graine) | sous-ensemble pièges |
| E4 | BM25 / dense / fusion RRF (k = 60) ; filtres type / statut ; reranking cross-encoder si le temps le permet | composant ajouté | B-SYN, B-REAL |
| E5 | unité seule vs unité + tour précédent | texte encodé | B-REAL (conditionnel) |
| E6 | e5-small vs `intfloat/multilingual-e5-base` (révision `d128750597153bb5987e10b1c3493a34e5a4502a`) | taille du modèle | B-SYN, B-REAL (conditionnel) |
| E7 | fenêtres fixes de 64 mots vs tours vs unités | granularité | B-REAL, chemin brut (conditionnel) |

Le benchmark E1/E2 est **isolé** : même corpus, mêmes requêtes, même découpage, aucun reranker ni filtre.

## 6. Entraînement (E2, E3)

- Perte : Multiple Negatives Ranking Loss (InfoNCE avec négatifs du batch) + un négatif difficile explicite par exemple ; échelle (inverse de la température) 20.
- Faux négatifs : un batch ne contient jamais deux exemples du même projet ni deux exemples partageant un positif ; les négatifs difficiles candidats sont filtrés s'ils sont annotés pertinents pour la requête.
- Données : uniquement B-SYN train + unités B-REAL train (réunions du split train, manuelles ou ASR). **Aucune donnée de val ou de test**, ni comme ancre, ni comme positif, ni comme négatif.
- Sélection du checkpoint : nDCG@10 sur **B-SYN val**, évalué toutes les 100 étapes ; arrêt anticipé après 3 évaluations sans amélioration ; au plus 3 epochs. Hyperparamètres de départ : lr 2e-5, warmup 10 %, batch 64, précision mixte si GPU.
- Recherche d'hyperparamètres : au plus 4 configurations, sur val uniquement.
- Avant le run complet : test des dimensions, vérification de la perte sur un batch connu, sur-apprentissage volontaire d'un mini-lot (la perte doit tendre vers 0), mesure du temps par étape et de la mémoire. Ces diagnostics sont journalisés comme tels.
- Chaque run produit `runs/<run_id>/` : `config.yaml`, `manifest.json` (commit, état dirty, versions, révision du modèle, empreintes des données, matériel, début/fin), `train_log.jsonl`, `metrics_val.json`, et `metrics_test.json` après l'évaluation finale seulement.

Échec reconnaissable : perte qui ne baisse pas, nDCG val inférieur à E1 dès les premières évaluations, effondrement (tous les cosinus proches de 1), ou gain sur B-SYN avec chute sur B-REAL (sur-spécialisation sur nos patrons).

## 7. Règles d'accès au test

1. Le **périmètre** du test est figé : réunions listées dans `splits/summre_v1.json` (`test`) et, pour B-SYN, les projets de graine test (définis à la génération).
2. Les requêtes et pertinences de test sont figées **dès leur création**, avant toute évaluation : leur SHA-256 est inscrit dans `JOURNAL.md`.
3. Le test n'est évalué qu'avec une configuration finale choisie sur val. Chaque accès est consigné dans `runs/TEST_ACCESS.log` (horodatage, run, motif).
4. L'analyse d'erreurs sur le test est autorisée **après** les mesures finales, et ne sert pas à modifier le système. Si une modification est faite ensuite, le nouveau résultat est étiqueté post hoc ; un nouveau holdout est créé si les données le permettent.
5. Les seuils (abstention, classification, PAWS) sont fixés sur val ou dev.

## 8. Budget

- Calcul : Google Colab gratuit (GPU non garanti). Estimation à confirmer par le diagnostic : e5-small, ~20 000 triplets, 128 tokens, batch 64 → environ 300 étapes par epoch, quelques minutes par epoch sur T4. Budget plafond : 3 h de GPU pour l'ensemble E2 + E3 + E6.
- Si aucun GPU n'est disponible : E2 sur CPU avec un sous-échantillon, signalé, et E6 abandonné.
- Inférence : mesurée sur la VM (2 vCPU) pour la latence système.

## 9. Ce que ce protocole ne permet pas de conclure

- Un gain sur B-SYN montre une meilleure discrimination des pièges **sur nos propres constructions** ; seul B-REAL renseigne sur la généralisation à de l'oral réel.
- Les annotations de B-REAL sont provisoires tant que l'étudiant ne les a pas relues ; les résultats B-REAL sont étiquetés selon la part relue.
- La similarité ne prouve ni la validation ni la contradiction : ces relations sont évaluées par le module de relations, séparément.
