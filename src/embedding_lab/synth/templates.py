"""Patrons du benchmark synthétique B-SYN.

Chaque type d'unité et chaque type de requête a **quatre ou cinq familles** de formulations.
Les familles sont affectées aux splits sans recouvrement (``FAMILIES_BY_SPLIT``) : le test
n'emploie jamais une formulation vue à l'entraînement. Les familles du test ont été écrites
avec un vocabulaire volontairement différent (« feu vert », « entériner », « enveloppe »…).

Variables : {X} {Y} montants ; {D1} {D2} {D3} dates ; {A} {B} {C} personnes ; {P} projet ;
{DUE} échéance.
"""

# famille -> split. Unités : 0, 1 = train ; 2 = val ; 3 = test.
UNIT_FAMILIES_BY_SPLIT = {"train": (0, 1), "val": (2,), "test": (3,)}
# Requêtes : 0, 1 = train ; 2 = val ; 3, 4 = test.
QUERY_FAMILIES_BY_SPLIT = {"train": (0, 1), "val": (2,), "test": (3, 4)}

UNITS: dict[str, tuple[str, ...]] = {
    # ---------- budget ----------
    "b_prop": (
        "je propose qu'on parte sur un budget de {X} pour {P}",
        "moi je verrais bien {X} pour le budget, qu'est-ce que vous en pensez",
        "proposition budget {P} : {X}, à discuter",
        "je mets {X} sur la table pour l'enveloppe, on en reparle",
    ),
    "b_cond": (
        "d'accord pour {X} mais seulement si la direction suit",
        "ok pour les {X} à condition que le client confirme sa commande",
        "budget {X} accepté sous réserve de l'accord des achats",
        "l'enveloppe de {X} me va, pourvu que le financement soit débloqué",
    ),
    "b_valid": (
        "c'est validé, le budget de {P} est fixé à {X}",
        "bon on est tous d'accord, on part sur {X}, c'est voté",
        "décision : budget {P} = {X}, approuvé",
        "feu vert pour l'enveloppe de {X}, c'est entériné",
    ),
    "b_reject": (
        "non, on ne valide pas les {X}, c'est refusé",
        "les {X} c'est non, le budget est rejeté",
        "budget {X} refusé",
        "l'enveloppe de {X} ne passe pas, on l'écarte",
    ),
    "b_new": (
        "on revient sur le budget : finalement ce sera {Y} et plus {X}",
        "changement, le budget passe de {X} à {Y}, c'est validé",
        "budget révisé : {Y} au lieu de {X}, approuvé",
        "on corrige le tir, l'enveloppe est ramenée à {Y}, les {X} c'est terminé",
    ),
    "b_cancel": (
        "le budget de {P} est annulé, on arrête tout",
        "finalement on annule le budget, le projet est mis en pause",
        "budget {P} annulé",
        "on abandonne l'enveloppe prévue, plus rien n'est engagé sur {P}",
    ),
    "b_mention": (
        "il faudra qu'on reparle du budget, ça risque d'être serré",
        "le budget ça m'inquiète un peu quand même",
        "point budget à revoir plus tard",
        "côté finances on n'est pas tranquilles, à surveiller",
    ),
    # ---------- date de lancement ----------
    "d_prop": (
        "je propose de lancer {P} le {D1}",
        "pourquoi pas un lancement le {D1}, ça vous irait",
        "date de lancement envisagée : {D1}",
        "on pourrait viser une mise en route le {D1}",
    ),
    "d_valid": (
        "c'est confirmé, le lancement de {P} aura lieu le {D1}",
        "allez on fixe le lancement au {D1}, c'est décidé",
        "décision : lancement le {D1}",
        "on acte le démarrage au {D1}, c'est arrêté",
    ),
    "d_postpone": (
        "le lancement est reporté, ce sera le {D2} au lieu du {D1}",
        "petit changement, on décale le lancement au {D2}, le {D1} c'est fini",
        "lancement repoussé au {D2}",
        "le démarrage glisse au {D2}, oubliez le {D1}",
    ),
    "d_neg": (
        "on ne lance pas le {D1}, ce n'est pas possible",
        "le {D1} non, ça ne marchera pas pour le lancement",
        "lancement le {D1} : exclu",
        "pas question de démarrer le {D1}",
    ),
    "d_conflict": (
        "attendez, pour moi le lancement c'était le {D3}, non",
        "j'avais noté le {D3} pour le lancement moi",
        "lancement : {D3} selon le compte rendu du service",
        "de mon côté on m'a parlé du {D3} pour la mise en route",
    ),
    # ---------- responsable et échéance du dossier ----------
    "o_question": (
        "qui s'occupe d'envoyer le dossier pour {P}",
        "et le dossier, quelqu'un peut l'envoyer",
        "envoi du dossier : responsable à désigner",
        "il nous faut quelqu'un pour transmettre le dossier",
    ),
    "o_request": (
        "{B}, est-ce que tu pourrais envoyer le dossier",
        "{B} tu veux bien t'occuper du dossier",
        "demande à {B} pour l'envoi du dossier",
        "on pourrait confier le dossier à {B}, à voir avec {B}",
    ),
    "o_commit": (
        "je m'engage à envoyer le dossier avant le {DUE}",
        "ok je m'occupe du dossier, je l'envoie pour le {DUE}",
        "envoi du dossier : je prends, échéance {DUE}",
        "je me charge de transmettre le dossier, ce sera fait d'ici le {DUE}",
    ),
    "o_reassign": (
        "finalement c'est {C} qui enverra le dossier, {A} n'est plus disponible",
        "changement, {C} reprend le dossier à la place de {A}",
        "dossier réattribué à {C} (au lieu de {A})",
        "{C} récupère l'envoi du dossier, {A} n'en a plus la charge",
    ),
}

