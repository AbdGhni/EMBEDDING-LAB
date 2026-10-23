# Démonstration (5 à 10 minutes)

## Préparer

```bash
git clone https://github.com/AbdGhni/EMBEDDING-LAB.git && cd EMBEDDING-LAB
git checkout el-019-intents
uv sync --locked --extra dev --extra ml
```

Optionnel, pour l'encodeur fine-tuné : télécharger depuis Google Drive le dossier
`embedding_lab_checkpoints/E2-e5s-s13-bs64-lr2e-05-2026-10-23T1234/best` (≈ 470 Mo) et noter son chemin.

## Lancer les 9 scénarios avec leurs contrôles

```bash
uv run python -I scripts/run_scenarios.py                         # E1
uv run python -I scripts/run_scenarios.py --weights <chemin>/best # E2
```

La transcription complète est écrite dans `runs/SCN-…/transcript.md`.

## Démonstration interactive

```bash
uv run python -I scripts/agent_cli.py --weights <chemin>/best
```

Mémoire : projet fictif Atlas (3 réunions : lundi 5, jeudi 8, jeudi 15 octobre 2026) ; date de référence : mardi 20 octobre 2026. Questions à poser, dans l'ordre :

1. `Quelle date de lancement a été validée pour Atlas ?` — décision en vigueur (24 novembre) et ancienne proposition en historique, avec extraits.
2. `Est-ce qu'on a validé l'augmentation du budget de communication ?` — **échec connu** : classée comme comparaison. Le montrer et l'expliquer (erreur du modèle d'intentions, non corrigée pour ne pas régler le système sur la démo).
3. `Est-ce que la réunion de jeudi contredit celle de lundi ?` — deux mises à jour et une contradiction non tranchée, avec la différence entre les deux.
4. `Prépare un dossier complet sur le projet Atlas : historique, décisions, budget, risques, prochaines étapes et personnes impliquées.` — chaque ligne cite ses sources ; informations absentes signalées.
5. `Rédige un mail à la personne responsable du budget pour lui demander la dernière version validée avant vendredi.` — Marie (explicitement responsable), pas Karim (seulement cité) ; adresse vide ; demande de confirmation ; `executed: false`.
6. `Écris au responsable de la communication d'Atlas pour lancer les visuels.` — demande de précision (Lucas ou Sophie, non tranché).
7. `On pourrait peut-être revoir le budget.` — aucune action.

Bonus : `Qui s'est engagé à transmettre le dossier et pour quand ?` ; `Qu'a dit Lucas à propos du budget lors du comité de suivi ?` (consigne cachée dans la transcription, sans effet).

## Ce qu'il faut dire

- Aucun e-mail, aucune tâche, aucun événement n'est créé : toutes les sorties sont des propositions JSON validées par schéma.
- Les réponses sont extractives : chaque affirmation renvoie à une unité et à son extrait.
- Les chiffres de recherche viennent du test (`docs/FINAL_REPORT.md`), pas de la démo, qui est trop petite pour mesurer la recherche.
