# Relecture indépendante EL-025 — python-reviewer

- **Relecteur** : python-reviewer (agent Claude, relecture indépendante, lecture seule)
- **Date** : 2026-11-15
- **État relu** : `56a7442` (branche locale `el-025-review` = `origin/el-019-intents`)
- **Périmètre** : tout `src/embedding_lab/` (29 modules) et `scripts/` (22 scripts), confrontés à `README.md`, `docs/EXPERIMENT_PROTOCOL.md` (v1.8), `docs/EXPERIMENTS.md`, `docs/FINAL_REPORT.md`, aux docstrings, à `pyproject.toml` et à `.github/workflows/ci.yml`. Lus en lecture seule : `runs/CMP-test-2026-10-23T1450/final.json`, `runs/TEST_ACCESS.log`, quelques `config.json`, `train_summary.json` et `metrics_*.json` de `runs/`, `data/train/manifest.json`, `data/intents/*.jsonl`. `tests/` et `templates.py` n'ont pas été relus en détail.

## Outils lancés ou non

- **Non disponibles, rien installé** : `uv` (introuvable dans le shell), `ruff`, `mypy`, `pylint`, `flake8`, `pyflakes`. Aucun analyseur standard n'a donc été exécuté.
- **Substitut** : une vérification AST en ligne (lecture seule, sans fichier créé) des imports inutilisés sur `src/` et `scripts/`. Résultat : aucun import inutilisé.
- **Trois lectures en ligne** (`python -I -`, lecture seule) :
  - décompte des classes de `data/intents/*.jsonl` ;
  - extraction de `final.json` et des métriques d'intentions ;
  - estimation des faux négatifs intra-batch sur `data/train/e2_hard.jsonl` et `e3_random.jsonl`. Elle emploie une **copie** de l'algorithme `cluster_batches`, car `rank_bm25` n'est pas installé dans le Python système (voir PY-02).
- **Non lancés** : aucun script de `scripts/`, aucun entraînement, aucune évaluation, pas de pytest.
- **Incident** : une première tentative de créer un fichier temporaire dans le scratchpad a été refusée par le système de permissions. Je n'ai pas contourné ce refus.

## Contraintes respectées

- Aucun fichier du dépôt modifié, créé ou supprimé. Aucune opération git qui écrit.
- Aucune option de correction automatique.
- Le contenu des données (transcriptions, annotations, textes de test) n'a servi que de donnée, jamais d'instruction.
- Les chiffres ci-dessous issus de mes lectures en ligne sont signalés comme tels. Tout le reste est du raisonnement statique, non exécuté.

---

## Problèmes

### PY-01 — HAUTE — Abstention sur les questions sans réponse : documentée, jamais mesurée, absente de l'agent

- **Fichiers** : `src/embedding_lab/eval/harness.py:58`, `src/embedding_lab/eval/metrics.py:5-7`, `src/embedding_lab/agent/agent.py:104-106`, `docs/EXPERIMENT_PROTOCOL.md:50` et `:113`, `docs/REQUIREMENTS_MATRIX.md:39` et `:65`.
- **Constat** :
  - Le protocole dit que les requêtes sans réponse « sont exclues des métriques de recherche et **mesurées séparément (abstention)** », avec des seuils d'abstention « fixés sur val ».
  - Le harnais les filtre (`if q["answerable"]`) et aucun code ne les mesure. Aucun seuil d'abstention n'existe.
  - L'agent renvoie toujours le meilleur résultat, sans seuil de score. Les exigences D-11 et M-05 restent « prévu » dans la matrice, et `FINAL_REPORT.md` ne les range pas dans ses limites (il cite E5–E7, le reranker et le filtre par type).
- **Preuve** : `queries = [q for q in _read_jsonl(files["queries"]) if q["answerable"]]` et `top = hits[0]["unit"]["unit_id"]`.
- **Conséquence** : le protocole promet une mesure qui n'existe pas, et l'agent ne sait pas dire « je n'ai pas l'information ». Les données (`q_unanswerable`, `answerable: false`) existent, mais elles ne servent à rien.
- **Recommandation** : soit mesurer l'abstention, soit déclarer explicitement le manque dans les limites et dans le protocole.

