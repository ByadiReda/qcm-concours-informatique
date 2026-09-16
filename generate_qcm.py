from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from questions import QUESTIONS

ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT / "QCM_Concours.pdf"
PDF_AUTHOR = os.environ.get("QCM_PDF_AUTHOR", "qcm-concours-informatique")
FONT_NAME = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"
LEFT_MARGIN = 1.5 * cm
RIGHT_MARGIN = 1.5 * cm
TOP_MARGIN = 1.5 * cm
BOTTOM_MARGIN = 1.8 * cm
CONTENT_WIDTH = A4[0] - LEFT_MARGIN - RIGHT_MARGIN

CATEGORY_COLORS = {
    "Génie logiciel": colors.HexColor("#1d4ed8"),
    "Java": colors.HexColor("#b45309"),
    "Spring / Spring Boot": colors.HexColor("#15803d"),
    "SQL / Bases de données": colors.HexColor("#0f766e"),
    "Développement Web": colors.HexColor("#7c3aed"),
    "Algorithmes et structures de données": colors.HexColor("#be123c"),
}


def resolve_font_path(file_name: str) -> Path:
    candidates = []
    font_dir = os.environ.get("QCM_FONT_DIR")
    if font_dir:
        candidates.append(Path(font_dir) / file_name)
    candidates.extend(
        [
            ROOT / "fonts" / file_name,
            Path("/usr/share/fonts/truetype/dejavu") / file_name,
            Path("/usr/local/share/fonts") / file_name,
            Path.home() / ".local" / "share" / "fonts" / file_name,
            Path("/Library/Fonts") / file_name,
            Path("/System/Library/Fonts") / file_name,
            Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / file_name,
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Police introuvable: {file_name}. "
        "Définissez QCM_FONT_DIR ou placez la police dans ./fonts."
    )


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont(FONT_NAME, str(resolve_font_path("DejaVuSans.ttf"))))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(resolve_font_path("DejaVuSans-Bold.ttf"))))


ARABIC_RESHAPER = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})


