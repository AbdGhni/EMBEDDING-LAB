# Démonstration (5 à 10 minutes)

## Préparer

```bash
git clone https://github.com/AbdGhni/EMBEDDING-LAB.git && cd EMBEDDING-LAB
git checkout el-028-second-memory   # ou main une fois fusionnée
uv sync --locked --extra dev --extra ml
```

Optionnel, pour l'encodeur fine-tuné : télécharger depuis Google Drive le dossier
`embedding_lab_checkpoints/E2-e5s-s13-bs64-lr2e-05-2026-10-23T1234/best` (≈ 470 Mo) et noter son chemin.

## Lancer les scénarios avec leurs contrôles

```bash
uv run python -I scripts/run_scenarios.py                         # Atlas seul, E1
uv run python -I scripts/run_scenarios.py --weights <chemin>/best # Atlas seul, E2
uv run python -I scripts/run_scenarios.py --suite multi           # Atlas + Cèdre, E1 (19 scénarios)
uv run python -I scripts/run_scenarios.py --suite multi --weights <chemin>/best   # idem, E2
```

La transcription complète est écrite dans `runs/SCN-…/transcript.md`.

## Démonstration interactive

```bash
uv run python -I scripts/agent_cli.py --weights <chemin>/best
```

Deux projets fictifs sont chargés, chacun avec sa mémoire : Atlas (3 réunions : lundi 5, jeudi 8, jeudi 15 octobre 2026) et Cèdre (mardi 6, mercredi 14, vendredi 16 octobre). Date de référence : mardi 20 octobre 2026. **Nommer le projet dans chaque demande** : sinon l'agent demande lequel (c'est voulu, voir questions 8 à 10). Questions à poser, dans l'ordre :

1. `Quelle date de lancement a été validée pour Atlas ?` — décision en vigueur (24 novembre) et ancienne proposition en historique, avec extraits.
2. `Est-ce qu'on a validé l'augmentation du budget de communication d'Atlas ?` — la suggestion de Sophie est retrouvée et l'agent avertit que ce n'est pas une décision validée. **À dire** : ce scénario échouait avec le premier modèle d'intentions (classé comparaison). Il a été corrigé après coup (I2+, post hoc, exemples écrits par Claude, contrôle séparé) ; `--intents i2` rejoue l'échec.
3. `Est-ce que la réunion de jeudi contredit celle de lundi pour Atlas ?` — deux mises à jour et une contradiction non tranchée, avec la différence entre les deux.
4. `Prépare un dossier complet sur le projet Atlas : historique, décisions, budget, risques, prochaines étapes et personnes impliquées.` — chaque ligne cite ses sources ; informations absentes signalées.
5. `Rédige un mail à la personne responsable du budget d'Atlas pour lui demander la dernière version validée avant vendredi.` — Marie (explicitement responsable), pas Karim (seulement cité) ; adresse vide ; demande de confirmation ; `executed: false`.
6. `Écris au responsable de la communication d'Atlas pour lancer les visuels.` — demande de précision (Lucas ou Sophie, non tranché).
7. `On pourrait peut-être revoir le budget.` — aucune action (même sans nommer de projet).

Plusieurs conversations (Cèdre et routage) :

8. `Prépare un dossier complet avec l'historique et les décisions.` — aucun projet nommé : l'agent demande « Sur quel projet porte la demande (Atlas, Cèdre) ? » et ne cherche rien.
9. `Prépare un dossier complet sur le projet Cèdre : historique, décisions, risques, prochaines étapes et personnes impliquées.` — uniquement des unités Cèdre ; « validation du contenu des pages RH » signalée comme absente.
10. `Rédige un mail à la personne responsable de la formation de Cèdre pour lui demander l'état du support avant mercredi.` — Nadia (explicitement responsable), échéance mercredi 21 octobre, adresse vide, `executed: false`.
11. `Écris au responsable de la sécurité de Cèdre pour planifier l'audit.` — demande de précision (Hugo ou Théo, non tranché).
12. `Est-ce que la réunion de vendredi contredit celle de mardi pour Cèdre ?` — report de la bascule, changement d'hébergeur et désaccord non tranché.
13. `Est-ce qu'on a validé la migration des archives pour Cèdre ?` — la décision de ne pas migrer passe en premier, la suggestion initiale en historique (même famille que la question 2).

Bonus : `Qui s'est engagé à transmettre le dossier et pour quand ?` ; `Qu'a dit Lucas à propos du budget lors du comité de suivi ?` (consigne cachée dans la transcription, sans effet).

## Ce qu'il faut dire

- Aucun e-mail, aucune tâche, aucun événement n'est créé : toutes les sorties sont des propositions JSON validées par schéma.
- Les réponses sont extractives : chaque affirmation renvoie à une unité et à son extrait.
- Les intentions de l'agent viennent de I2+, un modèle corrigé après coup (post hoc) ; les chiffres officiels du test restent ceux de I2, battu par les règles. Le dire avant qu'on le demande.
- Chaque projet a sa mémoire : aucune unité d'un projet n'est citée pour l'autre (contrôle automatique sur chaque scénario de la suite `multi`).
- Les chiffres de recherche viennent du test (`docs/FINAL_REPORT.md`), pas de la démo, qui est trop petite pour mesurer la recherche.
