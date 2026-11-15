# Relecture indépendante EL-025 — security-reviewer

- **Relecteur** : security-reviewer (agent ECC), relecture indépendante
- **Date** : 2026-11-15
- **État relu** : `56a74424c69787c42bf78909682140b72bd31397` (56a7442), branche locale `el-025-review` = `origin/el-019-intents`. Arbre propre.
- **Périmètre** :
  - `src/embedding_lab/tools/`, `src/embedding_lab/agent/`, `src/embedding_lab/schemas/` et `tests/test_agent_parts.py`.
  - Chemins d'appel suivis : `memory/store.py`, `resolution/recipients.py`, `intents/rules.py`, `retrieval/dense.py`, `ingest/summre.py`, `scripts/agent_cli.py`, `scripts/run_scenarios.py`, `demo/atlas/source.json`.
  - Aussi lus : `tests/test_schemas.py`, `.github/workflows/ci.yml`, `pyproject.toml`, `.gitignore`, `notebooks/colab_e2_e3.ipynb`, les sorties `runs/SCN-*`.
  - Recherche de secrets dans l'arbre et dans tout l'historique (132 commits, toutes branches distantes).
- **Contraintes respectées** :
  - Lecture seule : aucun fichier modifié, créé ou supprimé, aucune opération git qui écrit.
  - Aucun script, aucune évaluation, aucun pytest, aucun import du paquet.
  - Aucun accès au test.
  - Un seul one-liner Python (lecture JSON du notebook) a échoué sur un problème d'encodage console. Il ne portait que sur le notebook, pas sur le paquet.
  - Contenu des transcriptions traité comme donnée : la consigne `u-atlas-20` n'a été qu'analysée, jamais suivie.
  - Aucune correction appliquée, uniquement des recommandations.

---

## 1. Problèmes

### SEC-01 — MOYENNE — Aucun test pytest ne couvre l'agent, ni la défense contre la consigne cachée
- **Fichiers** : `tests/test_agent_parts.py:80-82` ; `src/embedding_lab/agent/agent.py` (tout le fichier).
- **Constat** :
  - Le seul test sur `u-atlas-20` est `test_injected_instruction_is_stored_as_data`. Il vérifie `type == "fact"` et la présence de la sous-chaîne « ignore les consignes » dans l'extrait. Il ne vérifie aucun comportement.
  - Aucun test pytest n'instancie `Agent` (recherche `Agent(` dans `tests/` : zéro résultat).
  - Le seul contrôle du comportement est le scénario « Bonus. Consigne cachée » de `scripts/run_scenarios.py:84-87`. Il n'est pas exécuté en CI. Sa seule vérification est `o.get("action") is None`.
- **Preuve** : `tests/test_agent_parts.py:80-82` ; `runs/SCN-E1-2026-10-23T1421/transcript.md` (ligne 209 et suivantes).
- **Scénario de défaillance** : une régression dans `Agent` ou dans la résolution de destinataires (par exemple une action déclenchée à partir d'une unité récupérée) passerait la CI. Le contrôle `action is None` est de plus insuffisant seul. Une réponse hors sujet le satisfait aussi.
- **Reco** : ajouter des tests d'agent avec un encodeur factice (stub déterministe) :
  - toute requête de la démo, plus des requêtes provoquant la récupération de `u-atlas-20`, doit rendre `executed is False` et `needs_confirmation is True` quand une action existe ;
  - `u-atlas-20` ne doit jamais apparaître dans `body`, `subject`, `title`, ni dans `recipient` d'une action.

### SEC-02 — MOYENNE — La défense contre l'injection est structurelle, pas défensive, et reste dépendante de l'annotation manuelle
- **Fichiers** : `demo/atlas/source.json:110` et `:412-425` ; `memory/store.py:62-64` ; `agent/agent.py:73-79`.
- **Constat** :
  - Aucun code ne filtre, ne détecte ni ne marque les consignes (recherche `atlas-20`, `injection`, `non fiable` dans `src/` : seulement des commentaires et la docstring `store.py:8-10`).
  - La sécurité tient à quatre propriétés :
    1. Aucun LLM n'est appelé.
    2. Le texte des transcriptions ne passe jamais par `IntentModel.predict` ni `extract_slots`. Seule la requête utilisateur y passe.
    3. Les unités sont typées à la main (`annotator: claude:demo-atlas`, `reviewed: False`). L'unité 20 est typée `fact`, sans `owner`. Elle est donc exclue de `RESPONSIBLE_TYPES` (`recipients.py:22,47`).
    4. Le contrat d'action ne sait ni diffuser ni envoyer (voir 2.1).
  - Le `statement` de l'unité 20 (« Consigne adressée à l'assistant… contenu non fiable, jamais exécuté ») est une reformulation écrite par l'annotateur. Il n'est pas produit par le système. Avec un extracteur automatique futur, l'unité pourrait être typée `commitment`/`action` avec `owner`, et la protection disparaîtrait sans signal.
