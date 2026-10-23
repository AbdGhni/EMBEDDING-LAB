"""Jeu d'intentions synthétique (EL-019, protocole § 12).

Huit intentions. Chaque intention a quatre **familles** de gabarits (constructions
syntaxiques différentes) : familles 0 et 1 pour le train, 2 pour la validation, 3 pour le test.
Les projets, personnes et échéances sont tirés de listes **disjointes** entre splits ; seuls
les sujets génériques (budget, planning…) sont partagés. Chaque exemple porte ses slots or.
"""

from __future__ import annotations

import random
import re
from typing import Any

INTENTS = ("answer", "compare", "build_dossier", "draft_email", "create_task",
           "schedule_event", "clarify", "no_action")
FAMILY_SPLIT = {0: "train", 1: "train", 2: "val", 3: "test"}

ENTITIES = {
    "train": {"proj": ["Orion", "Narval", "Cobalt", "Sirius", "Pégase", "Lynx"],
              "p": ["Julie", "Thomas", "Nadia", "Karim", "Sophie", "Lucas", "Inès", "Paul"],
              "date": ["vendredi", "lundi prochain", "demain", "samedi",
                       "le 12 mars", "mercredi"]},
    "val": {"proj": ["Héron", "Basalte", "Comète"], "p": ["Claire", "Mehdi", "Léa"],
            "date": ["jeudi", "la semaine prochaine", "le 3 avril"]},
    "test": {"proj": ["Zénith", "Ivoire", "Quartz", "Mistral"],
             "p": ["Aurélie", "Bastien", "Yasmine", "Hugo", "Chloé"],
             "date": ["mardi", "le 21 juin", "jeudi prochain", "le 30 juin"]},
}
TOPICS = ["budget", "planning", "recrutement", "lancement", "contrat", "prestataire",
          "lieu", "programme", "devis", "calendrier"]
OBJECTS = ["la dernière version du devis", "le planning validé", "les chiffres à jour",
           "la liste des intervenants", "le contrat signé", "le compte rendu"]
ACTIONS = [("relancer le prestataire", "relance le prestataire"),
           ("envoyer le devis", "envoie le devis"),
           ("réserver la salle", "réserve la salle"),
           ("mettre à jour le planning", "mette à jour le planning"),
           ("vérifier le contrat", "vérifie le contrat")]

