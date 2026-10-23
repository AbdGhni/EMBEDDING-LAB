# EMBEDDING LAB — rapport final

Projet individuel, octobre 2026. Sujet : `docs/BRIEF_ORIGINAL.txt`. Tous les chiffres renvoient à un dossier `runs/<id>/` (configuration, manifeste avec commit, métriques par requête). Détail des expériences : `docs/EXPERIMENTS.md` ; protocole : `docs/EXPERIMENT_PROTOCOL.md` (v1.8) ; journal horodaté : `docs/JOURNAL.md`.

## 1. Question

Peut-on entraîner un encodeur qui ne se contente pas de retrouver le bon sujet, mais aide un agent à savoir ce qui a été décidé, qui est responsable et quelle information est encore valable ? Et cet encodeur, avec des modules de relations et d'intentions, suffit-il à un agent qui répond avec preuves, construit des dossiers et prépare des actions sans rien inventer ?

## 2. Données

| Jeu | Contenu | Rôle | Limite principale |
|---|---|---|---|
| SUMM-RE (Linagora, CC BY-SA 4.0, révision `47cb4ec`) | 283 réunions orales françaises, dont des transcriptions manuelles | source réelle | aucune annotation de décision ou de responsabilité |
| Splits `summre_v1` | composantes de groupes reliés par un locuteur commun (union-find) : 178 / 60 / 45 réunions | éviter toute fuite de personne | les splits officiels partagent 30 groupes entre train et test (fuite évitée) |
| B-SYN | projets synthétiques à 3 réunions, 240 / 32 / 48 projets, familles de gabarits, personnes, projets, dates et montants disjoints entre splits ; pièges par construction | cas difficiles contrôlés | mesure surtout notre propre générateur |
| B-REAL | unités, relations, requêtes et pertinences annotées sur SUMM-RE par des sous-agents Claude (mandat écrit) : train 38 groupes (325 requêtes), val 10 (78), test 9 (104) | validité externe | annotateur IA unique ; test : relecture IA du sous-ensemble tiré au sort, puis relecture humaine ciblée des 43 désaccords |
| I-SYN, I-MAN | intentions : 888 / 432 / 444 requêtes générées ; 80 requêtes écrites par Claude | intentions et slots | I-MAN n'est pas indépendant de l'auteur du système |
| Atlas | projet fictif de 3 réunions, 21 unités, 8 liens | démonstration | écrit à la main, petit |

Aucune donnée personnelle réelle n'a été ajoutée ; les annotateurs ont écarté les passages de santé ou de vie privée ; aucune adresse e-mail n'existe dans les sources de démonstration.

## 3. Méthode

- **Encodeur** : `intfloat/multilingual-e5-small` (révision figée), pooling moyen, normalisation, préfixes « query: » / « passage: », 128 jetons, évaluation en fp32.
- **Fine-tuning (E2)** : Multiple Negatives Ranking Loss (InfoNCE, échelle 20) avec un négatif difficile explicite par exemple ; négatifs = pièges annotés (statut, remplacement, personne, date, montant, négation, sujet seul) + négatifs extraits par l'encodeur initial sur le train seulement ; batchs sans deux exemples du même projet ni du même positif ; lr 2e-5, batch 64, ≤ 3 epochs, sélection sur nDCG@10 B-SYN val, garde-fou B-REAL val ; 7 343 exemples (6 222 B-SYN + 1 121 B-REAL) ; Colab T4, ~2 min par run ; 3 graines (13, 42, 1234), aucune graine choisie.
- **E3** : même budget, négatifs tirés au hasard. **E2S** (diagnostique) : E2 sans les exemples B-REAL.
- **Relations** : couples orientés dans le temps (X récent, Y ancien) ; R0 majoritaire, R1 table des types, R2 régression logistique sur variables structurelles, R3 R2 + plongements gelés.
- **Hybride (E4)** : RRF BM25 + E2 ; rétrogradation des unités remplacées selon R2.
- **Intentions** : 8 classes ; I0 règles, I1 TF-IDF, I2 régression logistique sur e5 gelé ; slots par règles.
- **Agent** : étapes explicites, sorties extractives (aucun modèle de langue ne rédige) ; actions par outils simulés validés par schéma (`needs_confirmation: true`, `executed: false`).
- **Statistiques** : décision par test de permutation apparié par grappes (projets B-SYN, composantes de personnes B-REAL), estimation par bootstrap par grappes, Holm sur H1–H2 ; test évalué une seule fois après gel des configurations.

## 4. Résultats sur le test

| Système | B-SYN nDCG@10 | B-SYN paires | B-REAL nDCG@10 | B-REAL paires |
|---|---|---|---|---|
| E0 BM25 | 0,548 | 0,735 | 0,207 | 0,573 |
| E1 e5-small | 0,841 | 0,831 | 0,333 | 0,589 |
| **E2 fine-tuné** | **0,903** | 0,901 | **0,563** | 0,708 |
| E3 négatifs aléatoires | 0,898 | 0,837 | 0,564 | 0,691 |
| E4-dem hybride retenu | 0,900 | 0,911 | 0,539 | 0,736 |

