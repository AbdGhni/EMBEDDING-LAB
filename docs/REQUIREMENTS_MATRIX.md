# Matrice de traçabilité des exigences

Source : `docs/BRIEF_ORIGINAL.txt` (empreinte SHA-256 `3120508a…aca52`). Les références « §… » renvoient aux sections du sujet.

Statuts : **prévu** · **en cours** · **exécuté non validé** · **validé** · **bloqué**.
Règle : « code présent » ou « test réussi » ne valide pas une amélioration scientifique ; seule une métrique sur le test gelé, comparée à la baseline sur le même protocole, le fait.

Catégories : **S** = exigence du sujet · **O** = objectif ajouté par nous (méthode) · **X** = extension facultative.

## 1. Livrables (§ Livrables)

| ID | Cat. | Exigence | Module / fichier | Test / scénario | Preuve attendue | Statut |
|---|---|---|---|---|---|---|
| L-01 | S | Dépôt structuré, exécutable, documenté | dépôt entier, `README.md` | installation propre + parcours démo | log d'installation propre | prévu |
| L-02 | S | Documentation datasets : provenance, licences, préparation, annotations, splits | `docs/DATA_CARD.md` | relecture + script de vérification des splits | DATA_CARD complète, empreintes des splits | en cours |
| L-03 | S | Baselines + modèle d'embeddings adapté, scripts d'entraînement et d'inférence | `src/embedding_lab/train/`, `scripts/` | E0, E1, E2 | `runs/<id>/` avec config, logs, métriques, checkpoint référencé | prévu |
| L-04 | S | Recherche sémantique renvoyant unités, scores, preuves | `src/embedding_lab/retrieval/` | tests unitaires + E4 | sortie JSON avec `unit_id`, score, extrait | prévu |
| L-05 | S | Module de relations (au minimum pertinence, contradiction, remplacement) | `src/embedding_lab/relations/` | évaluation relations | macro-F1, matrice de confusion | exécuté non validé (val : R2 macro-F1 0,648 ; test à faire) |
| L-06 | S | Module d'intentions (réponse, dossier, préparation d'action) | `src/embedding_lab/intents/` | évaluation intentions | macro-F1, exactitude des slots | prévu |
| L-07 | S | Mini-agent avec interface ou API, dossiers et brouillons sourcés | `src/embedding_lab/agent/`, CLI | 7 scénarios | transcriptions de démo | prévu |
| L-08 | S | Connecteurs simulés + contrats JSON, sans exécution réelle | `src/embedding_lab/tools/`, `schemas/` | test « executed=false » + schémas | CI verte sur ces tests | en cours (schémas + tests écrits ; connecteurs à venir) |
| L-09 | S | Rapport : comparaisons, métriques, ablations, erreurs, coûts, limites | `docs/FINAL_REPORT.md` | relecture indépendante | rapport | prévu |
| L-10 | S | Démonstration reproductible sur plusieurs conversations | `docs/DEMO.md`, commande de lancement | exécution sur machine propre | log de démo | prévu |

## 2. Difficultés sémantiques (§ Problématique, § Données)

| ID | Cat. | Cas difficile | Où il est mesuré | Statut |
|---|---|---|---|---|
| D-01 | S | Pertinence malgré vocabulaire différent (reformulations, requêtes courtes) | Retrieval E0/E1/E2 | prévu |
| D-02 | S | Proposition vs décision vs annulation vs rejet | sous-ensemble hard negatives « statut » | prévu |
| D-03 | S | Accord conditionnel vs validation définitive | hard negatives « condition » | prévu |
| D-04 | S | Négation | hard negatives « négation » + tests | prévu |
| D-05 | S | Changement de date, budget, montant, responsable | hard negatives « valeur » + relations `supersedes` | prévu |
| D-06 | S | Même sujet sur plusieurs réunions | requêtes multi-sources, scénario 3 | prévu |
| D-07 | S | Information obsolète ou contradictoire | relations `contradicts` / `supersedes` | prévu |
| D-08 | S | Personne citée vs personne responsable | hard negatives « rôle » + destinataires | prévu |
| D-09 | S | Demande d'information vs instruction d'action | intentions | prévu |
| D-10 | S | Destinataire absent ou ambigu | destinataires, scénario 6 | prévu |
| D-11 | S | Questions sans réponse dans les sources | abstention, tests | prévu |
| D-12 | S | Nombres et dates (dont dates relatives « vendredi ») | slots + date de référence injectée | prévu |

## 3. Expériences et comparaisons (§ Axes 1–4, § Évaluation)