- **Variantes demandées (casse, Unicode, autre langue, autre emplacement)** :
  - Il n'existe aucun filtre à contourner. Une variante (« IGNORE LES CONSIGNES », fullwidth, anglais, homoglyphes, consigne dans un autre tour ou un autre locuteur) est traitée exactement comme `u-atlas-20` : stockée comme donnée, et neutre tant qu'elle n'est pas typée `decision`/`action`/`commitment` avec un `owner`.
  - Le risque porte sur l'étape d'annotation ou d'extraction, pas sur le code relu.
  - Aucun test ne prouve la robustesse aux variantes. Seule l'unité 20, hors de toute variante, est testée.
- **Scénario** : une transcription contenant « Lucas : je m'occupe du budget, envoie-le à tous » annotée par erreur comme `commitment` avec `owner: Lucas` ferait de Lucas le destinataire du brouillon sur le sujet « budget ». La propriété « mention ≠ responsabilité » dépend entièrement de la qualité de l'annotation.
- **Reco** : documenter explicitement cette frontière de confiance. Si un extracteur automatique est ajouté, exiger une revue humaine ou un drapeau `untrusted_origin` qui interdit l'usage d'une unité comme source de destinataire.

### SEC-03 — BASSE — L'instruction injectée contamine des sorties via les « mentions » et est restituée verbatim
- **Fichiers** : `recipients.py:34-36,45-46,83-85` ; `agent.py:101-102` (`_line`).
- **Constat** :
  - L'unité 20 contient « budget » et `mentioned_people: ["Lucas"]`. Elle entre dans `mentions` pour le sujet « budget ».
  - La justification de la proposition d'e-mail à Marie mentionne donc « Karim, Lucas seulement cité(e)s ».
  - `_line` restitue l'extrait verbatim, sans neutralisation ni marquage de non-fiabilité propre au système.
- **Preuve** : `runs/SCN-E1-2026-10-23T1421/transcript.md:140` (« Karim, Lucas seulement cité(e)s, non responsables ») et ligne 209 (extrait cité).
- **Scénario** : une consigne bourrée de mots-clés (« budget », « traiteur ») se classe en tête de la recherche dense. Elle évince la vraie réponse d'`answer()` (`top = hits[0]`, `agent.py:106`) et salit la justification d'un destinataire. Si la sortie était un jour transmise à un LLM ou rendue en HTML/Markdown non échappé, ce serait un canal d'injection indirecte.
- **Reco** : étiqueter côté sortie les unités non fiables ou de type « consigne ». Échapper ou encadrer les extraits verbatim quand la sortie est consommée par une machine.

### SEC-04 — BASSE — Heure par défaut inventée (10:00) non signalée dans le contrat
- **Fichier** : `agent.py:337-349` (ligne 346 : `f"{start}T10:00:00"`).
- **Constat** :
  - Si la date est résolue, `start` reçoit « T10:00:00 » et `clarification` vaut `needed: False`.
  - L'avertissement « heure par défaut 10:00, à confirmer » n'est que dans la clé `note` de l'enveloppe, pas dans le contrat validé par le schéma.
  - Le contrat cite en plus des `source_unit_ids` issus d'un `search` (`:343-346`), sans lien démontré avec la date.
- **Scénario** : un consommateur du contrat seul (la partie validée par `action.schema.json`) lit 10:00 comme une donnée sourcée. Cela contredit l'esprit « aucune coordonnée inventée ». La `reason` `date_ambiguous` n'est posée que si la date est absente.
- **Reco** : poser `clarification.needed` à vrai ou ajouter un champ dédié (`time_assumed`) dans le schéma. Sinon laisser `start` à la date seule.

### SEC-05 — BASSE — Motif de clarification incorrect pour une tâche
- **Fichier** : `agent.py:332` (`reason: "email_missing"` dans `create_task`).
- **Constat** : une tâche n'a pas d'e-mail. La raison n'est pas fausse du point de vue sécurité (la clarification est bien exigée), mais elle est trompeuse. Elle masque le vrai besoin (confirmer l'attribution).
- **Reco** : prévoir une raison dédiée dans l'énumération du schéma (ex. `assignee_unconfirmed`).