QUERIES: dict[str, tuple[str, ...]] = {
    "q_budget_current": (
        "quel budget a finalement été validé pour {P}",
        "où en est le budget de {P}",
        "budget actuel de {P}",
        "à combien s'élève l'enveloppe retenue pour {P}",
        "quel montant est en vigueur pour {P} aujourd'hui",
    ),
    "q_date_current": (
        "quelle date de lancement a été retenue pour {P}",
        "quand est-ce que {P} est lancé",
        "date de lancement définitive de {P}",
        "pour quand le démarrage de {P} est-il arrêté",
        "à quelle date {P} va-t-il réellement commencer",
    ),
    "q_owner_current": (
        "qui doit envoyer le dossier pour {P}",
        "qui est responsable de l'envoi du dossier de {P}",
        "responsable dossier {P}",
        "à qui revient la transmission du dossier de {P}",
        "quelle personne a la charge du dossier de {P}",
    ),
    "q_deadline": (
        "pour quand le dossier de {P} doit-il être envoyé",
        "c'est quoi l'échéance du dossier de {P}",
        "échéance envoi dossier {P}",
        "d'ici quand le dossier de {P} sera-t-il transmis",
        "quelle est la date limite pour le dossier de {P}",
    ),
    "q_budget_history": (
        "comment le budget de {P} a-t-il évolué",
        "quels montants ont été discutés pour {P}",
        "historique budget {P}",
        "par quelles étapes est passée l'enveloppe de {P}",
        "retrace les discussions financières sur {P}",
    ),
    "q_unanswerable": (
        "qui a validé le plan de recrutement de {P}",
        "quel prestataire a été choisi pour {P}",
        "budget communication {P}",
        "quel cabinet accompagne {P} sur le juridique",
        "combien de stagiaires sont prévus sur {P}",
    ),
}

# Tours sans contenu décisionnel (bruit), non indexés comme unités.
FILLERS: tuple[tuple[str, ...], ...] = (
    (
        "bonjour à tous",
        "on commence",
        "tout le monde m'entend",
        "je partage mon écran",
        "on fait un tour de table rapide",
        "merci pour vos retours",
    ),
    (
        "salut",
        "bon on y va",
        "ça marche",
        "attends je retrouve mes notes",
        "ouais ouais",
        "on avance",
    ),
    (
        "ouverture de séance",
        "tour de table",
        "point d'étape",
        "questions diverses",
        "fin de séance",
        "prochain point à caler",
    ),
    (
        "hello, on démarre quand vous voulez",
        "je vous écoute",
        "très bien",
        "je note",
        "parfait pour moi",
        "on se dit à la prochaine",
    ),
)

# Pools disjoints par split.
PEOPLE = {
    "train": [
        "Marie",
        "Karim",
        "Sophie",
        "Thomas",
        "Léa",
        "Nicolas",
        "Camille",
        "Julien",
        "Inès",
        "Hugo",
        "Chloé",
        "Antoine",
        "Sarah",
        "Mehdi",
        "Emma",
        "Lucas",
        "Manon",
        "Yanis",
        "Julie",
        "Maxime",
        "Clara",
        "Romain",
        "Nadia",
        "Pierre",
        "Laura",
        "Sami",
        "Pauline",
        "Alexandre",
        "Amina",
        "Vincent",
        "Élodie",
        "Bruno",
        "Fatou",
        "Olivier",
        "Justine",
        "Rachid",
        "Margaux",
        "Kevin",
        "Anaïs",
        "Damien",
    ],
    "val": [
        "Agathe",
        "Bastien",
        "Céline",
        "Dylan",
        "Estelle",
        "Farid",
        "Gaëlle",
        "Hervé",
        "Ilyes",
        "Jeanne",
        "Loïc",
        "Maëva",
    ],
    "test": [
        "Victor",
        "Zoé",
        "Malik",
        "Héloïse",
        "Gaspard",
        "Salomé",
        "Noé",
        "Yasmine",
        "Firmin",
        "Ophélie",
        "Baptiste",
        "Leïla",
        "Edgar",
        "Capucine",
        "Idriss",
        "Solène",
        "Achille",
        "Maïwenn",
        "Rayan",
        "Apolline",
    ],
}

PROJECT_WORDS = {
    "train": [
        "Aigle",
        "Albatros",
        "Bison",
        "Castor",
        "Condor",
        "Cygne",
        "Dauphin",
        "Faucon",
        "Gazelle",
        "Hermine",
        "Ibis",
        "Jaguar",
        "Koala",
        "Lynx",
        "Martin",
        "Narval",
        "Ocelot",
        "Panda",
        "Puma",
        "Renard",
        "Saumon",
        "Tapir",
        "Vison",
        "Zèbre",
        "Héron",
        "Loutre",
        "Mouette",
        "Orque",
        "Pélican",
        "Phoque",
    ],
    "train_suffix": ["Nord", "Sud", "Est", "Ouest", "Plus", "Pro", "Lab", "Hub"],
    "val": ["Agate", "Basalte", "Calcite", "Diorite", "Émeraude", "Feldspath", "Grenat", "Jaspe"],
    "val_suffix": ["Un", "Deux", "Trois", "Quatre"],
    "test": [
        "Rhône",
        "Loire",
        "Garonne",
        "Seine",
        "Dordogne",
        "Meuse",
        "Moselle",
        "Durance",
        "Vienne",
        "Charente",
        "Allier",
        "Cher",
    ],
    "test_suffix": ["Alpha", "Delta", "Sigma", "Oméga"],
}

# Projet réservé à la démo (jamais dans B-SYN).
RESERVED_PROJECTS = frozenset({"Atlas"})
