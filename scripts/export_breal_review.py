"""EL-007b — classeur de relecture humaine des réunions tirées au sort.

Usage : uv run python -I scripts/export_breal_review.py
(sortie par défaut : annotations/breal/review/relecture_v1.xlsx)
L'étudiant remplit seulement les colonnes « Correct ? » et « Correction / commentaire ».
"""

import argparse
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from embedding_lab.ingest.breal import load_meetings

THIN = Side(style="thin", color="000000")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD_FILL = PatternFill("solid", fgColor="D9D9D9")
FONT = Font(name="Arial", size=10)
BOLD = Font(name="Arial", size=10, bold=True)
WRAP = Alignment(wrap_text=True, vertical="top")


def table(ws, headers, rows, widths):
    ws.append(headers)
    for row in rows:
        ws.append(row)
    for r in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=len(headers)):
        for c in r:
            c.font, c.border, c.alignment = FONT, BORDER, WRAP
    for c in ws[1]:
        c.font, c.fill = BOLD, HEAD_FILL
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    ws.freeze_panes = "A2"
    dv = DataValidation(type="list", formula1='"oui,non"', allow_blank=True)
    ws.add_data_validation(dv)
    col = chr(65 + headers.index("Correct ? (oui/non)"))
    dv.add(f"{col}2:{col}{ws.max_row}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("annotations/breal/review/relecture_v2.xlsx"))
    ap.add_argument("--ia", type=Path, default=Path("annotations/breal/review/ia"),
                    help="relectures IA à afficher en regard (colonnes « Avis IA »)")
    args = ap.parse_args()
    lines = Path("splits/summre_v1_test_human_review.txt").read_text().splitlines()
    targets = [x for x in lines if x and not x.startswith("#")]
    meetings = load_meetings(Path("data/processed/summre_meetings.jsonl"))
    wb = Workbook()
    readme = wb.active
    readme.title = "Lisez-moi"
    notes = [
        "Relecture des annotations B-REAL (EMBEDDING LAB, ticket EL-007b)",
        "Réunions à relire (tirées au sort avant toute annotation) : " + ", ".join(targets),
        "Annotations produites par Claude (provisoires). Ton avis humain sert de contrôle.",
        "Version 2 : les corrections d'une relecture IA indépendante sont déjà appliquées ; "
        "les colonnes « Avis IA » montrent ce que ce relecteur IA a dit (ok, erreur, douteux). "
        "Les lignes « douteux » sont celles où ton avis compte le plus.",
        "",
        "À remplir : uniquement les deux dernières colonnes de chaque onglet.",
        "Correct ? : oui si l'annotation te paraît juste, non sinon.",
        "Correction / commentaire : ce qui ne va pas (mauvais statut, mauvais responsable, "
        "pertinence trop haute ou trop basse, unité manquante...).",
        "Onglet Unités : une ligne par unité extraite (décision, engagement, question...).",
        "Onglet Questions : une ligne par couple (question, unité jugée). "
        "Pertinence 2 = répond et en vigueur, 1 = utile mais partiel ou ancien, 0 = piège.",
        "Si une bonne réponse manque pour une question, l'écrire dans le commentaire "
        "d'une ligne de cette question.",
        "",
        "Exemple de ligne remplie (onglet Unités) :",
        "statut = proposed | Correct ? = non | Correction = « c'est une décision : "
        "tout le monde dit d'accord juste après (tour t0213) »",
    ]
    for n in notes:
        readme.append([n])
    for c in readme["A"]:
        c.font, c.alignment = FONT, Alignment(wrap_text=True)
    readme["A1"].font = BOLD
    readme.column_dimensions["A"].width = 110

    unit_rows, query_rows = [], []
    for mid in targets:
        group = meetings[mid]["group_id"]
        raw = json.loads(Path(f"annotations/breal/raw/{group}.json").read_text(encoding="utf-8"))
        units = {u["key"]: u for u in raw["units"]}
        ia_path = args.ia / f"{mid}.json"
        ia = json.loads(ia_path.read_text(encoding="utf-8")) if ia_path.exists() else {}
        ia_u = {x["key"]: x for x in ia.get("units", [])}
        ia_q = {(x["query"], x["unit"]): x for x in ia.get("query_judgments", [])}
        ia_q.update({(x["query"], x["unit"]): {**x, "verdict": "manquante (ajoutée)"}
                     for x in ia.get("missing", [])})

        def ia_text(x):
            if not x:
                return "", ""
            extra = " ; ".join(str(x[k]) for k in ("field", "correction", "suggested_rel")
                               if x.get(k) is not None)
            return x["verdict"], (extra + " — " if extra else "") + x.get("comment", "")
        for u in raw["units"]:
            if u["meeting_id"] != mid:
                continue
            spk = next(t["speaker"] for t in meetings[mid]["turns"]
                       if t["turn_id"].endswith(":" + u["turn"]))
            unit_rows.append([mid, u["key"], u["turn"], spk, u["evidence"], u["type"],
                              u["status"], u.get("owner") or "", u["statement"],
                              *ia_text(ia_u.get(u["key"])), "", ""])
        for q in raw["queries"]:
            if q["about_meeting"] != mid:
                continue
            traps = {t["unit"]: t["trap"] for t in q.get("traps", [])}
            if not q.get("answerable", True):
                query_rows.append([mid, q["key"], q["text"], "(aucune réponse attendue)", "",
                                   "", "", "", "", "", ""])
                continue
            for k, v in sorted(q["qrels"].items(), key=lambda kv: -kv[1]):
                query_rows.append([mid, q["key"], q["text"], k, v, traps.get(k, ""),
                                   units[k]["evidence"], *ia_text(ia_q.get((q["key"], k))),
                                   "", ""])
    table(wb.create_sheet("Unités"),
          ["Réunion", "Clé", "Tour", "Locuteur", "Extrait (texte exact)", "Type", "Statut",
           "Responsable", "Reformulation", "Avis IA", "Détail IA", "Correct ? (oui/non)",
           "Correction / commentaire"],
          unit_rows, [12, 7, 7, 9, 50, 11, 11, 12, 40, 11, 40, 12, 40])
    table(wb.create_sheet("Questions"),
          ["Réunion", "Question", "Texte de la question", "Unité", "Pertinence", "Piège",
           "Extrait de l'unité", "Avis IA", "Détail IA", "Correct ? (oui/non)",
           "Correction / commentaire"],
          query_rows, [12, 9, 40, 8, 10, 11, 50, 11, 40, 12, 40])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.out)
    print(f"{args.out} : {len(unit_rows)} unités, {len(query_rows)} lignes de questions")


if __name__ == "__main__":
    main()
