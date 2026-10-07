"""Configuration typographique, palette de couleurs et styles ReportLab pour le rapport PFA."""

import os
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# Enregistrement des polices TrueType Times New Roman (Windows)
FONT_DIR = "C:/Windows/Fonts"
HAS_TIMES = os.path.exists(f"{FONT_DIR}/times.ttf")

if HAS_TIMES:
    pdfmetrics.registerFont(TTFont("TimesNewRoman", f"{FONT_DIR}/times.ttf"))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", f"{FONT_DIR}/timesbd.ttf"))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Italic", f"{FONT_DIR}/timesi.ttf"))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-BoldItalic", f"{FONT_DIR}/timesbi.ttf"))
    registerFontFamily(
        "TimesNewRoman",
        normal="TimesNewRoman",
        bold="TimesNewRoman-Bold",
        italic="TimesNewRoman-Italic",
        boldItalic="TimesNewRoman-BoldItalic"
    )
    BASE_FONT = "TimesNewRoman"
    BASE_FONT_BOLD = "TimesNewRoman-Bold"
    BASE_FONT_ITALIC = "TimesNewRoman-Italic"
else:
    BASE_FONT = "Helvetica"
    BASE_FONT_BOLD = "Helvetica-Bold"
    BASE_FONT_ITALIC = "Helvetica-Oblique"

# Palette de couleurs sobre et institutionnelle
PRIMARY = colors.HexColor("#0F2942")       # Bleu Marine Profond (Titres majeurs)
SECONDARY = colors.HexColor("#1E4E79")     # Bleu Acier Institutionnel
ACCENT = colors.HexColor("#A87A1E")        # Or Antique (Rappel XAU)
DARK_TEXT = colors.HexColor("#1A202C")     # Anthracite Foncé (Texte courant)
MUTED_TEXT = colors.HexColor("#4A5568")    # Gris neutre (En-têtes, légendes)
LIGHT_BG = colors.HexColor("#F8FAFC")      # Blanc cassé / gris doux
BORDER_COLOR = colors.HexColor("#CBD5E1")  # Bordures de tableaux
HIGHLIGHT = colors.HexColor("#F1F5F9")     # Alternance de lignes
SUCCESS = colors.HexColor("#1B4D3E")       # Vert forêt sobre
DANGER = colors.HexColor("#7A2525")        # Bordeaux sobre

