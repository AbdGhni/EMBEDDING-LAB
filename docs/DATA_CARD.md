# Fiche des données

Statut : **EL-003 exécuté, choix à valider (EL-004)**. Aucune donnée n'est encore téléchargée dans le projet ; seules des lectures de métadonnées et de colonnes texte ont servi à l'inventaire.

Date d'accès des sources : 2026-10-20. Langue cible : **français** (décision D-004).

## 1. Comparatif des candidats

| Corpus | Langue | Contenu | Taille | Licence (source) | Redistribution | Pertinence | Verdict |
|---|---|---|---|---|---|---|---|
| **SUMM-RE** (LINAGORA, ANR-20-CE23-0017) | FR | Réunions spontanées de 3–4 personnes, ~20 min ; types *reporting*, *decision*, *planning* ; transcriptions mot à mot horodatées par locuteur | 283 réunions (210 train ≈ 67 h ASR ; 36 dev + 37 test ≈ 24 h transcrites à la main) | CC BY-SA 4.0 (fiche HF) | oui, avec attribution et même licence pour les dérivés | **forte** : décisions, planification, attribution de rôles réelles | **corpus principal** |
| FREDSum (linto-ai) | FR | Débats politiques télévisés, résumés extractifs/abstractifs | non précisé sur la page | CC BY-SA 4.0 (dépôt GitHub) | oui, mêmes conditions | faible : débats, peu de décisions/actions | écarté (éventuel test de robustesse) |
| PAWS-X (Google) | FR inclus | Paires de paraphrases adversariales (ordre des mots) | fr : 49 401 train (traduit automatiquement), 2 000 dev, 2 000 test (traduits humainement) | « may be freely used for any purpose » (fiche HF) | oui | moyenne : robustesse aux reformulations proches | **évaluation complémentaire** |
| XNLI | FR inclus | Paires NLI traduites | 2 500 dev + 5 000 test par langue | **non vérifiée** (la page officielle renvoie à l'article) | non vérifiée | moyenne : relations contradiction/implication | en attente de vérification de licence |
| AMI | EN | ~100 h de réunions, actes de dialogue | ~100 h | CC BY 4.0 (page officielle) | oui | forte en anglais, mais hors langue cible | écarté (traduction = biais supplémentaire) |
| ICSI, QMSum, MeetingBank | EN | Réunions / résumés | — | non examinées en détail | — | hors langue cible | écartés |

## 2. Constats vérifiés sur SUMM-RE

- Révision figée : `47cb4ec3437ef5497b6092b8c6d1e0b5b1d86dc0` (dernière modification 2024-10-15), accès non restreint.
- Structure : une ligne par **piste de locuteur** (`meeting_id`, `speaker_id`, `audio`, `segments`, `transcript`). Les `segments` portent `start`/`end` en secondes et les mots horodatés : on peut reconstruire les tours de parole en interclassant les pistes par temps.
- Les parquets pèsent ~300–540 Mo chacun à cause de l'audio ; la lecture des seules colonnes texte prend ~4 s par fichier (`scripts/inspect_summre.py`). **Aucun téléchargement de l'audio n'est nécessaire.**
- Volume texte : dev 783 257 caractères, test 784 243, train 4 246 662.
- Transcriptions en minuscules, sans ponctuation (ex. « attention aux jours fériés là on a rien … qui serait moi je dis qu' alexandre … »). Le train est transcrit automatiquement (Whisper) : qualité inférieure.
- Une partie du dev a été anonymisée semi-automatiquement ; les participants sont des personnes réelles recrutées (campus, Prolific). Les prénoms dans les transcriptions sont donc à traiter avec prudence (voir § 5).

### Fuite dans les splits officiels

L'identifiant `004c_PAPH` se lit : expérience `004`, réunion `c` (trois réunions par expérience), puis un code de scénario. En comparant les numéros d'expérience :

| Paire | Groupes partagés |
|---|---|
| train / test | **30** |
| train / dev | **27** |
| dev / test | 0 |

Les trois réunions d'une même expérience réunissent vraisemblablement les mêmes personnes sur un projet suivi (hypothèse à confirmer dans l'article SUMM-RE). Utiliser les splits officiels mettrait donc les mêmes personnes, et probablement le même projet, en train et en test. **Nous redécouperons par groupe d'expérience** (EL-008).

## 2 bis. Acquisition réalisée (EL-007, 2026-10-20)

Commande : `uv run python -I scripts/fetch_summre.py` (révision `47cb4ec`, durée observée 23:42:06 → 23:46:53, Europe/Paris). Lit seulement les colonnes texte.

| Fichier (hors Git) | Lignes | SHA-256 |
|---|---|---|
| `data/raw/summre/tracks_dev.jsonl` | 130 pistes | `0b422230…463525b` |
| `data/raw/summre/tracks_test.jsonl` | 124 pistes | `7bf11019…a421eaca` |
| `data/raw/summre/tracks_train.jsonl` | 684 pistes | `4e248e79…5616d56bad11` |
| `data/processed/summre_meetings.jsonl` | 283 réunions, 100 651 tours, 6,32 M caractères | `05a46a7f…69665298` |

Empreintes complètes : `data/raw/summre/manifest.json` et `data/processed/summre_meetings.manifest.json`. Une première version de `summre_meetings.jsonl` (`43c2c6a6…`), sans les métadonnées de réunion, a été remplacée.

Contrôles :
- 0 tour dont le texte ne correspond pas à ses offsets dans le texte canonique.
- Types de réunion (code de la fiche) : manuelles = 25 décision, 26 planification, 22 reporting ; ASR = 69, 68 et 73.
- 92 groupes de 3 réunions, 3 groupes de 2, 1 groupe d'une seule réunion.
- **Aucun groupe n'est entièrement transcrit à la main** : 57 groupes mélangent réunions manuelles et ASR, 39 sont entièrement ASR.
- Tours courts : 6 mots en médiane, 25 au 90e centile. Conventions de transcription : mots composés liés par `_` (`en_fait`, `il_y a`), marqueurs `+` et `*`, disfluences (« euh », « ben »). La tokenisation de BM25 devra en tenir compte.
- Les marqueurs de décision réels existent bien (ex. « ben c'est gravé dans le marbre » dans `006b_EADH`).

Conséquence pour les splits (EL-008) : un groupe de test contiendra aussi des réunions ASR. Proposition : on annote en priorité les réunions manuelles des groupes de test ; leurs réunions ASR restent dans le test comme contexte (évolution d'une décision d'une réunion à l'autre) et ne servent jamais à l'entraînement.

## 2 ter. Splits `summre_v1` (EL-008)

Fichier versionné : `splits/summre_v1.json` (identifiants uniquement), SHA-256 `d6992f5d7548a0b5e42c8f692f86c85ef4e511c16041150d2cf4bc6934f4109f`. Commande : `uv run python -I scripts/make_splits.py` (graine 13, 20 000 tirages, ~2 s). Entrée : `summre_meetings.jsonl` `05a46a7f…`.

**Unité de découpage** : composante connexe de groupes d'expérience reliés par un identifiant de locuteur commun. 80 identifiants sur 212 apparaissent dans plusieurs groupes. Les identifiants sont numérotés de 001 à 212 pour tout le corpus, ce qui suggère des participants revenus pour plusieurs expériences ; la fiche ne le dit pas explicitement : **hypothèse prudente**. On obtient 41 composantes, dont une de 27 groupes (81 réunions), affectée d'office au train.

| Split | Réunions | Manuelles (décision / planif. / reporting) | ASR | Scénarios |
|---|---|---|---|---|
| train | 178 | 47 (16 / 16 / 15) | 131 | A, B, C, D, E |
| val | 60 | 11 (4 / 3 / 4) | 49 | A, B, D, E |
| test | 45 | 15 (5 / 7 / 3) | 30 | A, B, D, E |

Contrôles (`leakage` dans le fichier) :
- 0 groupe et 0 identifiant de locuteur présents dans plusieurs splits.
- Recouvrement de 8-grammes avec le train : médiane 0,09 %, maximum 8,2 % (`008a_EARH`). L'inspection montre que ce maximum vient de répétitions (« c'est c'est c'est ») et de jetons de remplacement, pas de contenu partagé.
- **Limite** : les sujets de scénario A, B, D, E figurent à la fois en train et en test (seulement 5 scénarios pour tout le corpus). Les *personnes* et les *groupes* du test sont inédits, pas les *thèmes*. Les données synthétiques apporteront des projets entièrement inédits.

### Artefact : jetons `w_N` / `sil`

Des séquences comme `sil w_1 w_2 w_3 w_4 w_5 sil` (vraisemblablement des passages masqués ou inintelligibles) touchent 385 tours ASR sur 71 571 (0,54 %) et 34 tours manuels sur 29 080 (0,12 %), dans 9 réunions. Elles seront exclues des unités et des requêtes (EL-007b) et neutralisées pour BM25.

## 2 quater. B-SYN (EL-007c)

Générateur : `src/embedding_lab/synth/` ; commande `uv run python -I scripts/make_bsyn.py --out data/bsyn` (graines 2024 / 2025 / 2026). Données entièrement fictives produites par notre code : aucune contrainte de licence tierce ; elles restent hors Git car régénérables à l'identique (vérifié : deuxième génération identique à l'octet près). Manifeste : `data/bsyn/manifest.json` (SHA-256 `050f8e7d…`).

| Split | Projets | Réunions | Unités | Requêtes (avec réponse) | Triplets à piège |
|---|---|---|---|---|---|
| train | 240 | 720 | 1 897 | 2 049 (1 920) | 3 104 |
| val | 32 | 96 | 255 | 175 (160) | 235 |
| test | 48 | 144 | 377 | 414 (384) | 622 |

Pièges du test, par type : status 172, topic_only 196 (dont 48 d'un autre projet), superseded 82, person 54, negation 52, date 48, condition 18.

Construction :
- Trois objets par projet (budget, date de lancement, dossier), chacun avec un scénario tiré au sort (5, 4 et 3 scénarios). Relations générées : `supersedes`, `contradicts` (conflit non résolu), `answers`, `unrelated`.
- 16 types d'unités × 4 familles de formulations : familles 0–1 en train, 2 en val, 3 en test. 6 types de requêtes × 5 familles : 0–1 train, 2 val, 3–4 test. Montants disjoints (milliers ≡ 0, 1, 2 mod 3), années disjointes (2024, 2025, 2026), prénoms et noms de projets disjoints ; « Atlas » réservé à la démo.
- Contrôles : 0 prénom et 0 projet partagés entre splits ; 4-grammes des unités de test présents dans le train (entités et nombres retirés) : **0 %** ; requêtes : 1,8 %.
- Pertinence : 2 = réponse en vigueur, 1 = utile (historique, conflit non résolu à signaler), 0 = piège. Requêtes sans réponse : marquées `answerable: false`, sans pertinences.

Limites :
- Texte écrit, assez court et régulier : bien plus facile que l'oral de SUMM-RE.
- Un seul auteur (Claude) pour toutes les familles ; les types de pièges sont identiques entre train et test.
- Accords grammaticaux approximatifs possibles (prénoms sans genre).
- Pendant la mise au point du générateur, l'orchestrateur a affiché les unités et requêtes d'un projet de test (`bs-test-000`) pour corriger deux bugs de rendu. Aucun modèle n'a été évalué et rien n'a été ajusté en fonction d'un score.

## 2 quinquies. B-REAL (EL-007b)

Annotation **provisoire** de SUMM-RE par des sous-agents Claude (mandat `docs/mandates/EL-007b-annotation.md` v2 ; pilote sur 015), une tâche par groupe d'expérience. Fichiers bruts versionnés : `annotations/breal/raw/<groupe>.json` (CC BY-SA 4.0, voir `annotations/breal/README.md`). Assemblage : `uv run python -I scripts/assemble_breal.py` → `data/breal/` (hors Git, régénérable depuis les fichiers bruts).

| Split | Groupes | Unités | Requêtes (avec réponse) | Triplets à piège | Grappes (composantes) |
|---|---|---|---|---|---|
| val | 10 | 1 255 | 89 (78) | 262 | — |
| test | 9 | 975 | 120 (105) | 303 | 7 (28, 21, 14, 14, 14, 7, 7 requêtes) |

Pièges du test : topic_only 139, superseded 68, person 43, date 19, amount 13, status 12, condition 6, negation 3. Contrairement à B-SYN, les pièges réels sont surtout des propositions écartées et des voisins thématiques ; les pièges « statut » purs y sont rares.

Écarts et limites :
- Annotateur unique (Claude) pour val et test ; aucune relecture humaine à ce stade. Sous-ensemble de relecture : 5 réunions de test (35 requêtes répondables), classeur `annotations/breal/review/relecture_v1.xlsx`.
- Quatre groupes de val (008, 014, 015, 021) ont été annotés avant la consigne « 40 unités au plus par réunion » ; 014 a 8 questions répondables au lieu de 7 au plus.
- Identités des locuteurs déduites de la transcription (`speaker_names`), souvent incertaines ; transcription ASR très bruitée pour les réunions non manuelles.
- Les annotateurs ont volontairement écarté des informations personnelles ou de santé sans rapport avec la tâche.
- Interruption de trois tâches par la limite d'usage (reprises depuis leur contexte).

### Relecture IA du sous-ensemble et test v2 (2026-10-22)

Cinq relecteurs IA **neufs** (sous-agents Claude n'ayant pas produit les annotations ; mandat `docs/mandates/EL-007b-relecture-ia.md`) ont relu les 5 réunions tirées au sort. Ce n'est **pas** un accord inter-annotateurs humain : c'est un accord entre deux passes de Claude.

| Élément jugé | Correct | Erreur | Douteux | Taux d'accord |
|---|---|---|---|---|
| Unités (197) | 182 | 4 | 11 | 92,4 % |
| Couples question–unité (182) | 157 | 17 | 8 | 86,3 % |
| Bonnes réponses oubliées | — | 5 | — | — |

Erreur dominante : 12 des 17 erreurs de pertinence sont des unités notées 1 (« utile ») alors qu'elles ne répondent pas à la question (même sujet, sans l'information demandée). Ce biais concerne probablement aussi les réunions non relues : les qrels de pertinence 1 de B-REAL sont donc **légèrement trop généreuses**, ce qui gonfle un peu nDCG pour tous les systèmes de la même façon.

Arbitrage (`scripts/apply_breal_review.py`, journal `annotations/breal/review/ia/adjudication.json`) : 27 corrections appliquées (4 unités, 17 pertinences, 5 ajouts, 1 question retirée car devenue sans réponse directe : 047c q12, genre musical du DJ jamais tranché) ; les verdicts « douteux » ne changent rien. Le test B-REAL **v2** (104 requêtes répondables, 302 triplets) remplace la v1 ; aucune évaluation n'a été faite sur la v1.

## 3. Stratégie retenue (D-008)

1. **Test réel indépendant** : réunions transcrites à la main de SUMM-RE, groupes d'expérience entiers, **jamais vus à l'entraînement**. Unités, requêtes et pertinences annotées (pré-annotation LLM provisoire + échantillon relu par l'étudiant).
2. **Entraînement** : (a) conversations synthétiques françaises multi-réunions construites pour les cas difficiles (proposition/décision/annulation, réattribution, dates, montants), avec patrons, projets et entités séparés entre splits ; (b) unités extraites des réunions SUMM-RE des groupes d'entraînement.
3. **Évaluation complémentaire** : PAWS-X fr (dev/test traduits humainement) pour la robustesse aux reformulations ; XNLI fr pour les relations si la licence est confirmée.
4. **Démo** : projet fictif (type « Atlas ») distinct du test, contacts fictifs uniquement.

Limite connue : le test réel est oral et spontané alors que l'entraînement synthétique est écrit. C'est voulu, pour ne pas mesurer seulement la reconnaissance de nos propres patrons, mais cela risque de réduire le gain mesuré.

## 4. Licences et obligations

- SUMM-RE et FREDSum sont sous CC BY-SA 4.0 : citation obligatoire, et nos annotations dérivées de SUMM-RE devront être publiées sous CC BY-SA 4.0 si on les diffuse.
- La licence du code du dépôt (à choisir) est distincte de celle des données.
- Les corpus restent hors Git ; on versionne des scripts d'acquisition à révision figée et des empreintes.

## 5. Données personnelles

- Les contacts et e-mails de la démo sont exclusivement fictifs.
- Aucune adresse ni identité réelle n'est ajoutée aux données SUMM-RE. Les prénoms éventuels restent ceux de la transcription publiée, sans enrichissement.
