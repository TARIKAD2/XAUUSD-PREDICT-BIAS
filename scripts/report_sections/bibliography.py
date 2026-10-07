"""Bibliographie et Webographie du rapport de PFA."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable
from .styles import PRIMARY

def get_bibliography_story(styles):
    story = []

    story.append(Paragraph("Bibliographie et Webographie", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("1. Publications Académiques & Ouvrages de Référence", styles['SectionTitle']))

    academic_refs = [
        "<b>[1] Aronson, D. R. (2006).</b> <i>Evidence-Based Technical Analysis: Applying the Scientific Method and Statistical Inference to Trading Signals</i>. John Wiley & Sons, Hoboken, New Jersey. (Ouvrage fondamental démontrant la nécessité de corriger le biais de sélection dans l'évaluation des règles d'analyse technique).",
        "<b>[2] Brier, G. W. (1950).</b> Verification of forecasts expressed in terms of probability. <i>Monthly Weather Review</i>, 78(1), 1-3. (Formalisation mathématique du Brier Score utilisé pour mesurer l'étalonnage probabiliste des prédictions).",
        "<b>[3] Cont, R. (2001).</b> Empirical properties of asset returns: stylized facts and statistical issues. <i>Quantitative Finance</i>, 1(2), 223-236. (Revue de référence sur les faits stylisés des séries temporelles de prix d'actifs : queues lourdes, leptokurticité et regroupement de volatilité).",
        "<b>[4] Fama, E. F. (1970).</b> Efficient Capital Markets: A Review of Theory and Empirical Work. <i>The Journal of Finance</i>, 25(2), 383-417. (Article fondateur posant la théorie moderne de l'efficience des marchés financiers sous ses trois formes : faible, semi-forte et forte).",
        "<b>[5] Lo, A. W. (2004).</b> The Adaptive Markets Hypothesis: Market efficiency from an evolutionary perspective. <i>Journal of Portfolio Management</i>, 30(5), 15-29. (Théorie des marchés adaptatifs réconciliant l'efficience économique et l'émergence transitoire d'anomalies comportementales).",
        "<b>[6] Lundberg, S. M., & Lee, S. I. (2017).</b> A unified approach to interpreting model predictions. <i>Advances in Neural Information Processing Systems (NeurIPS)</i>, 30, 4765-4774. (Théorie unifiée des valeurs de Shapley pour l'explicabilité locale des modèles d'apprentissage automatique — SHAP).",
        "<b>[7] Malkiel, B. G. (2003).</b> The Efficient Market Hypothesis and Its Critics. <i>Journal of Economic Perspectives</i>, 17(1), 59-82. (Synthèse critique sur la prédictibilité des marchés et la marche aléatoire des prix).",
        "<b>[8] Murphy, J. J. (1999).</b> <i>Technical Analysis of the Financial Markets: A Comprehensive Guide to Trading Methods and Applications</i>. New York Institute of Finance. (Manuel de référence pour la formalisation mathématique des indicateurs RSI, MACD et moyennes mobiles).",
        "<b>[9] Pardo, R. (2008).</b> <i>The Evaluation and Optimization of Trading Strategies</i>. John Wiley & Sons. (Méthodologie formelle de validation temporelle par fenêtres glissantes et walk-forward analysis sans fuite de données).",
        "<b>[10] Platt, J. (1999).</b> Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods. <i>Advances in Large Margin Classifiers</i>, 10(3), 61-74. (Méthode de calibration probabiliste sigmoïde des sorties de classifieurs).",
    ]

    for ref in academic_refs:
        story.append(Paragraph(ref, styles['Bullet']))
        story.append(Spacer(1, 2 * mm))

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("2. Documentations Officielles & Sources Techniques", styles['SectionTitle']))

    technical_refs = [
        "<b>[11] FastAPI Documentation.</b> Tiangolo, S. (2024). <i>FastAPI: Modern, fast (high-performance) web framework for building APIs with Python</i>. URL : <font color='#1E4E79'>https://fastapi.tiangolo.com/</font>",
        "<b>[12] Next.js 15 Documentation.</b> Vercel Inc. (2024). <i>Next.js: The React Framework for the Web (App Router & Server Components)</i>. URL : <font color='#1E4E79'>https://nextjs.org/docs</font>",
        "<b>[13] Scikit-Learn Documentation.</b> Pedregosa, F. et al. (2024). <i>Scikit-Learn: Machine Learning in Python (Pipeline, StandardScaler, LogisticRegression)</i>. URL : <font color='#1E4E79'>https://scikit-learn.org/stable/</font>",
        "<b>[14] Twelve Data API Documentation.</b> Twelve Data Pte. Ltd. (2024). <i>Financial APIs & Real-Time WebSocket Streaming Documentation</i>. URL : <font color='#1E4E79'>https://twelvedata.com/docs</font>",
        "<b>[15] MongoDB Server & Motor Documentation.</b> MongoDB Inc. (2024). <i>MongoDB Manual & Motor Asynchronous Python Driver for Tornado and AsyncIO</i>. URL : <font color='#1E4E79'>https://www.mongodb.com/docs/</font>",
        "<b>[16] ReportLab Reference Manual.</b> ReportLab Europe Ltd. (2024). <i>ReportLab PDF Generation User Guide and API Reference</i>. URL : <font color='#1E4E79'>https://www.reportlab.com/documentation/</font>",
    ]

    for ref in technical_refs:
        story.append(Paragraph(ref, styles['Bullet']))
        story.append(Spacer(1, 2 * mm))

    story.append(PageBreak())

    return story

