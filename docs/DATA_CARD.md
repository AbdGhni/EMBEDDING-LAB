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

## 3. Stratégie proposée (à valider en EL-004)

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
