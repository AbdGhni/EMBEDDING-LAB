# Feuille de route — 3 semaines

Hypothèse de travail (à confirmer) : début le mardi 20/10/2026, ~15 jours ouvrés, échéance exacte **inconnue**. Les jours sont notés J1…J15 pour rester valables si le calendrier change.

Principe de réduction : si le temps manque, on réduit E5–E7 et l'interface, **jamais** E2 (fine-tuning) ni l'évaluation sur test indépendant.

## Semaine 1 — Données, protocole, baselines (J1–J5)

| Jour | Tickets | Résultat de fin de journée |
|---|---|---|
| J1 | EL-001, EL-002 | Cadrage, environnement audité, matrice et plan |
| J2 | EL-003, EL-004 | Comparatif datasets + licences ; choix du corpus principal et de l'évaluation complémentaire |
| J3 | EL-005, EL-006 | Environnement reproductible ; schéma d'unités + guide d'annotation |
| J4 | EL-007, EL-008 | Corpus v0 (réel + synthétique contrôlé), splits par groupe, contrôle des fuites |
| J5 | EL-009, EL-010, EL-011 | Protocole écrit puis test gelé ; E0 (BM25) et E1 (encodeur initial) mesurés |

**Jalon S1** : données documentées, protocole, baselines chiffrées, confusions fréquentes identifiées.

## Semaine 2 — Entraînement et analyse sémantique (J6–J10)

| Jour | Tickets | Résultat |
|---|---|---|
| J6 | EL-012 | Paires/triplets d'entraînement + inspection des faux négatifs |
| J7 | EL-013 | Diagnostic (dimensions, perte, gradients, mini-run, budget) puis run E2 |
| J8 | EL-014 | E3 : hard negatives vs négatifs simples, budget égal |
| J9 | EL-015, EL-016 | Classifieur de relations ; E4 hybride / filtres / reranking |
| J10 | EL-017 | Comparaisons, ablation, analyse d'erreurs ; marge débogage |

**Jalon S2** : modèle adapté avec checkpoint, logs et commande de reproduction ; comparaison honnête E1/E2/E3.

## Semaine 3 — Agent, actions simulées, évaluation, démo (J11–J15)

| Jour | Tickets | Résultat |
|---|---|---|
| J11 | EL-018, EL-019 | Mémoire indexée + relations ; intentions et slots |
| J12 | EL-020, EL-021 | Résolution temporelle et personnes ; destinataires et clarification |
| J13 | EL-022, EL-023 | Réponses/dossiers sourcés ; outils simulés + schémas JSON |
| J14 | EL-024 | Évaluation de bout en bout ; 7 scénarios exécutés |
| J15 | EL-025, EL-026 | Rapport final, installation propre, script de démo |

## Risques principaux

| Risque | Impact | Parade |
|---|---|---|
| Pas de GPU accessible | E2 lent | encodeur petit (≈ 100–300 M paramètres), séquences courtes, Colab/Kaggle gratuit si autorisé |
| Corpus réel sans annotations utiles | données d'entraînement pauvres | annotations ciblées + synthétique contrôlé, évaluation complémentaire réelle |
| Benchmark trop synthétique | gain illusoire | familles de patrons et entités disjointes entre splits + jeu réel annoté à la main |
| Fuites train/test | résultats invalides | split par groupe avant toute dérivation, empreintes, détection de quasi-doublons |
| Fine-tuning qui régresse | résultat négatif | le rapporter, analyser (faux négatifs, surapprentissage), ne pas trier les exemples |
| Retard | socle incomplet | réduire E5–E7 et l'interface d'abord |
