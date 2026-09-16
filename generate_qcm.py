from __future__ import annotations

import html
import os
import re
import unicodedata
from collections import Counter, defaultdict
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

from questions import CATEGORY_ORDER, CATEGORY_PREFIXES, DIFFICULTY_ORDER, QUESTIONS

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


ARABIC_RESHAPER = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})


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


def shape_arabic(text: str) -> str:
    return get_display(ARABIC_RESHAPER.reshape(text))


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleQCM", parent=styles["Title"], fontName=FONT_BOLD, fontSize=20, leading=24, alignment=TA_CENTER, textColor=colors.HexColor("#0f172a"), spaceAfter=14))
    styles.add(ParagraphStyle(name="SubTitleQCM", parent=styles["Normal"], fontName=FONT_NAME, fontSize=12, leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#334155"), spaceAfter=8))
    styles.add(ParagraphStyle(name="ArabicTitle", parent=styles["Normal"], fontName=FONT_BOLD, fontSize=16, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#166534"), spaceAfter=10))
    styles.add(ParagraphStyle(name="SectionQCM", parent=styles["Heading2"], fontName=FONT_BOLD, fontSize=15, leading=18, textColor=colors.white, backColor=colors.HexColor("#1e293b"), borderPadding=(6, 8, 6), spaceBefore=8, spaceAfter=8))
    styles.add(ParagraphStyle(name="CategoryTitle", parent=styles["Heading1"], fontName=FONT_BOLD, fontSize=16, leading=20, textColor=colors.HexColor("#0f172a"), spaceBefore=8, spaceAfter=8))
    styles.add(ParagraphStyle(name="DifficultyTitle", parent=styles["Heading3"], fontName=FONT_BOLD, fontSize=12.5, leading=16, textColor=colors.HexColor("#1f2937"), spaceBefore=6, spaceAfter=6))
    styles.add(ParagraphStyle(name="QuestionMeta", parent=styles["Normal"], fontName=FONT_BOLD, fontSize=10, textColor=colors.white, leading=12))
    styles.add(ParagraphStyle(name="QuestionText", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=11, leading=15, textColor=colors.HexColor("#111827"), spaceAfter=6))
    styles.add(ParagraphStyle(name="OptionText", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=10.5, leading=14, leftIndent=12, textColor=colors.HexColor("#1f2937"), spaceAfter=1))
    styles.add(ParagraphStyle(name="AnswerText", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=10.5, leading=14, textColor=colors.HexColor("#111827"), spaceAfter=6))
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontName=FONT_NAME, fontSize=9.5, leading=12, textColor=colors.HexColor("#475569"), spaceAfter=4))
    styles.add(ParagraphStyle(name="TocEntry", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=10.5, leading=14, textColor=colors.HexColor("#0f172a"), spaceAfter=3))
    styles.add(ParagraphStyle(name="TocSubEntry", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=9.8, leading=13, leftIndent=14, textColor=colors.HexColor("#334155"), spaceAfter=2))
    return styles


def ordered_questions():
    grouped = defaultdict(list)
    for question in QUESTIONS:
        grouped[(question["category"], question["difficulty"])].append(question)

    numbered = []
    global_number = 1
    category_numbers = Counter()
    for category in CATEGORY_ORDER:
        for difficulty in DIFFICULTY_ORDER:
            for question in grouped[(category, difficulty)]:
                category_numbers[category] += 1
                numbered.append(
                    {
                        **question,
                        "number": global_number,
                        "category_number": category_numbers[category],
                        "category_id": f"{CATEGORY_PREFIXES[category]}-{category_numbers[category]:03d}",
                    }
                )
                global_number += 1
    return numbered


def cover_table(styles, numbered_questions):
    category_counts = Counter(question["category"] for question in numbered_questions)
    category_difficulty_counts = Counter((question["category"], question["difficulty"]) for question in numbered_questions)
    rows = [[Paragraph("<b>Catégorie</b>", styles["QuestionText"]), Paragraph("<b>Questions</b>", styles["QuestionText"]), Paragraph("<b>Répartition</b>", styles["QuestionText"])]]
    for category in CATEGORY_ORDER:
        distribution = " / ".join(
            f"{category_difficulty_counts[(category, difficulty)]} {difficulty}"
            for difficulty in DIFFICULTY_ORDER
        )
        rows.append([
            Paragraph(category, styles["QuestionText"]),
            Paragraph(str(category_counts[category]), styles["QuestionText"]),
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


def anchor_paragraph(anchor: str, text: str, style):
    return Paragraph(f'<a name="{anchor}"/>{html.escape(text)}', style)


def toc_link(label: str, target: str) -> str:
    return f'<link href="#{target}">{html.escape(label)}</link>'


def question_block(question: dict, styles):
    color = CATEGORY_COLORS[question["category"]]
    meta_text = f"Q{question['number']} • {question['category_id']} • {question['category']} • Niveau {question['difficulty']}"
    header = colored_header(meta_text, color, styles)
    flowables = [KeepTogether([header, Spacer(1, 0.12 * cm), Paragraph(html.escape(question["statement"]), styles["QuestionText"])])]
    for label, option in zip(["A", "B", "C", "D"], question["options"]):
        flowables.append(Paragraph(f"<b>{label}.</b> {html.escape(option)}", styles["OptionText"]))
    flowables.append(Spacer(1, 0.25 * cm))
    return flowables


def answer_block(question: dict, styles):
    color = CATEGORY_COLORS[question["category"]]
    title = colored_header(
        f"Corrigé Q{question['number']} • {question['category_id']} • Niveau {question['difficulty']}",
        color,
        styles,
    )
    return [
        KeepTogether([title, Spacer(1, 0.12 * cm), Paragraph(html.escape(question["statement"]), styles["QuestionText"])]),
        Paragraph(f"<b>Bonne réponse :</b> {question['answer']}", styles["AnswerText"]),
        Paragraph(f"<b>Explication :</b> {html.escape(question['explanation'])}", styles["AnswerText"]),
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
    numbered_questions = ordered_questions()
    grouped = defaultdict(list)
    for question in numbered_questions:
        grouped[question["category"]].append(question)

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

    total_questions = len(numbered_questions)
    toc_anchor = "toc-top"
    story = [
        Paragraph(f'<a name="{toc_anchor}"/>QCM Concours Informatique', styles["TitleQCM"]),
        Paragraph(shape_arabic("هندسة البرمجيات والتطوير"), styles["ArabicTitle"]),
        Paragraph("Préparation concours • Génie logiciel • Java • Spring • SQL • Web • Algorithmes", styles["SubTitleQCM"]),
        Paragraph(
            f"Ce document contient {total_questions} QCM répartis en 6 grandes catégories. Chaque catégorie est organisée par niveau (Basique, Intermédiaire, Avancé) et suivie de son corrigé détaillé.",
            styles["QuestionText"],
        ),
        Spacer(1, 0.2 * cm),
        Paragraph("Table des matières", styles["SectionQCM"]),
    ]

    for category in CATEGORY_ORDER:
        category_slug = slugify(category)
        question_anchor = f"questions-{category_slug}"
        answer_anchor = f"answers-{category_slug}"
        story.append(
            Paragraph(
                f"{toc_link(category, question_anchor)} — {len(grouped[category])} questions — {toc_link('Corrigé', answer_anchor)}",
                styles["TocEntry"],
            )
        )
        for difficulty in DIFFICULTY_ORDER:
            difficulty_slug = slugify(difficulty)
            count = sum(1 for question in grouped[category] if question["difficulty"] == difficulty)
            story.append(
                Paragraph(
                    f"• {toc_link(difficulty, f'{question_anchor}-{difficulty_slug}')} ({count} questions)",
                    styles["TocSubEntry"],
                )
            )

    story.extend(
        [
            Spacer(1, 0.12 * cm),
            cover_table(styles, numbered_questions),
            Spacer(1, 0.3 * cm),
            Paragraph("Répartition cible atteinte par catégorie : 38 Basique • 43 Intermédiaire • 27 Avancé (108 questions).", styles["SmallMuted"]),
            Paragraph("Numérotation globale continue : Q1 à Q648. Identifiants locaux par catégorie : GL-001, JAVA-001, SPR-001, SQL-001, WEB-001, ALGO-001, etc.", styles["SmallMuted"]),
            PageBreak(),
        ]
    )

    for category_index, category in enumerate(CATEGORY_ORDER):
        category_slug = slugify(category)
        question_anchor = f"questions-{category_slug}"
        answer_anchor = f"answers-{category_slug}"
        color = CATEGORY_COLORS[category]
        questions_for_category = grouped[category]

        story.append(anchor_paragraph(question_anchor, f"{category} — Questions", styles["CategoryTitle"]))
        story.append(Paragraph(f"<font color='{color.hexval()}'><b>Préfixe catégorie :</b> {CATEGORY_PREFIXES[category]} — <b>Total :</b> {len(questions_for_category)} questions — <link href='#{toc_anchor}'>Retour à la table des matières</link></font>", styles["SmallMuted"]))
        story.append(Spacer(1, 0.1 * cm))

        for difficulty in DIFFICULTY_ORDER:
            difficulty_slug = slugify(difficulty)
            questions_for_level = [question for question in questions_for_category if question["difficulty"] == difficulty]
            story.append(anchor_paragraph(f"{question_anchor}-{difficulty_slug}", f"Niveau {difficulty}", styles["DifficultyTitle"]))
            story.append(Paragraph(f"{len(questions_for_level)} questions pour ce niveau.", styles["SmallMuted"]))
            for question in questions_for_level:
                story.extend(question_block(question, styles))

        story.extend([
            PageBreak(),
            anchor_paragraph(answer_anchor, f"{category} — Corrigé", styles["CategoryTitle"]),
            Paragraph(f"<b>Corrigé de la catégorie {html.escape(category)}</b> — <link href='#{question_anchor}'>Retour aux questions de la catégorie</link> • <link href='#{toc_anchor}'>Retour à la table des matières</link>", styles["SmallMuted"]),
            Spacer(1, 0.1 * cm),
        ])
        for question in questions_for_category:
            story.extend(answer_block(question, styles))
        if category_index < len(CATEGORY_ORDER) - 1:
            story.append(PageBreak())

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


if __name__ == "__main__":
    build_pdf()
    print(f"PDF généré : {OUTPUT_FILE}")
