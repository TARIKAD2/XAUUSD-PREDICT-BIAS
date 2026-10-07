"""Script de génération du rapport complet de PFA en PDF pour le projet AI Market Intelligence (XAU/USD).

Conformité totale aux exigences académiques et aux audits factuels du dépôt local.
"""

import os
import sys
import shutil
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Palette de couleurs académique & professionnelle
PRIMARY = colors.HexColor("#0F2942")      # Bleu Nuit Impérial
SECONDARY = colors.HexColor("#1E4E79")    # Bleu Acier Profond
ACCENT = colors.HexColor("#C59B27")       # Or Sombre / Ambré (XAU)
DARK_TEXT = colors.HexColor("#2D3748")    # Gris Anthracite
LIGHT_BG = colors.HexColor("#F8FAFC")     # Fond très clair
BORDER_COLOR = colors.HexColor("#CBD5E1") # Bordure grise claire
HIGHLIGHT = colors.HexColor("#EDF2F7")    # Gris doux pour alternance tables
SUCCESS = colors.HexColor("#22543D")      # Vert sombre
DANGER = colors.HexColor("#742A2A")       # Rouge sombre

class NumberedCanvas(canvas.Canvas):
    """Canvas personnalisé permettant la numérotation dynamique 'Page X sur Y'
    et l'insertion d'en-têtes et pieds de page académiques.
    """
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
        # La page 1 est la page de garde officielle : pas d'en-tête ni de pied de page
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))

        # En-tête courant
        self.drawString(20 * mm, 283 * mm, "AI Market Intelligence — Rapport PFA (Marché XAU/USD)")
        self.drawRightString(190 * mm, 283 * mm, "Audit & Conception Système")
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.6)
        self.line(20 * mm, 281 * mm, 190 * mm, 281 * mm)

        # Pied de page courant
        self.line(20 * mm, 15 * mm, 190 * mm, 15 * mm)
        self.drawString(20 * mm, 11 * mm, "Plateforme de Recherche et d'Aide à la Décision")
        page_str = f"Page {self._pageNumber} sur {page_count}"
        self.drawRightString(190 * mm, 11 * mm, page_str)

        self.restoreState()


def get_academic_styles():
    """Initialise et retourne le dictionnaire de styles typographiques."""
    base = getSampleStyleSheet()

    styles = {
        'CoverInstitution': ParagraphStyle(
            'CoverInstitution',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=PRIMARY,
            textTransform='uppercase'
        ),
        'CoverSubInstitution': ParagraphStyle(
            'CoverSubInstitution',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            alignment=TA_CENTER,
            textColor=DARK_TEXT
        ),
        'CoverType': ParagraphStyle(
            'CoverType',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            alignment=TA_CENTER,
            textColor=ACCENT,
            spaceBefore=15,
            spaceAfter=15
        ),
        'CoverTitle': ParagraphStyle(
            'CoverTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=21,
            leading=26,
            alignment=TA_CENTER,
            textColor=PRIMARY,
            spaceBefore=10,
            spaceAfter=10
        ),
        'CoverSubtitle': ParagraphStyle(
            'CoverSubtitle',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=SECONDARY,
            spaceAfter=25
        ),
        'CoverMeta': ParagraphStyle(
            'CoverMeta',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            alignment=TA_LEFT,
            textColor=DARK_TEXT
        ),
        'CoverYear': ParagraphStyle(
            'CoverYear',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=PRIMARY
        ),
        'ChapterTitle': ParagraphStyle(
            'ChapterTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            alignment=TA_LEFT,
            textColor=PRIMARY,
            spaceBefore=15,
            spaceAfter=10,
            keepWithNext=True
        ),
        'SectionTitle': ParagraphStyle(
            'SectionTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12.5,
            leading=16,
            alignment=TA_LEFT,
            textColor=SECONDARY,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True
        ),
        'SubSectionTitle': ParagraphStyle(
            'SubSectionTitle',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=14,
            alignment=TA_LEFT,
            textColor=DARK_TEXT,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13.5,
            alignment=TA_JUSTIFY,
            textColor=DARK_TEXT,
            spaceAfter=6
        ),
        'Bullet': ParagraphStyle(
            'Bullet',
            parent=base['Normal'],
            fontName='Helvetica',
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
            fontName='Helvetica-Oblique',
            fontSize=9,
            leading=13,
            alignment=TA_JUSTIFY,
            textColor=DARK_TEXT,
            spaceBefore=4,
            spaceAfter=4
        ),
        'TableText': ParagraphStyle(
            'TableText',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            alignment=TA_LEFT,
            textColor=DARK_TEXT
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11.5,
            alignment=TA_CENTER,
            textColor=colors.white
        ),
        'CodeSnippet': ParagraphStyle(
            'CodeSnippet',
            parent=base['Normal'],
            fontName='Courier',
            fontSize=8,
            leading=10.5,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#1A202C")
        ),
        'Caption': ParagraphStyle(
            'Caption',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
            textColor=SECONDARY,
            spaceBefore=4,
            spaceAfter=8,
            keepWithNext=True
        ),
        'TOCItem': ParagraphStyle(
            'TOCItem',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=DARK_TEXT
        ),
        'TOCPage': ParagraphStyle(
            'TOCPage',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=14,
            alignment=TA_RIGHT,
            textColor=PRIMARY
        )
    }
    return styles

