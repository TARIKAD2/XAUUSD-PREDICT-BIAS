"""Chapitre 9 — Discussion Critique, Limites et Perspectives."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable
from .styles import PRIMARY

def get_chapter9_story(styles):
    story = []

    story.append(Paragraph("Chapitre 9 — Discussion Critique, Limites et Perspectives", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("9.1 Synthèse critique des performances ML et confrontation théorique", styles['SectionTitle']))
    story.append(Paragraph(
        "L'évaluation empirique hors-échantillon rapportée au Chapitre 5 met en évidence des performances réelles "
        "modestes : une justesse (accuracy) de <b>45.71%</b> sur l'horizon journalier 24H et de <b>39.20%</b> sur l'horizon hebdomadaire 120H. "
        "Dans les deux cas, le modèle de production (Régression Logistique) sous-performe la règle naïve de classe majoritaire "
        "(lift négatif de -2.33% en Daily et de -4.57% en Weekly). "
        "Loin de traduire une anomalie logicielle ou une déficience de programmation — le code et la pipeline ayant été certifiés "
        "sans faille par 117 tests automatisés —, ces résultats s'accordent rigoureusement avec les fondements théoriques majeurs "
        "établis par l'économie financière et la recherche économétrique contemporaine :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>L'Hypothèse d'Efficience des Marchés (Fama, 1970 ; Malkiel, 2003) :</b><br/>"
        "Selon la formulation semi-forte de l'Hypothèse d'Efficience des Marchés (<i>Efficient Market Hypothesis — EMH</i>), "
        "les cours des actifs financiers négociés sur des marchés hautement liquides reflètent instantanément l'ensemble "
        "de l'information publique disponible, y compris l'historique complet des prix, des volumes et des indicateurs techniques dérivés. "
        "Par conséquent, les variations futures de cours obéissent pour l'essentiel à une marche aléatoire (<i>random walk</i>) "
        "ou à un processus de martingale où les rendements futurs non anticipés sont imprévisibles sur la base des seules séries passées. "
        "Tenter d'extraire un signal purement directionnel à partir de combinaisons linéaires d'indicateurs classiques (RSI, MACD, moyennes mobiles) "
        "se heurte à cette barrière d'arbitrage : toute inefficience prévisible a déjà été absorbée par les algorithmes des teneurs de marché.",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>L'Hypothèse des Marchés Adaptatifs (Lo, 2004) :</b><br/>"
        "Le professeur Andrew Lo propose une synthèse réconciliant l'efficience des marchés et les anomalies comportementales. "
        "Dans le cadre de l'Hypothèse des Marchés Adaptatifs (<i>Adaptive Markets Hypothesis — AMH</i>), le degré d'efficience "
        "d'un marché n'est pas une constante immuable mais fluctue dynamiquement en fonction du nombre de compétiteurs, des ressources technologiques "
        "déployées et de l'environnement macroéconomique. Les poches de prédictibilité statistique sont éphémères : dès qu'une relation technique "
        "devient détectable, l'afflux d'ordres institutionnels exploitant ce signal détruit l'inefficience par arbitrage, "
        "ramenant le ratio signal sur bruit vers zéro.",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>L'évaluation scientifique de l'analyse technique (Aronson, 2006) :</b><br/>"
        "Dans son ouvrage de référence <i>Evidence-Based Technical Analysis</i>, David Aronson démontre au moyen d'inférences statistiques rigoureuses "
        "et de tests de rééchantillonnage de Monte Carlo que l'immense majorité des règles de l'analyse technique traditionnelle "
        "(croisements de moyennes mobiles, niveaux de surachat/survente du RSI, figures chartistes) ne présentent aucun pouvoir prédictif statistiquement "
        "significatif par rapport au hasard pur une fois corrigées du biais de sélection (<i>data-mining bias</i>). "
        "Nos résultats expérimentaux corroborent fidèlement ces conclusions académiques.",
        styles['Body']
    ))

    story.append(Paragraph("9.2 Analyse approfondie du biais haussier du modèle", styles['SectionTitle']))
    story.append(Paragraph(
        "L'examen attentif des matrices de confusion obtenues sur l'échantillon de test (Tableaux 5.3 et 5.4) met en évidence "
        "une asymétrie d'inférence spectaculaire : sur l'horizon Daily, le modèle émet <b>1 948 prédictions haussières (BULLISH)</b> "
        "contre seulement <b>196 prédictions baissières (BEARISH)</b>, soit une proportion de 90.8% d'appels à la hausse. "
        "Ce comportement s'explique par les mécanismes suivants :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>L'empreinte du régime macroéconomique d'apprentissage (2022-2025) :</b><br/>"
        "Durant la période couverte par le jeu d'entraînement, le marché de l'or a traversé un cycle haussier historique exceptionnel, "
        "propulsé par l'inflation mondiale consécutive à la pandémie, les tensions géopolitiques majeures et les achats records "
        "d'or physique par les banques centrales émergentes. Le cours XAU/USD a enregistré une progression continue, créant un déséquilibre "
        "naturel dans les données historiques.<br/>"
        "2. <b>L'optimisation des coefficients linéaires :</b><br/>"
        "Pour maximiser la fonction de vraisemblance sur les données d'entraînement, l'algorithme de Régression Logistique a ajusté ses poids "
        "de manière à favoriser la classe majoritaire de l'échantillon passé. Lorsque le marché a ensuite abordé une phase de consolidation "
        "et de corrections baissières sur le jeu de test final de 2026, le modèle a persisté à anticiper la continuation de la hausse séculaire, "
        "engendrant un volume élevé de faux positifs (1 041 faux signaux haussiers) et pénalisant sa justesse globale.",
        styles['Body']
    ))

    story.append(Paragraph("9.3 Limites techniques et contraintes d'infrastructure", styles['SectionTitle']))
    story.append(Paragraph(
        "Au-delà des contraintes théoriques de marché, le déploiement opérationnel d'une telle plateforme se heurte à des contraintes "
        "techniques matérielles et réseau :<br/>"
        "• <b>Quotas et limitation de débit des API externes (Twelve Data Rate Limiting) :</b><br/>"
        "Les forfaits d'accès standards imposent des plafonds d'appels stricts par minute (8 requêtes par minute sur les clés de base), "
        "contraignant l'architecture à réguler sévèrement les interrogations REST et interdisant une reconstruction à trop haute fréquence "
        "des séries de chandeliers.<br/>"
        "• <b>Discontinuités de liquidité de fin de semaine (Weekend Gaps) :</b><br/>"
        "La fermeture du marché spot de l'or du vendredi soir au dimanche soir crée une interruption de cotation de près de 48 heures. "
        "Lorsque des événements géopolitiques surviennent durant le week-end, la réouverture des cotations le dimanche soir s'effectue "
        "souvent par un saut de cours abrupt (<i>gap</i>) que les indicateurs techniques continus lissés peinent à anticiper.<br/>"
        "• <b>Absence de framework de tests frontend automatisés :</b><br/>"
        "Bien que la compilation Next.js s'exécute sans erreur, l'absence de tests unitaires et de tests de bout en bout (E2E) "
        "sur les composants React constitue une limite d'assurance qualité qu'un cycle de développement industriel devrait combler.",
        styles['Body']
    ))

    story.append(Paragraph("9.4 Perspectives de recherche future et pistes d'évolution", styles['SectionTitle']))
    story.append(Paragraph(
        "Pour surmonter ces limites et ouvrir la voie à des avancées quantitatives substantielles, plusieurs axes d'investigation "
        "scientifique prometteurs sont identifiés :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Modélisation Séquentielle Profonde et Attention Temporelle :</b><br/>"
        "Remplacer les modèles linéaires statiques par des architectures d'apprentissage profond dédiées aux séries temporelles, "
        "telles que les réseaux récurrents à mémoire longue (LSTM, GRU) ou les <i>Temporal Fusion Transformers (TFT)</i>. "
        "Ces modèles sont capables d'apprendre des dépendances temporelles multi-échelles et d'isoler dynamiquement les régimes de marché "
        "grâce à des mécanismes d'attention auto-adaptatifs.",
        styles['Body']
    ))
    story.append(Paragraph(
        "2. <b>Enrichissement Exogène Multi-Marchés :</b><br/>"
        "Le cours XAU/USD étant profondément influencé par des variables macroéconomiques globales, le pipeline prédictif gagnerait "
        "à intégrer des séries exogènes causales en temps réel : les rendements obligataires réels à 10 ans (TIPS), l'indice du dollar (DXY), "
        "le spread de crédit souverain et le ratio or/argent (XAU/XAG).",
        styles['Body']
    ))
    story.append(Paragraph(
        "3. <b>Apprentissage Continu Incrémental (Online Learning) :</b><br/>"
        "Mettre en place un mécanisme de réentraînement adaptatif glissant (<i>rolling window online updating</i>) : à chaque clôture "
        "d'une nouvelle bougie H1 ou quotidienne, les poids du modèle seraient ajustés par descente de gradient stochastique en ligne, "
        "permettant au système de s'adapter aux mutations rapides de volatilité et d'atténuer le biais haussier persistant.",
        styles['Body']
    ))
    story.append(PageBreak())

    return story