| ID | Cat. | Exigence | Expérience | Preuve | Statut |
|---|---|---|---|---|---|
| X-E0 | S | Baseline lexicale (BM25 / TF-IDF) | E0 | `runs/E0-*/metrics_*.json` | en cours (val : B-SYN nDCG@10 0,517, B-REAL 0,206 ; test non mesuré) |
| X-E1 | S | Encodeur pré-entraîné sans adaptation | E1 | `runs/E1-*/metrics.json` | prévu |
| X-E2 | S | Encodeur fine-tuné contrastif, comparé à E1 sur test indépendant | E2 | métriques + checkpoint + commande | prévu |
| X-E3 | S | Hard negative mining ; effet du choix des négatifs (ablation) | E3 : hard vs négatifs simples, budget égal | métriques appariées | prévu |
| X-E4 | S | Lexical / dense / hybride, filtres, reranking | E4 | tableau comparatif | partiel (lexical, dense, RRF, rétrogradation ; filtre de type et reranker non faits) |
| X-E5 | S | Effet du contexte ajouté | E5 : unité seule vs unité + contexte | métriques | prévu (modeste) |
| X-E6 | S | Effet de la taille du modèle | E6 : petit vs moyen encodeur | métriques | prévu (modeste) |
| X-E7 | S | Stratégies de représentation : chunking fixe, tour de parole, unités structurées | E7 | métriques | prévu (modeste) |
| X-R1 | S | Classifieur de relations (LogReg/MLP sur embeddings et/ou cross-encoder/NLI) | R1 | macro-F1 | partiel (LogReg sur variables et sur plongements gelés ; cross-encoder/NLI non fait) |
| X-I1 | S | Classification d'intentions + slots (règles vs ML) | I1 | macro-F1, exactitude slots | prévu |

## 4. Métriques (§ Évaluation expérimentale)

| ID | Composant | Métriques | Dénominateur à préciser dans le protocole | Statut |
|---|---|---|---|---|
| M-01 | Retrieval | Recall@K, MRR, nDCG@K | requêtes du test ayant ≥ 1 pertinent annoté | en cours (définies dans le protocole v1.0, implémentées et testées dans `eval/metrics.py`) |
| M-02 | Embeddings | gain absolu/relatif vs E1 ; score sur sous-ensemble hard negatives | mêmes requêtes que M-01 | en cours (précision par paires + bootstrap par grappes implémentés) |
| M-03 | Relations | macro-F1, P/R par classe, matrice de confusion | paires annotées du test | prévu |
| M-04 | Intentions / slots | macro-F1 ; exact match / F1 slots ; taux de clarification appropriée | requêtes du test d'intentions | prévu |
| M-05 | Destinataires | Precision@1 (cas choisis), faux destinataires, couverture, abstentions justifiées / incorrectes | demandes d'action du test | prévu |
| M-06 | Réponses / dossiers | couverture des faits, citations valides et pertinentes, affirmations non étayées | faits attendus annotés | prévu |
| M-07 | Système | latence, mémoire, coût d'inférence (conditions de mesure documentées) | — | prévu |
| M-08 | Analyse qualitative | négations, changements temporels, confusions de personnes, attributions, dossiers incomplets, requêtes sans preuve | échantillon documenté | prévu |

## 5. Scénarios de démonstration (§ Démonstration attendue)

| ID | Scénario | Statut |
|---|---|---|
| SC-1 | Question sur une décision précise, avec preuve et référence | prévu |
| SC-2 | Question ambiguë opposant proposition et décision | prévu |
| SC-3 | Comparaison de deux réunions avec modification d'une information | prévu |
| SC-4 | Dossier multi-sources, affirmations traçables | prévu |
| SC-5 | E-mail à la personne pertinente, destinataire justifié | prévu |
| SC-6 | Demande de précision plutôt que choix arbitraire ou invention | prévu |
| SC-7 | Phrase hypothétique ne déclenchant aucune action | prévu |

## 6. Contraintes transverses

| ID | Cat. | Contrainte | Vérification | Statut |
|---|---|---|---|---|
| C-01 | S | Aucun envoi / aucune modification de service externe ; toute action reste une proposition | test CI : tout contrat d'action a `executed: false`, aucun client réseau dans `tools/` | prévu |
| C-02 | S | Aucune adresse, contact ou décision inventés | tests destinataires + schéma (`email` nul si inconnu) | prévu |
| C-03 | S | Split par conversation / groupe de réunions ; test avec projets, formulations, personnes non vus si possible | script de contrôle des splits + détection de quasi-doublons | validé pour SUMM-RE (`splits/summre_v1.json` : 0 groupe/locuteur partagé ; thèmes partagés = limite documentée) ; à refaire pour le synthétique |
| C-04 | S | Pas de données personnelles réelles sans autorisation ; contacts fictifs | DATA_CARD | prévu |
| C-05 | S | Le LLM éventuel ne masque pas les erreurs du moteur : évaluation séparée des composants | protocole | prévu |
| C-06 | S | Une relation temporelle n'est pas déduite de la seule similarité | tests relations (dates, projet, preuve) | prévu |
| C-07 | O | Contenu ingéré = donnée non fiable (injection dans une transcription) | test dédié | prévu |
| C-08 | O | Test gelé après validation du protocole | empreinte du test enregistrée dans JOURNAL | en cours (protocole et périmètre figés ; `runs/TEST_ACCESS.log` obligatoire ; qrels à figer) |
| C-09 | O | Annotations LLM = provisoires ; échantillon de contrôle relu par l'étudiant | fichier d'échantillon + statut de relecture | prévu |

## 7. Extensions facultatives (hors socle)

| ID | Extension | Statut |
|---|---|---|
| EXT-01 | Export PDF/DOCX des dossiers | non planifié |
| EXT-02 | Interface Streamlit/Gradio (une CLI suffit au socle) | non planifié |
| EXT-03 | Formulation des réponses par LLM (gabarits extractifs par défaut) | non planifié |
