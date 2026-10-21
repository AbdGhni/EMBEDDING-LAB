# Relecture EL-008 / EL-009 — `mle-reviewer` (ECC 2.2.3)

- **Exécution** : par l'étudiant, Claude Code sur son PC, branche `el-009-protocol` @ `088707a`, durée affichée 3 min 25 s. Mandat : `docs/mandates/EL-009-review.md`. L'agent n'a modifié aucun fichier.
- **Contenu ci-dessous** : résumé transmis par l'étudiant le 2026-10-21T15:22+02:00. Le rapport complet (verdicts avec fichier:ligne) est resté sur le PC ; il pourra être ajouté ici tel quel.

## Non vérifié par le relecteur

- pytest absent de l'interpréteur utilisé (environnement `uv` non installé sur le clone) : tests lus, non exécutés.
- `data/` absent du clone (hors Git par conception) : recoupements de locuteurs non recalculés, confiance accordée à `splits/summre_v1.json`.

## Verdicts et suites données

| # | Constat | Verdict relecteur | Vérification par l'orchestrateur | Suite |
|---|---|---|---|---|
| 1 | Splits : aucun groupe ni locuteur partagé ; effectifs conformes aux cibles | OK | confirmé (`leakage` du JSON) | — |
| 1b | Une réunion sans locuteur échapperait au contrôle | risque | 0 réunion sans locuteur dans les vraies données | `group_components` lève désormais une erreur ; test ajouté ; splits régénérés, empreinte inchangée `d6992f5d…` |
| 3 | Bootstrap par grappes correct | OK | — | — |
| 3b | Bootstrap percentile trop optimiste avec peu de grappes (≈ 4 % au lieu de 2,5 % pour 12 grappes) | risque | B-REAL test ne compte que **7 grappes** avec réunions manuelles (aggravation du constat) | test de permutation apparié par grappes ajouté et devenu la règle de décision |
| 3c | Pas de score par triplet pour H2/H4 | risque | confirmé | `pairwise_win` ajouté |
| C1 | Taille de B-SYN test non fixée | bloquant pour le gel | confirmé | protocole v1.1 : 240 / 32 / 48 projets |
| C2 | H3 à −0,02 quasi impossible à tenir avec 12–15 réunions | bloquant pour le gel | confirmé (7 grappes) | H3 devient descriptive, sans verdict |
| C3 | Origine des pièges du test non définie (risque de gain acquis d'avance) | bloquant pour le gel | confirmé | pièges du test définis par construction ou annotation, jamais par un modèle évalué |
| R1 | Même annotateur (Claude) pour train et test B-REAL | risque | confirmé | sous-ensemble de 5 réunions tiré avant annotation, relu par l'étudiant, rapporté à part |
| R2 | Même générateur pour train et test B-SYN | risque | confirmé | limite écrite dans le protocole § 9 |
| R3 | Thèmes partagés | risque | déjà connu (D-010) | E3 toujours rapporté avec E2 |
| R4 | Sélection de graine non encadrée ; meilleur comparateur de H5 choisi sur le test | risque | confirmé | moyenne sur graines, aucune sélection ; comparateur désigné sur val |
| R5 | Une seule graine : variance absente des IC | risque | confirmé | 3 graines si budget, sinon limite déclarée |
| R6 | `test_access.py` non imposé | risque | confirmé | imposé par le point d'entrée commun d'évaluation (EL-010) |
| R7 | Isolation E1/E2 non garantie par du code | risque | confirmé (code inexistant) | point d'entrée commun (EL-010) |
| R8 | Doublons dans un classement non détectés | risque | confirmé | les métriques refusent un classement avec doublons ; test ajouté |

## Points supplémentaires du rapport complet (traités en protocole v1.3)

| Constat | Suite |
|---|---|
| Hypothèse « un identifiant = une personne » risquée dans les deux sens | limite ajoutée au § 9 |
| Sélection du checkpoint sur B-SYN val seulement | B-REAL val journalisé comme garde-fou |
| Composition des batchs E2/E3 à préciser | même règle pour E2 et E3 |
| dtype et configuration d'évaluation à figer | même dtype fp32, empreinte de configuration, test d'égalité (EL-010) |
| Pondération par requêtes dans le bootstrap | moyenne par grappe calculée en contrôle |
| Recouvrement B-SYN / SUMM-RE test non contrôlé | mesuré : 0,36 % des 4-grammes ; prénoms communs signalés |
| Ablation « patrons hors distribution » | satisfait par construction : la famille de test (3) n'apparaît jamais en train |
| Contamination du préentraînement d'e5 | limite ajoutée |
| Distracteurs ASR dans B-REAL | limite ajoutée |