def shape_arabic(text: str) -> str:
    return get_display(ARABIC_RESHAPER.reshape(text))


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleQCM", parent=styles["Title"], fontName=FONT_BOLD, fontSize=20, leading=24, alignment=TA_CENTER, textColor=colors.HexColor("#0f172a"), spaceAfter=14))
    styles.add(ParagraphStyle(name="SubTitleQCM", parent=styles["Normal"], fontName=FONT_NAME, fontSize=12, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#334155"), spaceAfter=8))
    styles.add(ParagraphStyle(name="ArabicTitle", parent=styles["Normal"], fontName=FONT_BOLD, fontSize=16, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#166534"), spaceAfter=10))
    styles.add(ParagraphStyle(name="SectionQCM", parent=styles["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18, textColor=colors.white, backColor=colors.HexColor("#1e293b"), borderPadding=(6, 8, 6), spaceBefore=8, spaceAfter=8))
    styles.add(ParagraphStyle(name="QuestionMeta", parent=styles["Normal"], fontName=FONT_BOLD, fontSize=10, textColor=colors.white, leading=12))
    styles.add(ParagraphStyle(name="QuestionText", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=11, leading=15, textColor=colors.HexColor("#111827"), spaceAfter=6))
    styles.add(ParagraphStyle(name="OptionText", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=10.5, leading=14, leftIndent=12, textColor=colors.HexColor("#1f2937"), spaceAfter=1))
    styles.add(ParagraphStyle(name="AnswerText", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=10.5, leading=14, textColor=colors.HexColor("#111827"), spaceAfter=6))
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontName=FONT_NAME, fontSize=9.5, leading=12, textColor=colors.HexColor("#475569"), spaceAfter=4))
    return styles


def cover_table(styles):
    category_counts = Counter(question["category"] for question in QUESTIONS)
    category_difficulty_counts = Counter((question["category"], question["difficulty"]) for question in QUESTIONS)
    rows = [[Paragraph("<b>Catégorie</b>", styles["QuestionText"]), Paragraph("<b>Questions</b>", styles["QuestionText"]), Paragraph("<b>Répartition</b>", styles["QuestionText"])]]
    for category, count in category_counts.items():
        distribution = " / ".join(
            f"{category_difficulty_counts[(category, difficulty)]} {difficulty}"
            for difficulty in ("Basique", "Intermédiaire", "Avancé")
        )
        rows.append([
            Paragraph(category, styles["QuestionText"]),
            Paragraph(str(count), styles["QuestionText"]),
            Paragraph(distribution, styles["QuestionText"]),
        ])
    table = Table(rows, colWidths=[6.1 * cm, 2.2 * cm, 7.2 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def colored_header(text: str, color, styles):
    header = Table([[Paragraph(text, styles["QuestionMeta"])]], colWidths=[CONTENT_WIDTH])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return header


def question_block(index: int, question: dict, styles):
    color = CATEGORY_COLORS[question["category"]]
    meta_text = f"Q{index} • {question['category']} • Niveau {question['difficulty']}"
    header = colored_header(meta_text, color, styles)
    flowables = [KeepTogether([header, Spacer(1, 0.12 * cm), Paragraph(question["statement"], styles["QuestionText"])])]
    for label, option in zip(["A", "B", "C", "D"], question["options"]):
        flowables.append(Paragraph(f"<b>{label}.</b> {option}", styles["OptionText"]))
    flowables.append(Spacer(1, 0.25 * cm))
    return flowables


def answer_block(index: int, question: dict, styles):
    color = CATEGORY_COLORS[question["category"]]
    title = colored_header(
        f"Corrigé Q{index} • {question['category']} • Niveau {question['difficulty']}",
        color,
        styles,
    )
    return [
        KeepTogether([title, Spacer(1, 0.12 * cm), Paragraph(question["statement"], styles["QuestionText"])]),
        Paragraph(f"<b>Bonne réponse :</b> {question['answer']}", styles["AnswerText"]),
        Paragraph(f"<b>Explication :</b> {question['explanation']}", styles["AnswerText"]),
        Spacer(1, 0.22 * cm),
    ]


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()



def build_pdf() -> None:
    register_fonts()
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="QCM Concours Informatique",
        author=PDF_AUTHOR,
    )

    story = [
        Paragraph("QCM Concours Informatique", styles["TitleQCM"]),
        Paragraph(shape_arabic("هندسة البرمجيات والتطوير"), styles["ArabicTitle"]),
        Paragraph("Préparation concours • Génie logiciel • Développement informatique • Base de données", styles["SubTitleQCM"]),
        Paragraph("Ce document contient 108 QCM répartis équitablement sur 6 catégories, avec 3 niveaux de difficulté et une section corrigés détaillée en fin de document.", styles["QuestionText"]),
        Spacer(1, 0.2 * cm),
        Paragraph("Table des matières", styles["SectionQCM"]),
        Paragraph("1. Questions numérotées Q1 à Q108", styles["QuestionText"]),
        Paragraph("2. Corrigés et explications Q1 à Q108", styles["QuestionText"]),
        Spacer(1, 0.1 * cm),
        cover_table(styles),
        Spacer(1, 0.35 * cm),
        Paragraph("Niveaux : Basique, Intermédiaire, Avancé", styles["SmallMuted"]),
        Paragraph("Catégories : Génie logiciel, Java, Spring / Spring Boot, SQL / Bases de données, Développement Web, Algorithmes et structures de données", styles["SmallMuted"]),
        PageBreak(),
        Paragraph("Questions", styles["SectionQCM"]),
    ]

    for index, question in enumerate(QUESTIONS, start=1):
        story.extend(question_block(index, question, styles))

    story.extend([PageBreak(), Paragraph("Corrigés", styles["SectionQCM"])])

    for index, question in enumerate(QUESTIONS, start=1):
        story.extend(answer_block(index, question, styles))

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


if __name__ == "__main__":
    build_pdf()
    print(f"PDF généré : {OUTPUT_FILE}")