class NumberedCanvas(canvas.Canvas):
    """Canvas avec numérotation dynamique 'Page X sur Y' et en-têtes académiques."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # La page 1 est la page de garde officielle : aucun en-tête ni pied de page
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont(BASE_FONT, 8)
        self.setFillColor(MUTED_TEXT)

        # En-tête courant supérieur
        self.drawString(20 * mm, 283 * mm, "AI Market Intelligence — Rapport PFA (Marché XAU/USD)")
        self.drawRightString(190 * mm, 283 * mm, "Architecture Full-Stack & Modélisation Quantitative")
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(20 * mm, 281 * mm, 190 * mm, 281 * mm)

        # Pied de page inférieur
        self.line(20 * mm, 15 * mm, 190 * mm, 15 * mm)
        self.drawString(20 * mm, 11 * mm, "Mémoire de Projet de Fin d'Année — Université & Laboratoire")
        page_str = f"Page {self._pageNumber} sur {page_count}"
        self.drawRightString(190 * mm, 11 * mm, page_str)

        self.restoreState()


def get_academic_styles():
    """Initialise et retourne le dictionnaire des styles typographiques."""
    base = getSampleStyleSheet()

    styles = {
        'CoverInstitution': ParagraphStyle(
            'CoverInstitution',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=PRIMARY,
            textTransform='uppercase'
        ),
        'CoverSubInstitution': ParagraphStyle(
            'CoverSubInstitution',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=13.5,
            alignment=TA_CENTER,
            textColor=DARK_TEXT
        ),
        'CoverType': ParagraphStyle(
            'CoverType',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=13,
            leading=17,
            alignment=TA_CENTER,
            textColor=ACCENT,
            spaceBefore=12,
            spaceAfter=12
        ),
        'CoverTitle': ParagraphStyle(
            'CoverTitle',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=PRIMARY,
            spaceBefore=10,
            spaceAfter=8
        ),
        'CoverSubtitle': ParagraphStyle(
            'CoverSubtitle',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=11.5,
            leading=16,
            alignment=TA_CENTER,
            textColor=SECONDARY,
            spaceAfter=20
        ),
        'CoverMeta': ParagraphStyle(
            'CoverMeta',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=14,
            alignment=TA_LEFT,
            textColor=DARK_TEXT
        ),
        'CoverYear': ParagraphStyle(
            'CoverYear',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=PRIMARY
        ),
        'ChapterNumber': ParagraphStyle(
            'ChapterNumber',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=13,
            leading=16,
            alignment=TA_LEFT,
            textColor=ACCENT,
            spaceBefore=10,
            spaceAfter=2,
            keepWithNext=True
        ),
        'ChapterTitle': ParagraphStyle(
            'ChapterTitle',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=17,
            leading=22,
            alignment=TA_LEFT,
            textColor=PRIMARY,
            spaceBefore=2,
            spaceAfter=10,
            keepWithNext=True
        ),
        'SectionTitle': ParagraphStyle(
            'SectionTitle',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=12.5,
            leading=16,
            alignment=TA_LEFT,
            textColor=SECONDARY,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        ),
        'SubSectionTitle': ParagraphStyle(
            'SubSectionTitle',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=10.5,
            leading=14.5,
            alignment=TA_LEFT,
            textColor=DARK_TEXT,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True
        ),
        'SubSubSectionTitle': ParagraphStyle(
            'SubSubSectionTitle',
            parent=base['Normal'],
            fontName=BASE_FONT_ITALIC,
            fontSize=9.5,
            leading=13.5,
            alignment=TA_LEFT,
            textColor=SECONDARY,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=DARK_TEXT,
            spaceAfter=6
        ),
        'BodyIndent': ParagraphStyle(
            'BodyIndent',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=DARK_TEXT,
            leftIndent=15,
            spaceAfter=5
        ),
        'Bullet': ParagraphStyle(
            'Bullet',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=9.5,
            leading=13.5,
            alignment=TA_LEFT,
            textColor=DARK_TEXT,
            leftIndent=15,
            spaceAfter=3
        ),
        'Callout': ParagraphStyle(
            'Callout',
            parent=base['Normal'],
            fontName=BASE_FONT_ITALIC,
            fontSize=9,
            leading=13,
            alignment=TA_JUSTIFY,
            textColor=DARK_TEXT,
            spaceBefore=4,
            spaceAfter=4
        ),
        'Formula': ParagraphStyle(
            'Formula',
            parent=base['Normal'],
            fontName=BASE_FONT_ITALIC,
            fontSize=9.5,
            leading=14,
            alignment=TA_CENTER,
            textColor=PRIMARY,
            spaceBefore=5,
            spaceAfter=5
        ),
        'TableText': ParagraphStyle(
            'TableText',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=8.5,
            leading=11.5,
            alignment=TA_LEFT,
            textColor=DARK_TEXT
        ),
        'TableTextCenter': ParagraphStyle(
            'TableTextCenter',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=8.5,
            leading=11.5,
            alignment=TA_CENTER,
            textColor=DARK_TEXT
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=8.5,
            leading=11.5,
            alignment=TA_CENTER,
            textColor=colors.white
        ),
        'CodeSnippet': ParagraphStyle(
            'CodeSnippet',
            parent=base['Normal'],
            fontName='Courier',
            fontSize=7.5,
            leading=10,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#0F172A")
        ),
        'Caption': ParagraphStyle(
            'Caption',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=8.5,
            leading=11.5,
            alignment=TA_CENTER,
            textColor=SECONDARY,
            spaceBefore=4,
            spaceAfter=8,
            keepWithNext=True
        ),
        'TOCItem': ParagraphStyle(
            'TOCItem',
            parent=base['Normal'],
            fontName=BASE_FONT,
            fontSize=9,
            leading=13.5,
            textColor=DARK_TEXT
        ),
        'TOCPage': ParagraphStyle(
            'TOCPage',
            parent=base['Normal'],
            fontName=BASE_FONT_BOLD,
            fontSize=9,
            leading=13.5,
            alignment=TA_RIGHT,
            textColor=PRIMARY
        )
    }
    return styles