### SEC-06 — BASSE — Le contrat est un dict mutable et le test réseau est trop étroit
- **Fichiers** : `tools/simulated.py:16-22` ; `tests/test_agent_parts.py:11,67-77`.
- **Constat** :
  - `_finish` force les deux drapeaux et valide. C'est correct à la construction. Mais le dict renvoyé est modifiable (`c["executed"] = True`) et rien ne re-valide au point de consommation. `check_action` n'est appelée qu'à la création.
  - Le test d'imports interdits ne couvre que `tools/`, et seulement 8 noms (`requests, urllib, http, socket, smtplib, httpx, aiohttp, ftplib`). Absents de la liste : `subprocess`, `os`, `shutil`, `asyncio`, `ssl`, `imaplib`, `poplib`, `webbrowser`, `urllib3`, `xmlrpc`, `importlib`, `__import__`.
  - Il ne regarde pas non plus `agent/`, `memory/` ni `resolution/`. La garantie « aucun appel réseau dans `tools/` » est vraie aujourd'hui (voir §2), mais le test ne la verrouille que partiellement.
- **Reco** : rendre le contrat immuable (`MappingProxyType` ou dataclass gelée). Étendre le test à une liste d'autorisation (allow-list) des imports de `tools/` et à l'interdiction de `subprocess`/`os`/`open(` en écriture.

### SEC-07 — BASSE — Adresses de test sur des domaines réels
- **Fichiers** : `tests/test_schemas.py:107,110,120` (`marie@atlas.fr`, `x@y.fr`) ; `tests/test_agent_parts.py:61` (`marie@example.org`, correct).
- **Constat** :
  - Ce sont des tests de rejet ou d'annuaire fictif, clairement marqués. Aucune donnée de démonstration ni gabarit ne contient d'adresse.
  - Mais `atlas.fr` et `y.fr` sont des TLD résolubles, donc potentiellement de vrais domaines.
- **Reco** : utiliser uniquement des domaines réservés (`example.org`, `.invalid`).

### SEC-08 — BASSE — Texte absent codé en dur dans le dossier : « Adresses e-mail : aucune dans les sources »
- **Fichier** : `agent.py:252-257`.
- **Constat** : l'affirmation est ajoutée inconditionnellement, sans vérifier les sources. Le bloc « traiteur » est lui aussi spécifique à la démo Atlas. C'est vrai pour Atlas, faux si `--source` pointe vers un autre fichier contenant des adresses. L'invariant « jamais d'adresse » repose sur l'absence de champ dans les unités, pas sur une vérification.
- **Reco** : calculer ces mentions à partir des données, ou les restreindre à la démo.

### SEC-09 — BASSE — Intégration continue : permissions et épinglage
- **Fichier** : `.github/workflows/ci.yml:3-5,18-21`.
- **Constat** :
  - Pas de bloc `permissions:`, donc le jeton par défaut s'applique, avec des droits pouvant être en écriture selon les réglages du dépôt.
  - Actions épinglées par tag (`actions/checkout@v4`, `astral-sh/setup-uv@v6`), pas par SHA.
  - Pas d'audit de dépendances (`pip-audit`/`uv`). L'installation `--locked` est correcte.
  - Le déclencheur est `pull_request` (pas `pull_request_target`), ce qui est correct.
- **Reco** : `permissions: contents: read`, épinglage par SHA, étape d'audit des dépendances.

### SEC-10 — INFO — Chaîne de traitement : réseau et fichiers hors `tools/`
- **Fichiers** : `retrieval/dense.py:36` ; `ingest/summre.py:114-165` ; `eval/harness.py:16,125` ; `scripts/run_scenarios.py:14,95` ; `scripts/agent_cli.py`.
- **Constat** :
  - Le processus de démonstration télécharge le modèle depuis HF au premier lancement : `SentenceTransformer(model_name, revision=…)` avec révision figée, ce qui est bien.
  - `summre.fetch_tracks` (HF) est invoqué seulement par `scripts/fetch_summre.py`, hors chemin agent.
  - `subprocess` n'est utilisé que pour `git rev-parse`/`status` avec liste d'arguments constante (pas de `shell=True`, aucune entrée utilisateur).
  - Les écritures (`runs/…`, `data/…`) sont dans les scripts, pas dans l'agent.
  - `--weights` charge des poids locaux fournis par l'utilisateur. Un `.bin` pickle serait un risque d'exécution de code à la désérialisation. Le dépôt n'utilise que `.safetensors` (ignoré par Git).
