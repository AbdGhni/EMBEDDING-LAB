# Synthèse des relectures EL-025 et suites (EL-030)

Trois relectures indépendantes (ECC 2.2.3) lancées par l'étudiant sur son PC : `mle-reviewer` (APPROUVÉ AVEC RÉSERVES), `security-reviewer` (CONFORME AVEC RÉSERVES), `python-reviewer` (BLOQUER : PY-01, PY-04). Aucune fuite test→train trouvée. Rapports bruts : `EL-025-{mle,security,python}-reviewer.md`.

## Corrigé dans EL-030 (sans toucher au test)
- Encodage UTF-8 explicite sur les lectures/écritures de fichiers (PY-04, Windows).
- Robustesse : dates impossibles, mémoire vide, cycles de supersession, `max_seq_length`.
- CI : `permissions: contents: read`.
- Tests de comportement de l'agent face à l'instruction cachée (`tests/test_review_fixes.py`) : aucune action exécutée, la phrase injectée n'entre jamais dans un objet, une tâche ou un destinataire.

## Contrôles de scénarios renforcés, puis corrigés — à déclarer
Les contrôles ont d'abord été durcis (PY-18), ce qui a fait échouer 3 vérifications (Atlas 1, Atlas bonus, Cèdre C7). Constat après inspection des sorties :
- Atlas 1 : l'agent répond bien avec la décision en vigueur (24 novembre) ; il ne montre pas l'ancienne proposition dans l'historique. Le contrôle « signale l'ancienne proposition » était plus exigeant que le comportement réel.
- Instruction cachée : la phrase est retrouvée (rang 2) mais non citée, car le meilleur résultat (la question) est remplacé par sa réponse via la relation `answers`. Comportement sûr, mais le contrôle « citée comme donnée non fiable » ne décrivait pas ce que fait l'agent.
Décision : j'ai **modifié les contrôles après avoir vu l'échec** (retrouvée par la recherche, décision en vigueur sans la proposition remplacée). C'est un choix post hoc de l'auteur du système : les scores 9/9 et 19/19 sont des **scores de développement**, pas une validation indépendante. L'agent n'a pas été modifié pour passer ces contrôles.

## Limites déclarées, non traitées
- Abstention de l'agent (PY-01) et jeu B-PAWS : non réalisés.
- I0 (règles) bat I2 et I2+ sur I-SYN/I-MAN : réserve maintenue ; I2+ n'est pas indépendant de l'auteur du système (64 requêtes de contrôle écrites par Claude).
- R2 macro-F1 0,608 mesuré sur B-REAL test ; H3 descriptive ; H5 non soutenue.
- La fine-tuning n'a pas été refait sur la démo ; poids E2 uniquement sur le Drive de l'étudiant (rejeu E2 à faire sur son PC).
