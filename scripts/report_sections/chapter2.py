"""Chapitre 2 — Analyse et Spécification des Besoins."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, BORDER_COLOR, HIGHLIGHT, LIGHT_BG

def get_chapter2_story(styles):
    story = []

    story.append(Paragraph("Chapitre 2 — Analyse et Spécification des Besoins", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("2.1 Typologie des acteurs et cas d'usage", styles['SectionTitle']))
    story.append(Paragraph(
        "L'ingénierie des exigences débute par l'identification exhaustive des entités humaines et logicielles appelées "
        "à interagir avec la plateforme. L'architecture distingue trois catégories d'acteurs :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>L'Analyste Quantitatif / Chercheur (Acteur Primaire)</b> : Utilisateur final de la plateforme. Il consulte "
        "l'application web via son navigateur pour observer le flux spot en continu, évaluer le biais directionnel binaire "
        "calculé par le moteur d'apprentissage, basculer entre l'horizon journalier (24H) et hebdomadaire (120H), "
        "analyser les contributions linéaires des 8 indicateurs les plus influents, et examiner les scénarios de marché "
        "avec leurs conditions formelles d'invalidation.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>L'Auditeur / Administrateur Système (Acteur Secondaire)</b> : Ingénieur chargé de superviser l'intégrité "
        "opérationnelle de l'infrastructure. Il interroge les endpoints de métrologie et de santé (<code>/api/health</code>, "
        "<code>/api/data-quality</code>), vérifie la persistance des métriques réelles (<code>/api/model-performance</code>) "
        "et s'assure du bon fonctionnement des workers d'arrière-plan.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>Le Fournisseur de Données Externe (Twelve Data — Acteur Système)</b> : Service cloud tiers fournissant l'accès "
        "aux marchés financiers mondiaux. Il alimente la plateforme via deux canaux complémentaires : un flux de cotations spot "
        "poussé en temps réel par socket sécurisé (WebSocket) et une interface REST permettant la collecte à la demande "
        "de séries historiques de bougies OHLCV fermées.",
        styles['Bullet']
    ))

    story.append(Paragraph("2.2 Spécification détaillée des besoins fonctionnels", styles['SectionTitle']))
    story.append(Paragraph(
        "Les exigences fonctionnelles traduisent les capacités opérationnelles que le système doit offrir à ses utilisateurs. "
        "Chaque exigence est identifiée de manière univoque :",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>BF-01 : Streaming des cotations spot en temps réel</b><br/>"
        "Le système doit maintenir une connexion WebSocket persistante avec le fournisseur Twelve Data "
        "(<code>wss://ws.twelvedata.com/v1/quotes/price</code>). Dès réception d'un événement de prix pour le symbole XAU/USD, "
        "le backend doit valider l'horodatage UTC, mettre à jour son cache interne de dernier cours (<i>ticker</i>) et redistribuer "
        "instantanément le tick à l'ensemble des navigateurs clients connectés via le point de terminaison <code>/api/ws/market</code>.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>BF-02 : Inférence directionnelle binaire (BULLISH / BEARISH)</b><br/>"
        "Le système doit exposer un service d'inférence statistique prédisant l'orientation future probable du cours. "
        "La prédiction doit appartenir strictement à l'ensemble binaire {<b>BULLISH</b>, <b>BEARISH</b>}. "
        "Le service doit obligatoirement calculer et restituer la distribution probabiliste complémentaire $P(\\text{BULLISH})$ "
        "et $P(\\text{BEARISH})$ vérifiant formellement $P(\\text{BULLISH}) + P(\\text{BEARISH}) = 1.0$, ainsi qu'un indice "
        "de confiance normalisé sur l'intervalle $[0, 1]$.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>BF-03 : Bascule dynamique d'horizon prévisionnel (Daily 24H vs Weekly 120H)</b><br/>"
        "L'utilisateur doit pouvoir basculer interactivement depuis l'interface entre deux échelles d'analyse distinctes : "
        "un horizon court terme journalier (Daily — 24 barres H1 fermées) et un horizon moyen terme hebdomadaire "
        "(Weekly — 120 barres H1 fermées). La sélection doit recharger instantanément les artefacts de modèle correspondants "
        "et actualiser les probabilités sans rechargement de page.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>BF-04 : Explicabilité causale des décisions (Top 8 Facteurs Linéaires)</b><br/>"
        "Pour chaque prédiction formulée, le système doit décomposer le logit de décision du modèle linéaire en contributions "
        "individuelles de features. Il doit extraire et ordonner les 8 caractéristiques ayant le plus fort impact absolu, "
        "en précisant pour chacune sa valeur brute, le sens de sa contribution (positive ou négative) et son rang d'importance.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>BF-05 : Génération contextuelle de scénarios de marché et conditions d'invalidation</b><br/>"
        "Le système doit synthétiser automatiquement trois scénarios opérationnels structurés (Scénario Base, Scénario Bullish, "
        "Scénario Bearish). Chaque scénario doit préciser ses hypothèses de maintien du prix (par exemple au-dessus ou en-dessous "
        "des moyennes mobiles SMA 20/50/200), son orientation directionnelle attendue et sa condition formelle d'invalidation technique.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>BF-06 : Visualisation graphique des séries historiques et indicateurs</b><br/>"
        "Le tableau de bord doit intégrer un graphique réactif traçant l'historique récent des bougies fermées H1 de l'or, "
        "avec indication visuelle du dernier cours spot et un panneau d'analyse technique détaillant les moyennes mobiles "
        "(SMA 20, 50, 200 ; EMA 12, 20, 50) et les oscillateurs (RSI 14, MACD, ATR 14).",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>BF-07 : Internationalisation trilingue (Anglais, Français, Arabe) avec support RTL</b><br/>"
        "L'interface web doit être intégralement traduisible à la volée entre trois langues : Anglais (EN), Français (FR) "
        "et Arabe (AR). Lors du basculement vers la langue arabe, l'agencement graphique doit s'inverser de manière bidirectionnelle "
        "(Right-to-Left — RTL), ajustant la disposition des grilles, des textes et des icônes conformément aux standards linguistiques.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>BF-08 : Télémétrie, métrologie et surveillance de la qualité des données</b><br/>"
        "Le système doit exposer des points de contrôle permettant de vérifier l'état opérationnel du serveur (<code>/api/health</code>), "
        "la fraîcheur des séries de bougies en base (<code>/api/data-quality</code>) et les performances historiques réelles persistées "
        "(<code>/api/model-performance</code>).",
        styles['Body']
    ))

    story.append(Paragraph("2.3 Exigences non fonctionnelles critiques", styles['SectionTitle']))
    story.append(Paragraph(
        "Les contraintes architecturales et exigences de qualité logicielle s'imposent avec une rigueur absolue :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>NF-01 : Étanchéité causale et absence absolue de Data Leakage (Priorité Critique Absolue)</b> :<br/>"
        "Il est formellement interdit qu'une caractéristique calculée pour une bougie fermée à l'instant $T$ incorpore la moindre "
        "information survenue après $T$. Tout indicateur centré ou bilatéral est prohibé. Les fusions multi-timeframes doivent "
        "s'effectuer strictement selon la règle $t_{\\text{contexte}} + \\Delta t \\le T$.",
        styles['BodyIndent']
    ))
    story.append(Paragraph(
        "• <b>NF-02 : Robustesse et refus de prédiction fictive (Fail-Safe Integrity)</b> :<br/>"
        "Le système s'interdit formellement de fabriquer des prédictions aléatoires ou de complaisance si les conditions requises "
        "ne sont pas réunies. Si les artefacts du modèle sont introuvables, si le jeu de caractéristiques est incomplet ou si les données "
        "sont périmées, le moteur doit basculer vers un statut explicite <code>MODEL_NOT_READY</code> ou <code>NO_DATA</code> "
        "assorti d'un message d'erreur documenté (code HTTP 503).",
        styles['BodyIndent']
    ))
    story.append(Paragraph(
        "• <b>NF-03 : Performance et latence d'exécution asynchrone</b> :<br/>"
        "Le traitement d'un tick de prix entrant et sa redistribution aux clients WebSocket connectés doit s'exécuter en moins "
        "de 20 millisecondes sur le serveur. Le temps de réponse d'une requête REST de calcul d'inférence prédictive complète "
        "ne doit pas excéder 200 millisecondes.",
        styles['BodyIndent']
    ))
    story.append(Paragraph(
        "• <b>NF-04 : Idempotence et intégrité de la persistance MongoDB</b> :<br/>"
        "Toutes les écritures de données de marché et de prédictions doivent être rigoureusement idempotentes. "
        "La base de données doit empêcher l'insertion de doublons grâce à des index uniques composés stricts.",
        styles['BodyIndent']
    ))
    story.append(Paragraph(
        "• <b>NF-05 : Portabilité et reproductibilité d'exécution</b> :<br/>"
        "L'ensemble du système doit être entièrement conteneurisable via Docker et Docker Compose, garantissant une exécution "
        "identique sur n'importe quel environnement Linux ou Windows.",
        styles['BodyIndent']
    ))

    story.append(Paragraph("2.4 Matrice de traçabilité des exigences", styles['SectionTitle']))
    story.append(Paragraph(
        "Le Tableau 2.1 détaille la traçabilité complète reliant chaque besoin fonctionnel au composant logiciel "
        "et aux fichiers sources réalisateurs audités dans le dépôt.",
        styles['Body']
    ))

    req_matrix = [
        [Paragraph("Code Exigence", styles['TableHeader']), Paragraph("Désignation du Besoin", styles['TableHeader']), Paragraph("Composant Réalisateur", styles['TableHeader']), Paragraph("Fichiers Sources Associés", styles['TableHeader'])],
        [Paragraph("<b>BF-01</b>", styles['TableText']), Paragraph("Flux temps réel WebSocket", styles['TableText']), Paragraph("LiveMarketService Singleton", styles['TableText']), Paragraph("<code>app/services/live_market.py</code><br/><code>app/api/routes/live_market.py</code>", styles['TableText'])],
        [Paragraph("<b>BF-02</b>", styles['TableText']), Paragraph("Inférence binaire BULLISH / BEARISH", styles['TableText']), Paragraph("ModelServingEngine (STEP 5)", styles['TableText']), Paragraph("<code>app/ml/step5_serving.py</code><br/><code>app/schemas/prediction.py</code>", styles['TableText'])],
        [Paragraph("<b>BF-03</b>", styles['TableText']), Paragraph("Double horizon Daily / Weekly", styles['TableText']), Paragraph("PredictionCard & Service", styles['TableText']), Paragraph("<code>frontend/components/PredictionCard.js</code><br/><code>models/xauusd/</code>, <code>xauusd_weekly/</code>", styles['TableText'])],
        [Paragraph("<b>BF-04</b>", styles['TableText']), Paragraph("Explicabilité (Top 8 features)", styles['TableText']), Paragraph("Linear Logit Decomposer", styles['TableText']), Paragraph("<code>app/services/predictions.py</code><br/><code>app/ml/step5_serving.py</code>", styles['TableText'])],
        [Paragraph("<b>BF-05</b>", styles['TableText']), Paragraph("Scénarios & conditions invalidation", styles['TableText']), Paragraph("ScenarioBuilder Engine", styles['TableText']), Paragraph("<code>app/services/predictions.py</code><br/><code>frontend/components/ScenarioPanel.js</code>", styles['TableText'])],
        [Paragraph("<b>BF-06</b>", styles['TableText']), Paragraph("Visualisation graphique & technique", styles['TableText']), Paragraph("SVG Chart & TechPanel", styles['TableText']), Paragraph("<code>frontend/components/PriceChart.js</code><br/><code>frontend/components/TechnicalPanel.js</code>", styles['TableText'])],
        [Paragraph("<b>BF-07</b>", styles['TableText']), Paragraph("Internationalisation EN/FR/AR & RTL", styles['TableText']), Paragraph("LanguageContext & Locales", styles['TableText']), Paragraph("<code>frontend/context/LanguageContext.js</code><br/><code>frontend/locales/{en,fr,ar}.json</code>", styles['TableText'])],
        [Paragraph("<b>BF-08</b>", styles['TableText']), Paragraph("Surveillance santé & métrologie", styles['TableText']), Paragraph("Health & Quality Routers", styles['TableText']), Paragraph("<code>app/api/routes/health.py</code><br/><code>app/api/routes/quality.py</code>", styles['TableText'])],
    ]
    t_req = Table(req_matrix, colWidths=[24 * mm, 50 * mm, 46 * mm, 52 * mm])
    t_req.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_req)
    story.append(Paragraph("Tableau 2.1 : Matrice de traçabilité des exigences fonctionnelles du système", styles['Caption']))

    story.append(Paragraph("2.5 Modélisation formelle des cas d'utilisation", styles['SectionTitle']))
    story.append(Paragraph(
        "La formalisation des cas d'utilisation permet de cartographier avec précision la frontière du système "
        "et les interactions avec les acteurs externes. Les cas d'utilisation sont modélisés dans le fichier PlantUML "
        "<code>docs/uml/use_cases.puml</code> :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Consulter le flux spot XAU/USD en direct</b> : L'analyste se connecte au tableau de bord. L'interface ouvre "
        "une connexion WebSocket avec le backend, qui transmet instantanément le dernier cours disponible puis diffuse en continu "
        "chaque variation de prix reçue de Twelve Data.",
        styles['Body']
    ))
    story.append(Paragraph(
        "2. <b>Obtenir le biais directionnel binaire (Cas d'utilisation central)</b> : L'analyste sélectionne l'horizon désiré "
        "(Daily ou Weekly). Le système interroge le point d'accès <code>/api/predictions/XAUUSD?horizon=...</code>, "
        "construit la matrice de 87 features causales à partir des dernières bougies fermées, exécute l'inférence via "
        "<code>ModelServingEngine</code>, et restitue le statut (BULLISH ou BEARISH), les probabilités étalonnées, l'indice de confiance, "
        "les 8 contributions explicatives et les 3 scénarios.",
        styles['Body']
    ))
    story.append(Paragraph(
        "3. <b>Changer la langue d'affichage et l'orientation textuelle</b> : L'analyste clique sur le sélecteur de langue. "
        "L'application met à jour le contexte global <code>LanguageContext</code>, persiste le choix dans le stockage local "
        "du navigateur et adapte dynamiquement la disposition en inversant l'interface si l'arabe (RTL) est sélectionné.",
        styles['Body']
    ))
    story.append(Paragraph(
        "4. <b>Superviser la santé de la plateforme et auditer les métriques</b> : L'auditeur système interroge les endpoints "
        "spécialisés pour examiner la latence du WebSocket Twelve Data, l'état de la connexion MongoDB et l'historique "
        "des métriques d'évaluation validées en holdout.",
        styles['Body']
    ))

    story.append(Paragraph("2.6 Règles de gestion et contraintes d'intégrité", styles['SectionTitle']))
    story.append(Paragraph(
        "Le fonctionnement opérationnel de la plateforme est encadré par des règles de gestion rigoureusement codifiées :<br/>"
        "• <b>RG-01 (Clôture temporelle stricte)</b> : Une bougie de période H1 débutant à l'instant $t$ n'est considérée comme valide "
        "et exploitable pour le calcul des indicateurs qu'après sa clôture effective à $t + 1\\text{h}$. Aucun indicateur prédictif "
        "n'est calculé sur une bougie en cours de formation.<br/>"
        "• <b>RG-02 (Somme unitaire des probabilités)</b> : Les probabilités restituées doivent satisfaire en tout point la contrainte "
        "$|P(\\text{BULLISH}) + P(\\text{BEARISH}) - 1.0| < 10^{-3}$, contrôlée par validation Pydantic (<code>probabilities_sum_to_one</code>).<br/>"
        "• <b>RG-03 (Neutralité exclue du modèle)</b> : Le système ne doit en aucun cas émettre une prédiction de classe neutre. "
        "L'espace de sortie est strictement binaire.<br/>"
        "• <b>RG-04 (Immutabilité des historiques nettoyés)</b> : Les fichiers bruts issus de LiteFinance demeurent strictement protégés "
        "en lecture seule. Aucune bougie de comblement n'est injectée lors des week-ends.",
        styles['Body']
    ))
    story.append(PageBreak())

    return story

