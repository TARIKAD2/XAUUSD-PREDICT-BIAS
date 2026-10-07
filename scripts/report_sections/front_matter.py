"""Pages préliminaires du rapport PFA : Page de garde, Dédicace, Remerciements, Résumé, Abstract, TOC, Listes."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, ACCENT, HIGHLIGHT, BORDER_COLOR, LIGHT_BG

def get_front_matter_story(styles):
    story = []

    # =========================================================================
    # 1. PAGE DE GARDE OFFICIELLE
    # =========================================================================
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("RÉPUBLIQUE ALGÉRIENNE DÉMOCRATIQUE ET POPULAIRE", styles['CoverInstitution']))
    story.append(Paragraph("MINISTÈRE DE L'ENSEIGNEMENT SUPÉRIEUR ET DE LA RECHERCHE SCIENTIFIQUE", styles['CoverInstitution']))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("FACULTÉ DES SCIENCES ET TECHNOLOGIES — DÉPARTEMENT D'INFORMATIQUE", styles['CoverSubInstitution']))
    story.append(Spacer(1, 12 * mm))

    story.append(Paragraph("MÉMOIRE DE PROJET DE FIN D'ANNÉE (PFA)", styles['CoverType']))
    story.append(Paragraph("Pour l'obtention du Diplôme d'Ingénieur d'État en Informatique", styles['CoverSubInstitution']))
    story.append(Paragraph("Option : Systèmes Intelligents & Science des Données", styles['CoverSubInstitution']))
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("CONCEPTION ET RÉALISATION D'UNE PLATEFORME D'INTELLIGENCE QUANTITATIVE ET D'AIDE À LA DÉCISION POUR LE MARCHÉ DE L'OR (XAU/USD)", styles['CoverTitle']))
    story.append(Paragraph("Architecture Asynchrone Full-Stack (FastAPI & Next.js), Inférence Directionnelle Binaire (BULLISH / BEARISH) et Évaluation Empirique Walk-Forward", styles['CoverSubtitle']))
    story.append(Spacer(1, 12 * mm))

    meta_table = [
        [
            Paragraph("<b>Présenté par :</b><br/>Étudiant Ingénieur en Informatique", styles['CoverMeta']),
            Paragraph("<b>Devant le jury composé de :</b><br/>Président du Jury : Professeur d'Enseignement Supérieur", styles['CoverMeta'])
        ],
        [
            Paragraph("<b>Sous la direction de :</b><br/>Encadrant Pédagogique & Technique", styles['CoverMeta']),
            Paragraph("Examinateur 1 : Maître de Conférences<br/>Examinateur 2 : Maître de Conférences", styles['CoverMeta'])
        ]
    ]
    t_meta = Table(meta_table, colWidths=[85 * mm, 85 * mm])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_meta)

    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph("Année Universitaire : 2025 / 2026", styles['CoverYear']))
    story.append(PageBreak())

    # =========================================================================
    # 2. DÉDICACE
    # =========================================================================
    story.append(Paragraph("Dédicace", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=15))

    story.append(Spacer(1, 15 * mm))
    story.append(Paragraph(
        "<i>À mes très chers parents,<br/>"
        "Aucun mot, aucune dédicace ne saurait exprimer mon éternelle reconnaissance et mon profond amour. "
        "Pour vos prières silencieuses, votre patience inébranlable et les innombrables sacrifices consentis "
        "pour illuminer mon chemin vers le savoir. Que ce modeste travail soit le fruit de vos bénédictions.</i>",
        styles['BodyIndent']
    ))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "<i>À mes frères et sœurs,<br/>"
        "Pour votre soutien constant, vos encouragements chaleureux et la complicité fraternelle "
        "qui m'a procuré force et équilibre tout au long de mes années d'études.</i>",
        styles['BodyIndent']
    ))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "<i>À tous mes enseignants et mentors académiques,<br/>"
        "Qui m'ont transmis la passion de l'informatique, le goût de l'effort intellectuel "
        "et la rigueur méthodologique sans laquelle aucune recherche digne de ce nom ne saurait exister.</i>",
        styles['BodyIndent']
    ))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "<i>À mes fidèles amis et camarades de promotion,<br/>"
        "Avec qui j'ai partagé des moments d'apprentissage inoubliables, des débats scientifiques passionnés "
        "et une fraternité sincère.</i>",
        styles['BodyIndent']
    ))
    story.append(PageBreak())

    # =========================================================================
    # 3. REMERCIEMENTS
    # =========================================================================
    story.append(Paragraph("Remerciements", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=15))

    story.append(Paragraph(
        "Au terme de la réalisation de ce mémoire de Projet de Fin d'Année, il m'est particulièrement agréable "
        "d'exprimer ma gratitude et mes vifs remerciements à l'ensemble des personnes qui m'ont accompagné "
        "et soutenu tout au long de ce projet d'ingénierie et de recherche.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Mes remerciements les plus sincères s'adressent en premier lieu à mon encadrant pédagogique "
        "pour la qualité exceptionnelle de son suivi, sa disponibilité constante, ses précieux conseils "
        "et ses exigences de rigueur scientifique qui ont grandement enrichi ce travail.",
        styles['Body']
    ))
    story.append(Paragraph(
        "J'exprime ma profonde gratitude aux membres du jury d'avoir accepté d'examiner et de juger ce projet. "
        "Leur regard critique, leurs observations constructives et leur expertise technique constituent une étape "
        "cruciale dans la validation académique de cette plateforme.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Je tiens également à remercier l'ensemble des professeurs et intervenants du Département d'Informatique "
        "pour les solides connaissances théoriques et pratiques transmises au cours de mon cycle de formation.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Enfin, je remercie chaleureusement toute personne ayant contribué de près ou de loin, par une discussion technique, "
        "une relecture attentive ou un encouragement moral, à l'aboutissement de ce projet.",
        styles['Body']
    ))
    story.append(PageBreak())

    # =========================================================================
    # 4. RÉSUMÉ & ABSTRACT
    # =========================================================================
    story.append(Paragraph("Résumé", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "Ce mémoire de Projet de Fin d'Année documente la conception, l'ingénierie logicielle et l'évaluation "
        "expérimentale d'une plateforme modulaire d'intelligence quantitative dédiée au marché de l'or au comptant contre "
        "dollar américain (XAU/USD). "
        "Face aux spécificités intrinsèques des séries temporelles financières — non-stationnarité, rapport signal/bruit "
        "extrêmement réduit, dynamique de volatilité changeante —, la plateforme implémente une chaîne d'ingénierie "
        "de 87 caractéristiques techniques multi-échelles temporelles (M15, H1, H4). "
        "Une stricte étanchéité causale est garantie par un alignement asynchrone rétrograde (<i>backward as-of join</i>) "
        "éliminant toute fuite d'information prospective (<i>data leakage</i>).<br/>"
        "La tâche prédictive est modélisée sous la forme d'une classification binaire stricte opposant deux régimes : "
        "<b>BULLISH</b> et <b>BEARISH</b>. Aucune classe neutre n'est intégrée dans l'espace de décision : "
        "les observations situées dans une zone morte d'amplitude inférieure à un seuil paramétrique (0.5% en 24H, 1.0% en 120H) "
        "sont systématiquement filtrées lors de la préparation du jeu d'apprentissage. "
        "L'évaluation empirique repose sur un protocole <i>walk-forward</i> expansif à 4 plis avec période d'embargo. "
        "Sur l'échantillon de test final hors-échantillon, la Régression Logistique pénalisée surpasse les modèles d'arbres "
        "ensemblistes (Random Forest, LightGBM) disqualifiés en raison d'un surapprentissage massif et d'effondrements de classes, "
        "obtenant une justesse (accuracy) de 45.71% à 24 heures et de 39.20% à 120 heures (inférieures à leurs baselines majoritaires respectives). "
        "L'infrastructure articule un backend asynchrone FastAPI, un flux continu WebSocket connecté à Twelve Data, "
        "une persistance MongoDB et une interface terminal réactive Next.js supportant l'internationalisation trilingue (EN/FR/AR).",
        styles['Body']
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "<b>Mots-clés :</b> Marché spot XAU/USD, Apprentissage Automatique, Classification Binaire, "
        "Walk-Forward Validation, Prévention du Data Leakage, Inférence Causale, FastAPI, WebSocket, Next.js, Explicabilité Linéaire.",
        styles['Callout']
    ))
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Abstract", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "This engineering thesis presents the architectural design, software development, and empirical assessment "
        "of a modular quantitative intelligence and decision-support web platform dedicated to the Gold versus US Dollar "
        "(XAU/USD) spot market. "
        "Addressing the core challenges of financial econometrics — non-stationarity, low signal-to-noise ratio, and heteroskedasticity —, "
        "the architecture establishes a causal feature engineering pipeline generating 87 technical features across M15, H1, "
        "and H4 timeframes. Strict mathematical causal ordering is enforced via backward as-of alignment, completely preventing lookahead data leakage.<br/>"
        "Market directional forecasting is formulated as a strict binary classification problem between two exclusive regimes: "
        "<b>BULLISH</b> and <b>BEARISH</b>. No neutral prediction class exists: variations within a threshold deadband (0.5% for 24H, "
        "1.0% for 120H) are deliberately filtered out during dataset synthesis. "
        "Under an expanding walk-forward validation protocol with embargo across 4 folds, penalized Logistic Regression "
        "demonstrates superior generalization stability over tree-based ensembles (Random Forest, LightGBM) that suffer from severe overfitting "
        "and class collapse. Out-of-sample holdout evaluation yields an accuracy of 45.71% (24H horizon) and 39.20% (120H horizon), "
        "both falling below their respective majority class baselines. "
        "The production stack combines an asynchronous FastAPI backend, a resilient Twelve Data WebSocket streaming engine, "
        "MongoDB persistence schemas, and an interactive Next.js dashboard featuring complete trilingual internationalization (EN/FR/AR) with native RTL support.",
        styles['Body']
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "<b>Keywords:</b> XAU/USD Spot Market, Machine Learning, Binary Classification, Walk-Forward Validation, "
        "Lookahead Leakage Prevention, FastAPI, WebSocket Streaming, Next.js, Linear Logit Explainability.",
        styles['Callout']
    ))
    story.append(PageBreak())

    # =========================================================================
    # 5. TABLE DES MATIÈRES DÉTAILLÉE
    # =========================================================================
    story.append(Paragraph("Table des Matières", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    toc_elements = [
        ("Dédicace", "ii", True),
        ("Remerciements", "iii", True),
        ("Résumé & Abstract", "iv", True),
        ("Table des Matières", "vi", True),
        ("Liste des Figures & Tableaux", "viii", True),
        ("Liste des Abréviations", "ix", True),
        ("Introduction Générale", "9", True),
        ("1. Contexte macroéconomique et monétaire de l'or", "9", False),
        ("2. Dynamique du marché spot XAU/USD et microstructure", "9", False),
        ("3. Problématique scientifique et technique", "10", False),
        ("4. Motivation de la recherche empirique", "10", False),
        ("5. Objectifs opérationnels et scientifiques", "11", False),
        ("6. Méthodologie scientifique adoptée", "11", False),
        ("7. Organisation détaillée du mémoire", "11", False),
        ("Chapitre 1 — Contexte Général et Étude de l'Existant", "12", True),
        ("1.1 Présentation approfondie du marché spot XAU/USD", "12", False),
        ("1.2 Microstructure et déterminants fondamentaux du cours", "12", False),
        ("1.3 Propriétés statistiques des séries temporelles de prix", "13", False),
        ("1.4 Étude critique des solutions et outils existants", "13", False),
        ("1.5 Limites méthodologiques observées dans la pratique", "14", False),
        ("1.6 Solution proposée : Architecture d'intelligence quantitative", "15", False),
        ("1.7 Comparatif fonctionnel exhaustif", "15", False),
        ("Chapitre 2 — Analyse et Spécification des Besoins", "16", True),
        ("2.1 Typologie des acteurs et cas d'usage", "16", False),
        ("2.2 Spécification détaillée des besoins fonctionnels (BF-01 à BF-08)", "16", False),
        ("2.3 Exigences non fonctionnelles critiques", "17", False),
        ("2.4 Matrice de traçabilité des exigences", "17", False),
        ("2.5 Modélisation formelle des cas d'utilisation (PlantUML)", "18", False),
        ("2.6 Règles de gestion et contraintes d'intégrité", "18", False),
        ("Chapitre 3 — Analyse et Conception Système", "19", True),
        ("3.1 Architecture globale en couches micro-services", "19", False),
        ("3.2 Conception logicielle Backend FastAPI", "19", False),
        ("3.3 Architecture réactive Frontend Next.js 15", "20", False),
        ("3.4 Modélisation de la persistance et schémas MongoDB", "20", False),
        ("3.5 Stratégie d'indexation unique et optimisation", "21", False),
        ("3.6 Conception des flux de communication (WebSocket & REST)", "21", False),
        ("3.7 Diagrammes d'architecture, de séquence et de données", "21", False),
        ("Chapitre 4 — Acquisition et Préparation des Données de Marché", "22", True),
        ("4.1 Collecte des données historiques LiteFinance", "22", False),
        ("4.2 Ingestion temps réel Twelve Data REST et WebSocket", "22", False),
        ("4.3 Protocole de nettoyage, validation et audit d'intégrité (Étape 1)", "22", False),
        ("4.4 Ingénierie des caractéristiques : Décomposition des 87 features MTF", "23", False),
        ("4.5 Formulation mathématique détaillée des indicateurs techniques", "24", False),
        ("4.6 Prévention mathématique du Data Leakage par alignement causal", "25", False),
        ("4.7 Synthèse de l'intégrité du jeu de données final", "25", False),
        ("Chapitre 5 — Machine Learning et Prédiction Directionnelle", "26", True),
        ("5.1 Formalisation mathématique de la cible binaire (BULLISH vs BEARISH)", "26", False),
        ("5.2 Filtrage de la zone morte et justification de l'espace binaire", "26", False),
        ("5.3 Algorithmes benchmarkés et protocole Walk-Forward expansif", "27", False),
        ("5.4 Analyse comparative détaillée des plis et sélection du modèle", "27", False),
        ("5.5 Analyse exhaustive des métriques réelles hors-échantillon", "28", False),
        ("5.6 Modélisation de la confiance et scénarios probabilistes", "30", False),
        ("5.7 Explicabilité causale : Coefficients logit linéaires et SHAP", "30", False),
        ("Chapitre 6 — Réalisation et Développement Applicatif", "31", True),
        ("6.1 Implémentation du backend FastAPI et cycle de vie lifespan", "31", False),
        ("6.2 Gestionnaire temps réel WebSocket singleton et distribution", "31", False),
        ("6.3 Développement du frontend Next.js 15 et Dashboard Terminal", "32", False),
        ("6.4 Composants d'interface, bascule d'horizon et visualisation", "32", False),
        ("6.5 Internationalisation trilingue (EN / FR / AR) et support RTL", "32", False),
        ("Chapitre 7 — Tests, Validation et Assurance Qualité", "33", True),
        ("7.1 Stratégie globale de test et suite automatisée Pytest (117 tests)", "33", False),
        ("7.2 Tests d'étanchéité temporelle et d'absence de fuite prospective", "34", False),
        ("7.3 Validation de l'ingestion WebSocket et résilience d'API", "34", False),
        ("7.4 Audit des tests frontend et statut des captures d'écran", "34", False),
        ("Chapitre 8 — Déploiement et DevOps", "35", True),
        ("8.1 Conteneurisation Docker multi-services", "35", False),
        ("8.2 Orchestration locale Docker Compose et healthchecks", "35", False),
        ("8.3 Configuration de déploiement cloud (Railway & Vercel)", "36", False),
        ("8.4 Intégration MongoDB Atlas et gestion des environnements", "36", False),
        ("8.5 Variables d'environnement et matrice de déploiement", "37", False),
        ("Chapitre 9 — Discussion Critique, Limites et Perspectives", "38", True),
        ("9.1 Synthèse critique des performances ML et confrontation théorique", "38", False),
        ("9.2 Analyse approfondie du biais haussier du modèle", "39", False),
        ("9.3 Limites techniques et contraintes d'infrastructure", "39", False),
        ("9.4 Perspectives de recherche future et pistes d'évolution", "39", False),
        ("Conclusion Générale", "40", True),
        ("Bibliographie et Webographie", "41", True),
        ("Annexes Exhaustives", "43", True),
        ("Annexe A : Code source des 8 diagrammes PlantUML", "43", False),
        ("Annexe B : Spécification exhaustive des points de terminaison d'API", "46", False),
        ("Annexe C : Extraits de code sources fondamentaux du dépôt", "47", False),
        ("Annexe D : Inventaire complet des 87 caractéristiques techniques", "49", False),
    ]

    t_data = []
    for title, page, is_major in toc_elements:
        if is_major:
            p_title = Paragraph(f"<b>{title}</b>", styles['TOCItem'])
            p_page = Paragraph(f"<b>{page}</b>", styles['TOCPage'])
        else:
            p_title = Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{title}", styles['TOCItem'])
            p_page = Paragraph(f"{page}", styles['TOCPage'])
        t_data.append([p_title, p_page])

    t_toc = Table(t_data, colWidths=[150 * mm, 20 * mm])
    t_toc.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    # =========================================================================
    # 6. LISTE DES FIGURES ET LISTE DES TABLEAUX
    # =========================================================================
    story.append(Paragraph("Liste des Figures", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    fig_items = [
        ("Figure 1.1 : Structure globale du marché spot mondial de l'or de gré à gré (OTC)", "8"),
        ("Figure 2.1 : Diagramme des cas d'utilisation du système (PlantUML use_cases.puml)", "26"),
        ("Figure 3.1 : Diagramme d'architecture modulaire multi-couches (architecture.puml)", "30"),
        ("Figure 3.2 : Diagramme de séquence du calcul et service d'inférence (sequence_prediction.puml)", "39"),
        ("Figure 3.3 : Diagramme de séquence de diffusion de ticks réactifs WebSocket (sequence_websocket.puml)", "41"),
        ("Figure 3.4 : Diagramme entité-relation des collections MongoDB (database.puml)", "42"),
        ("Figure 4.1 : Diagramme d'activité de la chaîne de préparation de données (data_flow.puml)", "46"),
        ("Figure 4.2 : Principe d'alignement causal temporel rétrograde (backward as-of merge)", "55"),
        ("Figure 5.1 : Découpage walk-forward expansif à 4 plis avec embargo temporel", "62"),
        ("Figure 5.2 : Matrice de confusion réelle du modèle Daily sur test holdout", "70"),
        ("Figure 5.3 : Pipeline d'inférence, de scoring de confiance et de dérivation de scénarios", "72"),
        ("Figure 6.1 : Arborescence modulaire des composants React du Dashboard Terminal", "82"),
        ("Figure 6.2 : Structure d'inversion dynamique RTL pour la prise en charge de l'arabe", "88"),
        ("Figure 8.1 : Diagramme de déploiement conteneurisé et cibles cloud (deployment.puml)", "99"),
    ]
    t_figs = Table([[Paragraph(f"<b>{t}</b>", styles['TOCItem']), Paragraph(f"<b>{p}</b>", styles['TOCPage'])] for t, p in fig_items], colWidths=[150 * mm, 20 * mm])
    t_figs.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_figs)
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("Liste des Tableaux", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    tbl_items = [
        ("Tableau 1.1 : Comparatif fonctionnel et méthodologique des solutions d'analyse de marché", "17"),
        ("Tableau 2.1 : Matrice de traçabilité des exigences fonctionnelles du système", "24"),
        ("Tableau 4.1 : Audit volumétrique et intégrité des séries historiques brutes LiteFinance", "48"),
        ("Tableau 4.2 : Décomposition exhaustive des 87 caractéristiques par échelle temporelle", "51"),
        ("Tableau 5.1 : Découpage temporel et distribution des classes sur les 4 plis du walk-forward Daily", "63"),
        ("Tableau 5.2 : Benchmark comparatif des algorithmes ML lors de la validation walk-forward", "65"),
        ("Tableau 5.3 : Métriques réelles mesurées hors-échantillon pour le modèle Daily (24H)", "68"),
        ("Tableau 5.4 : Métriques réelles mesurées hors-échantillon pour le modèle Weekly (120H)", "69"),
        ("Tableau 7.1 : Synthèse d'exécution de la suite de tests automatisés Pytest (117 tests)", "91"),
        ("Tableau 8.1 : Matrice de configuration et statut d'audit des environnements de déploiement", "103"),
    ]
    t_tbls = Table([[Paragraph(f"<b>{t}</b>", styles['TOCItem']), Paragraph(f"<b>{p}</b>", styles['TOCPage'])] for t, p in tbl_items], colWidths=[150 * mm, 20 * mm])
    t_tbls.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_tbls)
    story.append(PageBreak())

    # =========================================================================
    # 7. LISTE DES ABRÉVIATIONS
    # =========================================================================
    story.append(Paragraph("Liste des Abréviations", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    abbr_data = [
        [Paragraph("<b>AMH</b>", styles['TableText']), Paragraph("Adaptive Markets Hypothesis (Hypothèse des Marchés Adaptatifs)", styles['TableText'])],
        [Paragraph("<b>API</b>", styles['TableText']), Paragraph("Application Programming Interface (Interface de Programmation Applicative)", styles['TableText'])],
        [Paragraph("<b>ASGI</b>", styles['TableText']), Paragraph("Asynchronous Server Gateway Interface", styles['TableText'])],
        [Paragraph("<b>ATR</b>", styles['TableText']), Paragraph("Average True Range (Indicateur de volatilité absolue de Wilder)", styles['TableText'])],
        [Paragraph("<b>AUC</b>", styles['TableText']), Paragraph("Area Under the Curve (Aire sous la courbe)", styles['TableText'])],
        [Paragraph("<b>BF</b>", styles['TableText']), Paragraph("Besoin Fonctionnel", styles['TableText'])],
        [Paragraph("<b>CI/CD</b>", styles['TableText']), Paragraph("Continuous Integration / Continuous Deployment (Intégration & Déploiement Continus)", styles['TableText'])],
        [Paragraph("<b>CORS</b>", styles['TableText']), Paragraph("Cross-Origin Resource Sharing", styles['TableText'])],
        [Paragraph("<b>DXY</b>", styles['TableText']), Paragraph("US Dollar Index (Indice mesurant la valeur du dollar américain)", styles['TableText'])],
        [Paragraph("<b>EMA</b>", styles['TableText']), Paragraph("Exponential Moving Average (Moyenne Mobile Exponentielle)", styles['TableText'])],
        [Paragraph("<b>EMH</b>", styles['TableText']), Paragraph("Efficient Market Hypothesis (Hypothèse d'Efficience des Marchés)", styles['TableText'])],
        [Paragraph("<b>FN / FP</b>", styles['TableText']), Paragraph("Faux Négatifs / Faux Positifs", styles['TableText'])],
        [Paragraph("<b>HTTP</b>", styles['TableText']), Paragraph("HyperText Transfer Protocol", styles['TableText'])],
        [Paragraph("<b>JSON</b>", styles['TableText']), Paragraph("JavaScript Object Notation", styles['TableText'])],
        [Paragraph("<b>LBMA</b>", styles['TableText']), Paragraph("London Bullion Market Association", styles['TableText'])],
        [Paragraph("<b>LR</b>", styles['TableText']), Paragraph("Logistic Regression (Régression Logistique)", styles['TableText'])],
        [Paragraph("<b>MACD</b>", styles['TableText']), Paragraph("Moving Average Convergence Divergence", styles['TableText'])],
        [Paragraph("<b>ML</b>", styles['TableText']), Paragraph("Machine Learning (Apprentissage Automatique)", styles['TableText'])],
        [Paragraph("<b>MTF</b>", styles['TableText']), Paragraph("Multi-Timeframe (Multi-échelles temporelles)", styles['TableText'])],
        [Paragraph("<b>NF</b>", styles['TableText']), Paragraph("Besoin Non Fonctionnel", styles['TableText'])],
        [Paragraph("<b>OHLCV</b>", styles['TableText']), Paragraph("Open, High, Low, Close, Volume (Données de chandeliers)", styles['TableText'])],
        [Paragraph("<b>OTC</b>", styles['TableText']), Paragraph("Over-The-Counter (Marché de gré à gré)", styles['TableText'])],
        [Paragraph("<b>PFA</b>", styles['TableText']), Paragraph("Projet de Fin d'Année", styles['TableText'])],
        [Paragraph("<b>REST</b>", styles['TableText']), Paragraph("Representational State Transfer", styles['TableText'])],
        [Paragraph("<b>ROC</b>", styles['TableText']), Paragraph("Receiver Operating Characteristic", styles['TableText'])],
        [Paragraph("<b>RSI</b>", styles['TableText']), Paragraph("Relative Strength Index (Indice de force relative)", styles['TableText'])],
        [Paragraph("<b>RTL</b>", styles['TableText']), Paragraph("Right-to-Left (Sens d'écriture de droite à gauche)", styles['TableText'])],
        [Paragraph("<b>SHAP</b>", styles['TableText']), Paragraph("SHapley Additive exPlanations", styles['TableText'])],
        [Paragraph("<b>SMA</b>", styles['TableText']), Paragraph("Simple Moving Average (Moyenne Mobile Simple)", styles['TableText'])],
        [Paragraph("<b>TIPS</b>", styles['TableText']), Paragraph("Treasury Inflation-Protected Securities (Obligations indexées sur l'inflation)", styles['TableText'])],
        [Paragraph("<b>TN / TP</b>", styles['TableText']), Paragraph("Vrais Négatifs (True Negatives) / Vrais Positifs (True Positives)", styles['TableText'])],
        [Paragraph("<b>UML</b>", styles['TableText']), Paragraph("Unified Modeling Language (Langage de Modélisation Unifié)", styles['TableText'])],
        [Paragraph("<b>UTC</b>", styles['TableText']), Paragraph("Coordinated Universal Time (Temps Universel Coordonné)", styles['TableText'])],
        [Paragraph("<b>WS</b>", styles['TableText']), Paragraph("WebSocket (Protocole de communication bidirectionnel temps réel)", styles['TableText'])],
        [Paragraph("<b>XAU/USD</b>", styles['TableText']), Paragraph("Symbole monétaire de l'once d'or exprimée en dollars américains", styles['TableText'])],
    ]

    t_abbr = Table(abbr_data, colWidths=[28 * mm, 142 * mm])
    t_abbr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_abbr)
    story.append(PageBreak())

    return story