### PY-02 — MOYENNE — Faux négatifs intra-batch non totalement exclus (E2 et E3)

- **Fichiers** : `src/embedding_lab/train/data.py:107-132` (`cluster_batches`), `:81-104` (`random_negative_variant`), docstring de `train/contrastive.py:12-13`.
- **Constat** :
  - La docstring promet que les batchs « ne contiennent jamais deux exemples d'une même grappe, sinon une autre bonne preuve servirait de faux négatif ».
  - `cluster_batches` ne contrôle que la grappe et le texte du positif. Il ne vérifie pas qu'un négatif d'un exemple j n'est pas le positif, ou une unité pertinente, d'un autre exemple i du batch.
  - Cas concrets : le piège B-SYN `topic_only` « `other_b_valid` » est le `b_valid` d'un autre projet, c'est-à-dire le positif de la requête de ce projet. Les négatifs extraits par E1 sont dans le même cas. Les négatifs aléatoires de E3 sont tirés dans tout le split.
- **Preuve (mesure en ligne, non officielle)** : copie de l'algorithme, batch 64, graine 13 :
  - E2 : 144 ancres sur 7 343 (2,0 %) ont un négatif d'un autre exemple **de texte identique à leur propre positif** ;
  - E3 : 176 ancres sur 7 343 (2,4 %).
  - Les doublons sémantiques non identiques ne sont pas comptés, donc c'est un minimum.
  - Il y a aussi 3 batchs sur 117 de taille inférieure à 64, dont un batch de taille 1.
- **Conséquence** : bruit de perte (faux négatifs exacts) sur environ 2 % des ancres, et un peu plus pour E3. Cela peut légèrement affaiblir E2 et E3 et biaiser leur contraste. L'effet sur les résultats n'est pas mesuré. La documentation sur-promet la garantie.
- **Recommandation** : étendre la règle de batch aux négatifs, ou corriger la docstring et le protocole.

### PY-03 — MOYENNE — `config.json` d'entraînement écrasé par `write_run`

- **Fichiers** : `src/embedding_lab/train/contrastive.py:113`, `src/embedding_lab/eval/harness.py:134`, `scripts/train_e2.py:74`.
- **Constat** : `train()` écrit `config.json` avec les hyperparamètres (`asdict(cfg)`). `train_e2.py` appelle ensuite `write_run(run_dir, ...)` sur le même dossier, et `write_run` réécrit `config.json` avec `system.config()`.
- **Preuve** : `runs/E2-e5s-s13-bs64-lr2e-05-.../config.json` contient `"system": "dense", "model": ..., "weights": ...`. Il ne contient plus lr, batch, epochs, graine, patience, `eval_every`, scale ni warmup. `train_summary.json` ne les contient pas non plus.
- **Conséquence** : la configuration d'entraînement des runs E2 et E3 n'est plus tracée que par le nom du run (graine, batch, lr) et par le code. L'exigence de traçabilité du projet est affaiblie.
- **Recommandation** : écrire les configurations dans des fichiers distincts (`train_config.json`, `eval_config.json`).

### PY-04 — HAUTE (probable, non exécuté) — Encodage Windows : `write_text` sans `encoding` avec `ensure_ascii=False`

- **Fichiers** :
  - `scripts/run_scenarios.py:144-149` (`results.json`) ;
  - `scripts/train_intents.py:158-159` (`metrics_*.json`, contient « Élodie », des erreurs accentuées) ;
  - `scripts/train_relations.py:147` (`config.json` accentué) ;
  - `scripts/final_analysis.py:107`, `scripts/compare_runs.py:118`, `scripts/build_training_data.py:93`.