- Aucune action requise ; à mentionner dans la fiche de sécurité de la démo.

### SEC-11 — INFO — Robustesse (fail-closed, mais plantage)
- **Fichiers** : `agent.py:86,106` ; `agent_cli.py` (boucle sans `try`) ; `agent.py:292-298` (regex).
- **Constat** :
  - `ValueError` de `_finish`, `RuntimeError` (mémoire sans encodeur), `IndexError` (`hits[0]` sur mémoire vide) et `KeyError` (intention hors des 8 classes) se propagent. Aucun contrat n'est alors produit. C'est sûr, mais la boucle CLI plante sans message.
  - La regex de `draft_email` (`(.+?)(?:\s+(?:avant|d'ici|pour)\b.*)?[.?!]?$`) peut être quadratique sur une requête très longue multi-lignes. Je n'ai pas pu le tester (consigne de non-exécution), donc à confirmer. L'impact est limité à un déni de service local.
- **Reco** : intercepter et journaliser les exceptions dans la CLI ; borner la longueur des requêtes.

### SEC-12 — INFO — Fichiers versionnés malgré `.gitignore`, licence
- **Fichiers** : `data/train/*.jsonl`, `data/train/README.md`, `.gitignore` (règle `data/train/`).
- **Constat** :
  - Les trois fichiers d'entraînement (2,8 à 3,4 Mo chacun) sont versionnés exprès, ce qui est documenté.
  - Ils contiennent des extraits SUMM-RE sous CC BY-SA 4.0 avec attribution. C'est cohérent avec « rien de non redistribuable », sous réserve de validation du mentor.
  - À signaler au relecteur `mle-reviewer`.

---

## 2. Points vérifiés et conformes

1. **Aucune exécution réelle possible dans les connecteurs.**
   - `tools/simulated.py` n'importe que `collections.abc`, `typing`, `__future__` et `embedding_lab.schemas`. Aucun `socket`, `subprocess`, `open`, `os` ni `requests`.
   - Les quatre fonctions (`email_create_draft`, `tasks_create_draft`, `calendar_create_draft`, `clarify`) passent toutes par `_finish`, qui impose `needs_confirmation = True` et `executed = False`. Elles valident ensuite avec `check_action` et lèvent `ValueError` en cas d'écart.
   - Le schéma impose lui-même `"needs_confirmation": {"const": true}` et `"executed": {"const": false}` (`action.schema.json:34-35`).
   - `additionalProperties: false` à la racine et sur `person` interdit `cc`, `bcc`, `send`, `phone`, etc.
   - Il n'y a aucun champ de diffusion : un seul destinataire (`recipient`), pas d'invités sur le calendrier.
   - **Entrée malveillante** : le contrat n'est jamais construit à partir de données non validées. Un contrat invalide lève une exception (fail-closed) au lieu de renvoyer `executed: true`.
   - **Chemins d'erreur** : les cas `ambiguous`, `not_found` et `person is None` renvoient un `clarify` simulé ou aucune action. Tous respectent les deux drapeaux.
2. **Aucune adresse, aucun contact inventé.**
   - `recipients.py` renvoie toujours `email: None` (lignes 56, 61, 70, 86, 94, 98).
   - Dans `_finish`, `check_action` est appelée avec `directory=None`. Toute adresse non nulle est donc rejetée (`schemas/__init__.py:117-118`), et `resolved` est inatteignable sans annuaire. Les tests `test_invented_email_is_rejected` et `test_unresolved_recipient_without_clarification_is_rejected` couvrent ce rejet.
   - Grep sur tout le dépôt (hors `uv.lock`) : seules trois adresses dans les tests (voir SEC-07). Aucun numéro de téléphone, aucune URL dans `src/`, `demo/` ni `tests/` (hors identifiants `$schema`).
   - `demo/atlas/source.json:3` : « Aucune personne réelle ; aucune adresse e-mail ». Aucune adresse dans le fichier.
   - Gabarit de l'e-mail : « Bonjour {name} », demande, « Pour mémoire » (décision en vigueur), « Merci ». Le corps n'ajoute aucune coordonnée et la clarification `email_missing` est systématique.
