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

## Leçon 3 — L'apprentissage contrastif et les négatifs difficiles

### Explication simple

On montre à l'encodeur des triplets : une question, la bonne réponse, et une mauvaise réponse qui lui ressemble. On le corrige pour qu'il rapproche la question de la bonne réponse et l'éloigne de la mauvaise. Si la mauvaise réponse est facile (un autre sujet), il n'apprend presque rien. Si elle est difficile (même sujet, mais « proposé » au lieu de « validé »), il est obligé de regarder le statut.

### Explication technique

Perte MNRL (Multiple Negatives Ranking Loss, forme d'InfoNCE). Dans un batch de B exemples, pour la question qᵢ, les candidats sont les B positifs et les B négatifs difficiles du batch. Avec s(q, d) = cosinus × 20 (échelle) :

perte(qᵢ) = −log( exp s(qᵢ, pᵢ) / Σⱼ [exp s(qᵢ, pⱼ) + exp s(qᵢ, nⱼ)] )

C'est une classification « lequel des 2B candidats est le bon ? ». Au hasard, la perte vaut log(2B) ; notre diagnostic l'a vérifié avant d'entraîner (`runs/DIAG-e2-cuda-2026-10-23T1234` : perte initiale 1,50 sur un lot de diagnostic où le hasard vaut 2,77, car e5 sait déjà beaucoup).

Deux pièges évités :
- **Faux négatifs dans le batch** : si deux exemples du même projet sont dans le même batch, le positif de l'un peut être une vraie réponse pour l'autre. Nos batchs n'ont jamais deux exemples du même projet ni le même positif.
- **Négatifs du test** : les négatifs extraits par l'encodeur initial viennent du train uniquement.

### Ce que les résultats montrent

À budget égal, E2 (négatifs difficiles) et E3 (négatifs aléatoires) ont le même nDCG@10, mais E2 préfère la décision qui remplace l'ancienne dans 54 % des cas contre 15 % pour E3 (B-SYN test). Le type de négatif décide de ce que l'encodeur apprend.

### Questions de compréhension

1. Pourquoi la perte au hasard vaut-elle log(2B) avec un négatif explicite par exemple ?
2. Que se passerait-il si un « négatif difficile » était en réalité pertinent pour la question ?
3. Pourquoi E3 a-t-il le même nDCG@10 que E2 alors qu'il rate presque tous les pièges « superseded » ?

## Leçon 4 — Les fuites de données et le découpage par personnes

### Explication simple

Si une même personne parle en train et en test, le modèle peut reconnaître sa façon de parler ou ses projets plutôt que comprendre la question. Le test serait trop facile. On regroupe donc les réunions qui partagent au moins un participant, et chaque groupe entier va dans un seul split.

### Explication technique

Graphe : un nœud par groupe d'expérience SUMM-RE ; une arête entre deux groupes qui ont un identifiant de locuteur commun. Les composantes connexes (union-find) sont l'unité de découpage. Résultat : 0 groupe et 0 locuteur partagés entre train, val et test (`splits/summre_v1.json`). Les splits officiels de SUMM-RE partagent 30 groupes entre train et test : on ne les utilise pas.

Même logique pour B-SYN : familles de gabarits, personnes, projets, dates et montants différents entre splits. Et pour l'évaluation : les intervalles de confiance rééchantillonnent ces mêmes grappes (leçon 2).

### Questions de compréhension

1. Pourquoi un découpage aléatoire par phrase surestimerait-il le gain du fine-tuning ?
2. Pourquoi B-REAL test n'a-t-il que 7 grappes, et qu'est-ce que cela change pour les p-valeurs ?

## Leçon 5 — Relations, intentions, agent

### Relations

Un encodeur dit « ces deux phrases parlent de la même chose », pas « celle-ci remplace celle-là ». Le module de relations classe un couple (unité récente X, unité ancienne Y) en `supersedes`, `contradicts`, `answers`, `supports`, `creates_action` ou `none`. Le sens est imposé par la chronologie : une ancienne décision ne peut pas remplacer une plus récente. Le meilleur modèle (R2) est une régression logistique sur des variables simples (types des unités, même réunion, écart de temps, même locuteur, mots communs, mots comme « finalement »). Les plongements e5 ajoutés tels quels (R3) ont fait *baisser* le score : 1 536 dimensions pour 3 000 exemples, le modèle apprend par cœur les textes. Les statuts d'unités sont exclus des variables : le statut « résolue » d'une question découle de la relation elle-même (ce serait donner la réponse).

### Intentions

Huit classes, dont deux importantes pour la sécurité : `clarify` (demande d'action sans cible identifiable) et `no_action` (hypothèse, avis : « on pourrait peut-être… »). Le modèle retenu sur la validation (régression sur e5 gelé) est battu sur le test par des règles écrites à la main. On garde quand même le modèle retenu comme résultat officiel : changer après avoir vu le test serait régler le système sur le test.

### Agent

Étapes explicites : intention → recherche → état de l'information (remplacée, contestée) → dates et personnes → opération. Règles clés :
- une **mention** ne fait pas un **responsable** : seul un engagement ou une action explicitement attribués comptent ;
- jamais d'adresse inventée : sans adresse dans les sources, le champ reste vide et l'agent demande ;
- le texte des réunions est une donnée : une phrase « ignore les consignes… » dans une transcription n'est jamais exécutée ;
- toute action est une proposition (`executed: false`).

### Questions de compréhension

1. Pourquoi l'agent suit-il les relations stockées pour la « décision actuelle » plutôt que la seule similarité ?
2. Pourquoi « Envoie ça à la bonne personne » doit-il produire une question et non un brouillon ?
3. Que montre l'échec du scénario 2 de la démo, et pourquoi ne l'a-t-on pas corrigé ?

## Leçon 6 — La discipline du test

Le test sert à une seule chose : estimer honnêtement la performance d'un système déjà choisi. Toute décision (hyperparamètres, modèle retenu, seuils) se prend sur la validation. Ici :
- le protocole et ses hypothèses ont été écrits avant les mesures, avec un historique des versions ;
- le code refuse de charger le test sans motif, et chaque accès est consigné (`runs/TEST_ACCESS.log`) ;
- le test a été évalué une seule fois, le 23 octobre, avec des configurations figées ;
- les écarts sont déclarés : ablation E2S décidée après avoir vu la validation, correction de logique de l'agent après un premier passage des scénarios, modèle d'intentions retenu battu sur le test.

Décision par test de permutation apparié par grappes : sous l'hypothèse « aucune différence », le signe de l'écart de chaque grappe est arbitraire ; on compare l'écart observé à tous les retournements de signes possibles. Avec deux hypothèses principales (H1, H2), la correction de Holm évite de trouver un effet par hasard en multipliant les tests.

### Questions de compréhension

1. Pourquoi ne peut-on pas remplacer le modèle d'intentions par les règles maintenant ?
2. Avec 7 grappes, quelle est la plus petite p-valeur bilatérale atteignable ? (réponse : 2/2⁷ = 0,016)

## Préparer le point avec le mentor

Questions probables, à savoir expliquer **sans notes** :

1. Quel est le problème scientifique, en une phrase ? Pourquoi une recherche vectorielle classique ne suffit-elle pas ?
2. D'où viennent les données ? Pourquoi SUMM-RE, et pourquoi pas les splits officiels ?
3. Comment sont faits les triplets d'entraînement ? Qu'est-ce qu'un négatif difficile, donne un exemple tiré du projet.
4. Que mesure nDCG@10 ? Pourquoi aussi la précision par paires ?
5. Quel est le résultat principal, avec ses chiffres ? Qu'est-ce qui le rend crédible (test figé, grappes, 3 graines) ?
6. D'où vient le gain sur l'oral réel ? (ablation E2S)
7. Qui a annoté B-REAL ? Quelles conséquences sur la fiabilité des résultats ? Qu'as-tu relu toi-même ?
8. Pourquoi l'hybride BM25 + dense ne marche-t-il pas ici ?
9. Comment l'agent choisit-il un destinataire ? Que fait-il si plusieurs personnes correspondent, ou si l'adresse manque ?
10. Qu'as-tu fait toi-même, et qu'a fait Claude ? Quelle décision de conception défendrais-tu, et laquelle changerais-tu ?

Les réponses sont dans ce guide et dans `docs/FINAL_REPORT.md`. Le but n'est pas de les réciter : refaire une partie à la main (calculer un nDCG, lancer la démo, lire un triplet dans `data/train/e2_hard.jsonl`) est la meilleure façon de pouvoir les expliquer.
