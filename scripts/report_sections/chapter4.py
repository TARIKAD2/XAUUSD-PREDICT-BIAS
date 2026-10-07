"""Chapitre 4 — Acquisition et Préparation des Données de Marché."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, BORDER_COLOR, HIGHLIGHT, LIGHT_BG

def get_chapter4_story(styles):
    story = []

    story.append(Paragraph("Chapitre 4 — Acquisition et Préparation des Données de Marché", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("4.1 Collecte des données historiques LiteFinance", styles['SectionTitle']))
    story.append(Paragraph(
        "La phase d'entraînement et d'évaluation rétrospective des modèles de Machine Learning nécessite une profondeur "
        "d'historique conséquente afin de confronter les algorithmes à une variété représentative de régimes de marché "
        "(marchés haussiers séculaires, consolidations latérales prolongées, paniques baissières et chocs de volatilité). "
        "Le socle de données historiques exploité dans ce projet provient d'exports bruts issus des serveurs de courtage "
        "de la plateforme <b>LiteFinance</b> (environnement MetaTrader), stockés dans le répertoire <code>data/raw/litefinance/</code> "
        "sous trois résolutions temporelles distinctes :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Série H1 (Résolution Pivot — 1 Heure)</b> : Fichier <code>XAUUSD_H1.csv</code> couvrant une profondeur chronologique "
        "exceptionnelle s'étendant du 17 novembre 2009 au 18 septembre 2026, totalisant 100 000 barres brutes de cotation.<br/>"
        "• <b>Série H4 (Résolution Macro — 4 Heures)</b> : Fichier <code>XAUUSD_H4.csv</code> couvrant la période du 1er janvier 2009 "
        "au 18 septembre 2026, totalisant 43 333 barres brutes (ramenées à 27 805 barres après filtrage des doublons de week-ends).<br/>"
        "• <b>Série M15 (Résolution Micro — 15 Minutes)</b> : Fichier <code>XAUUSD_M15.csv</code> couvrant la période du 1er juillet 2022 "
        "au 18 septembre 2026, comprenant 100 000 barres brutes haute fréquence.",
        styles['Body']
    ))

    story.append(Paragraph("4.2 Ingestion temps réel Twelve Data REST et WebSocket", styles['SectionTitle']))
    story.append(Paragraph(
        "Pour assurer le fonctionnement opérationnel de la plateforme en environnement de production, les données proviennent "
        "de la passerelle de cotation professionnelle <b>Twelve Data</b> selon un double canal complémentaire :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Interface REST Time Series</b> : Interrogée de manière planifiée par le composant <code>TwelveDataCollector</code> "
        "et le worker d'ingestion (<code>XAUUSDIngestionWorker</code>). Ce canal récupère périodiquement les bougies fermées H1 "
        "dès leur clôture formelle, vérifie leur intégrité géométrique et les insère de façon idempotente dans la collection "
        "MongoDB <code>market_data</code>.<br/>"
        "• <b>Flux WebSocket Streaming</b> : Maintenu en permanence par le singleton <code>LiveMarketService</code> "
        "(connecté à <code>wss://ws.twelvedata.com/v1/quotes/price</code>). Il reçoit en flux continu chaque micro-variation "
        "du cours spot XAU/USD (prix bid/ask, volume du tick, horodatage UTC). Ce flux alimente le cache mémoire interne "
        "et est redistribué instantanément aux clients web via le protocole WebSocket.",
        styles['Body']
    ))

    story.append(Paragraph("4.3 Protocole de nettoyage, validation et audit d'intégrité (Étape 1)", styles['SectionTitle']))
    story.append(Paragraph(
        "L'étape 1 du pipeline de données (implémentée dans <code>backend/app/data/litefinance.py</code> et auditée dans "
        "<code>data/processed/litefinance/step1_audit.json</code>) applique une charte d'intégrité d'une rigueur absolue :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Immutabilité des fichiers bruts</b> : Les fichiers sources situés dans <code>data/raw/</code> sont traités en lecture seule "
        "stricte (paramètre d'audit vérifié <code>never_modified_raw: true</code>). Les transformations sont écrites exclusivement dans "
        "des fichiers dérivés au sein de <code>data/processed/litefinance/</code>.<br/>"
        "2. <b>Refus catégorique d'interpolation artificielle</b> : Une erreur classique en finance consiste à combler artificiellement "
        "les périodes de fermeture de marché (week-ends et jours fériés) par des bougies synthétiques interpolées. Notre pipeline "
        "s'interdit formellement toute injection de chandeliers fictifs (audit vérifié <code>never_created_candles: true</code>). "
        "Les fermetures effectives de fin de semaine (vendredi soir au dimanche soir) sont intégralement préservées comme des discontinuités "
        "légitimes de liquidité.<br/>"
        "3. <b>Contrôle strict des contraintes géométriques OHLC</b> : Chaque chandelier subit un ensemble de contrôles géométriques stricts : "
        "$High \\ge \\max(Open, Close)$, $Low \\le \\min(Open, Close)$, $Low > 0$, $TickVolume \\ge 0$. Toute ligne violant l'une de ces propriétés "
        "est rejetée.<br/>"
        "4. <b>Validation chronologique et unicité temporelle</b> : Vérification que les horodatages sont strictement croissants "
        "et dépourvus du moindre doublon (<code>duplicates_removed: 0</code> sur H1 et M15).",
        styles['Body']
    ))

    tbl_audit1 = [
        [Paragraph("Série Historique", styles['TableHeader']), Paragraph("Barres Brutes", styles['TableHeader']), Paragraph("Barres Nettoyées", styles['TableHeader']), Paragraph("Intervalle Temporel Vérifié", styles['TableHeader']), Paragraph("Gaps Réels Préservés", styles['TableHeader'])],
        [Paragraph("<b>XAUUSD H1</b>", styles['TableText']), Paragraph("100 000", styles['TableText']), Paragraph("100 000", styles['TableText']), Paragraph("17/11/2009 au 18/09/2026", styles['TableText']), Paragraph("4 338 (dont 509 week-ends)", styles['TableText'])],
        [Paragraph("<b>XAUUSD H4</b>", styles['TableText']), Paragraph("43 333", styles['TableText']), Paragraph("27 805", styles['TableText']), Paragraph("01/01/2009 au 18/09/2026", styles['TableText']), Paragraph("1 373 (dont 552 week-ends)", styles['TableText'])],
        [Paragraph("<b>XAUUSD M15</b>", styles['TableText']), Paragraph("100 000", styles['TableText']), Paragraph("100 000", styles['TableText']), Paragraph("01/07/2022 au 18/09/2026", styles['TableText']), Paragraph("1 022 (dont 212 week-ends)", styles['TableText'])],
    ]
    t_a1 = Table(tbl_audit1, colWidths=[28 * mm, 24 * mm, 26 * mm, 50 * mm, 42 * mm])
    t_a1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_a1)
    story.append(Paragraph("Tableau 4.1 : Audit volumétrique et intégrité des séries historiques brutes LiteFinance", styles['Caption']))

    story.append(Paragraph("4.4 Ingénierie des caractéristiques : Décomposition des 87 features MTF", styles['SectionTitle']))
    story.append(Paragraph(
        "L'étape 2 (implémentée dans <code>backend/app/data/mtf_features.py</code> et auditée dans <code>data/processed/ml/step2_audit.json</code>) "
        "construit le jeu de données unifié d'apprentissage <code>XAUUSD_features.csv</code>. "
        "Ce fichier rassemble <b>25 012 observations</b> et <b>87 caractéristiques techniques</b> calculées de façon causale. "
        "L'échantillon débute le 01/07/2022, date marquant la disponibilité conjointe des trois échelles temporelles (M15, H1, H4). "
        "Les 87 variables se répartissent rigoureusement comme suit :",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>A. Base OHLCV de la barre pivot H1 (5 caractéristiques) :</b><br/>"
        "• <code>open</code>, <code>high</code>, <code>low</code>, <code>close</code> : Niveaux de prix bruts de la bougie H1.<br/>"
        "• <code>tick_volume</code> : Nombre de variations de cotation (ticks) enregistrées durant l'heure.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>B. Indicateurs techniques sur l'échelle pivot H1 (32 caractéristiques) :</b><br/>"
        "• <i>Rendements temporels</i> : Rendement simple 1 heure <code>h1_ret_1</code>, rendement logarithmique <code>h1_log_ret_1</code>, "
        "rendement 4 heures <code>h1_ret_4</code> et rendement 24 heures <code>h1_ret_24</code>.<br/>"
        "• <i>Morphologie du chandelier</i> : Taille absolue du corps <code>h1_body = |close - open|</code>, amplitude totale de la bougie "
        "<code>h1_range = high - low</code>, mèche supérieure <code>h1_upper_wick = high - max(open, close)</code>, mèche inférieure "
        "<code>h1_lower_wick = min(open, close) - low</code>, ratio de corps <code>h1_body_ratio = h1_body / h1_range</code>, et position "
        "relative de la clôture dans l'intervalle <code>h1_close_loc = (close - low) / h1_range</code>.<br/>"
        "• <i>Moyennes mobiles et écarts de tendance</i> : Moyennes mobiles simples sur 20, 50 et 200 périodes (<code>h1_sma_20</code>, "
        "<code>h1_sma_50</code>, <code>h1_sma_200</code>), moyennes mobiles exponentielles sur 12, 20 et 50 périodes (<code>h1_ema_12</code>, "
        "<code>h1_ema_20</code>, <code>h1_ema_50</code>), indicateur de croisement de tendance <code>h1_trend_ema = (ema_20 - ema_50) / ema_50</code>, "
        "et distances relatives du cours de clôture aux moyennes : <code>h1_close_vs_sma20</code>, <code>h1_close_vs_sma50</code>, <code>h1_close_vs_sma200</code>.<br/>"
        "• <i>Oscillateur RSI (Relative Strength Index de Wilder à 14 périodes)</i> : Formulé mathématiquement comme suit :<br/>"
        "Soit $U_t = \\max(C_t - C_{t-1}, 0)$ et $D_t = \\max(C_{t-1} - C_t, 0)$. Les moyennes lissées exponentielles $\\overline{U}_t$ "
        "et $\\overline{D}_t$ sont calculées avec $\\alpha = 1/14$. L'indicateur est donné par :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;RSI_{14} = 100 - \\frac{100}{1 + \\frac{\\overline{U}_t}{\\overline{D}_t}}</font><br/>"
        "• <i>MACD (Moving Average Convergence Divergence)</i> : Calculé selon les paramètres classiques d'Appel (12, 26, 9) :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;MACD = EMA_{12}(C) - EMA_{26}(C),&nbsp;&nbsp;&nbsp;&nbsp;Signal = EMA_9(MACD),&nbsp;&nbsp;&nbsp;&nbsp;Hist = MACD - Signal</font><br/>"
        "Générant les variables <code>h1_macd</code>, <code>h1_macd_signal</code> et <code>h1_macd_hist</code>.<br/>"
        "• <i>Indicateurs de volatilité</i> : Amplitude vraie moyenne de Wilder à 14 périodes (<code>h1_atr_14</code>) dérivée du True Range "
        "$TR_t = \\max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|)$, pourcentage ATR <code>h1_atr_pct = atr_14 / close</code>, "
        "volatilité historique glissante sur 20 périodes <code>h1_vol_20</code> (écart-type des rendements horaires), moyenne mobile "
        "de l'amplitude sur 20 périodes <code>h1_range_ma_20</code> et volume relatif <code>h1_rel_volume_20 = volume / sma_{20}(volume)</code>.<br/>"
        "• <i>Variables temporelles calendaires</i> : Heure de la journée (<code>h1_hour</code> $\\in [0, 23]$), jour de la semaine "
        "(<code>h1_dow</code> $\\in [0, 6]$) et nombre d'heures écoulées depuis la bougie précédente <code>h1_gap_hours</code> "
        "(détectant les réouvertures post-week-end).",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>C. Indicateurs techniques sur l'échelle macro H4 (27 caractéristiques) :</b><br/>"
        "Agrégation des tendances de moyen terme : clôture H4 (<code>h4_close</code>), volume H4 (<code>h4_tick_volume</code>), "
        "rendements H4 (<code>h4_ret_1</code>, <code>h4_log_ret_1</code>, <code>h4_ret_4</code>), morphologie de chandelier (<code>h4_body</code>, "
        "<code>h4_range</code>, <code>h4_upper_wick</code>, <code>h4_lower_wick</code>, <code>h4_body_ratio</code>, <code>h4_close_loc</code>), "
        "moyennes mobiles H4 (<code>h4_sma_20</code>, <code>h4_sma_50</code>, <code>h4_ema_20</code>, <code>h4_ema_50</code>, <code>h4_trend_ema</code>), "
        "distances à la moyenne (<code>h4_close_vs_sma20</code>, <code>h4_close_vs_sma50</code>), oscillateurs H4 (<code>h4_rsi_14</code>, "
        "<code>h4_macd</code>, <code>h4_macd_signal</code>, <code>h4_macd_hist</code>), volatilité H4 (<code>h4_atr_14</code>, "
        "<code>h4_atr_pct</code>, <code>h4_vol_20</code>, <code>h4_rel_volume_20</code>) et <b>latence causale macro</b> : "
        "<code>h4_age_hours</code> (nombre d'heures écoulées entre la clôture de la barre H4 disponible et l'instant de prédiction).",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>D. Indicateurs techniques sur l'échelle micro M15 (23 caractéristiques) :</b><br/>"
        "Capture de la microstructure intra-horaire : clôture M15 (<code>m15_close</code>), volume M15 (<code>m15_tick_volume</code>), "
        "rendements M15 (<code>m15_ret_1</code>, <code>m15_log_ret_1</code>), morphologie (<code>m15_body</code>, <code>m15_range</code>, "
        "<code>m15_upper_wick</code>, <code>m15_lower_wick</code>, <code>m15_body_ratio</code>, <code>m15_close_loc</code>), "
        "moyennes mobiles rapides (<code>m15_sma_20</code>, <code>m15_ema_20</code>, <code>m15_ema_50</code>, <code>m15_trend_ema</code>, "
        "<code>m15_close_vs_sma20</code>), oscillateurs rapides (<code>m15_rsi_14</code>, <code>m15_macd_hist</code>), "
        "volatilité rapide (<code>m15_atr_14</code>, <code>m15_atr_pct</code>, <code>m15_vol_20</code>, <code>m15_rel_volume_20</code>), "
        "comptage intra-horaire <code>m15_bars_in_h1</code> (validant qu'exactement 4 barres M15 composent la période H1) et "
        "<b>latence causale micro</b> <code>m15_age_minutes</code> (minutes écoulées depuis la dernière barre M15).",
        styles['Body']
    ))

    story.append(Paragraph("4.5 Formulation mathématique détaillée des indicateurs techniques", styles['SectionTitle']))
    story.append(Paragraph(
        "Afin de garantir une rigueur mathématique irréprochable et la reproductibilité totale des calculs, "
        "cette section détaille les équations différentielles discrètes et les formulations statistiques sous-jacentes aux indicateurs majeurs :",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>1. Moyennes Mobiles Simples (SMA) et Exponentielles (EMA) :</b><br/>"
        "La Moyenne Mobile Simple sur une fenêtre de $N$ périodes est la moyenne arithmétique non pondérée des cours passés :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;\\text{SMA}_N(t) = \\frac{1}{N} \\sum_{i=0}^{N-1} C_{t-i}</font><br/>"
        "La Moyenne Mobile Exponentielle applique un facteur de lissage géométrique $\\alpha = \\frac{2}{N + 1}$, pondérant davantage "
        "les observations récentes :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;\\text{EMA}_N(t) = \\alpha \\cdot C_t + (1 - \\alpha) \\cdot \\text{EMA}_N(t-1)</font><br/>"
        "Le pipeline implémente $\\text{SMA}_{20}$, $\\text{SMA}_{50}$, $\\text{SMA}_{200}$, $\\text{EMA}_{12}$, $\\text{EMA}_{20}$ et $\\text{EMA}_{50}$.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>2. True Range (TR) et Average True Range (ATR de Wilder) :</b><br/>"
        "Le True Range mesure la volatilité absolue non biaisée en intégrant les éventuels sauts de cotation (gaps) entre bougies consécutives :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;TR_t = \\max\\left(H_t - L_t, \\ |H_t - C_{t-1}|, \\ |L_t - C_{t-1}|\\right)</font><br/>"
        "L'indicateur $\\text{ATR}_{14}$ est ensuite obtenu par le lissage de Wilder (équivalent à une EMA avec $\\alpha = 1/14$) :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;\\text{ATR}_{14}(t) = \\frac{13 \\cdot \\text{ATR}_{14}(t-1) + TR_t}{14}</font><br/>"
        "Pour éliminer la dépendance au niveau absolu du prix de l'or (qui oscille entre 1 700 $ et plus de 2 600 $ l'once), "
        "le pipeline normalise cette volatilité sous forme d'un ratio sans dimension : <code>atr_pct = ATR_14 / Close</code>.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>3. Volatilité Historique Réalisée sur 20 Périodes ($\\text{Vol}_{20}$) :</b><br/>"
        "Mesure statistique de la dispersion des rendements horaires arithmétiques $R_t = \\frac{C_t - C_{t-1}}{C_{t-1}}$ sur une fenêtre glissante :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;\\text{Vol}_{20}(t) = \\sqrt{\\frac{1}{19} \\sum_{i=0}^{19} \\left(R_{t-i} - \\overline{R}_t\\right)^2}&nbsp;&nbsp;&nbsp;&nbsp;\\text{où}&nbsp;&nbsp;\\overline{R}_t = \\frac{1}{20} \\sum_{i=0}^{19} R_{t-i}</font><br/>"
        "Cette variable quantifie directement le régime de turbulence à court terme du marché.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>4. Volume Relatif à 20 Périodes ($\\text{RelVolume}_{20}$) :</b><br/>"
        "Défini comme le ratio entre le volume de ticks de la barre courante et sa moyenne mobile simple sur 20 périodes :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;\\text{RelVolume}_{20}(t) = \\frac{\\text{Volume}_t}{\\text{SMA}_{20}(\\text{Volume})(t)}</font><br/>"
        "Une valeur supérieure à 2.0 signale une anomalie d'activité institutionnelle ou la publication d'un événement macroéconomique majeur.",
        styles['Body']
    ))

    story.append(Paragraph("4.6 Prévention mathématique du Data Leakage par alignement causal", styles['SectionTitle']))
    story.append(Paragraph(
        "L'élimination formelle de toute contamination prospective constitue la signature scientifique fondamentale de cette architecture. "
        "Pour toute bougie H1 dont l'horodatage d'ouverture est noté $t_{\\text{start}}$, sa formation physique s'étend sur une heure entière. "
        "Son cours de clôture, son volume final et l'ensemble de ses indicateurs techniques ne sont connus et figés dans le monde réel "
        "qu'à l'instant exact de sa clôture :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;t_{\\text{disponibilité, H1}} = t_{\\text{start}} + 1\\text{h}</font><br/>"
        "Par conséquent, lors de la fusion d'informations issues des séries temporelles H4 et M15 à l'instant de décision "
        "$T = t_{\\text{disponibilité, H1}}$, la règle d'or causale impose que :<br/>"
        "<i>Aucune barre H4 ou M15 dont l'instant de clôture effective est strictement supérieur à $T$ ne peut être prise en compte.</i>",
        styles['Body']
    ))
    story.append(Paragraph(
        "Cette contrainte est appliquée dans le code (<code>backend/app/data/mtf_features.py</code>) par :<br/>"
        "1. L'attribution à chaque série d'un horodatage de disponibilité explicite : "
        "<code>available_at = timestamp + delta_timeframe</code>.<br/>"
        "2. L'exécution d'une jointure asynchrone rétrograde stricte via la méthode Pandas :<br/>"
        "<code>pd.merge_asof(h1_df, h4_df, on='available_at', direction='backward')</code>.<br/>"
        "3. La validation automatisée par assertion logique : vérification que "
        "<code>(h4_available_at &gt; h1_available_at).sum() == 0</code> et <code>(m15_available_at &gt; h1_available_at).sum() == 0</code>.<br/>"
        "4. L'interdiction absolue de toute fonction glissante centrée ou bilatérale. L'ensemble des moyennes et écarts-types "
        "est calculé exclusivement sur des fenêtres glissantes passées (<i>trailing windows</i>).",
        styles['Body']
    ))

    story.append(Paragraph("4.7 Synthèse de l'intégrité du jeu de données final", styles['SectionTitle']))
    story.append(Paragraph(
        "Le résultat de cette chaîne de traitement rigoureuse est consigné dans le jeu de données final "
        "<code>data/processed/ml/XAUUSD_features.csv</code> :<br/>"
        "• <b>Nombre d'observations exploitables</b> : 25 012 lignes chronologiques sans aucune valeur manquante (<i>NaN</i>) "
        "ni valeur infinie (<i>Inf</i>).<br/>"
        "• <b>Période couverte</b> : Du 01/07/2022 09:00:00 UTC au 18/09/2026 18:00:00 UTC.<br/>"
        "• <b>Empreinte cryptographique</b> : Le fichier de features généré est scellé par une empreinte SHA-256 tracée "
        "dans les audits de l'étape 3 et de l'étape 4, garantissant une reproductibilité numérique parfaite.",
        styles['Body']
    ))
    story.append(PageBreak())

    return story