- **H1 confirmée** : E2 > E1 sur B-SYN, +0,062 nDCG@10 [+0,041 ; +0,083], p Holm 0,0002.
- **H2 confirmée** : E2 > E1 sur les pièges B-SYN, +0,070 [+0,049 ; +0,090], p Holm 0,0002.
- **H3 (descriptive)** : sur l'oral réel, +0,229 [+0,152 ; +0,296] ; gain dans les 7 composantes de personnes (p = 0,016, minimum atteignable).
- **H4** : à budget égal, négatifs difficiles > aléatoires sur les pièges B-SYN (+0,064, p < 0,001) ; aucun écart en nDCG@10 ni sur B-REAL.
- **H5 non soutenue** : l'hybride retenu sur val ne fait pas mieux que E2 (−0,003 sur B-SYN, −0,024 sur B-REAL, non significatif).
- **Relations** : R2 macro-F1 0,608 sur B-REAL test (R1 0,574) ; `answers` bien reconnu (0,88), `contradicts` mal (0,37).
- **Intentions** : I2, retenu sur val, obtient 0,817 (I-SYN test) et 0,863 (I-MAN) ; les règles I0 font mieux sur le test (0,948 / 0,914). Rapporté tel quel.
- **Agent** : 8 scénarios sur 9 réussis, avec E1 comme avec E2 ; l'échec est une intention mal classée (question prise pour une comparaison).

## 5. Analyse

1. **Ce qui marche** : le fine-tuning contrastif apporte un gain net et reproductible, surtout sur l'oral réel. L'ablation E2S montre que ce gain vient des exemples réels annotés : entraîné sur le synthétique seul, l'encodeur progresse sur le synthétique (+0,12 en val) mais pas du tout sur l'oral (+0,015).
2. **Ce que les négatifs difficiles changent** : pas le classement global, mais la préférence pour l'information à jour (`superseded` 0,54 contre 0,15 avec des négatifs aléatoires). C'est exactement le comportement visé, et il reste incomplet.
3. **Limite des embeddings** : même après fine-tuning, préférer la décision qui remplace la précédente n'est réussi qu'une fois sur deux sur B-SYN. Le brief le prévoit : « une proximité vectorielle n'est pas une preuve de compatibilité logique ». L'agent s'appuie donc sur les relations stockées dans la mémoire pour suivre les remplacements, plutôt que sur la seule similarité.
4. **Hybride** : après fine-tuning, BM25 n'apporte plus rien et dégrade une fusion à poids égaux ; la rétrogradation par R2 aide en tête de liste mais prédit trop de remplacements (classes équilibrées à l'entraînement, seuil 0,5 fixé a priori).
5. **Intentions** : un classifieur sur plongements gelés généralise moins bien qu'on ne l'espérait à de nouvelles constructions de phrases. Les règles gagnent sur le test, avec un biais d'auteur probable.

## 6. Limites

- Annotations B-REAL produites par une IA ; la même IA a annoté train, val et test. Une partie du gain B-REAL peut refléter son style de questions. La relecture humaine n'a porté que sur les 43 désaccords d'un sous-ensemble ; aucun accord inter-annotateurs humain n'est revendiqué.
- B-SYN, I-SYN et la démonstration Atlas sont générés ou écrits par l'auteur du système.
- B-REAL test : 7 composantes de personnes seulement ; les intervalles et les p sont larges, H3 reste descriptive.
- Les thèmes de scénario SUMM-RE sont partagés entre splits.
- Une seule taille de modèle (e5-small) ; E5–E7 (contexte, e5-base, granularité) non faits ; pas de reranker cross-encoder ni de filtre par type.
- Agent : mémoire de démonstration de 21 unités ; la recherche n'y est pas mise à l'épreuve ; aucune mesure M-05/M-06 sur un jeu dédié (destinataires, couverture des dossiers) au-delà des contrôles de scénarios.

## 7. Coûts

Entraînement : 6 runs × ~2 min sur T4 (Colab), plus ~1 min par run de sauvegarde sur Drive. Inférence sur la VM (2 vCPU) : évaluation complète de e5-small sur B-SYN val et B-REAL val (≈ 2 300 unités, 238 requêtes) en 44 s (run `E1-e5-small-val-2026-10-22T1130`) ; agent : 24 à 384 ms par requête hors chargement des modèles. Poids : ~470 Mo par checkpoint, hors Git.

## 8. Reproductibilité

`README.md` (installation), `notebooks/colab_e2_e3.ipynb` (entraînement), `scripts/verify_data.py` (empreintes des données, identiques sur la VM et sur Colab), `runs/` (tous les résultats), `runs/TEST_ACCESS.log` (accès au test). Démonstration : `docs/DEMO.md`.

## 9. Ce qui reste à faire

Relectures indépendantes par les agents ECC sur le PC de l'étudiant (protocole d'entraînement, rapport, sécurité des outils) ; démonstration rejouée sur une machine propre avec les poids E2 ; troisième jeu d'intentions écrit par l'étudiant ; mesure M-05/M-06 sur un jeu dédié.