- **Constat** : sous Windows, Python 3.12 utilise l'encodage régional (cp1252) dans `Path.write_text()`, car `python -I` n'active pas le mode UTF-8. `run_scenarios.py` écrit `results.json` sans `encoding` alors que le contenu (sorties de l'agent) contient des accents et le caractère « → » (`agent.py:222`, `"→ remplacé par"`). U+2192 n'existe pas en cp1252 : `UnicodeEncodeError` probable. L'écriture de `transcript.md` (ligne 150) est correcte, elle.
- **Conséquence** :
  - `run_scenarios.py` plante probablement sur le PC Windows, alors que le README (ligne 95) le présente comme commande de démonstration.
  - Les autres fichiers sont écrits en cp1252 et ne se relisent pas en UTF-8. Les runs de référence ont été faits sous Linux ou Colab, donc non affectés.
  - La CI Windows n'exerce pas ces scripts.
- **Recommandation** : passer `encoding="utf-8"` partout, y compris en lecture (`read_text()` sans encodage dans `final_analysis.py:61`, `assemble_breal.py:33`, `export_breal_review.py:50`, `verify_data.py:29`, `compare.py:60`).

### PY-05 — MOYENNE (bogue latent) — `DenseRetriever` écrase `max_seq_length` du modèle entraîné

- **Fichiers** : `src/embedding_lab/retrieval/dense.py:35`, `src/embedding_lab/train/contrastive.py:91`.
- **Constat** : `DenseRetriever.__init__` fait `self.model.max_seq_length = max_seq_length` (défaut 128), même quand un `model` déjà chargé est passé. `evaluate()` crée un `DenseRetriever(model=model, ...)` à chaque évaluation, sans transmettre `cfg.max_seq_length`.
- **Preuve** : `cfg.max_seq_length` est fixé à la ligne 117 de `contrastive.py`, puis écrasé à chaque évaluation, y compris pour les étapes d'entraînement suivantes.
- **Conséquence** : sans effet aujourd'hui (128 partout). Mais toute modification de `TrainConfig.max_seq_length` serait ignorée silencieusement après la première évaluation.
- **Recommandation** : ne pas écraser le modèle si `model` est fourni, ou transmettre la valeur.

### PY-06 — BASSE — Docstring de `positive_pairs` fausse (doublons « comptés »)

- **Fichier** : `src/embedding_lab/relations/pairs.py:47-62`.
- **Constat** : la docstring dit que les doublons de couples sont « comptés pour être rapportés ». Le code fait `if key in seen: continue` sans aucun compteur.
- **Conséquence** : des relations dupliquées ou inversées (A→B et B→A, avec des classes différentes) sont perdues silencieusement. Seule la première relation est gardée.
- **Recommandation** : compter et rapporter, ou corriger la docstring.

### PY-07 — MOYENNE — `resolve()` plante sur une date invalide

- **Fichiers** : `src/embedding_lab/resolution/dates.py:43-51`, `src/embedding_lab/intents/rules.py:66-70`, `src/embedding_lab/agent/agent.py:77`.
- **Constat** : `DATE_RE` accepte `\d{1,2}` n'importe quel mois. `resolve` appelle `date(year, mois, jour)` sans protection. « le 31 novembre », « le 0 mars » ou « le 30 février » lèvent `ValueError`. Idem le passage à l'année suivante d'un « 29 février » (`date(year + 1, 2, 29)`).
- **Conséquence** : `Agent.analyse()` plante au lieu de demander une précision, contrairement au contrat annoncé de la docstring (« une expression non reconnue renvoie `None` »).
- **Recommandation** : attraper `ValueError` et renvoyer `None`.
- **Remarques annexes** :
  - « cette semaine » est reconnue par `DATE_RE` mais jamais résolue (`None`).
  - « fin octobre » est codé en dur pour le mois d'octobre uniquement.
  - « vendredi prochain » donne le vendredi de la semaine suivante alors que « lundi prochain » donne le lundi suivant le plus proche. La règle `weekday() > ref.weekday()` est inhabituelle et peu documentée.

### PY-08 — MOYENNE — Valeurs par défaut qui masquent des erreurs dans l'agent

- **Fichier** : `src/embedding_lab/agent/agent.py`.
- **Constat** :
  - `:188` (`build_dossier`) et `:291`, `:342` : si aucun projet n'est reconnu dans la demande, le premier projet est pris sans le dire (`m.projects()[0]`).
  - `:106` : `hits[0]` lève `IndexError` si la mémoire est vide.
  - `:151` : `meetings[0][0]` idem dans `compare`.
  - `Memory.search` : si le filtre `types` ne laisse aucun candidat, `np.stack([])` lève `ValueError`. Cela peut arriver dans `draft_email`, qui cherche `types=["decision"]`.
  - `:159-161` : la boucle `while final in m.superseded_by` n'a pas de garde anti-cycle. Elle boucle indéfiniment si deux unités de même date se remplacent mutuellement, ce que `check_relation` autorise (« au moins aussi récente »). `Memory.current` a une garde, pas ce `while`.
  - `memory/store.py:94` : `superseded_by[r["to_id"]] = r["from_id"]` écrase silencieusement une seconde relation de remplacement sur la même cible.
- **Conséquence** : sur une demande hors périmètre, l'agent produit un dossier ou un e-mail sur un projet non demandé, ou plante.
- **Recommandation** : refuser ou demander une clarification explicite.

### PY-09 — BASSE — Logique de l'agent codée pour la démonstration Atlas

- **Fichier** : `src/embedding_lab/agent/agent.py:254-257` et `:27-29`.
- **Constat** : le test « Prestataire traiteur : ni choix ni responsable » est inscrit en dur, ainsi que la liste `TOPICS`. L'annotateur `"claude:demo-atlas"` est codé en dur dans `memory/store.py:62`.
- **Conséquence** : le comportement de l'agent est surajusté à une seule mémoire de démonstration, ce qui est peu transposable. À signaler honnêtement dans les limites.

### PY-10 — MOYENNE — Correspondances par sous-chaîne sans bornes de mots

- **Fichiers** :
  - `src/embedding_lab/relations/features.py:14-17` et `:44-50` ;
  - `src/embedding_lab/agent/agent.py:41-44` ;
  - `src/embedding_lab/intents/rules.py:42-56`.
- **Constat** :
  - `CUES` (« non », « pas », « plus », « ok », « oui », « report », « change ») et `_NUM` (`dix`, `six`, `cent`, `mille`, `euro`…) sont cherchés par `in` / `re.search` sans `\b`. « mille » est trouvé dans « famille », « ok » dans « book », « pas » dans « passer », « cent » dans « centre ».
  - `find_topic` : « lieu » est trouvé dans « milieu ».
  - `rules.py` : `DEICTIC` contient `"le "`, `EVENT` contient `"point "` et `"cale "`, etc.
- **Conséquence** : bruit dans les variables de R2, qui pilote la rétrogradation E4 (pour mémoire, « prédit trop souvent `supersedes` », `EXPERIMENTS.md:174`). Le protocole parle de « liste fixée a priori », pas de correspondances de sous-chaînes.
- **Recommandation** : documenter le choix, ou ajouter des bornes de mots.

### PY-11 — MOYENNE — Les règles I0 contiennent des mots qui n'apparaissent que dans les gabarits de test

- **Fichiers** : `src/embedding_lab/intents/rules.py:14-32`, `src/embedding_lab/intents/data.py`, historique git `eadb349`.
- **Constat** : `HEDGES` contient « à voir » et `EVENT` contient « organise ». Dans `data.py`, ces deux expressions ne figurent que dans la famille 3, c'est-à-dire la famille de test (« Ce serait bien que {p} s'occupe du {topic}, à voir. » ; « Organise une visio… »). « cale » n'apparaît que dans la famille de val. Règles et données ont été commitées ensemble (`eadb349`, « avant mesure »).
- **Conséquence** : le biais d'auteur est reconnu (`FINAL_REPORT.md:58`), mais la proximité entre mots-clés et gabarits du test est concrète. La conclusion « les règles battent I2 sur le test » reste un fait mesuré, mais ne dit rien sur de vraies formulations.
- **Recommandation** : citer cet élément précis dans l'écart déclaré.

