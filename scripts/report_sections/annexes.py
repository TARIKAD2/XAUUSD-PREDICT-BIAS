"""Annexes techniques et extraits de code pour le rapport de PFA."""

from pathlib import Path
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, BORDER_COLOR, HIGHLIGHT, LIGHT_BG

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def _load_file_snippet(relative_path: str, max_lines: int = 50) -> str:
    """Charge un extrait de fichier texte en UTF-8."""
    file_path = ROOT_DIR / relative_path
    if not file_path.exists():
        return f"# Fichier non trouvé : {relative_path}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        snippet = "".join(lines[:max_lines])
        if len(lines) > max_lines:
            snippet += f"\n# ... [Tronqué : {len(lines) - max_lines} lignes supplémentaires non affichées] ...\n"
        # Remplacer les caractères spéciaux pour l'affichage Platypus
        snippet = snippet.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return snippet
    except Exception as e:
        return f"# Erreur de lecture : {e}"

def get_annexes_story(styles):
    story = []

    story.append(Paragraph("Annexes Exhaustives", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    # =========================================================================
    # ANNEXE A : DIAGRAMMES PLANTUML
    # =========================================================================
    story.append(Paragraph("Annexe A : Code Source des 8 Diagrammes PlantUML du Système", styles['SectionTitle']))
    story.append(Paragraph(
        "L'ensemble des diagrammes d'architecture, de cas d'utilisation, de flux de données et de séquences a été modélisé "
        "en syntaxe déclarative PlantUML et archivé sous forme de fichiers textuels dans le répertoire <code>docs/uml/</code>. "
        "Les extraits ci-dessous reproduisent les sources textuelles intégrales certifiées du projet :",
        styles['Body']
    ))

    uml_files = [
        ("A.1 Diagramme des Cas d'Utilisation", "docs/uml/use_cases.puml"),
        ("A.2 Diagramme des Composants d'Architecture Full-Stack", "docs/uml/architecture.puml"),
        ("A.3 Diagramme de Séquence du Calcul de Prédiction", "docs/uml/sequence_prediction.puml"),
        ("A.4 Diagramme de Séquence de Streaming WebSocket", "docs/uml/sequence_websocket.puml"),
        ("A.5 Diagramme d'Activité du Pipeline Machine Learning (Étapes 1 à 5)", "docs/uml/pipeline_ml.puml"),
        ("A.6 Diagramme de Flux de Données End-to-End", "docs/uml/data_flow.puml"),
        ("A.7 Diagramme de Déploiement Conteneurisé et Cloud", "docs/uml/deployment.puml"),
        ("A.8 Diagramme Entité-Relation des Collections MongoDB", "docs/uml/database.puml"),
    ]

    for title, rel_path in uml_files:
        story.append(Paragraph(f"<b>{title} (<code>{rel_path}</code>)</b>", styles['SubSectionTitle']))
        snippet = _load_file_snippet(rel_path, max_lines=70)
        t_box = Table([[Paragraph(f"<pre>{snippet}</pre>", styles['CodeSnippet'])]], colWidths=[170 * mm])
        t_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_box)
        story.append(Spacer(1, 4 * mm))

    story.append(PageBreak())

    # =========================================================================
    # ANNEXE B : SPÉCIFICATION EXHAUSTIVE DE L'API REST & WS
    # =========================================================================
    story.append(Paragraph("Annexe B : Spécification Exhaustive des Points de Terminaison d'API", styles['SectionTitle']))
    story.append(Paragraph(
        "Le tableau ci-dessous récapitule l'ensemble des points de terminaison HTTP et WebSocket exposés par le backend FastAPI, "
        "avec indication de leurs paramètres de requête, codes de réponse standards et exemples de charges utiles :",
        styles['Body']
    ))

    api_specs = [
        [Paragraph("Méthode & Route", styles['TableHeader']), Paragraph("Paramètres", styles['TableHeader']), Paragraph("Réponse & Code", styles['TableHeader']), Paragraph("Payload JSON Typique / Rôle Applicatif", styles['TableHeader'])],
        [Paragraph("<code>GET /api/health</code>", styles['TableText']), Paragraph("Aucun", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("<code>{\"status\": \"ok\", \"database\": \"CONNECTED\", \"ingestion\": \"RUNNING\"}</code>", styles['TableText'])],
        [Paragraph("<code>GET /api/market</code>", styles['TableText']), Paragraph("<code>timeframe</code> (opt)", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("<code>{\"symbol\": \"XAUUSD\", \"price\": 2650.50, \"change_24h\": 0.45}</code>", styles['TableText'])],
        [Paragraph("<code>GET /api/market/{symbol}</code>", styles['TableText']), Paragraph("<code>timeframe</code> (str)<br/><code>limit</code> (int)", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("Tableau de bougies fermées : <code>[{\"timestamp\": \"...\", \"open\": 2640, \"close\": 2645}]</code>", styles['TableText'])],
        [Paragraph("<code>GET /api/market/live-status</code>", styles['TableText']), Paragraph("Aucun", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("<code>{\"status\": \"LIVE\", \"provider\": \"TwelveData\", \"latency_ms\": 14}</code>", styles['TableText'])],
        [Paragraph("<code>GET /api/predictions/{symbol}</code>", styles['TableText']), Paragraph("<code>horizon</code><br/>(daily|weekly)", styles['TableText']), Paragraph("200 OK<br/>503 Service", styles['TableText']), Paragraph("<code>{\"direction\": \"BULLISH\", \"probabilities\": {\"bullish\": 0.62, \"bearish\": 0.38}, \"confidence\": 0.24, \"top_features\": [...], \"scenarios\": [...]}</code>", styles['TableText'])],
        [Paragraph("<code>GET /api/explanations/{symbol}</code>", styles['TableText']), Paragraph("<code>horizon</code> (opt)", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("<code>{\"model\": \"logistic_regression\", \"top_contributors\": [{\"feature\": \"h1_rsi_14\", \"contribution\": 0.34}]}</code>", styles['TableText'])],
        [Paragraph("<code>GET /api/model-performance</code>", styles['TableText']), Paragraph("Aucun", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("<code>{\"symbol\": \"XAUUSD\", \"accuracy\": 0.4571, \"balanced_accuracy\": 0.4731, \"f1\": 0.6091, \"brier\": 0.2871}</code>", styles['TableText'])],
        [Paragraph("<code>GET /api/data-quality</code>", styles['TableText']), Paragraph("<code>timeframe</code> (opt)", styles['TableText']), Paragraph("200 OK", styles['TableText']), Paragraph("<code>{\"symbol\": \"XAUUSD\", \"duplicates\": 0, \"gaps_detected\": 509, \"status\": \"VALID\"}</code>", styles['TableText'])],
        [Paragraph("<code>WS /api/ws/market</code>", styles['TableText']), Paragraph("Socket TCP", styles['TableText']), Paragraph("101 Switch", styles['TableText']), Paragraph("Streaming JSON push en continu : <code>{\"type\": \"price\", \"price\": 2650.80, \"timestamp\": \"...\"}</code>", styles['TableText'])],
    ]
    t_api = Table(api_specs, colWidths=[42 * mm, 30 * mm, 24 * mm, 74 * mm])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_api)
    story.append(PageBreak())

    # =========================================================================
    # ANNEXE C : EXTRAITS DE CODE SOURCES FONDAMENTAUX
    # =========================================================================
    story.append(Paragraph("Annexe C : Extraits de Code Sources Fondamentaux du Dépôt", styles['SectionTitle']))
    story.append(Paragraph(
        "Afin d'étayer formellement les affirmations techniques de ce rapport, les extraits de code source vérifiés "
        "suivants sont reproduits directement depuis le dépôt local :",
        styles['Body']
    ))

    code_files = [
        ("C.1 Définition binaire stricte des classes (CLASS_ORDER = ['BEARISH', 'BULLISH'])", "backend/app/ml/labels.py", 35),
        ("C.2 Validation Pydantic V2 de la somme unitaire des probabilités", "backend/app/schemas/prediction.py", 45),
        ("C.3 Alignement temporel causal rétrograde merge_asof backward", "backend/app/data/mtf_features.py", 45),
        ("C.4 Moteur de serving de production (STEP 5 : ModelServingEngine)", "backend/app/ml/step5_serving.py", 55),
        ("C.5 Descripteur d'orchestration locale avec healthcheck croisé", "docker-compose.yml", 30),
    ]

    for title, rel_path, max_l in code_files:
        story.append(Paragraph(f"<b>{title} (<code>{rel_path}</code>)</b>", styles['SubSectionTitle']))
        snippet = _load_file_snippet(rel_path, max_lines=max_l)
        t_box = Table([[Paragraph(f"<pre>{snippet}</pre>", styles['CodeSnippet'])]], colWidths=[170 * mm])
        t_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
            ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_box)
        story.append(Spacer(1, 4 * mm))

    story.append(PageBreak())

    # =========================================================================
    # ANNEXE D : INVENTAIRE EXHAUSTIF DES 87 CARACTÉRISTIQUES
    # =========================================================================
    story.append(Paragraph("Annexe D : Inventaire Exhaustif des 87 Caractéristiques Techniques", styles['SectionTitle']))
    story.append(Paragraph(
        "Le tableau ci-dessous répertorie l'intégralité des 87 variables prédictives calculées dans le jeu de données "
        "<code>XAUUSD_features.csv</code>, ventilées par échelle temporelle source :",
        styles['Body']
    ))

    feat_inventory = [
        [Paragraph("Groupe de Features", styles['TableHeader']), Paragraph("Nombre", styles['TableHeader']), Paragraph("Liste Exhaustive des Variables Générées (Noms de Colonnes)", styles['TableHeader'])],
        [Paragraph("<b>Base OHLCV</b>", styles['TableText']), Paragraph("5", styles['TableText']), Paragraph("<code>open</code>, <code>high</code>, <code>low</code>, <code>close</code>, <code>tick_volume</code>", styles['TableText'])],
        [Paragraph("<b>Échelle H1 (Pivot)</b>", styles['TableText']), Paragraph("32", styles['TableText']), Paragraph(
            "<code>h1_ret_1</code>, <code>h1_log_ret_1</code>, <code>h1_ret_4</code>, <code>h1_ret_24</code>, "
            "<code>h1_body</code>, <code>h1_range</code>, <code>h1_upper_wick</code>, <code>h1_lower_wick</code>, <code>h1_body_ratio</code>, <code>h1_close_loc</code>, "
            "<code>h1_sma_20</code>, <code>h1_sma_50</code>, <code>h1_sma_200</code>, <code>h1_ema_12</code>, <code>h1_ema_20</code>, <code>h1_ema_50</code>, <code>h1_trend_ema</code>, "
            "<code>h1_close_vs_sma20</code>, <code>h1_close_vs_sma50</code>, <code>h1_close_vs_sma200</code>, "
            "<code>h1_rsi_14</code>, <code>h1_macd</code>, <code>h1_macd_signal</code>, <code>h1_macd_hist</code>, "
            "<code>h1_atr_14</code>, <code>h1_atr_pct</code>, <code>h1_vol_20</code>, <code>h1_range_ma_20</code>, <code>h1_rel_volume_20</code>, "
            "<code>h1_hour</code>, <code>h1_dow</code>, <code>h1_gap_hours</code>", styles['TableText']
        )],
        [Paragraph("<b>Échelle H4 (Macro)</b>", styles['TableText']), Paragraph("27", styles['TableText']), Paragraph(
            "<code>h4_close</code>, <code>h4_tick_volume</code>, <code>h4_ret_1</code>, <code>h4_log_ret_1</code>, <code>h4_ret_4</code>, "
            "<code>h4_body</code>, <code>h4_range</code>, <code>h4_upper_wick</code>, <code>h4_lower_wick</code>, <code>h4_body_ratio</code>, <code>h4_close_loc</code>, "
            "<code>h4_sma_20</code>, <code>h4_sma_50</code>, <code>h4_ema_20</code>, <code>h4_ema_50</code>, <code>h4_trend_ema</code>, "
            "<code>h4_close_vs_sma20</code>, <code>h4_close_vs_sma50</code>, <code>h4_rsi_14</code>, "
            "<code>h4_macd</code>, <code>h4_macd_signal</code>, <code>h4_macd_hist</code>, "
            "<code>h4_atr_14</code>, <code>h4_atr_pct</code>, <code>h4_vol_20</code>, <code>h4_rel_volume_20</code>, "
            "<code>h4_age_hours</code>", styles['TableText']
        )],
        [Paragraph("<b>Échelle M15 (Micro)</b>", styles['TableText']), Paragraph("23", styles['TableText']), Paragraph(
            "<code>m15_close</code>, <code>m15_tick_volume</code>, <code>m15_ret_1</code>, <code>m15_log_ret_1</code>, "
            "<code>m15_body</code>, <code>m15_range</code>, <code>m15_upper_wick</code>, <code>m15_lower_wick</code>, <code>m15_body_ratio</code>, <code>m15_close_loc</code>, "
            "<code>m15_sma_20</code>, <code>m15_ema_20</code>, <code>m15_ema_50</code>, <code>m15_trend_ema</code>, <code>m15_close_vs_sma20</code>, "
            "<code>m15_rsi_14</code>, <code>m15_macd_hist</code>, <code>m15_atr_14</code>, <code>m15_atr_pct</code>, "
            "<code>m15_vol_20</code>, <code>m15_rel_volume_20</code>, <code>m15_bars_in_h1</code>, <code>m15_age_minutes</code>", styles['TableText']
        )],
    ]
    t_fi = Table(feat_inventory, colWidths=[35 * mm, 18 * mm, 117 * mm])
    t_fi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_fi)

    return story

