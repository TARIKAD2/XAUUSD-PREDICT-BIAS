"""Chapitre 1 — Contexte Général et Étude de l'Existant."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, BORDER_COLOR, HIGHLIGHT

def get_chapter1_story(styles):
    story = []

    story.append(Paragraph("Chapitre 1 — Contexte Général et Étude de l'Existant", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("1.1 Présentation approfondie du marché spot XAU/USD", styles['SectionTitle']))
    story.append(Paragraph(
        "L'or physique est négocié à l'échelle internationale selon deux modalités contractuelles prépondérantes : "
        "les contrats à terme standardisés (<i>Futures</i>), négociés sur des marchés organisés tels que le COMEX de New York, "
        "et le marché au comptant (<i>Spot</i>), régi par des transactions de gré à gré (<i>Over-The-Counter — OTC</i>). "
        "La paire <b>XAU/USD</b> représente l'échange immédiat d'une once troy d'or pur (0.995 au minimum) contre des dollars américains. "
        "Le marché spot de l'or est dominé par le marché de Londres (<i>London Bullion Market</i>), dont les standards de livraison "
        "sont administrés par la <i>London Bullion Market Association</i> (LBMA).",
        styles['Body']
    ))
    story.append(Paragraph(
        "Ce marché se distingue par une liquidité colossale, avec des volumes d'échange quotidiens moyens excédant fréquemment "
        "les 100 milliards de dollars américains. Contrairement aux marchés d'actions soumis à des horaires de négociation stricts "
        "et à des chambres de compensation centralisées, le marché de l'or spot opère de manière quasi ininterrompue du dimanche soir "
        "(22h00 UTC) au vendredi soir (21h00 UTC). Les cotations circulent sans discontinuer à travers les fuseaux horaires mondiaux, "
        "passant successivement de la session asiatique (Tokyo, Singapour, Hong Kong) à la session européenne (Londres, Zurich), "
        "puis à la session nord-américaine (New York, Chicago). Le pic d'activité et de volatilité intervient typiquement durant le chevauchement "
        "des sessions de Londres et de New York (entre 13h00 et 16h00 UTC), période où la profondeur du carnet d'ordres est la plus dense.",
        styles['Body']
    ))

    story.append(Paragraph("1.2 Microstructure et déterminants fondamentaux du cours", styles['SectionTitle']))
    story.append(Paragraph(
        "L'évolution du cours de l'once d'or ne répond pas aux modèles traditionnels d'actualisation des flux de trésorerie "
        "(tels que le modèle de Gordon-Shapiro pour les actions ou l'actualisation des coupons pour les obligations), car l'or "
        "ne génère aucun rendement intrinsèque (il ne verse ni dividende, ni coupon d'intérêt). Il induit au contraire des coûts de stockage, "
        "d'assurance et d'opportunité. Par conséquent, sa dynamique de prix est gouvernée par des forces macro-économiques spécifiques :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Les taux d'intérêt réels souverains (TIPS)</b> : Le coût d'opportunité de la détention d'or est mesuré par le rendement "
        "des obligations d'État protégées contre l'inflation à 10 ans émises par les États-Unis. Lorsque les taux réels augmentent, "
        "les investisseurs arbitrent en faveur d'actifs portant intérêt, exerçant une pression baissière sur le cours du métal jaune. "
        "Inversement, des taux réels nuls ou négatifs rendent la détention d'or particulièrement attractive.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>L'indice du dollar américain (DXY)</b> : L'or étant libellé en dollars américains sur le marché spot mondial, "
        "il existe une corrélation empirique négative structurelle entre le cours XAU/USD et la valeur relative du billet vert. "
        "Une dépréciation du dollar rend l'or moins coûteux pour les investisseurs détenant d'autres devises fiduciaires (euro, yen, livre sterling), "
        "stimulant la demande globale et propulsant les cours à la hausse.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>La demande des banques centrales et réserves de change</b> : Depuis la crise financière de 2008 et l'intensification "
        "des sanctions financières internationales, les banques centrales des pays émergents (notamment la Chine, la Russie, l'Inde et la Turquie) "
        "ont opéré une dédollarisation progressive de leurs réserves, accumulant des centaines de tonnes d'or physique chaque trimestre.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>La prime d'aversion au risque et tensions géopolitiques</b> : En tant qu'ultime réserve de valeur historique, l'or réagit "
        "immédiatement et violemment aux escalades militaires, crises bancaires systémiques et menaces de stagflation, absorbant "
        "les flux de fuite vers la qualité (<i>flight to safety</i>).",
        styles['Bullet']
    ))

    story.append(Paragraph("1.3 Propriétés statistiques des séries temporelles financières", styles['SectionTitle']))
    story.append(Paragraph(
        "Sur le plan de l'économétrie et de la modélisation statistique, les cours de marché financiers s'écartent radicalement "
        "des hypothèses simplificatrices de la théorie classique (loi normale des variations et indépendance des réalisations). "
        "Une analyse quantitative rigoureuse de la paire XAU/USD doit impérativement composer avec les « faits stylisés » universels "
        "mis en évidence par la littérature empirique (Cont, 2001) :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Non-stationnarité des séries brutes de prix</b> : La trajectoire brute des cours $C_t$ présente une racine unitaire "
        "(processus $I(1)$), oscillant de façon erratique sous l'effet de tendances séculaires. Modéliser directement les prix bruts "
        "conduit à des régressions fallacieuses (<i>spurious regressions</i>). Il est indispensable de transformer les séries en rendements "
        "arithmétiques $R_t = (C_t / C_{t-1}) - 1$ ou logarithmiques $r_t = \\ln(C_t / C_{t-1})$ pour stationnariser l'espérance mathématique.",
        styles['Body']
    ))
    story.append(Paragraph(
        "2. <b>Distribution leptokurtique à queues épaisses (Fat Tails)</b> : La distribution empirique des rendements de l'or présente "
        "un kurtosis nettement supérieur à 3 (l'étalon de la loi gaussienne). Les variations extrêmes (variations journalières supérieures "
        "à 3 ou 4 écarts-types) surviennent avec une fréquence statistique infiniment supérieure aux prédictions d'un modèle normal, "
        "rendant les estimateurs statistiques classiques basés sur les moindres carrés ordinaires très vulnérables aux valeurs atypiques.",
        styles['Body']
    ))
    story.append(Paragraph(
        "3. <b>Agglomération de volatilité (Volatility Clustering)</b> : Bien que les rendements journaliers ne présentent qu'une très faible "
        "autocorrélation linéaire directe, les rendements absolus $|R_t|$ ou quadratiques $R_t^2$ affichent une autocorrélation positive "
        "significative et durable dans le temps. Des phases de calme plat succèdent à des périodes d'extrême turbulence, "
        "témoignant d'une hétéroscédasticité conditionnelle marquée.",
        styles['Body']
    ))
    story.append(Paragraph(
        "4. <b>Rapport signal sur bruit extrêmement faible</b> : Sur les horizons temporels courts et intermédiaires (de 1 heure à 5 jours), "
        "l'information exploitable ne représente qu'une fraction marginale (souvent inférieure à 5% de la variance totale) face au bruit "
        "engendré par les transactions de microstructure, l'impact des carnets d'ordres et les flux de liquidité discrétionnaires.",
        styles['Body']
    ))

    story.append(Paragraph("1.4 Étude critique des solutions et outils existants", styles['SectionTitle']))
    story.append(Paragraph(
        "L'examen attentif du paysage logiciel contemporain dédié à l'analyse du marché de l'or permet de distinguer "
        "trois approches technologiques distinctes, chacune présentant des vertus techniques mais également des angles morts majeurs :",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>A. Plateformes graphiques d'analyse technique (TradingView, MetaTrader 5, cTrader) :</b><br/>"
        "Ces solutions constituent le standard d'usage des opérateurs de marché individuels et institutionnels. Elles offrent des moteurs "
        "de rendu graphique vectoriels ultra-performants, une connectivité native avec les courtiers et des langages de script dédiés "
        "(Pine Script, MQL5). Toutefois, leur faiblesse réside dans leur subjectivité fondamentale : l'analyse repose entièrement "
        "sur des tracés géométriques manuels (lignes de tendance, figures chartistes, zones de support/résistance) ou sur des indicateurs "
        "techniques isolés, laissant le décideur à la merci de ses biais cognitifs (biais de confirmation, ancrage psychologique). "
        "De plus, les fonctionnalités de Machine Learning y sont restreintes et s'exécutent généralement dans des bacs à sable "
        "propriétaires fermés et non reproductibles.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>B. Plateformes commerciales de signaux et algorithmes propriétaires fermés :</b><br/>"
        "Une multitude de services en ligne et de robots de trading prétendent fournir des prédictions directionnelles à haute fiabilité. "
        "Ces systèmes souffrent d'une opacité quasi totale (effet boîte noire) : le code source, la sélection des hyperparamètres, "
        "les données d'entraînement et les méthodes de validation ne sont jamais publiés. Plus grave encore, la plupart dissimulent "
        "leurs métriques d'erreur réelles et recourent à des méthodes d'évaluation méthodologiquement corrompues "
        "(test sur les données d'apprentissage, absence d'embargo, ajustement a posteriori des règles d'invalidation).",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>C. Écosystèmes et bibliothèques de recherche quantitative (Backtrader, Zipline, QSTrader, VectorBT) :</b><br/>"
        "Ces frameworks en langage Python constituent d'excellents environnements d'expérimentation pour les chercheurs et quants. "
        "Ils permettent de tester des hypothèses statistiques et d'exécuter des backtests événementiels. Néanmoins, ils sont conçus "
        "pour une utilisation en ligne de commande ou dans des notebooks Jupyter hors-ligne. Ils ne disposent pas d'interfaces utilisateurs "
        "modernes accessibles, n'intègrent pas d'architectures de streaming WebSocket bidirectionnel temps réel et ne fournissent pas "
        "de mécanismes natifs de serving d'inférence sécurisés pour la production.",
        styles['Body']
    ))

    story.append(Paragraph("1.5 Limites méthodologiques observées dans la pratique", styles['SectionTitle']))
    story.append(Paragraph(
        "L'analyse critique des implémentations de Machine Learning appliquées aux séries financières révèle quatre pièges "
        "méthodologiques récurrents que ce projet s'est formellement engagé à éradiquer :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>La contamination prospective (Lookahead Bias / Data Leakage)</b> : La normalisation standard d'un jeu de données "
        "sur l'intégralité de l'échantillon (calcul d'une moyenne ou d'un écart-type global incluant le futur), l'emploi de moyennes mobiles "
        "centrées ou la jointure naïve d'horodatages futurs contaminent le présent avec l'avenir. Le modèle apprend alors à 'tricher', "
        "affichant des performances exceptionnelles en laboratoire mais s'effondrant dès le premier tick réel.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>Le mélange aléatoire des observations (Shuffle Leakage)</b> : Appliquer une validation croisée aléatoire de type K-Fold "
        "sur une série temporelle viole le principe fondamental de causalité. Les points de validation se retrouvent intercalés "
        "entre des points d'apprentissage, permettant au modèle de mémoriser la trajectoire temporelle globale plutôt que d'apprendre "
        "une dynamique prédictive.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>L'absence d'étalonnage probabiliste et de zone morte</b> : Prétendre prédire une direction sur 100% des barres temporelles, "
        "y compris lorsque le marché traverse des phases de micro-fluctuation erratique inférieures au coût du spread, introduit "
        "un volume massif d'exemples bruités qui déstabilisent l'apprentissage.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>Le surapprentissage des modèles non linéaires complexes</b> : Déployer des modèles arborescents ultra-complexes ou des réseaux "
        "de neurones profonds sans pénalisation adéquate sur des séries à faible rapport signal/bruit conduit immanquablement "
        "à modéliser le bruit idiosyncratique de l'échantillon historique plutôt que la structure sous-jacente.",
        styles['Bullet']
    ))

    story.append(Paragraph("1.6 Solution proposée : Architecture d'intelligence quantitative", styles['SectionTitle']))
    story.append(Paragraph(
        "Face à ces constats, la solution développée au sein du projet <b>AI Market Intelligence (AI_XAUUSD)</b> s'affirme "
        "comme une plateforme de recherche et d'aide à la décision empirique, transparente et auditée. "
        "Ses piliers fondamentaux s'articulent autour de :<br/>"
        "1. <b>Une intégrité causale absolue</b> : Construction d'un jeu de données de 87 caractéristiques techniques multi-timeframes "
        "(M15, H1, H4) assemblées par jointure rétrograde (<code>merge_asof</code> backward), certifiant l'absence totale de fuite prospective.<br/>"
        "2. <b>Une modélisation binaire honnête</b> : Définition stricte de deux classes directionnelles (<b>BULLISH</b> / <b>BEARISH</b>), "
        "avec élimination systématique de la zone morte d'indécision à l'entraînement, et publication intégrale des métriques réelles.<br/>"
        "3. <b>Un protocole de test sans concession</b> : Validation temporelle walk-forward expansive sur 4 plis avec embargo de 24 barres.<br/>"
        "4. <b>Une stack technologique réactive moderne</b> : Backend asynchrone FastAPI, courtier WebSocket Singleton Twelve Data, "
        "persistance MongoDB avec index uniques composés, et interface web réactive Next.js 15 supportant l'arabe avec typographie RTL native.",
        styles['Body']
    ))

    story.append(Paragraph("1.7 Comparatif fonctionnel exhaustif", styles['SectionTitle']))
    story.append(Paragraph(
        "Le Tableau 1.1 dresse une comparaison systématique entre la solution proposée et les approches préexistantes du marché.",
        styles['Body']
    ))

    comp_data = [
        [Paragraph("Dimension / Critère", styles['TableHeader']), Paragraph("Outils Graphiques (MT5 / TradingView)", styles['TableHeader']), Paragraph("Systèmes Boîte Noire Commerciaux", styles['TableHeader']), Paragraph("AI Market Intelligence (Ce Projet)", styles['TableHeader'])],
        [Paragraph("<b>Flux de cotation</b>", styles['TableText']), Paragraph("Temps réel propriétaire courtier", styles['TableText']), Paragraph("Alertes différées ou opaques", styles['TableText']), Paragraph("<b>Temps réel WebSocket Twelve Data</b>", styles['TableText'])],
        [Paragraph("<b>Espace de décision</b>", styles['TableText']), Paragraph("Non applicable (Discrétionnaire)", styles['TableText']), Paragraph("Multiples classes non calibrées", styles['TableText']), Paragraph("<b>Classification binaire stricte (BULLISH/BEARISH)</b>", styles['TableText'])],
        [Paragraph("<b>Traitement de l'indécision</b>", styles['TableText']), Paragraph("Subjectif (Observation chartiste)", styles['TableText']), Paragraph("Arbitraire / Non explicité", styles['TableText']), Paragraph("<b>Zone morte filtrée mathématiquement</b>", styles['TableText'])],
        [Paragraph("<b>Garantie de non-fuite (Data Leakage)</b>", styles['TableText']), Paragraph("Non applicable", styles['TableText']), Paragraph("Non documentée / Biaisée", styles['TableText']), Paragraph("<b>Prouvée formellement (as-of backward)</b>", styles['TableText'])],
        [Paragraph("<b>Validation temporelle</b>", styles['TableText']), Paragraph("Backtests simples statiques", styles['TableText']), Paragraph("K-Fold aléatoire ou occulté", styles['TableText']), Paragraph("<b>Walk-Forward expansif (4 plis + embargo)</b>", styles['TableText'])],
        [Paragraph("<b>Transparence des métriques</b>", styles['TableText']), Paragraph("Non applicable", styles['TableText']), Paragraph("Embellies / Taux irréalistes", styles['TableText']), Paragraph("<b>Publication intégrale des métriques mesurées</b>", styles['TableText'])],
        [Paragraph("<b>Explicabilité causale</b>", styles['TableText']), Paragraph("Tracés manuels subjectifs", styles['TableText']), Paragraph("Nulle (Boîte noire)", styles['TableText']), Paragraph("<b>Top 8 contributions linéaires signées</b>", styles['TableText'])],
        [Paragraph("<b>Support multilingue étendu</b>", styles['TableText']), Paragraph("Interface standard traduite", styles['TableText']), Paragraph("Unilingue anglais généralement", styles['TableText']), Paragraph("<b>Trilingue natif (EN / FR / AR avec RTL)</b>", styles['TableText'])],
        [Paragraph("<b>Licence et ouverture</b>", styles['TableText']), Paragraph("Propriétaire fermé", styles['TableText']), Paragraph("Commercial fermé", styles['TableText']), Paragraph("<b>Code auditable et documenté</b>", styles['TableText'])],
    ]
    t_comp = Table(comp_data, colWidths=[38 * mm, 40 * mm, 42 * mm, 50 * mm])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_comp)
    story.append(Paragraph("Tableau 1.1 : Comparatif fonctionnel et méthodologique des solutions d'analyse de marché", styles['Caption']))
    story.append(PageBreak())

    return story