def build_pdf_report(output_path: str):
    """Compile et génère le document PDF complet de PFA."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = get_academic_styles()
    story = []

    # =========================================================================
    # PAGE DE GARDE OFFICIELLE
    # =========================================================================
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("RÉPUBLIQUE ALGÉRIENNE DÉMOCRATIQUE ET POPULAIRE", styles['CoverInstitution']))
    story.append(Paragraph("MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR ET DE LA RECHERCHE SCIENTIFIQUE", styles['CoverInstitution']))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("FACULTÉ DES SCIENCES ET TECHNOLOGIES — DÉPARTEMENT D'INFORMATIQUE", styles['CoverSubInstitution']))
    story.append(Spacer(1, 15 * mm))

    story.append(Paragraph("MÉMOIRE DE PROJET DE FIN D'ANNÉE (PFA)", styles['CoverType']))
    story.append(Paragraph("Pour l'obtention du Diplôme de Fin de Cycle", styles['CoverSubInstitution']))
    story.append(Spacer(1, 8 * mm))

    # Titre du Projet
    story.append(Paragraph("CONCEPTION ET DÉPLOIEMENT D'UNE PLATEFORME D'INTELLIGENCE QUANTITATIVE ET D'AIDE À LA DÉCISION POUR LE MARCHÉ DE L'OR (XAU/USD)", styles['CoverTitle']))
    story.append(Paragraph("Architecture Asynchrone FastAPI, Inférence Probabiliste Binaire et Interface Analytique Next.js", styles['CoverSubtitle']))
    story.append(Spacer(1, 15 * mm))

    # Métadonnées Encadrement / Auteur
    meta_data = [
        [
            Paragraph("<b>Réalisé par :</b><br/>Étudiant Chercheur en Ingénierie Logicielle & IA", styles['CoverMeta']),
            Paragraph("<b>Sous la direction de :</b><br/>Commission Académique d'Évaluation", styles['CoverMeta'])
        ],
        [
            Paragraph("<b>Spécialité :</b><br/>Systèmes d'Information & Science des Données", styles['CoverMeta']),
            Paragraph("<b>Entreprise / Laboratoire d'Accueil :</b><br/>Laboratoire de Recherche en IA Quantitative", styles['CoverMeta'])
        ]
    ]
    t_meta = Table(meta_data, colWidths=[85 * mm, 85 * mm])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_meta)

    story.append(Spacer(1, 25 * mm))
    story.append(Paragraph("Année Universitaire : 2025 / 2026", styles['CoverYear']))
    story.append(PageBreak())

    # =========================================================================
    # PAGES PRÉLIMINAIRES
    # =========================================================================

    # Dédicace
    story.append(Paragraph("Dédicace", styles['ChapterTitle']))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("<i>À mes parents, pour leur soutien inconditionnel, leur patience et leurs sacrifices continus tout au long de mon parcours académique.</i>", styles['Body']))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("<i>À mes professeurs et encadrants, qui m'ont inculqué la rigueur méthodologique, l'honnêteté intellectuelle et la curiosité scientifique indispensables à la recherche.</i>", styles['Body']))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("<i>À tous ceux qui contribuent à l'avancement de la science ouverte, du logiciel libre et de la technologie responsable.</i>", styles['Body']))
    story.append(PageBreak())

    # Remerciements
    story.append(Paragraph("Remerciements", styles['ChapterTitle']))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Au terme de ce Projet de Fin d'Année, je tiens à exprimer ma profonde gratitude à l'ensemble des personnes ayant contribué de près ou de loin à l'aboutissement de ce travail de recherche et d'ingénierie.", styles['Body']))
    story.append(Paragraph("Mes sincères remerciements s'adressent aux membres du corps professoral pour la qualité de leur enseignement et leurs orientations bienveillantes.", styles['Body']))
    story.append(Paragraph("Je remercie également les membres du jury d'avoir accepté d'examiner et d'évaluer ce mémoire, apportant ainsi leur expertise précieuse à la validation académique de cette plateforme.", styles['Body']))
    story.append(PageBreak())

    # Résumé & Abstract
    story.append(Paragraph("Résumé", styles['ChapterTitle']))
    story.append(Paragraph(
        "Ce mémoire présente la conception, la réalisation et l'évaluation rigoureuse d'une plateforme web modulaire "
        "d'aide à la décision pour le marché de l'or contre dollar américain (XAU/USD). "
        "Face à la complexité et à la non-stationnarité des cotations financières, le système intègre une chaîne causale "
        "stricte d'ingénierie de 87 caractéristiques multi-échelles temporelles (M15, H1, H4), conçue pour éliminer toute "
        "forme de fuite d'information prospective (data leakage). "
        "Contrairement aux approches intuitives, le problème est formulé comme une classification binaire stricte entre "
        "deux régimes directeurs : <b>BULLISH</b> et <b>BEARISH</b>. Les fluctuations marginales sous un seuil paramétrique "
        "déterminent une zone morte d'indécision filtrée à l'apprentissage et à la validation. "
        "L'évaluation empirique repose sur un protocole walk-forward expansif à 4 plis avec embargo. Sur l'échantillon de test "
        "hors-échantillon, la Régression Logistique surpasse les modèles ensemblistes arborescents pénalisés par le surapprentissage, "
        "obtenant une justesse (accuracy) de 45.71% à 24 heures et de 39.20% à 120 heures. "
        "L'infrastructure articule un backend asynchrone FastAPI, un flux continu WebSocket connecté à Twelve Data, "
        "une couche de persistance MongoDB et un tableau de bord analytique réactif Next.js supportant l'internationalisation trilingue (EN/FR/AR).",
        styles['Body']
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("<b>Mots-clés :</b> Marché XAU/USD, Apprentissage Automatique, Classification Binaire, Walk-Forward, Prévention du Data Leakage, FastAPI, WebSocket, Next.js, Explicabilité Linéaire.", styles['Callout']))
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Abstract", styles['ChapterTitle']))
    story.append(Paragraph(
        "This thesis presents the design, engineering, and empirical assessment of an asynchronous decision-support "
        "web platform dedicated to the Gold versus US Dollar (XAU/USD) financial market. "
        "Addressing the stochastic and non-stationary nature of financial time series, the architecture implements a strictly "
        "causal multi-timeframe feature engineering pipeline generating 87 features across M15, H1, and H4 timeframes, "
        "guaranteeing total absence of forward lookahead leakage through backward as-of alignment. "
        "The directional forecasting task is mathematically formulated as a strict binary classification problem between "
        "<b>BULLISH</b> and <b>BEARISH</b> regimes. Observations within an empirical threshold deadband are deliberately "
        "excluded during dataset generation. "
        "Under rigorous walk-forward expanding window cross-validation with an embargo period, Logistic Regression "
        "demonstrates superior generalization stability over tree-based ensembles afflicted with severe overfitting, "
        "yielding an out-of-sample accuracy of 45.71% over a 24-hour horizon and 39.20% over a 120-hour horizon. "
        "The production architecture integrates a high-throughput FastAPI backend, Twelve Data WebSocket live ingestion, "
        "MongoDB persistence schemas, and an interactive Next.js dashboard featuring full trilingual internationalization (EN/FR/AR).",
        styles['Body']
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("<b>Keywords:</b> XAU/USD Spot Market, Machine Learning, Binary Classification, Walk-Forward Validation, Data Leakage Prevention, FastAPI, WebSocket Streaming, Next.js, Linear Explainability.", styles['Callout']))
    story.append(PageBreak())

    # Table des Matières
    story.append(Paragraph("Table des Matières", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    
    toc_data = [
        [Paragraph("<b>Introduction Générale</b>", styles['TOCItem']), Paragraph("<b>1</b>", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 1 — Contexte Général et Étude de l'Existant</b>", styles['TOCItem']), Paragraph("<b>3</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1.1 Présentation du marché spot XAU/USD", styles['TOCItem']), Paragraph("3", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1.2 Problématique de l'analyse quantitative de l'or", styles['TOCItem']), Paragraph("4", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1.3 Analyse critique des solutions existantes", styles['TOCItem']), Paragraph("4", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1.4 Positionnement et contributions de la solution proposée", styles['TOCItem']), Paragraph("5", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 2 — Analyse et Spécification des Besoins</b>", styles['TOCItem']), Paragraph("<b>6</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2.1 Identification des acteurs du système", styles['TOCItem']), Paragraph("6", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2.2 Spécification des besoins fonctionnels", styles['TOCItem']), Paragraph("6", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2.3 Exigences non fonctionnelles et contraintes critiques", styles['TOCItem']), Paragraph("7", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2.4 Modélisation des cas d'utilisation", styles['TOCItem']), Paragraph("8", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 3 — Analyse et Conception Système</b>", styles['TOCItem']), Paragraph("<b>9</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.1 Architecture globale en couches micro-services", styles['TOCItem']), Paragraph("9", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.2 Architecture logicielle Backend FastAPI", styles['TOCItem']), Paragraph("10", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.3 Architecture logicielle Frontend Next.js", styles['TOCItem']), Paragraph("11", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.4 Schémas de données et indexation MongoDB", styles['TOCItem']), Paragraph("11", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3.5 Conception des flux réactifs et synchrones (REST & WS)", styles['TOCItem']), Paragraph("12", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 4 — Acquisition et Préparation des Données de Marché</b>", styles['TOCItem']), Paragraph("<b>14</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.1 Collecte des données historiques LiteFinance", styles['TOCItem']), Paragraph("14", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.2 Acquisition temps réel Twelve Data REST & WebSocket", styles['TOCItem']), Paragraph("15", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.3 Protocole de nettoyage et validation d'intégrité", styles['TOCItem']), Paragraph("15", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.4 Ingénierie des caractéristiques : pipeline de 87 features MTF", styles['TOCItem']), Paragraph("16", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4.5 Prévention mathématique du Data Leakage par alignement causal", styles['TOCItem']), Paragraph("18", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 5 — Machine Learning et Prédiction Directionnelle</b>", styles['TOCItem']), Paragraph("<b>19</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.1 Formalisation de la cible binaire (BULLISH vs BEARISH)", styles['TOCItem']), Paragraph("19", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.2 Filtrage de la zone morte et justification de l'absence de classe neutre", styles['TOCItem']), Paragraph("20", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.3 Algorithmes benchmarkés et protocole Walk-Forward", styles['TOCItem']), Paragraph("21", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.4 Analyse comparative et sélection du modèle de production", styles['TOCItem']), Paragraph("22", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.5 Métriques réelles obtenues hors-échantillon (Daily & Weekly)", styles['TOCItem']), Paragraph("23", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.6 Modélisation de la confiance et scénarios probabilistes", styles['TOCItem']), Paragraph("25", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;5.7 Explicabilité : coefficients logit linéaires et intégration SHAP", styles['TOCItem']), Paragraph("26", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 6 — Réalisation et Développement de l'Application</b>", styles['TOCItem']), Paragraph("<b>27</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;6.1 Implémentation du backend FastAPI et cycle de vie asynchrone", styles['TOCItem']), Paragraph("27", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;6.2 Gestionnaire WebSocket singleton et distribution des ticks", styles['TOCItem']), Paragraph("28", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;6.3 Développement du frontend Next.js et Dashboard Terminal", styles['TOCItem']), Paragraph("29", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;6.4 Composants d'affichage des prédictions et scénarios", styles['TOCItem']), Paragraph("30", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;6.5 Internationalisation trilingue (EN / FR / AR) et support RTL", styles['TOCItem']), Paragraph("31", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 7 — Tests, Validation et Assurance Qualité</b>", styles['TOCItem']), Paragraph("<b>32</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;7.1 Stratégie de test et suite automatisée Pytest (117 tests)", styles['TOCItem']), Paragraph("32", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;7.2 Tests de non-régression et d'absence de fuite prospective", styles['TOCItem']), Paragraph("33", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;7.3 Validation de l'ingestion WebSocket et des contrats d'API", styles['TOCItem']), Paragraph("34", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;7.4 Statut des tests frontend et génération dynamique de l'interface", styles['TOCItem']), Paragraph("34", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 8 — Déploiement et DevOps</b>", styles['TOCItem']), Paragraph("<b>35</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;8.1 Conteneurisation Docker multi-services", styles['TOCItem']), Paragraph("35", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;8.2 Orchestration locale via Docker Compose", styles['TOCItem']), Paragraph("36", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;8.3 Configuration de déploiement cloud (Railway & Vercel)", styles['TOCItem']), Paragraph("36", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;8.4 Intégration MongoDB Atlas et gestion des environnements", styles['TOCItem']), Paragraph("37", styles['TOCPage'])],
        [Paragraph("<b>Chapitre 9 — Discussion Critique, Limites et Perspectives</b>", styles['TOCItem']), Paragraph("<b>38</b>", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;9.1 Synthèse critique des performances ML et efficience de marché", styles['TOCItem']), Paragraph("38", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;9.2 Limites d'infrastructure et contraintes de connectivité", styles['TOCItem']), Paragraph("39", styles['TOCPage'])],
        [Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;9.3 Perspectives d'évolution et recherche future", styles['TOCItem']), Paragraph("40", styles['TOCPage'])],
        [Paragraph("<b>Conclusion Générale</b>", styles['TOCItem']), Paragraph("<b>41</b>", styles['TOCPage'])],
        [Paragraph("<b>Bibliographie et Webographie</b>", styles['TOCItem']), Paragraph("<b>42</b>", styles['TOCPage'])],
        [Paragraph("<b>Annexes</b>", styles['TOCItem']), Paragraph("<b>44</b>", styles['TOCPage'])],
    ]
    t_toc = Table(toc_data, colWidths=[150 * mm, 20 * mm])
    t_toc.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    # Liste des Tableaux et Liste des Abréviations
    story.append(Paragraph("Liste des Tableaux", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    table_list = [
        [Paragraph("Tableau 1.1 : Comparatif fonctionnel des solutions d'analyse de marché", styles['TOCItem']), Paragraph("5", styles['TOCPage'])],
        [Paragraph("Tableau 2.1 : Matrice de traçabilité des exigences fonctionnelles", styles['TOCItem']), Paragraph("7", styles['TOCPage'])],
        [Paragraph("Tableau 4.1 : Audit d'intégrité des séries historiques LiteFinance", styles['TOCItem']), Paragraph("15", styles['TOCPage'])],
        [Paragraph("Tableau 4.2 : Répartition des 87 caractéristiques par échelle temporelle", styles['TOCItem']), Paragraph("17", styles['TOCPage'])],
        [Paragraph("Tableau 5.1 : Benchmark comparatif des algorithmes ML (Walk-Forward)", styles['TOCItem']), Paragraph("22", styles['TOCPage'])],
        [Paragraph("Tableau 5.2 : Métriques hors-échantillon réelles du modèle Daily (24H)", styles['TOCItem']), Paragraph("24", styles['TOCPage'])],
        [Paragraph("Tableau 5.3 : Métriques hors-échantillon réelles du modèle Weekly (120H)", styles['TOCItem']), Paragraph("25", styles['TOCPage'])],
        [Paragraph("Tableau 7.1 : Synthèse d'exécution de la suite de tests automatisés (Pytest)", styles['TOCItem']), Paragraph("33", styles['TOCPage'])],
        [Paragraph("Tableau 8.1 : Matrice de configuration et statut d'audit des environnements", styles['TOCItem']), Paragraph("37", styles['TOCPage'])],
    ]
    t_tbl = Table(table_list, colWidths=[150 * mm, 20 * mm])
    t_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_tbl)
    story.append(Spacer(1, 10 * mm))

    story.append(Paragraph("Liste des Abréviations", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))
    abbr_data = [
        [Paragraph("<b>API</b>", styles['TableText']), Paragraph("Application Programming Interface", styles['TableText'])],
        [Paragraph("<b>ASGI</b>", styles['TableText']), Paragraph("Asynchronous Server Gateway Interface", styles['TableText'])],
        [Paragraph("<b>ATR</b>", styles['TableText']), Paragraph("Average True Range (Indicateur de volatilité)", styles['TableText'])],
        [Paragraph("<b>AUC</b>", styles['TableText']), Paragraph("Area Under the ROC Curve (Surface sous la courbe ROC)", styles['TableText'])],
        [Paragraph("<b>CORS</b>", styles['TableText']), Paragraph("Cross-Origin Resource Sharing", styles['TableText'])],
        [Paragraph("<b>EMA</b>", styles['TableText']), Paragraph("Exponential Moving Average (Moyenne mobile exponentielle)", styles['TableText'])],
        [Paragraph("<b>EMH</b>", styles['TableText']), Paragraph("Efficient Market Hypothesis (Hypothèse d'efficience des marchés)", styles['TableText'])],
        [Paragraph("<b>HTTP</b>", styles['TableText']), Paragraph("HyperText Transfer Protocol", styles['TableText'])],
        [Paragraph("<b>MACD</b>", styles['TableText']), Paragraph("Moving Average Convergence Divergence", styles['TableText'])],
        [Paragraph("<b>ML</b>", styles['TableText']), Paragraph("Machine Learning (Apprentissage Automatique)", styles['TableText'])],
        [Paragraph("<b>MTF</b>", styles['TableText']), Paragraph("Multi-Timeframe (Multi-échelles temporelles)", styles['TableText'])],
        [Paragraph("<b>OHLC</b>", styles['TableText']), Paragraph("Open, High, Low, Close (Données de chandeliers)", styles['TableText'])],
        [Paragraph("<b>REST</b>", styles['TableText']), Paragraph("Representational State Transfer", styles['TableText'])],
        [Paragraph("<b>ROC</b>", styles['TableText']), Paragraph("Receiver Operating Characteristic", styles['TableText'])],
        [Paragraph("<b>RSI</b>", styles['TableText']), Paragraph("Relative Strength Index (Indice de force relative)", styles['TableText'])],
        [Paragraph("<b>RTL</b>", styles['TableText']), Paragraph("Right-to-Left (Orientation du texte de droite à gauche)", styles['TableText'])],
        [Paragraph("<b>SHAP</b>", styles['TableText']), Paragraph("SHapley Additive exPlanations", styles['TableText'])],
        [Paragraph("<b>SMA</b>", styles['TableText']), Paragraph("Simple Moving Average (Moyenne mobile simple)", styles['TableText'])],
        [Paragraph("<b>UI / UX</b>", styles['TableText']), Paragraph("User Interface / User Experience", styles['TableText'])],
        [Paragraph("<b>UTC</b>", styles['TableText']), Paragraph("Coordinated Universal Time (Temps universel coordonné)", styles['TableText'])],
        [Paragraph("<b>WS</b>", styles['TableText']), Paragraph("WebSocket (Protocole bidirectionnel en temps réel)", styles['TableText'])],
        [Paragraph("<b>XAU/USD</b>", styles['TableText']), Paragraph("Once d'or exprimée en dollars américains", styles['TableText'])],
    ]
    t_abbr = Table(abbr_data, colWidths=[30 * mm, 140 * mm])
    t_abbr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_abbr)
    story.append(PageBreak())

    # =========================================================================
    # INTRODUCTION GÉNÉRALE
    # =========================================================================
    story.append(Paragraph("Introduction Générale", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Contexte Général", styles['SectionTitle']))
    story.append(Paragraph(
        "L'or physique (XAU) constitue depuis l'Antiquité un étalon monétaire et une réserve de valeur primordiale. "
        "Sur les marchés financiers contemporains, la paire XAU/USD (cours au comptant de l'once d'or exprimé en dollars américains) "
        "représente l'un des instruments les plus négociés au monde, caractérisé par une liquidité continue et une forte sensibilité "
        "aux anticipations d'inflation, aux variations de taux d'intérêt réels et aux chocs d'aversion au risque géopolitique. "
        "L'avènement des flux de données en continu et de l'analyse computationnelle a transformé l'étude de ce marché : "
        "les acteurs institutionnels et les analystes quantitatifs cherchent désormais à rationaliser leurs prises de décision "
        "en combinant modélisation probabiliste et architecture logicielle réactive.",
        styles['Body']
    ))

    story.append(Paragraph("Problématique", styles['SectionTitle']))
    story.append(Paragraph(
        "L'analyse quantitative du cours XAU/USD se heurte à des défis méthodologiques et techniques majeurs :<br/>"
        "1. <b>La dispersion et l'hétérogénéité des données</b> : Les cotations de marché se partagent entre historiques volumineux "
        "issus de plateformes de courtage et flux de streaming haute fréquence émis par des passerelles de données telles que Twelve Data.<br/>"
        "2. <b>Le risque d'asymétrie temporelle (Data Leakage)</b> : La fusion naïve de séries à échelles multiples (15 minutes, 1 heure, 4 heures) "
        "introduit fréquemment des fuites d'informations futures (lookahead bias), faussant dramatiquement la validité des modèles d'apprentissage.<br/>"
        "3. <b>L'illusion de prédictibilité et l'effet boîte noire</b> : De nombreuses solutions commerciales prétendent prédire l'orientation "
        "des marchés avec des taux de succès irréalistes, dissimulant le surapprentissage et privant l'utilisateur de toute métrique d'incertitude "
        "ou d'explicabilité causale.",
        styles['Body']
    ))

    story.append(Paragraph("Motivation et Objectifs", styles['SectionTitle']))
    story.append(Paragraph(
        "La motivation de ce Projet de Fin d'Année réside dans la construction d'une plateforme d'intelligence de marché rigoureuse, "
        "éthique et fondée sur des preuves tangibles. Le système s'interdit formellement tout passage d'ordre automatique ou promesse commerciale "
        "pour se concentrer exclusivement sur la recherche quantitative et l'aide à la décision factuelle.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Les objectifs opérationnels se déclinent selon quatre axes fondamentaux :<br/>"
        "• <i>Ingénierie des données causales</i> : Construire un pipeline unifié de 87 caractéristiques techniques multi-timeframes "
        "exempt de toute contamination prospective.<br/>"
        "• <i>Apprentissage statistique robuste</i> : Formuler le problème en classification binaire stricte (<b>BULLISH</b> / <b>BEARISH</b>), "
        "exclure empiriquement la zone morte d'indécision, et évaluer les modèles par validation temporelle sans tricherie (walk-forward).<br/>"
        "• <i>Explicabilité et quantification de l'incertitude</i> : Fournir des probabilités calibrées, un indice de confiance explicite "
        "et la décomposition des contributions linéaires des caractéristiques sur chaque décision.<br/>"
        "• <i>Architecture logicielle moderne</i> : Développer une pile asynchrone full-stack associant FastAPI, WebSocket, MongoDB et Next.js 15, "
        "dotée d'une interface terminal réactive et d'un support multilingue intégral (Anglais, Français, Arabe).",
        styles['Body']
    ))

    story.append(Paragraph("Méthodologie et Organisation du Rapport", styles['SectionTitle']))
    story.append(Paragraph(
        "La démarche adoptée s'inspire des principes méthodologiques d'ingénierie logicielle et d'évaluation expérimentale quantitative. "
        "Le présent mémoire s'articule en neuf chapitres structurés : le Chapitre 1 analyse le contexte et l'existant ; "
        "le Chapitre 2 spécifie les besoins et cas d'utilisation ; le Chapitre 3 présente la conception architecturale ; "
        "le Chapitre 4 détaille l'ingénierie des données et la prévention des fuites ; le Chapitre 5 expose le pipeline d'apprentissage "
        "automatique et ses résultats audités ; le Chapitre 6 documente le développement applicatif ; le Chapitre 7 présente l'assurance qualité "
        "et la validation par 117 tests automatisés ; le Chapitre 8 traite de la conteneurisation et du déploiement ; enfin, "
        "le Chapitre 9 engage une discussion critique sur les limites scientifiques et les perspectives du travail.",
        styles['Body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 1 — CONTEXTE GÉNÉRAL ET ÉTUDE DE L'EXISTANT
    # =========================================================================
    story.append(Paragraph("Chapitre 1 — Contexte Général et Étude de l'Existant", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("1.1 Présentation du marché spot XAU/USD", styles['SectionTitle']))
    story.append(Paragraph(
        "Le marché de l'or au comptant (XAU/USD spot) est un marché de gré à gré (Over-The-Counter — OTC) opérant 24 heures sur 24 "
        "durant les jours ouvrés, interconnectant les centres financiers de Londres, New York, Zurich et Tokyo. "
        "Contrairement aux devises fiduciaires régies par une banque centrale nationale, l'or ne présente aucun risque de défaut souverain "
        "ni de dépréciation par émission monétaire discrétionnaire. Sa dynamique est principalement gouvernée par le coût d'opportunité "
        "(taux réels des obligations souveraines), l'indice du dollar américain (DXY) et les primes de risque systémique.",
        styles['Body']
    ))

    story.append(Paragraph("1.2 Problématique de l'analyse quantitative de l'or", styles['SectionTitle']))
    story.append(Paragraph(
        "Sur le plan statistique, les séries temporelles de prix d'actifs financiers sont réputées non stationnaires, présentant "
        "des distributions de rendements à queues lourdes (leptokurtiques), des sauts de volatilité asymétriques et un rapport signal sur bruit "
        "extrêmement faible. Dans ce contexte, appliquer naïvement des algorithmes d'apprentissage conventionnels conduit inévitablement "
        "à capturer du bruit aléatoire plutôt qu'une structure sous-jacente prédictive.",
        styles['Body']
    ))

    story.append(Paragraph("1.3 Analyse critique des solutions existantes", styles['SectionTitle']))
    story.append(Paragraph(
        "Une étude comparative des plateformes de marché courantes permet de dégager trois grandes catégories d'outils :<br/>"
        "1. <b>Outils d'analyse technique graphique (ex. TradingView, MetaTrader 5)</b> : Offrent une richesse d'indicateurs visuels remarquables, "
        "mais reposent entièrement sur l'interprétation subjective de l'opérateur humain, sensible aux biais cognitifs (biais de confirmation, ancrage).<br/>"
        "2. <b>Plateformes de signaux et algorithmes propriétaires fermés</b> : Proposent des alertes directes sans transparence méthodologique, "
        "omettant les métriques d'erreur et dissimulant la dégradation des modèles en conditions réelles.<br/>"
        "3. <b>Bibliothèques quantitatives de recherche (ex. Backtrader, Zipline)</b> : Puissantes pour l'expérimentation hors-ligne mais dépourvues "
        "d'interfaces utilisateur temps réel accessibles et d'architectures de streaming unifiées.",
        styles['Body']
    ))

    story.append(Paragraph("1.4 Positionnement et contributions de la solution proposée", styles['SectionTitle']))
    story.append(Paragraph(
        "Le projet <b>AI Market Intelligence</b> comble ce fossé en fournissant une plateforme scientifique open-source, transparente et robuste. "
        "Elle réunit un flux de marché en continu, une batterie de 87 indicateurs calculés en temps réel de façon causale, un moteur de classification "
        "rigoureusement évalué sans fuite future, et un tableau de bord moderne facilitant l'exploration analytique.",
        styles['Body']
    ))

    comp_data = [
        [Paragraph("Critères d'évaluation", styles['TableHeader']), Paragraph("TradingView / MT5", styles['TableHeader']), Paragraph("Plateformes Commerciales", styles['TableHeader']), Paragraph("AI Market Intelligence (Ce projet)", styles['TableHeader'])],
        [Paragraph("Diffusion temps réel", styles['TableText']), Paragraph("Oui (Courtier / Propriétaire)", styles['TableText']), Paragraph("Oui (Alertes)", styles['TableText']), Paragraph("<b>Oui (WebSocket Twelve Data)</b>", styles['TableText'])],
        [Paragraph("Modélisation IA Probabiliste", styles['TableText']), Paragraph("Non (Scripts visuels isolés)", styles['TableText']), Paragraph("Boîte noire opaque", styles['TableText']), Paragraph("<b>Oui (Régression logistique validée)</b>", styles['TableText'])],
        [Paragraph("Garantie contre le Data Leakage", styles['TableText']), Paragraph("Non applicable", styles['TableText']), Paragraph("Non documentée / Non prouvée", styles['TableText']), Paragraph("<b>Prouvée mathématiquement (as-of)</b>", styles['TableText'])],
        [Paragraph("Explicabilité causale des prédictions", styles['TableText']), Paragraph("Subjective (Tracés manuels)", styles['TableText']), Paragraph("Nulle", styles['TableText']), Paragraph("<b>Coefficients logit signés & SHAP</b>", styles['TableText'])],
        [Paragraph("Transparence des métriques réelles", styles['TableText']), Paragraph("Non applicable", styles['TableText']), Paragraph("Fréquemment masquées", styles['TableText']), Paragraph("<b>Publication intégrale des métriques</b>", styles['TableText'])],
        [Paragraph("Support multilingue étendu", styles['TableText']), Paragraph("Partiel", styles['TableText']), Paragraph("Généralement anglais seul", styles['TableText']), Paragraph("<b>Trilingue natif (EN, FR, AR avec RTL)</b>", styles['TableText'])],
    ]
    t_comp = Table(comp_data, colWidths=[38 * mm, 38 * mm, 42 * mm, 52 * mm])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_comp)
    story.append(Paragraph("Tableau 1.1 : Comparatif fonctionnel des solutions d'analyse de marché", styles['Caption']))
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 2 — ANALYSE ET SPÉCIFICATION DES BESOINS
    # =========================================================================
    story.append(Paragraph("Chapitre 2 — Analyse et Spécification des Besoins", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("2.1 Identification des acteurs du système", styles['SectionTitle']))
    story.append(Paragraph(
        "Le système interagit avec deux catégories d'entités :<br/>"
        "• <b>L'Analyste de Marché / Chercheur (Acteur principal)</b> : Utilisateur consultant la plateforme via un navigateur web "
        "pour observer le cours XAU/USD, évaluer le biais directionnel calculé par le modèle, examiner les facteurs explicatifs et simuler des scénarios.<br/>"
        "• <b>Le Fournisseur de Données de Marché (Twelve Data - Acteur secondaire)</b> : Service externe alimentant l'infrastructure "
        "en cotations spot temps réel par socket sécurisé et en bougies historiques fermées par requêtes REST.",
        styles['Body']
    ))

    story.append(Paragraph("2.2 Spécification des besoins fonctionnels", styles['SectionTitle']))
    story.append(Paragraph(
        "Les fonctionnalités attendues sont définies et tracées comme suit :<br/>"
        "• <b>BF-01 : Streaming temps réel</b> : Le système doit maintenir une liaison WebSocket persistante avec le fournisseur et redistribuer "
        "les ticks de prix instantanément aux clients connectés sans blocage du serveur.<br/>"
        "• <b>BF-02 : Inférence directionnelle binaire</b> : Le système doit calculer et exposer l'orientation prévisionnelle du marché "
        "exclusivement sous les classes <b>BULLISH</b> ou <b>BEARISH</b>, assortie d'une probabilité calibrée et d'un score de confiance.<br/>"
        "• <b>BF-03 : Double horizon temporel</b> : L'utilisateur doit pouvoir basculer entre un horizon journalier (Daily — 24 heures) "
        "et un horizon hebdomadaire (Weekly — 120 heures).<br/>"
        "• <b>BF-04 : Explicabilité des décisions</b> : Chaque prédiction doit être accompagnée des 8 caractéristiques ayant le plus fort impact "
        "pondéré sur le logit du modèle, précisant leur valeur, leur direction et leur rang.<br/>"
        "• <b>BF-05 : Dérivation de scénarios de marché</b> : Le système doit générer trois scénarios structurés (Base, Bullish, Bearish) "
        "définissant des hypothèses de prix et des règles strictes d'invalidation.<br/>"
        "• <b>BF-06 : Internationalisation</b> : L'interface doit supporter dynamiquement l'anglais, le français et l'arabe avec bascule de mise en page RTL.<br/>"
        "• <b>BF-07 : Télémétrie et intégrité</b> : L'état opérationnel des workers, la fraîcheur des données et la connectivité base de données doivent être exposés.",
        styles['Body']
    ))

    story.append(Paragraph("2.3 Exigences non fonctionnelles et contraintes critiques", styles['SectionTitle']))
    story.append(Paragraph(
        "• <b>Absence de Data Leakage (Exigence critique absolue)</b> : Toute caractéristique calculée à l'instant $T$ doit résulter "
        "strictement d'observations clôturées à une estampille $\\le T$. Aucun indicateur centré ou prospectif n'est toléré.<br/>"
        "• <b>Résilience et tolérance aux pannes</b> : En cas d'indisponibilité du modèle ou d'insuffisance de données fraîches, le système "
        "doit basculer vers un statut explicite <code>MODEL_NOT_READY</code> ou <code>NO_DATA</code> plutôt que de fabriquer des prédictions fictives.<br/>"
        "• <b>Performance et concurrence</b> : Le backend doit exploiter les fonctionnalités asynchrones d'asyncio pour absorber des flux de ticks "
        "continus avec une latence de distribution interne inférieure à 20 millisecondes.",
        styles['Body']
    ))

    req_data = [
        [Paragraph("Code Exigence", styles['TableHeader']), Paragraph("Désignation Fonctionnelle", styles['TableHeader']), Paragraph("Priorité", styles['TableHeader']), Paragraph("Composant Réalisateur", styles['TableHeader'])],
        [Paragraph("BF-01", styles['TableText']), Paragraph("Flux temps réel WebSocket XAU/USD", styles['TableText']), Paragraph("Critique", styles['TableText']), Paragraph("LiveMarketService (FastAPI)", styles['TableText'])],
        [Paragraph("BF-02", styles['TableText']), Paragraph("Prédiction Binaire BULLISH / BEARISH", styles['TableText']), Paragraph("Critique", styles['TableText']), Paragraph("ModelServingEngine (Step 5)", styles['TableText'])],
        [Paragraph("BF-03", styles['TableText']), Paragraph("Double Horizon 24H (Daily) / 120H (Weekly)", styles['TableText']), Paragraph("Haute", styles['TableText']), Paragraph("PredictionService & PredictionCard", styles['TableText'])],
        [Paragraph("BF-04", styles['TableText']), Paragraph("Explicabilité (Coefficients linéaires signés)", styles['TableText']), Paragraph("Haute", styles['TableText']), Paragraph("ExplanationService / Panel", styles['TableText'])],
        [Paragraph("BF-05", styles['TableText']), Paragraph("Scénarios probabilistes & invalidations", styles['TableText']), Paragraph("Moyenne", styles['TableText']), Paragraph("build_scenarios / ScenarioPanel", styles['TableText'])],
        [Paragraph("BF-06", styles['TableText']), Paragraph("Internationalisation trilingue (EN/FR/AR)", styles['TableText']), Paragraph("Haute", styles['TableText']), Paragraph("LanguageContext (Next.js)", styles['TableText'])],
        [Paragraph("BF-07", styles['TableText']), Paragraph("Surveillance santé & qualité données", styles['TableText']), Paragraph("Moyenne", styles['TableText']), Paragraph("Health & Quality Routes", styles['TableText'])],
    ]
    t_req = Table(req_data, colWidths=[25 * mm, 65 * mm, 25 * mm, 55 * mm])
    t_req.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_req)
    story.append(Paragraph("Tableau 2.1 : Matrice de traçabilité des exigences fonctionnelles", styles['Caption']))

    story.append(Paragraph("2.4 Modélisation des cas d'utilisation", styles['SectionTitle']))
    story.append(Paragraph(
        "La modélisation UML des cas d'utilisation formalise les interactions entre l'utilisateur et les services opérationnels. "
        "Le cas d'utilisation central <i>'Obtenir le biais directionnel (BULLISH/BEARISH)'</i> englobe systématiquement "
        "l'accès aux probabilités complémentaires, à l'indice de confiance et aux facteurs explicatifs linéaires. "
        "Le fichier source PlantUML correspondant est archivé dans le dépôt sous <code>docs/uml/use_cases.puml</code>.",
        styles['Body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 3 — ANALYSE ET CONCEPTION SYSTÈME
    # =========================================================================
    story.append(Paragraph("Chapitre 3 — Analyse et Conception Système", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("3.1 Architecture globale en couches micro-services", styles['SectionTitle']))
    story.append(Paragraph(
        "L'application adopte une architecture découplée organisée en trois couches logiques majeures :<br/>"
        "1. <b>Couche d'ingestion et persistance</b> : Collecteurs et clients spécialisés assurant la normalisation des flux Twelve Data "
        "et le stockage persistant dans la base MongoDB.<br/>"
        "2. <b>Couche applicative Backend (FastAPI)</b> : Moteur d'API asynchrone orchestrant les services métier, la validation Pydantic, "
        "le service de streaming WebSocket et le moteur d'inférence statistique (ModelServingEngine).<br/>"
        "3. <b>Couche présentation Frontend (Next.js 15)</b> : Interface utilisateur riche construite selon l'architecture React App Router, "
        "interrogeant l'API via un client REST centralisé et maintenant une connexion WebSocket native pour les flux de cotation spot.",
        styles['Body']
    ))

    story.append(Paragraph("3.2 Architecture logicielle Backend FastAPI", styles['SectionTitle']))
    story.append(Paragraph(
        "Le point d'entrée ASGI est formalisé dans <code>backend/app/main.py</code> via une fonction usine <code>create_app()</code>. "
        "Le cycle de vie de l'application est supervisé par un gestionnaire asynchrone <code>lifespan</code> qui initialise la connexion MongoDB, "
        "lance la tâche d'arrière-plan de l'ingestion worker et active le singleton <code>LiveMarketService</code>. "
        "Les requêtes HTTP entrantes traversent un middleware de journalisation structurée avant d'atteindre les routeurs spécialisés : "
        "<code>health.py</code>, <code>market.py</code>, <code>predictions.py</code>, <code>explanations.py</code>, <code>performance.py</code>, "
        "<code>quality.py</code> et <code>live_market.py</code>.",
        styles['Body']
    ))

    story.append(Paragraph("3.3 Architecture logicielle Frontend Next.js", styles['SectionTitle']))
    story.append(Paragraph(
        "Le frontend exploite Next.js 15 avec React 19. La page principale <code>frontend/app/page.js</code> gère le cycle de vie "
        "des souscriptions et orchestre un ensemble de composants modulaires : <code>MarketCard</code> pour le ticker live, "
        "<code>PriceChart</code> pour le tracé graphique SVG des bougies, <code>PredictionCard</code> pour l'affichage de l'orientation ML "
        "et la bascule d'horizon, <code>TechnicalPanel</code> pour les oscillateurs, <code>ScenarioPanel</code> pour les scénarios "
        "et <code>ExplanationPanel</code> pour les décompositions de features. L'état linguistique est géré globalement par le contexte "
        "<code>LanguageContext</code>.",
        styles['Body']
    ))

    story.append(Paragraph("3.4 Schémas de données et indexation MongoDB", styles['SectionTitle']))
    story.append(Paragraph(
        "La base de données MongoDB utilise des collections dédiées munies d'index uniques composés garantissant l'idempotence des écritures "
        "et l'interdiction absolue des doublons :<br/>"
        "• <code>market_data</code> : Index unique sur <code>(symbol, timeframe, timestamp)</code>. Stocke les bougies historiques validées.<br/>"
        "• <code>predictions</code> : Index unique sur <code>(symbol, model_version, timestamp)</code> et index de recherche sur <code>(symbol, timestamp DESC)</code>.<br/>"
        "• <code>model_performance</code> : Index unique sur <code>(symbol, model, model_version, testing_period_end)</code>.<br/>"
        "• <code>ingestion_state</code> : Enregistre l'état d'exécution et les horodatages des cycles d'acquisition.",
        styles['Body']
    ))

    story.append(Paragraph("3.5 Conception des flux réactifs et synchrones (REST & WebSocket)", styles['SectionTitle']))
    story.append(Paragraph(
        "La communication entre le frontend et le backend s'organise selon un double canal complémentaire :<br/>"
        "• <b>Canal Push Temps Réel (WebSocket)</b> : Relié au point de terminaison <code>/api/ws/market</code>. Le backend reçoit les cotations "
        "de Twelve Data, les normalise et les pousse instantanément dans des files <code>asyncio.Queue</code> privées allouées à chaque client.<br/>"
        "• <b>Canal Requête/Réponse Synchrone (REST)</b> : Utilisé pour récupérer les bougies complètes, calculer les features, exécuter "
        "l'inférence ML, générer les scénarios et consulter la santé du système.",
        styles['Body']
    ))

    arch_box = [
        [Paragraph("<b>RÉSUMÉ ARCHITECTURAL DU SYSTÈME (AI_XAUUSD)</b>", styles['TableHeader'])],
        [Paragraph(
            "<b>Fournisseurs Externes :</b> Twelve Data (WebSocket Price Ticks & REST OHLCV Candles)<br/>"
            "<b>Couche Ingestion :</b> XAUUSDIngestionWorker (Bougies fermées H1) | LiveMarketService (Streaming WebSocket Singleton)<br/>"
            "<b>Couche Persistance :</b> MongoDB Client Manager (Motor async) | Collections market_data, predictions, ingestion_state<br/>"
            "<b>Couche ML Serving :</b> ModelServingEngine (Chargement sécurisé artefacts STEP 4 / 5 : logistic_regression_final.joblib)<br/>"
            "<b>Couche REST API :</b> FastAPI (Routes /api/health, /api/market, /api/predictions, /api/explanations, /api/data-quality)<br/>"
            "<b>Couche Présentation :</b> Next.js 15 App Router | Composants React réactifs | Support multilingue EN/FR/AR natif",
            styles['TableText']
        )]
    ]
    t_arch = Table(arch_box, colWidths=[170 * mm])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('BACKGROUND', (0,1), (-1,1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, SECONDARY),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_arch)
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 4 — ACQUISITION ET PRÉPARATION DES DONNÉES DE MARCHÉ
    # =========================================================================
    story.append(Paragraph("Chapitre 4 — Acquisition et Préparation des Données de Marché", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("4.1 Collecte des données historiques LiteFinance", styles['SectionTitle']))
    story.append(Paragraph(
        "Le socle d'entraînement historique provient d'exports bruts de la plateforme LiteFinance (MetaTrader) stockés "
        "dans <code>data/raw/litefinance/</code> sous trois résolutions temporelles : H1, H4 et M15. "
        "Le module <code>backend/app/data/litefinance.py</code> assure l'étape 1 de vérification et de nettoyage rigoureux.",
        styles['Body']
    ))

    story.append(Paragraph("4.2 Acquisition temps réel Twelve Data REST & WebSocket", styles['SectionTitle']))
    story.append(Paragraph(
        "En production opérationnelle, les cotations proviennent de l'API Twelve Data :<br/>"
        "• <i>REST Time Series</i> : Utilisé pour la collecte périodique des bougies fermées H1 via <code>TwelveDataCollector</code>.<br/>"
        "• <i>WebSocket Streaming</i> : Connecté à <code>wss://ws.twelvedata.com/v1/quotes/price</code> pour capter les variations spot de XAU/USD en direct.",
        styles['Body']
    ))

    story.append(Paragraph("4.3 Protocole de nettoyage et validation d'intégrité", styles['SectionTitle']))
    story.append(Paragraph(
        "L'audit du traitement (consigné dans <code>data/processed/litefinance/step1_audit.json</code>) applique des règles strictes :<br/>"
        "1. <b>Intégrité des fichiers bruts</b> : Les fichiers originaux ne sont jamais modifiés (<code>never_modified_raw: true</code>).<br/>"
        "2. <b>Refus absolu d'interpolation artificielle</b> : Aucune bougie synthétique n'est injectée lors des interruptions de marché "
        "(<code>never_created_candles: true</code>). Les fermetures réelles de fin de semaine et jours fériés sont préservées.<br/>"
        "3. <b>Contrôle des relations géométriques OHLC</b> : Vérification stricte des contraintes $High \\ge \\max(Open, Close)$ et "
        "$Low \\le \\min(Open, Close)$ ainsi que de la positivité des prix.",
        styles['Body']
    ))

    step1_data = [
        [Paragraph("Série Temporelle", styles['TableHeader']), Paragraph("Barres Brutes", styles['TableHeader']), Paragraph("Barres Nettoyées", styles['TableHeader']), Paragraph("Période Temporelle Vérifiée", styles['TableHeader']), Paragraph("Gaps Réels Préservés", styles['TableHeader'])],
        [Paragraph("<b>XAUUSD H1</b>", styles['TableText']), Paragraph("100 000", styles['TableText']), Paragraph("100 000", styles['TableText']), Paragraph("17/11/2009 au 18/09/2026", styles['TableText']), Paragraph("4 338 (dont 509 week-ends)", styles['TableText'])],
        [Paragraph("<b>XAUUSD H4</b>", styles['TableText']), Paragraph("43 333", styles['TableText']), Paragraph("27 805", styles['TableText']), Paragraph("01/01/2009 au 18/09/2026", styles['TableText']), Paragraph("1 373 (dont 552 week-ends)", styles['TableText'])],
        [Paragraph("<b>XAUUSD M15</b>", styles['TableText']), Paragraph("100 000", styles['TableText']), Paragraph("100 000", styles['TableText']), Paragraph("01/07/2022 au 18/09/2026", styles['TableText']), Paragraph("1 022 (dont 212 week-ends)", styles['TableText'])],
    ]
    t_step1 = Table(step1_data, colWidths=[28 * mm, 24 * mm, 26 * mm, 52 * mm, 40 * mm])
    t_step1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_step1)
    story.append(Paragraph("Tableau 4.1 : Audit d'intégrité des séries historiques LiteFinance", styles['Caption']))

    story.append(Paragraph("4.4 Ingénierie des caractéristiques : pipeline de 87 features MTF", styles['SectionTitle']))
    story.append(Paragraph(
        "L'étape 2 (implémentée dans <code>backend/app/data/mtf_features.py</code> et auditée dans <code>data/processed/ml/step2_audit.json</code>) "
        "construit le jeu de données unifié <code>XAUUSD_features.csv</code> comprenant <b>25 012 observations</b> et <b>87 caractéristiques</b>. "
        "L'échantillon démarre au 01/07/2022, date à laquelle le contexte M15 devient disponible.",
        styles['Body']
    ))

    mtf_summary = [
        [Paragraph("Échelle Temporelle", styles['TableHeader']), Paragraph("Nombre de Features", styles['TableHeader']), Paragraph("Nature des Indicateurs Techniques Générés", styles['TableHeader'])],
        [Paragraph("<b>Base OHLCV</b>", styles['TableText']), Paragraph("5", styles['TableText']), Paragraph("Prix bruts : open, high, low, close, tick_volume", styles['TableText'])],
        [Paragraph("<b>Échelle H1 (Pivot)</b>", styles['TableText']), Paragraph("32", styles['TableText']), Paragraph("Rendements (1, 4, 24 barres), chandeliers (body, range, wicks), moyennes mobiles (SMA 20/50/200, EMA 12/20/50), oscillateurs (RSI 14, MACD, MACD Signal/Hist), volatilité (ATR 14, ATR %, Volatilité 20, Rel Vol 20), variables calendaires (heure, jour de semaine, gap hours).", styles['TableText'])],
        [Paragraph("<b>Échelle H4 (Macro)</b>", styles['TableText']), Paragraph("27", styles['TableText']), Paragraph("Rendements H4, morphologie de bougie, SMA 20/50, EMA 20/50, RSI 14, MACD, ATR 14, volatilité relative et âge de la dernière barre fermée (h4_age_hours).", styles['TableText'])],
        [Paragraph("<b>Échelle M15 (Micro)</b>", styles['TableText']), Paragraph("23", styles['TableText']), Paragraph("Rendements M15, morphologie de bougie, SMA 20, EMA 20/50, RSI 14, MACD hist, ATR 14, nombre de bougies M15 dans la barre H1 (m15_bars_in_h1) et latence (m15_age_minutes).", styles['TableText'])],
    ]
    t_mtf = Table(mtf_summary, colWidths=[35 * mm, 30 * mm, 105 * mm])
    t_mtf.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_mtf)
    story.append(Paragraph("Tableau 4.2 : Répartition des 87 caractéristiques par échelle temporelle", styles['Caption']))

    story.append(Paragraph("4.5 Prévention mathématique du Data Leakage par alignement causal", styles['SectionTitle']))
    story.append(Paragraph(
        "L'élimination du biais prospectif constitue la clé de voûte de cette architecture. "
        "Pour toute bougie H1 débutant à l'instant $t_{start}$, sa clôture n'intervient qu'à $t_{close} = t_{start} + 1\\text{h}$. "
        "Par conséquent, les indicateurs H4 et M15 fusionnés doivent être strictement issus de barres dont la clôture effective "
        "est antérieure ou égale à $t_{close}$.<br/>"
        "Cette contrainte est appliquée par :<br/>"
        "1. L'attribution à chaque série d'un horodatage de disponibilité réel : <code>available_at = timestamp + delta_timeframe</code>.<br/>"
        "2. Une fusion par jointure asynchrone non prospective : <code>pd.merge_asof(..., on='available_at', direction='backward')</code>.<br/>"
        "3. L'exclusion stricte de tout indicateur bilatéral ou centré : toutes les moyennes mobiles et lissages exponentiels sont calculés "
        "exclusivement sur des fenêtres glissantes passées (trailing windows).",
        styles['Body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 5 — MACHINE LEARNING ET PRÉDICTION DIRECTIONNELLE
    # =========================================================================
    story.append(Paragraph("Chapitre 5 — Machine Learning et Prédiction Directionnelle", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("5.1 Formalisation de la cible binaire (BULLISH vs BEARISH)", styles['SectionTitle']))
    story.append(Paragraph(
        "L'objectif de modélisation consiste à anticiper le régime directionnel futur du cours XAU/USD. "
        "Soit $C_t$ le cours de clôture de la bougie H1 à l'instant $t$. Pour un horizon prévisionnel de $H$ périodes "
        "(où $H = 24$ pour le modèle journalier et $H = 120$ pour le modèle hebdomadaire), le rendement arithmétique futur est défini par :<br/>"
        "<font face='Helvetica-Oblique' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;R_{t, H} = (C_{t+H} / C_t) - 1</font><br/>"
        "La variable cible supervisée $Y_t$ est construite par rapport à un seuil d'amplitude $\\theta$ "
        "($\\theta = 0.005$ soit $0.5\\%$ en 24H ; $\\theta = 0.010$ soit $1.0\\%$ en 120H) :<br/>"
        "• <b>BULLISH (Classe 1)</b> si $R_{t, H} \\ge +\\theta$<br/>"
        "• <b>BEARISH (Classe 0)</b> si $R_{t, H} \\le -\\theta$",
        styles['Body']
    ))

    story.append(Paragraph("5.2 Filtrage de la zone morte et justification de l'absence de classe neutre", styles['SectionTitle']))
    story.append(Paragraph(
        "<b>Règle fondamentale d'espace de décision :</b> Le système ne comporte <b>AUCUNE classe NEUTRAL</b> dans son espace prédictif. "
        "Lorsque le rendement futur vérifie $|R_{t, H}| < \\theta$, l'observation se situe dans une zone morte d'indécision dominée "
        "par le bruit de microstructure et les coûts de transaction. "
        "Conformément à la spécification (<code>models/xauusd/label_definition.json</code>), ces observations sont <b>intégralement filtrées "
        "et exclues du dataset d'apprentissage et de validation</b>. "
        "L'espace de prédiction est donc un problème de classification binaire pure satisfaisant formellement :<br/>"
        "<font face='Helvetica-Oblique' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;P(BULLISH) + P(BEARISH) = 1.0</font>",
        styles['Body']
    ))

    story.append(Paragraph("5.3 Algorithmes benchmarkés et protocole Walk-Forward", styles['SectionTitle']))
    story.append(Paragraph(
        "Dans l'étape 4 (<code>models/xauusd/step4_audit.json</code>), quatre familles d'algorithmes ont été évaluées de manière comparative :<br/>"
        "1. <b>Régression Logistique (avec standardisation StandardScaler)</b><br/>"
        "2. <b>Forêt Aléatoire (Random Forest Classifier)</b><br/>"
        "3. <b>XGBoost (Extreme Gradient Boosting)</b><br/>"
        "4. <b>LightGBM (Light Gradient Boosting Machine)</b><br/>"
        "<b>Protocole expérimental :</b> L'évaluation utilise une validation temporelle glissante (Walk-Forward Validation) à <b>4 plis (folds) "
        "à fenêtre expansive (expanding window)</b>. Le jeu de données n'est jamais mélangé de façon aléatoire (<code>shuffle = False</code>), "
        "et un embargo de 24 barres est appliqué entre chaque fenêtre d'entraînement et de validation pour neutraliser toute dépendance sérielle.",
        styles['Body']
    ))

    story.append(Paragraph("5.4 Analyse comparative et sélection du modèle de production", styles['SectionTitle']))
    story.append(Paragraph(
        "Les résultats du benchmark walk-forward agrégés sur les 4 plis ont révélé des comportements discriminants majeurs :",
        styles['Body']
    ))

    bm_data = [
        [Paragraph("Algorithme", styles['TableHeader']), Paragraph("Accuracy Moyenne", styles['TableHeader']), Paragraph("Balanced Acc.", styles['TableHeader']), Paragraph("Écart Surapprentissage", styles['TableHeader']), Paragraph("Diagnostic & Décision de Sélection", styles['TableHeader'])],
        [Paragraph("<b>Logistic Regression</b>", styles['TableText']), Paragraph("57.37% (±2.52%)", styles['TableText']), Paragraph("52.38% (±1.73%)", styles['TableText']), Paragraph("<b>2.30%</b> (±1.85%)", styles['TableText']), Paragraph("<font color='#22543D'><b>SÉLECTIONNÉ POUR LA PRODUCTION</b><br/>Score = 0.3901 (Rang 1) | Aucun effondrement</font>", styles['TableText'])],
        [Paragraph("<b>Random Forest</b>", styles['TableText']), Paragraph("54.69% (±8.73%)", styles['TableText']), Paragraph("51.13% (±2.36%)", styles['TableText']), Paragraph("27.45% (±6.93%)", styles['TableText']), Paragraph("<font color='#742A2A'><b>DISQUALIFIÉ</b> : Effondrement de classe (fold 1) et surapprentissage massif.</font>", styles['TableText'])],
        [Paragraph("<b>XGBoost</b>", styles['TableText']), Paragraph("55.92% (±3.63%)", styles['TableText']), Paragraph("50.93% (±2.77%)", styles['TableText']), Paragraph("21.64% (±3.26%)", styles['TableText']), Paragraph("<font color='#C59B27'><b>Écarté</b> : Rang 2 (Score = 0.3748), surapprentissage élevé.</font>", styles['TableText'])],
        [Paragraph("<b>LightGBM</b>", styles['TableText']), Paragraph("54.02% (±5.05%)", styles['TableText']), Paragraph("49.22% (±2.41%)", styles['TableText']), Paragraph("33.54% (±4.52%)", styles['TableText']), Paragraph("<font color='#742A2A'><b>DISQUALIFIÉ</b> : Effondrement de classe (fold 1) et surapprentissage extrême.</font>", styles['TableText'])],
    ]
    t_bm = Table(bm_data, colWidths=[32 * mm, 32 * mm, 32 * mm, 34 * mm, 40 * mm])
    t_bm.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_bm)
    story.append(Paragraph("Tableau 5.1 : Benchmark comparatif des algorithmes ML (Walk-Forward)", styles['Caption']))

    story.append(Paragraph(
        "<b>Règle de disqualification :</b> Tout modèle présentant un effondrement de classe (prédiction d'une seule classe sur l'ensemble d'un fold) "
        "a été immédiatement disqualifié. La Régression Logistique a été sélectionnée comme l'unique modèle de production en raison de sa stabilité "
        "remarquable (écart train-val de seulement 2.30%) et de sa variance minimale.",
        styles['Body']
    ))
    story.append(PageBreak())

    story.append(Paragraph("5.5 Métriques réelles obtenues hors-échantillon (Daily & Weekly)", styles['SectionTitle']))
    story.append(Paragraph(
        "Conformément aux principes de transparence académique, nous reportons fidèlement les performances réelles mesurées "
        "sur le jeu de test holdout final hors-échantillon (totalement isolé et non vu durant la phase d'apprentissage).",
        styles['Body']
    ))

    story.append(Paragraph("Modèle Daily (Horizon 24H) — <code>models/xauusd/final_metrics.json</code>", styles['SubSectionTitle']))
    story.append(Paragraph(
        "Évalué sur <b>N = 2 144 bougies fermées</b> (période du 18/03/2026 au 17/09/2026) :",
        styles['Body']
    ))

    m_daily = [
        [Paragraph("Métrique Statistique", styles['TableHeader']), Paragraph("Valeur Mesurée", styles['TableHeader']), Paragraph("Interprétation Technique", styles['TableHeader'])],
        [Paragraph("<b>Accuracy (Justesse)</b>", styles['TableText']), Paragraph("<b>45.71%</b> (0.4571)", styles['TableText']), Paragraph("Inférieure à la baseline de classe majoritaire (48.04%).", styles['TableText'])],
        [Paragraph("<b>Balanced Accuracy</b>", styles['TableText']), Paragraph("<b>47.31%</b> (0.4731)", styles['TableText']), Paragraph("Moyenne arithmétique des rappels de chaque classe.", styles['TableText'])],
        [Paragraph("<b>Précision</b>", styles['TableText']), Paragraph("<b>46.56%</b> (0.4656)", styles['TableText']), Paragraph("Proportion de vrais positifs parmi les prédictions BULLISH.", styles['TableText'])],
        [Paragraph("<b>Rappel (Recall)</b>", styles['TableText']), Paragraph("<b>88.06%</b> (0.8806)", styles['TableText']), Paragraph("Forte sensibilité à capter les mouvements haussiers.", styles['TableText'])],
        [Paragraph("<b>F1-Score</b>", styles['TableText']), Paragraph("<b>60.91%</b> (0.6091)", styles['TableText']), Paragraph("Moyenne harmonique entre précision et rappel.", styles['TableText'])],
        [Paragraph("<b>ROC-AUC</b>", styles['TableText']), Paragraph("<b>49.28%</b> (0.4928)", styles['TableText']), Paragraph("Proche du niveau de discrimination aléatoire (50%).", styles['TableText'])],
        [Paragraph("<b>Brier Score</b>", styles['TableText']), Paragraph("<b>0.2871</b>", styles['TableText']), Paragraph("Mesure d'étalonnage probabiliste (écart quadratique moyen).", styles['TableText'])],
        [Paragraph("<b>Matrice de Confusion</b>", styles['TableText']), Paragraph("TN: 73 | FP: 1041<br/>FN: 123 | TP: 907", styles['TableText']), Paragraph("Biais d'inférence orienté vers la classe haussière (1 948 prédictions BULLISH contre 196 BEARISH).", styles['TableText'])],
        [Paragraph("<b>Majority Baseline Acc.</b>", styles['TableText']), Paragraph("<b>48.04%</b> (0.4804)", styles['TableText']), Paragraph("Performance d'un classifieur prédisant toujours la classe majoritaire.", styles['TableText'])],
        [Paragraph("<b>Accuracy Lift</b>", styles['TableText']), Paragraph("<b>-2.33%</b> (-0.0233)", styles['TableText']), Paragraph("Gain de justesse négatif par rapport à la baseline majoritaire.", styles['TableText'])],
    ]
    t_daily = Table(m_daily, colWidths=[45 * mm, 35 * mm, 90 * mm])
    t_daily.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_daily)
    story.append(Paragraph("Tableau 5.2 : Métriques hors-échantillon réelles du modèle Daily (24H)", styles['Caption']))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Modèle Weekly (Horizon 120H) — <code>models/xauusd_weekly/final_metrics.json</code>", styles['SubSectionTitle']))
    story.append(Paragraph(
        "Évalué sur <b>N = 2 472 bougies fermées</b> (période du 06/03/2026 au 11/09/2026) :",
        styles['Body']
    ))

    m_weekly = [
        [Paragraph("Métrique Statistique", styles['TableHeader']), Paragraph("Valeur Mesurée", styles['TableHeader']), Paragraph("Interprétation Technique", styles['TableHeader'])],
        [Paragraph("<b>Accuracy (Justesse)</b>", styles['TableText']), Paragraph("<b>39.20%</b> (0.3920)", styles['TableText']), Paragraph("Inférieure à la baseline de classe majoritaire (43.77%).", styles['TableText'])],
        [Paragraph("<b>Balanced Accuracy</b>", styles['TableText']), Paragraph("<b>43.90%</b> (0.4390)", styles['TableText']), Paragraph("Rappel équilibré entre classes sur 5 jours.", styles['TableText'])],
        [Paragraph("<b>Précision</b>", styles['TableText']), Paragraph("<b>40.37%</b> (0.4037)", styles['TableText']), Paragraph("Précision directionnelle hebdomadaire.", styles['TableText'])],
        [Paragraph("<b>Rappel (Recall)</b>", styles['TableText']), Paragraph("<b>81.61%</b> (0.8161)", styles['TableText']), Paragraph("Capacité de détection des impulsions haussières hebdomadaires.", styles['TableText'])],
        [Paragraph("<b>F1-Score</b>", styles['TableText']), Paragraph("<b>54.02%</b> (0.5402)", styles['TableText']), Paragraph("Score F1 du régime hebdomadaire.", styles['TableText'])],
        [Paragraph("<b>ROC-AUC</b>", styles['TableText']), Paragraph("<b>53.62%</b> (0.5362)", styles['TableText']), Paragraph("Capacité discriminante supérieure au hasard.", styles['TableText'])],
        [Paragraph("<b>Brier Score</b>", styles['TableText']), Paragraph("<b>0.4452</b>", styles['TableText']), Paragraph("Incertitude probabiliste plus prononcée à long terme.", styles['TableText'])],
        [Paragraph("<b>Matrice de Confusion</b>", styles['TableText']), Paragraph("TN: 86 | FP: 1304<br/>FN: 199 | TP: 883", styles['TableText']), Paragraph("Persistance du biais haussier (2 187 prédictions BULLISH contre 285 BEARISH).", styles['TableText'])],
        [Paragraph("<b>Majority Baseline Acc.</b>", styles['TableText']), Paragraph("<b>43.77%</b> (0.4377)", styles['TableText']), Paragraph("Performance de référence de la classe majoritaire.", styles['TableText'])],
        [Paragraph("<b>Accuracy Lift</b>", styles['TableText']), Paragraph("<b>-4.57%</b> (-0.0457)", styles['TableText']), Paragraph("Gain de justesse négatif à l'échelle hebdomadaire.", styles['TableText'])],
    ]
    t_weekly = Table(m_weekly, colWidths=[45 * mm, 35 * mm, 90 * mm])
    t_weekly.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_weekly)
    story.append(Paragraph("Tableau 5.3 : Métriques hors-échantillon réelles du modèle Weekly (120H)", styles['Caption']))

    story.append(Paragraph(
        "<b>Constat fondamental :</b> Les deux modèles affichent une justesse (accuracy) inférieure à leur baseline majoritaire "
        "(Lift de -2.33% en Daily et de -4.57% en Weekly). Cette réalité empirique démontre la difficulté inhérente à la prédiction des marchés "
        "financiers et confirme l'intégrité de notre chaîne d'évaluation, qui s'interdit d'embellir ou de falsifier les métriques.",
        styles['Body']
    ))

    story.append(Paragraph("5.6 Modélisation de la confiance et scénarios probabilistes", styles['SectionTitle']))
    story.append(Paragraph(
        "Dans <code>backend/app/ml/step5_serving.py</code>, l'indice de confiance est formulé mathématiquement comme l'écart normalisé "
        "à la frontière d'indécision (0.5) :<br/>"
        "<font face='Helvetica-Oblique' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;Confidence = |P(BULLISH) - 0.5| * 2  \\in [0, 1]</font><br/>"
        "Par ailleurs, le service dérive trois scénarios de marché contextuels (fonction <code>build_scenarios</code>) :<br/>"
        "• <b>Scénario Base</b> : Conditionné au maintien du prix dans le régime courant ; invalidé par toute nouvelle bougie modifiant les inputs.<br/>"
        "• <b>Scénario Bullish</b> : Conditionné au maintien au-dessus de la moyenne mobile (SMA 20/50/200) avec momentum positif ; invalidé par clôture sous la SMA.<br/>"
        "• <b>Scénario Bearish</b> : Conditionné au maintien sous la moyenne mobile avec momentum négatif ; invalidé par clôture au-dessus de la SMA.",
        styles['Body']
    ))

    story.append(Paragraph("5.7 Explicabilité : coefficients logit linéaires et intégration SHAP", styles['SectionTitle']))
    story.append(Paragraph(
        "Pour le modèle de production actuel (Régression Logistique), l'explicabilité principale repose sur la <b>décomposition linéaire "
        "des coefficients logit</b> (implémentée dans <code>_step5_linear_contributions</code>) :<br/>"
        "<font face='Helvetica-Oblique' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;Contribution_i = X_{scaled, i} * w_i</font><br/>"
        "Le système identifie et transmet les 8 caractéristiques ayant l'amplitude absolue $|Contribution_i|$ la plus forte, avec leur signe "
        "(positif ou négatif) et leur rang.<br/>"
        "<b>Statut réel de SHAP :</b> L'algorithme d'explication par valeurs de Shapley (<code>shap.TreeExplainer</code>) est implémenté "
        "dans le code source (<code>backend/app/services/predictions.py</code>, fonction <code>_tree_contributions</code>) en tant que mécanisme "
        "disponible et de repli pour les modèles arborescents (XGBoost, Random Forest). Toutefois, comme la Régression Logistique "
        "a été retenue pour la production, SHAP n'est pas le mécanisme actif en runtime pour l'artefact courant.",
        styles['Body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 6 — DÉVELOPPEMENT DE L'APPLICATION
    # =========================================================================
    story.append(Paragraph("Chapitre 6 — Développement de l'Application", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("6.1 Implémentation du backend FastAPI et cycle de vie asynchrone", styles['SectionTitle']))
    story.append(Paragraph(
        "Le backend est structuré selon les meilleures pratiques d'architecture logicielle Python contemporaine. "
        "Les modèles de données et contrats d'échange sont strictement typés via Pydantic V2 (héritant de <code>APIModel</code> avec configuration "
        "d'encodage datetime standardisé). "
        "Les erreurs applicatives sont interceptées par des gestionnaires typés dédiés dans <code>backend/app/api/errors.py</code> "
        "(par exemple <code>FeatureNotReadyError</code> renvoyant un statut HTTP 503 documenté avec payload d'erreur standardisé).",
        styles['Body']
    ))

    story.append(Paragraph("6.2 Gestionnaire WebSocket singleton et distribution des ticks", styles['SectionTitle']))
    story.append(Paragraph(
        "Le composant <code>LiveMarketService</code> (défini dans <code>backend/app/services/live_market.py</code>) implémente un patron Singleton "
        "qui maintient en arrière-plan une tâche de supervision asynchrone (<code>_supervisor_loop</code>). "
        "Il gère la connexion client WebSocket vers Twelve Data, traite les messages JSON entrants, valide les horodatages UTC "
        "et distribue immédiatement chaque tick aux files d'attente <code>asyncio.Queue</code> abonnées. "
        "Lors de la connexion d'un client au point de terminaison <code>/api/ws/market</code>, un message de type <code>initial_state</code> "
        "contenant le dernier tick en cache lui est immédiatement transmis pour éliminer tout délai d'attente à l'écran.",
        styles['Body']
    ))

    story.append(Paragraph("6.3 Développement du frontend Next.js et Dashboard Terminal", styles['SectionTitle']))
    story.append(Paragraph(
        "Le tableau de bord utilisateur (<code>frontend/app/page.js</code>) adopte une ergonomie inspirée des terminaux financiers institutionnels "
        "(palette de couleurs sombre, contrastes accentués, bordures fines). "
        "La disposition de la grille principale organise l'information de manière hiérarchisée :<br/>"
        "• <i>En-tête supérieur</i> : Titre de la plateforme, sous-titre dynamique traduit et sélecteur de langue <code>LanguageSwitcher</code>.<br/>"
        "• <i>Ligne principale supérieure</i> : Bloc d'exécution du marché à gauche (carte de cours spot <code>MarketCard</code> et graphique SVG "
        "<code>PriceChart</code>) juxtaposé au bloc de prédiction d'intelligence artificielle <code>PredictionCard</code> à droite.<br/>"
        "• <i>Ligne intermédiaire</i> : Analyse technique en temps réel <code>TechnicalPanel</code> (moyennes mobiles, RSI, MACD, ATR) "
        "et panneau des scénarios probabilistes <code>ScenarioPanel</code>.",
        styles['Body']
    ))

    story.append(Paragraph("6.4 Composants d'affichage des prédictions et scénarios", styles['SectionTitle']))
    story.append(Paragraph(
        "Le composant <code>PredictionCard.js</code> propose une expérience interactive avancée :<br/>"
        "• <b>Bascule d'horizon temporel</b> : Deux boutons permettent de basculer instantanément entre l'horizon journalier (Daily — 24H) "
        "et l'horizon hebdomadaire (Weekly — 120H), actualisant dynamiquement le vecteur de prédiction.<br/>"
        "• <b>Bannière de biais directionnel</b> : Affichage stylisé de l'orientation <code>BULLISH</code> (en vert doré) ou <code>BEARISH</code> "
        "(en rouge sombre) avec jauge de confiance numérique.<br/>"
        "• <b>Barre de probabilité proportionnelle</b> : Affichage des deux segments complémentaires représentant $P(\\text{BULLISH})$ "
        "et $P(\\text{BEARISH})$.<br/>"
        "• <b>Facteurs explicatifs linéaires</b> : Liste ordonnée des 8 variables les plus influentes avec mention de leur contribution chiffrée.",
        styles['Body']
    ))

    story.append(Paragraph("6.5 Internationalisation trilingue (EN / FR / AR) et support RTL", styles['SectionTitle']))
    story.append(Paragraph(
        "L'internationalisation est implémentée de façon exhaustive sans bibliothèque externe lourde :<br/>"
        "• Catalogues JSON structurés dans <code>frontend/locales/</code> : <code>en.json</code>, <code>fr.json</code> et <code>ar.json</code>.<br/>"
        "• Gestionnaire de contexte <code>LanguageContext.js</code> mémorisant la préférence linguistique dans le <code>localStorage</code>.<br/>"
        "• <b>Support bidirectionnel Right-to-Left (RTL) natif pour la langue arabe</b> : Dès la sélection de la langue arabe, l'attribut "
        "<code>dir=\"rtl\"</code> et la classe CSS <code>rtl</code> sont injectés sur les éléments racine du document HTML, inversant "
        "automatiquement l'alignement des textes, les grilles et les flux visuels conformément aux standards typographiques arabophones.",
        styles['Body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 7 — TESTS, VALIDATION ET ASSURANCE QUALITÉ
    # =========================================================================
    story.append(Paragraph("Chapitre 7 — Tests, Validation et Assurance Qualité", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("7.1 Stratégie de test et suite automatisée Pytest (117 tests)", styles['SectionTitle']))
    story.append(Paragraph(
        "La qualité logicielle repose sur une suite complète de tests unitaires, d'intégration et de non-régression "
        "exécutée via le framework Pytest dans l'environnement virtuel du projet. "
        "L'exécution intégrale (commande <code>pytest backend/tests -v</code>) a abouti au résultat vérifié suivant :<br/>"
        "<b>117 tests exécutés avec succès, 0 échec (taux de réussite : 100.0%)</b> en 179.25 secondes.",
        styles['Body']
    ))

    test_data = [
        [Paragraph("Module de Test", styles['TableHeader']), Paragraph("Tests", styles['TableHeader']), Paragraph("Périmètre Validé & Propriétés Critiques Vérifiées", styles['TableHeader']), Paragraph("Résultat", styles['TableHeader'])],
        [Paragraph("<code>test_litefinance_step1.py</code>", styles['TableText']), Paragraph("12", styles['TableText']), Paragraph("Nettoyage LiteFinance, détection des gaps, validité OHLC, absence de bougies synthétiques.", styles['TableText']), Paragraph("<font color='#22543D'><b>12/12 PASS</b></font>", styles['TableText'])],
        [Paragraph("<code>test_mtf_features_step2.py</code>", styles['TableText']), Paragraph("9", styles['TableText']), Paragraph("Causalité stricte des 87 features, absence de valeurs nulles/infinies, absence de lookahead dans les fenêtres glissantes.", styles['TableText']), Paragraph("<font color='#22543D'><b>9/9 PASS</b></font>", styles['TableText'])],
        [Paragraph("<code>test_step3.py</code>", styles['TableText']), Paragraph("9", styles['TableText']), Paragraph("Absence de shuffle, cible dérivée uniquement des clôtures futures, élimination de la zone morte.", styles['TableText']), Paragraph("<font color='#22543D'><b>9/9 PASS</b></font>", styles['TableText'])],
        [Paragraph("<code>test_step4.py</code>", styles['TableText']), Paragraph("27", styles['TableText']), Paragraph("Walk-forward expanding window, respect de l'embargo, protocoles de validation, détection de surapprentissage.", styles['TableText']), Paragraph("<font color='#22543D'><b>27/27 PASS</b></font>", styles['TableText'])],
        [Paragraph("<code>test_step5.py</code>", styles['TableText']), Paragraph("11", styles['TableText']), Paragraph("Moteur ModelServingEngine, probabilités valides (somme = 1), statut MODEL_NOT_READY si données incomplètes.", styles['TableText']), Paragraph("<font color='#22543D'><b>11/11 PASS</b></font>", styles['TableText'])],
        [Paragraph("<code>test_live_market.py</code>", styles['TableText']), Paragraph("14", styles['TableText']), Paragraph("Cycle de vie du WebSocket Twelve Data, reconnexion automatique, distribution asynchrone des ticks.", styles['TableText']), Paragraph("<font color='#22543D'><b>14/14 PASS</b></font>", styles['TableText'])],
        [Paragraph("<code>test_contracts.py</code> / <code>test_dataset.py</code>", styles['TableText']), Paragraph("35", styles['TableText']), Paragraph("Conformité des contrats Pydantic, schémas d'erreurs HTTP, intégrité des timestamps UTC.", styles['TableText']), Paragraph("<font color='#22543D'><b>35/35 PASS</b></font>", styles['TableText'])],
    ]
    t_test = Table(test_data, colWidths=[40 * mm, 16 * mm, 94 * mm, 20 * mm])
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_test)
    story.append(Paragraph("Tableau 7.1 : Synthèse d'exécution de la suite de tests automatisés (Pytest)", styles['Caption']))

    story.append(Paragraph("7.2 Tests de non-régression et d'absence de fuite prospective", styles['SectionTitle']))
    story.append(Paragraph(
        "Une attention scrupuleuse a été portée au test <code>test_4_no_future_information</code> et au test "
        "<code>test_mutating_future_close_does_not_change_x_at_t</code> : ces procédures modifient artificiellement les cours "
        "de clôture postérieurs à l'instant $T$ et vérifient mathématiquement que la matrice de caractéristiques calculée à l'instant $T$ "
        "demeure rigoureusement identique au bit près, prouvant l'étanchéité causale absolue de la chaîne.",
        styles['Body']
    ))

    story.append(Paragraph("7.3 Validation de l'ingestion WebSocket et des contrats d'API", styles['SectionTitle']))
    story.append(Paragraph(
        "Les tests de simulation d'indisponibilité du réseau et de déconnexion du fournisseur démontrent que le backend "
        "interrompt gracieusement la tâche de réception, met à jour le statut du symbole à <code>OFFLINE</code> ou <code>DELAYED</code>, "
        "et rétablit la communication dès la réouverture du socket sans fuite de mémoire ni exception non gérée.",
        styles['Body']
    ))

    story.append(Paragraph("7.4 Statut des tests frontend et génération dynamique de l'interface", styles['SectionTitle']))
    story.append(Paragraph(
        "<b>Audit factuel des tests frontend :</b> La compilation de production Next.js réussit sans erreur (<code>npm run build</code>). "
        "Toutefois, l'inspection de <code>frontend/package.json</code> révèle qu'<b>aucun framework de tests frontend automatisés dédié "
        "(tel que Jest, React Testing Library, Cypress ou Playwright) n'est configuré dans le dépôt</b>. "
        "La réussite de la commande <code>npm run build</code> valide la correction syntaxique et la résolution des types JSX, "
        "mais ne constitue pas une preuve de tests fonctionnels automatisés côté client.<br/>"
        "<b>Statut des captures d'écran :</b> Aucune capture d'écran statique pré-enregistrée (fichiers PNG/JPG) n'est présente dans le dépôt. "
        "L'interface utilisateur est entièrement générée dynamiquement par les composants React/Next.js.",
        styles['Body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 8 — DÉPLOIEMENT ET DEVOPS
    # =========================================================================
    story.append(Paragraph("Chapitre 8 — Déploiement et DevOps", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("8.1 Conteneurisation Docker multi-services", styles['SectionTitle']))
    story.append(Paragraph(
        "Le projet intègre une stratégie de conteneurisation assurant la reproductibilité complète de l'environnement d'exécution :<br/>"
        "• <b>Backend Dockerfile (<code>backend/Dockerfile</code>)</b> : Repose sur l'image officielle <code>python:3.13-slim</code>. "
        "Copie les spécifications de dépendances <code>requirements.txt</code>, installe les packages requis sans cache et lance le serveur Uvicorn "
        "sur le port 8000.<br/>"
        "• <b>Frontend Dockerfile (<code>frontend/Dockerfile</code>)</b> : Repose sur l'image <code>node:24-alpine</code>. "
        "Gère les arguments de build <code>NEXT_PUBLIC_API_URL</code>, installe les dépendances npm, compile le projet Next.js "
        "et expose le port 3000.",
        styles['Body']
    ))

    story.append(Paragraph("8.2 Orchestration locale via Docker Compose", styles['SectionTitle']))
    story.append(Paragraph(
        "Le fichier <code>docker-compose.yml</code> à la racine du dépôt orchestre l'ensemble des services avec surveillance de santé croisée :<br/>"
        "• Le service backend effectue un test de santé périodique (<code>healthcheck</code>) interrogeant <code>http://localhost:8000/api/health</code>.<br/>"
        "• Le service frontend déclare une dépendance conditionnelle stricte (<code>depends_on: { backend: { condition: service_healthy } }</code>), "
        "garantissant que l'interface utilisateur ne démarre qu'une fois l'API prête à répondre.",
        styles['Body']
    ))

    story.append(Paragraph("8.3 Configuration de déploiement cloud (Railway & Vercel)", styles['SectionTitle']))
    story.append(Paragraph(
        "Le dépôt contient les descripteurs de déploiement pour hébergement cloud managé :<br/>"
        "• <b>Backend Railway</b> : Défini via <code>Dockerfile.railway</code> et <code>railway.toml</code>. Déclare le chemin de healthcheck "
        "<code>/api/health</code> et le port dynamique <code>${PORT:-8000}</code>.<br/>"
        "• <b>Frontend Vercel</b> : Documenté dans <code>DEPLOYMENT.md</code>, configuré pour pointer vers l'URL de production du backend "
        "via la variable d'environnement <code>NEXT_PUBLIC_API_URL</code>.<br/>"
        "<b>Mention d'audit obligatoire :</b> <i>« Configuration de déploiement présente ; déploiement cloud non vérifié dans le présent audit local. »</i> "
        "L'audit local confirme la validité formelle des fichiers de configuration, mais ne peut certifier l'activité opérationnelle en temps réel "
        "d'une instance distante en l'absence de vérification runtime externe.",
        styles['Body']
    ))

    story.append(Paragraph("8.4 Intégration MongoDB Atlas et gestion des environnements", styles['SectionTitle']))
    story.append(Paragraph(
        "L'intégration avec MongoDB Atlas est implémentée au niveau applicatif via la chaîne de connexion <code>MONGODB_URI</code>. "
        "L'audit local établit la distinction essentielle suivante :<br/>"
        "• <i>Intégration logicielle</i> : Pleinement implémentée dans <code>backend/app/db/client.py</code> avec reconnexion automatique.<br/>"
        "• <i>Configuration Atlas</i> : Définie dans <code>.env.example</code> et <code>DEPLOYMENT.md</code>.<br/>"
        "• <i>État runtime vérifié</i> : Lors de l'exécution locale, le backend fonctionne soit avec une instance MongoDB locale accessible, "
        "soit reporte un statut dégradé <code>DISCONNECTED</code> sans crash système grâce aux blocs de protection <code>MongoClientManager</code>.",
        styles['Body']
    ))

    deploy_data = [
        [Paragraph("Composant", styles['TableHeader']), Paragraph("Cible d'Hébergement", styles['TableHeader']), Paragraph("Descripteurs Présents", styles['TableHeader']), Paragraph("Statut d'Audit Local", styles['TableHeader'])],
        [Paragraph("Backend API / WS", styles['TableText']), Paragraph("Railway Cloud", styles['TableText']), Paragraph("<code>Dockerfile.railway</code>, <code>railway.toml</code>", styles['TableText']), Paragraph("Configuration présente ; déploiement cloud non vérifié", styles['TableText'])],
        [Paragraph("Frontend Web", styles['TableText']), Paragraph("Vercel Edge", styles['TableText']), Paragraph("<code>frontend/package.json</code>, <code>DEPLOYMENT.md</code>", styles['TableText']), Paragraph("Configuration présente ; déploiement cloud non vérifié", styles['TableText'])],
        [Paragraph("Base de données", styles['TableText']), Paragraph("MongoDB Atlas", styles['TableText']), Paragraph("<code>app/db/client.py</code>, <code>.env.example</code>", styles['TableText']), Paragraph("Intégration implémentée ; cluster distant non vérifié", styles['TableText'])],
        [Paragraph("Orchestration locale", styles['TableText']), Paragraph("Docker Engine", styles['TableText']), Paragraph("<code>docker-compose.yml</code>", styles['TableText']), Paragraph("Vérifié et conforme", styles['TableText'])],
    ]
    t_dep = Table(deploy_data, colWidths=[35 * mm, 32 * mm, 50 * mm, 53 * mm])
    t_dep.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_dep)
    story.append(Paragraph("Tableau 8.1 : Matrice de configuration et statut d'audit des environnements", styles['Caption']))
    story.append(PageBreak())

    # =========================================================================
    # CHAPITRE 9 — DISCUSSION CRITIQUE, LIMITES ET PERSPECTIVES
    # =========================================================================
    story.append(Paragraph("Chapitre 9 — Discussion Critique, Limites et Perspectives", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("9.1 Synthèse critique des performances ML et efficience de marché", styles['SectionTitle']))
    story.append(Paragraph(
        "L'analyse des métriques obtenues sur le jeu de test final (45.71% en 24H et 39.20% en 120H) appelle une discussion scientifique "
        "approfondie. Loin de représenter une anomalie de codage, ces résultats s'expliquent par les propriétés fondamentales des marchés financiers "
        "documentées dans la littérature académique :<br/>"
        "• <b>L'Hypothèse d'Efficience des Marchés (Fama, 1970 ; Malkiel, 2003)</b> : Selon la forme semi-forte d'efficience, les cours de marché "
        "reflètent instantanément toute l'information publique disponible, y compris l'historique des prix et des indicateurs techniques passés. "
        "Dès lors, les variations futures s'apparentent à une marche aléatoire (random walk) où les signaux linéaires simples présentent "
        "un pouvoir prédictif marginal.<br/>"
        "• <b>L'Hypothèse des Marchés Adaptatifs (Lo, 2004)</b> : Andrew Lo démontre que le degré d'efficience évolue dynamiquement en fonction "
        "de la concurrence entre acteurs. Toute inefficience technique temporaire découverte est rapidement arbitrée et neutralisée par les participants.<br/>"
        "• <b>Le Biais de Sélection et les Pièges de l'Analyse Technique (Aronson, 2006)</b> : David Aronson a formellement prouvé dans "
        "<i>Evidence-Based Technical Analysis</i> que la plupart des règles techniques traditionnelles (croisements de moyennes mobiles, surachats RSI) "
        "ne délivrent aucun avantage statistique supérieur au hasard une fois corrigées du data mining bias.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Explication du Biais Haussier du Modèle :</b> La matrice de confusion révèle un déséquilibre marqué (1 948 prédictions BULLISH "
        "pour 196 BEARISH en 24H). Ce comportement s'explique par la tendance haussière séculaire très forte de l'or durant la période "
        "d'entraînement (2022-2026), qui a biaisé les poids du modèle vers la classe haussière, pénalisant sa justesse lorsque le marché "
        "a traversé des phases correctives sur le jeu de test.",
        styles['Body']
    ))

    story.append(Paragraph("9.2 Limites d'infrastructure et contraintes de connectivité", styles['SectionTitle']))
    story.append(Paragraph(
        "• <b>Contraintes de quotas API</b> : Les plans standards de Twelve Data limitent le nombre d'appels par minute, imposant "
        "la régulation stricte des requêtes par le worker et empêchant une reconstruction à trop haute fréquence des features complexes.<br/>"
        "• <b>Gaps de données de fin de semaine</b> : L'or ne cotant pas durant le week-end, les rendements calculés entre le vendredi soir "
        "et le dimanche soir traversent des discontinuités de liquidité que les modèles temporels continus peinent à intégrer sans saut.",
        styles['Body']
    ))

    story.append(Paragraph("9.3 Perspectives d'évolution et recherche future", styles['SectionTitle']))
    story.append(Paragraph(
        "Plusieurs pistes de recherche appliquées se dégagent pour approfondir ce travail :<br/>"
        "1. <b>Modélisation Séquentielle Profonde</b> : Remplacer la régression logistique statique par des architectures à mémoire "
        "(LSTM, GRU) ou des transformeurs temporels (Temporal Fusion Transformers — TFT) capables de capturer les dépendances non linéaires complexes.<br/>"
        "2. <b>Enrichissement Multi-Marchés</b> : Intégrer les corrélations croisées avec les rendements des bons du Trésor américain à 10 ans (US10Y), "
        "l'indice du dollar (DXY) et le ratio or/argent (XAU/XAG).<br/>"
        "3. <b>Pipeline d'Auto-Réentraînement Continu (Online Learning)</b> : Mettre en œuvre une mise à jour incrémentale des poids du modèle "
        "au fil de la clôture de chaque nouvelle bougie quotidienne pour adapter dynamiquement le système aux changements de régime.",
        styles['Body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # CONCLUSION GÉNÉRALE
    # =========================================================================
    story.append(Paragraph("Conclusion Générale", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Ce Projet de Fin d'Année a permis de concevoir, d'implémenter et de valider scientifiquement une plateforme logicielle complète "
        "d'intelligence de marché et d'aide à la décision pour la paire XAU/USD. "
        "Le projet s'est distingué par une adhésion intransigeante aux principes de rigueur et d'honnêteté académique : "
        "refus des modèles de complaisance, élimination prouvée des fuites d'information prospective (data leakage) et publication transparente "
        "de métriques réelles non tronquées.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Sur le plan méthodologique, nous avons démontré l'importance de traiter l'analyse directionnelle comme un problème binaire "
        "strict (<b>BULLISH</b> versus <b>BEARISH</b>), en éliminant la zone morte de volatilité résiduelle lors de la constitution du jeu d'apprentissage. "
        "Le protocole de validation temporelle expansive (walk-forward avec embargo) a mis en évidence le surapprentissage fatal "
        "des modèles arborescents complexes (Random Forest, LightGBM) et a justifié la sélection d'une Régression Logistique pénalisée, "
        "plus sobre et stable.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Sur le plan architectural et logiciel, le système démontre la viabilité d'une pile full-stack moderne articulant FastAPI, WebSocket, "
        "MongoDB et Next.js 15. La distribution des cotations spot en continu par flux réactif, couplée à un moteur d'inférence sécurisé "
        "garantissant un comportement sans faute face aux données manquantes, offre une expérience utilisateur de niveau professionnel. "
        "La prise en charge native de l'arabe avec orientation bidirectionnelle RTL illustre enfin le soin apporté à l'inclusivité et à l'ergonomie.",
        styles['Body']
    ))
    story.append(Paragraph(
        "En conclusion, ce travail pose des fondations techniques et scientifiques solides pour l'ingénierie financière computationnelle, "
        "démontrant qu'un système d'aide à la décision tire sa véritable valeur de sa transparence méthodologique, de son intégrité statistique "
        "et de sa résilience architecturale.",
        styles['Body']
    ))
    story.append(Spacer(1, 10 * mm))

    # =========================================================================
    # BIBLIOGRAPHIE ET WEBOGRAPHIE
    # =========================================================================
    story.append(Paragraph("Bibliographie et Webographie", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Publications Académiques & Ouvrages Scientifiques", styles['SectionTitle']))
    biblio_academic = [
        "<b>[1] Aronson, D. R. (2006).</b> <i>Evidence-Based Technical Analysis: Applying the Scientific Method and Statistical Inference to Trading Signals</i>. John Wiley & Sons, Hoboken, New Jersey.",
        "<b>[2] Brier, G. W. (1950).</b> Verification of forecasts expressed in terms of probability. <i>Monthly Weather Review</i>, 78(1), 1-3.",
        "<b>[3] Fama, E. F. (1970).</b> Efficient Capital Markets: A Review of Theory and Empirical Work. <i>The Journal of Finance</i>, 25(2), 383-417.",
        "<b>[4] Lo, A. W. (2004).</b> The Adaptive Markets Hypothesis: Market efficiency from an evolutionary perspective. <i>Journal of Portfolio Management</i>, 30(5), 15-29.",
        "<b>[5] Lundberg, S. M., & Lee, S. I. (2017).</b> A unified approach to interpreting model predictions. <i>Advances in Neural Information Processing Systems (NeurIPS)</i>, 30, 4765-4774.",
        "<b>[6] Malkiel, B. G. (2003).</b> The Efficient Market Hypothesis and Its Critics. <i>Journal of Economic Perspectives</i>, 17(1), 59-82.",
        "<b>[7] Murphy, J. J. (1999).</b> <i>Technical Analysis of the Financial Markets: A Comprehensive Guide to Trading Methods and Applications</i>. New York Institute of Finance.",
        "<b>[8] Pardo, R. (2008).</b> <i>The Evaluation and Optimization of Trading Strategies</i>. John Wiley & Sons.",
        "<b>[9] Platt, J. (1999).</b> Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods. <i>Advances in Large Margin Classifiers</i>, 10(3), 61-74.",
    ]
    for b in biblio_academic:
        story.append(Paragraph(b, styles['Bullet']))
        story.append(Spacer(1, 1.5 * mm))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Documentations Officielles & Sources Techniques", styles['SectionTitle']))
    biblio_web = [
        "<b>[10] FastAPI Documentation.</b> Tiangolo, S. (2024). <i>FastAPI: Modern, fast (high-performance) web framework for building APIs with Python</i>. URL : https://fastapi.tiangolo.com/",
        "<b>[11] Next.js 15 Documentation.</b> Vercel Inc. (2024). <i>The React Framework for the Web</i>. URL : https://nextjs.org/docs",
        "<b>[12] Scikit-Learn Documentation.</b> Pedregosa, F. et al. (2024). <i>Machine Learning in Python</i>. URL : https://scikit-learn.org/stable/",
        "<b>[13] Twelve Data API Reference.</b> Twelve Data Pte. Ltd. (2024). <i>Financial Market Data APIs and WebSocket Documentation</i>. URL : https://twelvedata.com/docs",
        "<b>[14] MongoDB Atlas Documentation.</b> MongoDB Inc. (2024). <i>MongoDB Server and Motor Asynchronous Python Driver</i>. URL : https://www.mongodb.com/docs/",
        "<b>[15] ReportLab Reference Manual.</b> ReportLab Europe Ltd. (2024). <i>ReportLab PDF Generation User Guide</i>. URL : https://www.reportlab.com/documentation/",
    ]
    for w in biblio_web:
        story.append(Paragraph(w, styles['Bullet']))
        story.append(Spacer(1, 1.5 * mm))
    story.append(PageBreak())

    # =========================================================================
    # ANNEXES
    # =========================================================================
    story.append(Paragraph("Annexes", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("Annexe A : Répertoire des Diagrammes UML (PlantUML)", styles['SectionTitle']))
    story.append(Paragraph(
        "L'ensemble des diagrammes d'architecture, de séquence et d'activité du système a été formalisé en langage PlantUML "
        "et sauvegardé sous forme de fichiers sources textuels dans le répertoire <code>docs/uml/</code> du dépôt local :<br/>"
        "• <code>docs/uml/use_cases.puml</code> : Diagramme des cas d'utilisation du système.<br/>"
        "• <code>docs/uml/architecture.puml</code> : Diagramme des composants de l'architecture full-stack.<br/>"
        "• <code>docs/uml/sequence_prediction.puml</code> : Diagramme de séquence de calcul et d'inférence de prédiction.<br/>"
        "• <code>docs/uml/sequence_websocket.puml</code> : Diagramme de séquence de souscription et diffusion de ticks WebSocket.<br/>"
        "• <code>docs/uml/pipeline_ml.puml</code> : Diagramme d'activité retraçant les étapes 1 à 5 du pipeline Machine Learning.<br/>"
        "• <code>docs/uml/data_flow.puml</code> : Diagramme de flux de données de bout en bout.<br/>"
        "• <code>docs/uml/deployment.puml</code> : Diagramme de déploiement conteneurisé et cloud.<br/>"
        "• <code>docs/uml/database.puml</code> : Diagramme entité-relation des collections et index MongoDB.",
        styles['Body']
    ))

    story.append(Paragraph("Extrait Source PlantUML : Séquence d'Inférence (sequence_prediction.puml)", styles['SubSectionTitle']))
    uml_code = (
        "@startuml\n"
        "autonumber\n"
        "actor Client -> Router: GET /api/predictions/XAUUSD?horizon=daily\n"
        "Router -> Service: one(AssetSymbol.XAUUSD, horizon='daily')\n"
        "Service -> Engine: get_step5_engine()\n"
        "Engine -> Disk: load logistic_regression_final.joblib & feature_schema.json\n"
        "Service -> Market: detail(XAUUSD, timeframe=H1, limit=400)\n"
        "Market -> DB: find closed H1 candles from MongoDB\n"
        "Service -> Service: build_feature_frame() (87 causal features via merge_asof)\n"
        "Service -> Engine: predict(last_row_features)\n"
        "Engine -> Engine: standardize & compute probabilities (BULLISH / BEARISH)\n"
        "Engine --> Service: PredictionOutput (direction, probas, confidence)\n"
        "Service -> Service: compute linear contributions (Top 8 features) & build_scenarios()\n"
        "Service --> Router: PredictionResponse (validated by Pydantic)\n"
        "Router --> Client: 200 OK JSON payload\n"
        "@enduml"
    )
    t_uml = Table([[Paragraph(f"<pre>{uml_code}</pre>", styles['CodeSnippet'])]], colWidths=[170 * mm])
    t_uml.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_uml)

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Annexe B : Spécification Exhaustive des Points de Terminaison d'API", styles['SectionTitle']))
    
    endpoints_data = [
        [Paragraph("Méthode & Route", styles['TableHeader']), Paragraph("Paramètres", styles['TableHeader']), Paragraph("Code Succès", styles['TableHeader']), Paragraph("Description & Rôle Fonctionnel", styles['TableHeader'])],
        [Paragraph("<code>GET /api/health</code>", styles['TableText']), Paragraph("Aucun", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("État de l'application, statut de connectivité MongoDB et worker d'ingestion.", styles['TableText'])],
        [Paragraph("<code>GET /api/market</code>", styles['TableText']), Paragraph("timeframe (opt)", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("Instantané du cours spot et variation journalière.", styles['TableText'])],
        [Paragraph("<code>GET /api/market/{symbol}</code>", styles['TableText']), Paragraph("timeframe, limit", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("Historique des bougies fermées vérifiées pour le symbole spécifié.", styles['TableText'])],
        [Paragraph("<code>GET /api/market/live-status</code>", styles['TableText']), Paragraph("Aucun", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("Statut de connexion Twelve Data (LIVE / DELAYED) et latence.", styles['TableText'])],
        [Paragraph("<code>GET /api/predictions/{symbol}</code>", styles['TableText']), Paragraph("horizon (daily|weekly)", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("Prédiction binaire ML, probabilités, confiance, top features et scénarios.", styles['TableText'])],
        [Paragraph("<code>GET /api/explanations/{symbol}</code>", styles['TableText']), Paragraph("Aucun", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("Contributions des caractéristiques explicatives du modèle.", styles['TableText'])],
        [Paragraph("<code>GET /api/model-performance</code>", styles['TableText']), Paragraph("Aucun", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("Métriques réelles persistées hors-échantillon.", styles['TableText'])],
        [Paragraph("<code>GET /api/data-quality</code>", styles['TableText']), Paragraph("timeframe", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("Rapport d'intégrité temporelle et de fraîcheur des bougies.", styles['TableText'])],
        [Paragraph("<code>WS /api/ws/market</code>", styles['TableText']), Paragraph("Socket bidirectionnel", styles['TableText']), Paragraph("101 Switch", styles['TableText']), Paragraph("Diffusion temps réel push des ticks de cours Twelve Data.", styles['TableText'])],
    ]
    t_end = Table(endpoints_data, colWidths=[42 * mm, 32 * mm, 20 * mm, 76 * mm])
    t_end.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_end)

    # Construction du document PDF
    print(f"Génération en cours du document PDF : {output_path}...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Document PDF généré avec succès ({output_path}).")

if __name__ == "__main__":
    out_dir = Path("output/pdf")
    out_dir.mkdir(parents=True, exist_ok=True)
    target_pdf = str(out_dir / "Rapport_PFA_AI_XAUUSD.pdf")
    
    build_pdf_report(target_pdf)
    
    # Copie de sauvegarde dans docs/report/
    docs_report_dir = Path("docs/report")
    docs_report_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(target_pdf, str(docs_report_dir / "Rapport_PFA_AI_XAUUSD.pdf"))
    print("Copie de sauvegarde créée dans docs/report/Rapport_PFA_AI_XAUUSD.pdf.")