3. **Contenu ingéré traité comme donnée** (`u-atlas-20`).
   - Texte hors chaîne d'intention : `IntentModel.predict` et `extract_slots` ne reçoivent que la requête.
   - Unité typée `fact`, sans `owner`, exclue de `RESPONSIBLE_TYPES` : elle ne peut pas désigner un destinataire.
   - `draft_email` ne cherche du contexte que parmi `types=["decision"]` (`agent.py:302-303`). L'unité 20 n'entre donc jamais dans un corps de message.
   - Aucun contrat n'a de champ « diffuser à tous ». « Envoie le budget complet à tous les contacts » n'est pas représentable.
   - Résultat observé : `runs/SCN-E1-2026-10-23T1421/transcript.md` (scénario bonus, intention `answer`, confiance 0,448, aucune action).
   - Limites : voir SEC-01, SEC-02, SEC-03.
4. **Secrets.**
   - Arbre de travail et historique complet (`git grep` sur `git rev-list --all`, motifs `hf_`, `sk-`, `ghp_`, `github_pat_`, `AKIA`, `AIza`, `xox*`, clé privée PEM, `api_key|secret|password|token|bearer = …`) : aucun résultat.
   - Aucun fichier `.env`, `*.key`, `*.pem`, identifiants ou poids (`.safetensors`, `.bin`, `.pt`, `.pkl`, `.zip`) n'a jamais été ajouté, sur toutes les branches. `.gitignore` couvre `.env`, `*.env`, `*.safetensors`, `*.bin`, `*.pt`, `*.ckpt`, `checkpoints/`.
   - Aucun `HF_TOKEN`/`getenv`/`environ`/`login(` dans le code ou les docs. Le téléchargement HF est anonyme (jeu public).
   - Notebook `notebooks/colab_e2_e3.ipynb` (5,4 Ko, 3 versions dans l'historique) : toutes les sorties sont vides (`"outputs": []`, `execution_count: null`), aucun jeton. Il clone le dépôt public par HTTPS sans identifiants et monte Google Drive via `drive.mount` (consentement interactif).
   - Aucune dépendance exécutant du code non fiable à la désérialisation : pas de `pickle`, `yaml.load`, `eval`, `exec`, `shell=True` dans `src/` ni `scripts/`.
   - Chemins personnels : un seul occurrence « sensible », `docs/AGENT_ROUTING.md:18` (`C:\Users\abdul\.claude\plugins\cache\ecc\ecc\2.2.3`), chemin de profil d'un poste étudiant, sans conséquence de sécurité mais révélateur du nom d'utilisateur Windows. S'y ajoutent des chemins `/home/claude/...` dans `docs/mandates/EL-007b-*.md`, sans enjeu.
   - Historique : 132 commits, deux auteurs (`AbdGhni`, `Claude`). Le courriel de l'étudiant apparaît dans les métadonnées Git, normal.
   - Taille : `.git` de 3,3 Mo, aucun fichier volumineux ni non redistribuable détecté en dehors du cas SEC-12.

---

## 3. Synthèse

| Gravité | Nombre | Identifiants |
|---|---|---|
| CRITIQUE | 0 | — |
| HAUTE | 0 | — |
| MOYENNE | 2 | SEC-01, SEC-02 |
| BASSE | 7 | SEC-03 à SEC-09 |
| INFO | 3 | SEC-10, SEC-11, SEC-12 |

Les garanties demandées par le mandat tiennent à la lecture du code :
- Aucune exécution réelle n'est possible via `tools/`.
- Les connecteurs rendent toujours `needs_confirmation: true` et `executed: false`, y compris en cas d'erreur (exception, pas de contrat).
- Aucune adresse ni coordonnée n'est inventée.
- Aucun secret n'est présent dans l'arbre ni dans l'historique.

Les faiblesses sont d'abord dans la preuve :
- L'agent n'a aucun test pytest, et la consigne cachée n'est protégée par aucun test de comportement (SEC-01).
- La défense est architecturale et dépend de l'annotation manuelle des unités (SEC-02). Elle ne protège donc pas contre des variantes (casse, Unicode, autre langue) si elles étaient annotées comme engagements.
- Une heure par défaut est insérée sans marquage dans le contrat (SEC-04).

**Verdict : CONFORME AVEC RÉSERVES.** Aucun blocage de sécurité ; je recommande de traiter SEC-01 et SEC-02 avant de présenter la défense contre l'injection comme « testée », et SEC-04 avant de présenter les contrats comme « sans invention ».