# {p} personne, {proj} projet, {topic} sujet, {date} échéance, {obj} objet, {act} action à
# l'infinitif, {acts} action au subjonctif
T: dict[str, dict[int, list[str]]] = {
    "answer": {
        0: ["Qu'a-t-on décidé pour le {topic} du projet {proj} ?",
            "Quelle est la décision actuelle sur le {topic} de {proj} ?",
            "Quelle décision a été prise sur le {topic} de {proj} ?"],
        1: ["Qui s'occupe du {topic} sur {proj} ?",
            "Qui est responsable du {topic} pour {proj} ?",
            "Qui s'est engagé à gérer le {topic} de {proj} ?"],
        2: ["Est-ce que le {topic} de {proj} a été validé ?",
            "Le {topic} de {proj} est-il confirmé ?",
            "On a bien acté le {topic} de {proj} ?"],
        3: ["Rappelle-moi ce qui a été dit sur le {topic} de {proj}.",
            "Je voudrais savoir où on en est sur le {topic} de {proj}.",
            "Tu peux me dire ce qu'on a retenu pour le {topic} de {proj} ?"],
    },
    "compare": {
        0: ["Qu'est-ce qui a changé sur le {topic} de {proj} depuis la dernière réunion ?",
            "Qu'est-ce qui a bougé sur le {topic} de {proj} ?"],
        1: ["Est-ce que la réunion de {date} contredit la précédente sur {proj} ?",
            "La dernière réunion de {proj} contredit-elle la première sur le {topic} ?"],
        2: ["Compare les deux dernières réunions de {proj} sur le {topic}.",
            "Fais la comparaison entre la première et la dernière réunion de {proj}."],
        3: ["Quelle différence entre ce qu'on avait dit et ce qu'on dit maintenant sur le "
            "{topic} de {proj} ?",
            "Le {topic} de {proj} a-t-il évolué d'une réunion à l'autre ?"],
    },
    "build_dossier": {
        0: ["Prépare un dossier complet sur le projet {proj}.",
            "Constitue un dossier sur {proj} avec l'historique et les décisions."],
        1: ["Fais-moi une synthèse documentée de {proj} : décisions, budget, risques.",
            "Rédige une synthèse sourcée de tout le projet {proj}."],
        2: ["J'ai besoin d'un récapitulatif structuré de tout ce qui concerne {proj}.",
            "Il me faut un document qui reprend tout le projet {proj}, sources à l'appui."],
        3: ["Monte un dossier sur le {topic} de {proj} avec les sources.",
            "Rassemble dans un document tout ce qu'on sait du {topic} de {proj}."],
    },
    "draft_email": {
        0: ["Rédige un mail à {p} pour lui demander {obj} avant {date}.",
            "Rédige un e-mail à {p} pour obtenir {obj}."],
        1: ["Écris au responsable du {topic} de {proj} pour avoir {obj}.",
            "Écris à la personne en charge du {topic} de {proj} pour lui demander {obj}."],
        2: ["Prépare un e-mail pour {p} au sujet du {topic} de {proj}.",
            "Prépare un courriel à {p} concernant le {topic} de {proj}."],
        3: ["Envoie un message à {p} : on a besoin de {obj} d'ici {date}.",
            "Fais un mail à {p} pour récupérer {obj} avant {date}."],
    },
    "create_task": {
        0: ["Prépare une tâche pour {p} : {act} avant {date}.",
            "Crée une tâche pour {p} : {act}."],
        1: ["Ajoute à la liste de {p} de {act}.",
            "Ajoute une tâche à {p} pour {act} d'ici {date}."],
        2: ["Crée une tâche « {act} » pour le projet {proj}, échéance {date}.",
            "Enregistre l'action « {act} » sur {proj} pour {date}."],
        3: ["Il faut que {p} {acts} d'ici {date}, mets-le dans ses tâches.",
            "Note dans les tâches de {p} qu'il faut {act} pour {date}."],
    },
    "schedule_event": {
        0: ["Prépare un point {date} avec {p} sur {proj}.",
            "Prépare une réunion {date} avec {p} à propos de {proj}."],
        1: ["Planifie une réunion sur le {topic} de {proj} {date}.",
            "Programme une réunion {date} sur le {topic} de {proj}."],
        2: ["Cale un créneau avec {p} {date} pour parler du {topic}.",
            "Trouve un créneau {date} avec {p} pour le {topic} de {proj}."],
        3: ["Organise une visio {date} pour faire le point sur {proj}.",
            "Monte une réunion d'équipe {date} sur l'avancement de {proj}."],
    },
    "clarify": {
        0: ["Envoie ça à la bonne personne.", "Transmets ça à qui de droit.",
            "Fais suivre à la personne concernée."],
        1: ["Préviens-le, s'il te plaît.", "Dis-lui de s'en occuper.",
            "Rappelle-lui ce qu'on a dit."],
        2: ["Fais le nécessaire pour ce dossier.", "Occupe-toi de ça.",
            "Règle ça avec eux."],
        3: ["Écris-leur pour leur dire.", "Relance la personne concernée.",
            "Envoie-lui un petit mot à ce sujet."],
    },
    "no_action": {
        0: ["On pourrait peut-être revoir le {topic}.",
            "On pourrait éventuellement décaler le {topic} de {proj}."],
        1: ["Il faudrait sans doute reparler du {topic} de {proj} un jour.",
            "Ce serait à rediscuter, le {topic} de {proj}, peut-être."],
        2: ["J'ai l'impression que le {topic} de {proj} va déraper.",
            "Le {topic} de {proj} me semble un peu juste."],
        3: ["Ce serait bien que {p} s'occupe du {topic}, à voir.",
            "Peut-être que {p} pourrait gérer le {topic} de {proj}, je ne sais pas."],
    },
}
SUFFIXES = ["", "", "", " stp", " merci"]
ACTION_LIKE = {"draft_email", "create_task", "schedule_event", "clarify", "build_dossier"}
_ELIDE = re.compile(r"\b(que|de) ([AEIOUÉÈÎaeiouéèî])")


def _fill(template: str, ents: dict[str, list[str]], rng: random.Random
          ) -> tuple[str, dict[str, Any]]:
    act = rng.choice(ACTIONS)
    values = {"p": rng.choice(ents["p"]), "proj": rng.choice(ents["proj"]),
              "date": rng.choice(ents["date"]), "topic": rng.choice(TOPICS),
              "obj": rng.choice(OBJECTS), "act": act[0], "acts": act[1]}
    text = _ELIDE.sub(lambda m: ("qu'" if m.group(1) == "que" else "d'") + m.group(2),
                      template.format(**values))
    slots = {"person": values["p"] if "{p}" in template else None,
             "project": values["proj"] if "{proj}" in template else None,
             "deadline": values["date"] if "{date}" in template else None,
             "topic": values["topic"] if "{topic}" in template else None}
    return text, slots


def _noise(text: str, rng: random.Random, intent: str) -> str:
    if text.endswith((".", "?")) and rng.random() < 0.3:
        text = text[:-1].rstrip()
    if rng.random() < 0.2:
        text = text[0].lower() + text[1:]
    suffix = rng.choice(SUFFIXES) if intent in ACTION_LIKE else ""
    return text + suffix if suffix and not text.endswith(("?", ".")) else text


def generate(split: str, per_family: int, seed: int = 0) -> list[dict[str, Any]]:
    """Exemples d'un split ; aucun texte n'est répété à l'intérieur du split."""
    rng = random.Random(f"{seed}-{split}")
    ents = ENTITIES[split]
    out, seen = [], set()
    for intent in INTENTS:
        for fam, templates in T[intent].items():
            if FAMILY_SPLIT[fam] != split:
                continue
            tries = 0
            made = 0
            while made < per_family and tries < per_family * 50:
                tries += 1
                text, slots = _fill(rng.choice(templates), ents, rng)
                text = _noise(text, rng, intent)
                if text in seen:
                    continue
                seen.add(text)
                made += 1
                out.append({"id": f"in-{split}-{len(out):04d}", "text": text,
                            "intent": intent, "family": fam, "slots": slots,
                            "origin": "synthetic_generator"})
    return out
