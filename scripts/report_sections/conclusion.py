"""Conclusion Générale du rapport de PFA."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable
from .styles import PRIMARY

def get_conclusion_story(styles):
    story = []

    story.append(Paragraph("Conclusion Générale", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph(
        "Ce Projet de Fin d'Année a permis de concevoir, de développer, de tester et d'évaluer de manière rigoureuse "
        "une plateforme web asynchrone full-stack d'intelligence quantitative et d'aide à la décision pour le marché "
        "de l'or au comptant contre dollar américain (<b>XAU/USD</b>). "
        "Au terme de ce travail d'ingénierie logicielle et de recherche empirique, nous pouvons dresser un bilan approfondi "
        "des réalisations accomplies au regard des défis initiaux énoncés dans la problématique.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>1. Une adhésion intransigeante à la rigueur méthodologique et à l'honnêteté scientifique :</b><br/>"
        "La contribution cardinale de ce projet réside dans son refus résolu de toute complaisance ou illusion de prédictibilité. "
        "À rebours des approches mercantiles qui masquent leurs échecs ou publient des métriques issues de protocoles méthodologiquement "
        "corrompus, notre travail a fait de la transparence intégrale sa règle directrice absolue :<br/>"
        "• <i>Éradication prouvée du Data Leakage</i> : Le pipeline multi-timeframes de 87 caractéristiques techniques applique un alignement "
        "as-of strictement rétrograde, validé par des tests de non-régression où la mutation délibérée des données futures ne modifie en rien "
        "la matrice prédictive présente.<br/>"
        "• <i>Formulation binaire pure et traitement mathématique de l'indécision</i> : L'espace de prédiction a été rigoureusement restreint "
        "aux deux régimes directeurs <b>BULLISH</b> et <b>BEARISH</b>, la zone morte des micro-fluctuations étant éliminée lors de l'apprentissage "
        "pour ne pas contaminer les estimateurs.<br/>"
        "• <i>Validation Walk-Forward avec embargo</i> : L'évaluation sur 4 plis expansifs a permis de disqualifier sans appel les modèles "
        "ensemblistes arborescents (Random Forest, LightGBM) en raison de leur surapprentissage massif et d'effondrements de classes, "
        "justifiant le choix d'une Régression Logistique pénalisée sobre et stable.<br/>"
        "• <i>Publication intégrale des métriques mesurées réelles</i> : L'évaluation hors-échantillon a rapporté fidèlement les justesses obtenues "
        "(45.71% en 24H et 39.20% en 120H), explicitant clairement leur infériorité par rapport aux baselines majoritaires et analysant "
        "le biais haussier résiduel à la lumière de l'Hypothèse d'Efficience des Marchés.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>2. L'excellence d'une architecture logicielle moderne, réactive et résiliente :</b><br/>"
        "Sur le plan du génie logiciel, le projet démontre l'efficacité et la robustesse d'une pile technologique d'avant-garde :<br/>"
        "• <i>Un backend asynchrone haute performance (FastAPI)</i> supervisé par un cycle de vie <code>lifespan</code>, doté de gestionnaires "
        "d'erreurs typés et d'un moteur d'inférence sécurisé qui bascule systématiquement vers <code>MODEL_NOT_READY</code> plutôt que de fabriquer "
        "des prédictions invalides en cas d'anomalie de données.<br/>"
        "• <i>Un gestionnaire WebSocket temps réel Singleton</i> maintenant une liaison continue avec Twelve Data et redistribuant instantanément "
        "les ticks de cotation à travers des files <code>asyncio.Queue</code> privées et isolées.<br/>"
        "• <i>Une persistance documentaire MongoDB</i> structurée autour de collections temporelles scellées par des index uniques composés, "
        "garantissant l'idempotence des écritures et la préservation de l'intégrité de l'audit.<br/>"
        "• <i>Une interface utilisateur réactive (Next.js 15)</i> offrant une expérience terminal professionnelle, un tracé graphique SVG fluide, "
        "des décompositions explicatives linéaires signées et une prise en charge trilingue native intégrant l'orientation bidirectionnelle RTL pour l'arabe.<br/>"
        "• <i>Une qualité logicielle certifiée</i> par le succès sans faille de 117 tests automatisés Pytest couvrant l'ensemble du périmètre.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>3. Enseignements académiques et perspectives :</b><br/>"
        "Ce mémoire illustre la réalité fondamentale de la finance computationnelle : la valeur d'une plateforme d'intelligence de marché "
        "ne se mesure pas à l'illusion d'une boule de cristal infaillible, mais à la robustesse de son architecture, à l'intégrité de ses flux de données "
        "et à la clarté avec laquelle elle quantifie l'incertitude pour éclairer la décision humaine. "
        "Les perspectives ouvertes par ce travail — intégration de variables exogènes multi-marchés (TIPS, DXY) et déploiement d'architectures "
        "d'apprentissage séquentiel profond (TFT) — constituent des prolongements naturels pour de futurs travaux de recherche.",
        styles['Body']
    ))
    story.append(PageBreak())

    return story