### PY-12 — MOYENNE — `generate()` produit moins d'exemples que demandé, sans avertissement

- **Fichiers** : `src/embedding_lab/intents/data.py:167-176`, `scripts/make_intents.py:12`.
- **Constat** : `while made < per_family and tries < per_family * 50` s'arrête sans erreur si les textes uniques manquent. Les gabarits de `clarify` n'ont presque aucun emplacement.
- **Preuve** (comptage en ligne de `data/intents/*.jsonl`) :
  - train : `clarify` 48 contre 120 pour les autres classes ;
  - val : `clarify` 24 et `build_dossier` 48 contre 60 ;
  - test : `clarify` 24 contre 60.
- **Conséquence** : classes déséquilibrées (macro-F1 sensible), et `clarify` sous-représentée alors que c'est une classe critique. Aucune alerte dans `make_intents.py`.
- **Recommandation** : lever une erreur ou journaliser le manque.

### PY-13 — BASSE — `while True` potentiellement infini dans `random_negative_variant`

- **Fichier** : `src/embedding_lab/train/data.py:94-101`.
- **Constat** : si le pool ne contient aucune unité admissible (pool réduit au groupe de l'exemple, ou toutes les unités jugées), la boucle ne termine jamais.
- **Recommandation** : borner les tentatives et lever une erreur.

### PY-14 — BASSE — `assert` utilisés comme validation de données

- **Fichiers** : `src/embedding_lab/train/data.py:73`, `src/embedding_lab/synth/bsyn.py:74` et `:283`, `src/embedding_lab/data/splits.py:99`, `scripts/assemble_breal.py:47`.
- **Constat** : ces vérifications disparaissent sous `python -O`.
- **Recommandation** : lever des exceptions explicites.

### PY-15 — BASSE — Divisions par zéro et formats sur `None` non protégés

- **Fichiers** :
  - `eval/metrics.py:96` (`mean_metric` sur un dict vide) ;
  - `eval/harness.py:114-115` (`ndcg@10_cluster_mean` sans requête) ;
  - `eval/compare.py:30` (`mean_over_seeds([])` lève `IndexError`) ;
  - `scripts/final_analysis.py:98-99` (`sum(rev)/len(rev)` si un sous-ensemble est vide) ;
  - `scripts/compare_runs.py:85` ;
  - `relations/metrics.py:75` (`report` sur `gold` vide).
- **Constat** : `scripts/train_e2.py:81-82` et `scripts/run_eval.py:47-49` formatent `pairwise_accuracy:.4f`, alors que le harnais renvoie `None` quand il n'y a aucun triplet. Cela lève `TypeError`.
- **Conséquence** : cas limites non couverts. Ils ne se produisent pas avec les données actuelles.

### PY-16 — BASSE — Collisions et écrasements silencieux de runs

- **Fichiers** : `scripts/*.py` (identifiants `…{started[:16]}`, précision à la minute), `src/embedding_lab/eval/harness.py:133`, `src/embedding_lab/train/contrastive.py:127`.
- **Constat** :
  - Deux runs de même nom lancés dans la même minute s'écrasent. `write_run` utilise `mkdir(exist_ok=True)`.
  - `train()` tronque `train_log.jsonl` (`write_text("")`) sans vérifier l'existence du run. Les scripts de comparaison et d'analyse, eux, utilisent `exist_ok=False`.
  - `final_analysis.py:27-30` utilise des motifs glob (`runs/E4-dense-s*-test-*`) et moyenne tous les dossiers trouvés. Un run de test dupliqué serait compté comme une graine supplémentaire, sans contrôle du nombre attendu.
- **Preuve** : `final.json` indique 1/1/3/3/3/3/1 graines, donc cohérent aujourd'hui.

### PY-17 — BASSE — Reproductibilité d'entraînement non verrouillée

- **Fichier** : `src/embedding_lab/train/contrastive.py:56-62`.
- **Constat** : pas de `torch.backends.cudnn.deterministic`, ni de `use_deterministic_algorithms`. Les graines des epochs sont `cfg.seed + e`, donc deux graines consécutives (13 et 14) partageraient des ordres de batch décalés. Ce n'est pas le cas avec 13, 42 et 1234.
- **Autre point** : le checkpoint de l'étape 0 (modèle initial) est enregistré comme « best ». Si rien ne s'améliore, le « modèle fine-tuné » est identique à E1 sans alerte (`best_step: 0` dans le résumé).
- **Conséquence** : conforme à ce qui est annoncé (ce n'est pas un bogue), mais à signaler.

### PY-18 — MOYENNE — Contrôles de scénarios qui ne peuvent pas échouer

- **Fichier** : `scripts/run_scenarios.py:35-36` et `:70-71`.
- **Constat** :
  - Scénario 1 : « signale l'ancienne proposition comme remplacée » est testé par `"u-atlas-01" not in citations[:1]`. Cela est vrai dès que la liste est vide, et ne vérifie pas le signalement.
  - Scénario 5 : « Karim écarté » ne regarde que `body.split("\n")[0]`, qui est toujours la ligne « Bonjour {nom}, ».
  - Scénario « consigne cachée » (lignes 87-89) : seul `action is None` est contrôlé, pas l'absence d'obéissance à la consigne.
- **Conséquence** : les « 8/9 » de la documentation reposent en partie sur des contrôles trop faibles. Les contrôles sont « écrits avant l'exécution », mais pas assez stricts.

### PY-19 — BASSE — `diagnose_training.py` est inutilisable sous Windows

- **Fichier** : `scripts/diagnose_training.py:13` et `:85`.
- **Constat** : `import resource` (module POSIX) en tête de script. Sous Windows, le script ne démarre pas. `ru_maxrss / 1024` suppose des Ko (Linux), alors que macOS rapporte des octets.
- **Recommandation** : import conditionnel.

### PY-20 — BASSE — Qualité Python : typage, API privée, duplication

- **Typage absent ou faible** :
  - `train/contrastive.py:65`, `:75`, `:85` : `embed`, `mnrl_loss` et `evaluate` n'ont pas d'annotations de modèle ou de retour ;
  - `scripts/*.py` : `git(*args)`, `matrices`, `act`, `load` sans annotation ;
  - `Any` fréquent (`DenseRetriever(model: Any)`, `Agent`) ;
  - pas de configuration `mypy` ; la CI ne lint que `src tests`, pas `scripts`.
- **API privée** : `encoder._encode` est appelé depuis `agent/agent.py:57` et `:62`, `scripts/train_intents.py`, `scripts/train_relations.py`, `scripts/build_training_data.py`.
- **Idiomes** : `retrieval/dense.py:34` `model or SentenceTransformer(...)` doit être `is not None`. `SentenceTransformer` hérite de `nn.Sequential`, donc son `__len__` déciderait de la valeur booléenne.
- **Duplication** :
  - `now()`, `git()`, `read_jsonl`, `weights_sha`, `dump` répétés dans au moins 7 scripts, plus `harness._git` ;
  - `relations/metrics.majority` duplique `relations/models.Majority` ;
  - le nom du modèle et la révision sont répétés dans `contrastive.TrainConfig` et `dense.E5_SMALL`.
- **Valeurs codées en dur qui doivent suivre les expériences** :
  - `IntentModel(C=10.0)` (`agent.py:51`) doit suivre le `C` retenu par `train_intents.py` ;
  - `R2_C = 0.1` (`predictor.py:18`) doit suivre `train_relations.py`. Une dérive silencieuse est possible si la sélection change.
- **Dépendance** : `pyyaml` est déclaré dans `pyproject.toml` mais aucun import n'a été trouvé dans `src/` ni dans `scripts/`.
- **PLAN de `make_bsyn.py:20`** : le tuple `(240, 2024)` est déballé en `(n, seed)`. La « graine » est en fait l'année affichée, ce qui est trompeur à la lecture.

### PY-21 — BASSE — Contrats d'actions simulées

- **Fichiers** : `src/embedding_lab/tools/simulated.py:16-22`, `src/embedding_lab/agent/agent.py:331-333`.
- **Constat** :
  - `_finish` appelle `check_action(contract)` sans `units` ni `directory`. L'existence des unités citées n'est donc jamais vérifiée à la construction. Un e-mail non nul serait refusé à juste titre, faute d'annuaire.
  - `create_task` met `"reason": "email_missing"` pour une confirmation d'attribution de tâche, ce qui est sémantiquement faux (il n'y a pas d'e-mail).
  - `needs_confirmation` et `executed` sont bien forcés à `True` et `False`, et aucune bibliothèque réseau n'est importée dans `tools/` : conforme au cadre du projet.

### PY-22 — BASSE — Fragilités de `build_from_source` et du harnais de test

- **Fichiers** : `src/embedding_lab/memory/store.py:45-50`, `src/embedding_lab/eval/test_access.py:27`, `scripts/final_analysis.py:61`.
- **Constat** :
  - `turn_text.find(ev)` prend la première occurrence : si l'extrait se répète dans un tour, l'offset est silencieusement faux mais « valide ». Le dépaquetage d'un tuple de 13 champs positionnels est fragile.
  - Le journal `TEST_ACCESS.log` est consultatif : il est écrit en ajout simple, sans verrou. Il fusionne deux machines (VM et Colab), d'où des horodatages non monotones, ce qui est visible dans le journal. `compare_runs.py`, `final_analysis.py`, `train_relations.py` et `train_intents.py` lisent les fichiers de test directement, sans passer par `load_benchmark`. Ils journalisent chacun leur accès avant, ce qui est bien.
  - `final_analysis.py:61` lit le fichier des réunions relues avec `.split()`, alors que `export_breal_review.py:51` ignore les lignes `#`. Sans conséquence aujourd'hui, car les mots du commentaire ne sont pas des identifiants de réunion.

### PY-23 — INFO — `synth/bsyn.py`, dates qui débordent sur l'année suivante

- **Fichier** : `src/embedding_lab/synth/bsyn.py:96-103`.
- **Constat** : jusqu'à environ 250 + 14 + 14 + 59 + 44 jours après le 1er janvier, soit près de 380 jours. Certaines dates (`D2`) peuvent donc tomber l'année suivante, donc dans l'année d'un autre split (`SPLIT_YEAR`).
- **Conséquence** : sans fuite textuelle, car `retrieval_text` utilise `fmt_date` sans année. Mais l'intention « un split par année » n'est pas strictement tenue. Les `event_date` des unités peuvent dépasser l'année.

### PY-24 — INFO — Points de mesure et de présentation à connaître

- **Extraction de slots** : le gazetteer de personnes et de projets passé aux extracteurs est la liste d'entités du split évalué (`train_intents.py:106-111`). C'est conforme au protocole (« gazetteer fourni en entrée »). `slot_accuracy` vaut 1,0 à l'identique pour I0, I1 et I2, car l'extraction ne dépend pas du classifieur. Ce n'est pas une information sur les modèles.
- **IC de bootstrap des intentions** : le bootstrap des intentions (`train_intents.py:54-62`) rééchantillonne des exemples individuels (iid) sur des textes générés par gabarits. L'IC est donc plus étroit que ne le justifient les données.
- **Troncature** : `DenseRetriever.truncated` ne compte que les passages (pas les requêtes) et n'est ni enregistré dans le manifeste ni affiché pour E2, E3 et E4. Il n'est affiché que par `run_eval.py`, d'où le « 0 passage tronqué » de E1 val dans `EXPERIMENTS.md:41`.
- **`DemoteSystem.applied`** : le compteur s'accumule sur B-SYN puis B-REAL et n'est qu'affiché (`run_e4.py:90-91`), pas écrit dans le manifeste.

---

## Éléments vérifiés sans anomalie

- **Statistiques** (`eval/metrics.py`, `eval/compare.py`, `scripts/final_analysis.py`) :
  - Le test de permutation par grappes est cohérent avec le protocole : énumération exacte jusqu'à 16 grappes, Monte-Carlo au-delà avec correction (la statistique observée compte), `min_attainable_p = 2/2^n`. Les 7 grappes de B-REAL donnent 2/128, comme annoncé.
  - Le bootstrap par grappes utilise 10 000 tirages et la graine 0. Holm sur H1–H2 est correct : `final.json` donne p = 9,999e-5 (plancher Monte-Carlo) et Holm 2,0e-4. H3 est exact (p = 0,0156, 7 grappes). H4 et H5 sont calculées comme annoncé.
  - nDCG, MRR et recall sont corrects. Le garde anti-doublon est présent. Le départage par identifiant rend les classements déterministes.
- **Alignement des triplets** : l'index `t{i:05d}` des triplets est identique dans `harness.py` et dans les grappes de `compare_runs.py` et `final_analysis.py`.
- **Splits** : `group_components` (union-find) est correct et déterministe. `leakage_report` fonctionne comme documenté.
- **Cohérence code ↔ documentation de l'entraînement** : MNRL avec échelle 20, lr 2e-5, batch 64, `eval_every` 100, patience 3, 3 epochs, sélection sur B-SYN val avec B-REAL val en garde-fou. Tout cela est conforme au protocole § 6 (lignes 96 et 100). Les 348 à 350 étapes annoncées s'expliquent par les petits batchs restants de `cluster_batches`.
- **Aucun import inutilisé** (vérification AST).
- **Portée de recherche** : les benchmarks B-SYN et B-REAL sont bien séparés (split entier contre groupe). Les noms de métriques du harnais (`ndcg@10`, `mrr@10`, `recall@1/5/10`, `pairwise_accuracy`) correspondent à la documentation.

---

## Synthèse

| Gravité | Nombre | Identifiants |
|---|---|---|
| CRITIQUE | 0 | — |
| HAUTE | 2 | PY-01 (abstention non mesurée), PY-04 (encodage Windows, probable) |
| MOYENNE | 8 | PY-02, PY-03, PY-05, PY-07, PY-08, PY-10, PY-11, PY-12, PY-18 |
| BASSE | 11 | PY-06, PY-09, PY-13 à PY-17, PY-19 à PY-22 |
| INFO | 2 | PY-23, PY-24 |

(PY-18 est comptée avec les MOYENNE : 9 entrées au total, la ligne ci-dessus en cite 9.)

- **Sécurité et réseau** : aucun problème CRITIQUE (injection, désérialisation, secrets, réseau dans `tools/`) trouvé. Aucun appel réseau dans `tools/`, aucune exécution réelle possible, `needs_confirmation` et `executed` forcés.
- **Chemin du cœur du projet** (harnais, métriques, statistiques, entraînement) : je n'ai trouvé aucune erreur qui remette en cause les chiffres du test publiés. Je ne les ai toutefois pas recalculés.
- **Points qui comptent pour la présentation** :
  - PY-01 : l'abstention est promise mais absente.
  - PY-02 : la garantie « pas de faux négatif intra-batch » est sur-vendue.
  - PY-03 : la configuration d'entraînement des runs finaux n'est plus conservée dans `config.json`.
  - PY-11 : les règles I0 contiennent des mots propres aux gabarits de test.
  - PY-18 : les contrôles de scénarios sont trop faibles.
- **Portabilité** : PY-04 et PY-19 limitent l'usage des scripts sous Windows, sur la machine même de l'étudiant.

## Verdict

**BLOQUER** selon la grille du mandat, à cause de deux problèmes HAUTE : PY-01, une promesse du protocole non tenue qui n'est pas déclarée comme limite, et PY-04, un plantage probable des commandes de démonstration sous Windows. C'est un verdict de qualité de code, pas une invalidation des résultats : le test a déjà été évalué, aucune évaluation n'est à relancer, et rien de ce que j'ai lu ne modifie les chiffres du test. Avant la soutenance, je recommande surtout :

1. déclarer l'abstention comme non réalisée (PY-01) ;
2. corriger l'encodage UTF-8 des scripts de démonstration (PY-04) ;
3. nuancer dans le rapport la garantie anti-faux-négatifs (PY-02) et la traçabilité des hyperparamètres (PY-03).

Fichiers de référence principaux : `C:\Users\abdul\embedding-lab\src\embedding_lab\train\data.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\train\contrastive.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\retrieval\dense.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\eval\harness.py`, `C:\Users\abdul\embedding-lab\src\embedding_lab\agent\agent.py`, `C:\Users\abdul\embedding-lab\scripts\run_scenarios.py`, `C:\Users\abdul\embedding-lab\scripts\train_e2.py`, `C:\Users\abdul\embedding-lab\docs\EXPERIMENT_PROTOCOL.md`.
