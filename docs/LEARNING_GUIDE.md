# Guide d'apprentissage

Cours progressif : chaque notion apparaît au moment où le projet en a besoin.

## Leçon 1 — Qu'est-ce qu'un embedding, et pourquoi la proximité ne prouve rien ?

### 1.1 Explication simple

Un embedding est une liste de nombres (un vecteur) qui représente le sens d'un texte. Deux textes qui parlent de la même chose obtiennent des vecteurs qui pointent dans des directions proches.

Analogie : chaque phrase reçoit des coordonnées sur une carte du sens. « Le budget est validé » et « Le budget a été approuvé » sont dans la même rue.
Limite de l'analogie : la carte est organisée surtout par **thème**. « Le budget est validé » et « Le budget est rejeté » sont aussi dans cette rue, à quelques maisons d'écart, parce que les modèles génériques ont surtout appris à regrouper ce qui parle du même sujet.

### 1.2 Explication technique

Un encodeur (Transformer de type BERT/E5/BGE) :

1. **Tokenisation** : le texte devient une suite d'identifiants de sous-mots, ex. `["▁Le", "▁budget", "▁est", "▁valid", "é"]`.
2. **Encodage** : le Transformer produit un vecteur par token → tenseur de forme `(batch, n_tokens, d)` avec `d` = 384, 768 ou 1024 selon le modèle.
3. **Pooling** : on agrège les vecteurs des tokens en un seul vecteur par phrase, souvent la **moyenne** pondérée par le masque d'attention → forme `(batch, d)`.
4. **Normalisation L2** : chaque vecteur est ramené à une norme 1.

La **similarité cosinus** entre deux phrases a et b vaut :

cos(a, b) = (a · b) / (‖a‖ ‖b‖), soit simplement a · b après normalisation. Valeur entre −1 et 1.

Exemple illustratif (valeurs indicatives, **non mesurées**) avec un encodeur générique :

| Requête | Candidat | cos |
|---|---|---|
| « Le budget est-il approuvé ? » | « Le budget a été voté et adopté. » | ≈ 0,86 |
| « Le budget est-il approuvé ? » | « Le budget a été rejeté après discussion. » | ≈ 0,81 |

L'écart est faible : un mot (« adopté » / « rejeté ») change le sens logique mais déplace peu le vecteur. Nous mesurerons ces écarts réels en E1.

### 1.3 Pourquoi la proximité ne prouve pas qu'une décision est validée

- Le cosinus mesure une **ressemblance**, pas une **implication logique**. Proposition, validation, rejet et annulation partagent le thème et la plupart des mots.
- Le cosinus n'est **pas une probabilité** : 0,81 ne veut pas dire « 81 % de chances d'être vrai ».
- Il ignore la **chronologie** : une décision du lundi annulée le jeudi reste très proche de la question.
- Il ignore le **rôle** : « Marie demande à Karim d'envoyer le dossier » ressemble fortement à « Marie s'engage à envoyer le dossier ».

Donc le système doit combiner : embeddings (trouver les candidats) + relations, dates, statuts et preuves (décider ce qui est vrai et en vigueur).

### 1.4 Ce que notre fine-tuning cherchera à améliorer

Objectif : **réordonner** les candidats pour que, pour une requête donnée, la preuve correcte passe devant les pièges thématiquement proches.

Nous entraînerons sur des triplets (ancre, positif, négatif difficile), par exemple :

- ancre « Quelle date a été validée ? »
- positif « Le lancement est confirmé au 22 novembre. »
- négatif « Le 22 novembre a été proposé, sans validation. »

Une perte contrastive (probablement *Multiple Negatives Ranking Loss*, une forme d'InfoNCE) pousse le score ancre–positif au-dessus de chaque score ancre–négatif. Nous détaillerons la formule, les batchs et les gradients en EL-013.

Ce que le fine-tuning **ne fera pas** : prouver une contradiction ou une validation. Il améliore la récupération ; le module de relations (EL-015) et la résolution temporelle (EL-020) tranchent ensuite.

Comment saurons-nous qu'il a marché ? Recall@K / MRR / nDCG sur un test **indépendant** (formulations, projets et personnes non vus), comparés à E1 **sur le même protocole**, avec un sous-ensemble dédié aux hard negatives. S'il régresse, nous le rapporterons.

### Questions de compréhension

1. Pourquoi normaliser les vecteurs avant de calculer le cosinus permet-il de le remplacer par un simple produit scalaire ?
2. Si le modèle fine-tuné classe mieux « confirmé » que « proposé » sur nos phrases d'entraînement, pourquoi cela ne suffit-il pas à prouver qu'il a appris la notion de validation ?

## Glossaire

| Terme | Définition courte |
|---|---|
| Embedding | vecteur numérique représentant un texte |
| Pooling | agrégation des vecteurs de tokens en un vecteur de phrase |
| Cosinus | mesure d'angle entre deux vecteurs, de −1 à 1 |
| Hard negative | exemple faux mais très proche de la requête par le thème |
| Recall@K | proportion des éléments pertinents retrouvés parmi les K premiers |

## Leçon 2 — Mesurer une recherche : nDCG, MRR, Recall et bootstrap par grappes

### Explication simple

Le système rend une liste classée. On veut savoir si les bonnes preuves sont en haut. Recall@5 : « parmi les bonnes preuves, combien sont dans les 5 premières ? ». MRR : « à quel rang arrive la première bonne preuve ? » (rang 2 → 0,5). nDCG : comme une note qui donne plus de points aux bonnes preuves placées tôt, et plus encore aux preuves très pertinentes.

### Explication technique

nDCG@K = DCG@K / IDCG@K, avec DCG@K = Σᵢ (2^relᵢ − 1) / log₂(i + 1) sur les K premiers rangs i = 1…K, et IDCG le DCG du classement idéal.

Exemple calculé (test `test_ndcg_hand_computed`) : pertinences {a: 2, b: 1}, classement [x, a, b].
DCG = 3 / log₂3 + 1 / log₂4 = 1,893 + 0,5 = 2,393 ; IDCG = 3 / log₂2 + 1 / log₂3 = 3 + 0,631 = 3,631 ; nDCG = 0,659.

Un piège classé premier (pertinence 0) ne rapporte rien et repousse la vraie décision : c'est exactement ce que le fine-tuning doit corriger.

### Pourquoi un bootstrap *par grappes* ?

Les requêtes d'un même projet se ressemblent : si le modèle comprend mal le projet Atlas, il rate toutes ses requêtes ensemble. Les traiter comme indépendantes donnerait un intervalle de confiance trop étroit. On rééchantillonne donc des **projets entiers** (ou des familles de personnes pour SUMM-RE), 10 000 fois, et on regarde l'intervalle des différences E2 − E1. Si cet intervalle contient 0, on ne peut pas affirmer que le fine-tuning aide.

### Questions de compréhension

1. Pourquoi exclut-on des métriques de recherche les questions sans réponse, et où les mesure-t-on ?
2. Avec 9 projets de test, que devient la largeur de l'intervalle de confiance par rapport à 200 requêtes supposées indépendantes ?
