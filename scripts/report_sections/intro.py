"""Introduction Générale du rapport de PFA."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, PageBreak, HRFlowable
from .styles import PRIMARY

def get_intro_story(styles):
    story = []

    story.append(Paragraph("Introduction Générale", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("1. Contexte macroéconomique et monétaire de l'or", styles['SectionTitle']))
    story.append(Paragraph(
        "Depuis l'aube des civilisations marchandes et l'instauration des premiers systèmes d'étalon métallique, "
        "l'or physique (désigné par le code ISO 4217 <code>XAU</code>) occupe une place singulière au cœur de l'économie mondiale. "
        "Contrairement aux devises fiduciaires modernes émises par les banques centrales contemporaines — dont la valeur intrinsèque "
        "repose sur la confiance accordée à la souveraineté étatique et dont la masse monétaire peut être étendue de manière discrétionnaire —, "
        "l'or constitue un actif tangible fini, dépourvu de tout risque de contrepartie ou de défaut souverain. "
        "Cette rareté géologique confère historiquement au métal jaune le statut de valeur refuge par excellence (<i>safe-haven asset</i>).",
        styles['Body']
    ))
    story.append(Paragraph(
        "Dans l'environnement macroéconomique contemporain, marqué par la globalisation des flux de capitaux et l'interconnexion "
        "des marchés financiers, le cours de l'or ne constitue pas un simple prix de matière première. Il opère comme un baromètre "
        "sensible des déséquilibres économiques mondiaux. Sa valorisation est étroitement corrélée aux anticipations d'inflation à long terme, "
        "aux rendements réels des obligations d'État (notamment les bons du Trésor américain indexés sur l'inflation — TIPS), aux tensions "
        "géopolitiques internationales ainsi qu'à la trajectoire séculaire du dollar américain (USD). En période de crise de liquidité, "
        "de dépréciation monétaire ou de choc géopolitique, les investisseurs institutionnels réallouent massivement leurs capitaux "
        "vers les avoirs libellés en or, provoquant des mouvements de cours d'une ampleur et d'une vélocité remarquables.",
        styles['Body']
    ))

    story.append(Paragraph("2. Dynamique du marché spot XAU/USD et microstructure", styles['SectionTitle']))
    story.append(Paragraph(
        "La cotation <b>XAU/USD</b> désigne la valeur marchande au comptant (<i>spot</i>) d'une once troy d'or fin (approximativement "
        "31.1035 grammes) exprimée en dollars américains. Le marché de l'or spot est l'un des marchés financiers les plus vastes, "
        "les plus liquides et les plus continus de la planète. Il fonctionne sous un régime de gré à gré (<i>Over-The-Counter — OTC</i>), "
        "opérant 24 heures sur 24 durant les cinq jours ouvrés de la semaine, relayé successivement par les bourses et centres de compensation "
        "de Sydney, Tokyo, Londres, Zurich et New York.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Sur le plan de la microstructure des marchés, le flux continu des cotations XAU/USD résulte de la confrontation permanente "
        "entre des ordres institutionnels aux horizons d'investissement hautement divergents : banques centrales consolidant leurs réserves "
        "stratégiques, fonds souverains, producteurs miniers couvrant leur production future (<i>hedging</i>), spéculateurs haute fréquence "
        "et investisseurs particuliers. Cette multiplicité d'intervenants engendre une dynamique de prix hautement complexe, "
        "caractérisée par une volatilité intraday intempestive, des régimes de tendance marqués succédant à des phases prolongées de congestion, "
        "et des discontinuités de cours (<i>gaps</i>) systématiques lors de la réouverture des cotations le dimanche soir après la pause hebdomadaire.",
        styles['Body']
    ))

    story.append(Paragraph("3. Problématique scientifique et technique", styles['SectionTitle']))
    story.append(Paragraph(
        "L'application des techniques modernes de science des données et d'apprentissage automatique (<i>Machine Learning</i>) "
        "à la modélisation prédictive du cours XAU/USD soulève des verrous méthodologiques et informatiques majeurs que la littérature "
        "académique et les praticiens s'accordent à qualifier de critiques :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>La non-stationnarité et le faible ratio signal/bruit</b> : Les séries chronologiques financières ne respectent pas "
        "l'hypothèse de distribution stationnaire. Leurs propriétés statistiques (moyenne, variance, autocorrélation) évoluent au cours "
        "du temps en raison de changements structurels de régime macroéconomique. Le niveau de bruit aléatoire domine largement "
        "l'information exploitable, exposant les modèles au risque aigu de surapprentissage (<i>overfitting</i>).",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>Le péril du biais prospectif (<i>Data Leakage</i>)</b> : Lors de la construction de caractéristiques prédictives "
        "combinant plusieurs granularités temporelles (par exemple 15 minutes, 1 heure, 4 heures), une synchronisation naïve sur les horodatages "
        "de début de période conduit inévitablement à intégrer des informations relatives à des événements futurs non encore survenus. "
        "Cette fuite d'information prospective engendre des métriques artificiellement spectaculaires en phase d'entraînement, "
        "suivies d'un effondrement dramatique lors de l'exécution sur données réelles.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>L'opacité méthodologique et les fausses promesses commerciales</b> : Une multitude d'applications commerciales revendiquent "
        "des taux de réussite illusoires (80% à 90%) en dissimulant leurs protocoles de test, en mélangeant aléatoirement des données temporelles "
        "(<i>shuffling</i>) et en présentant des modèles comme des « boîtes noires » dénuées de toute quantification d'incertitude ou d'explication causale.",
        styles['Bullet']
    ))
    story.append(Paragraph(
        "• <b>Le défi du streaming temps réel distribué</b> : Développer une architecture logicielle capable d'ingérer un flux continu de cotations "
        "en temps réel, de recalculer à la volée une matrice complexe de dizaines d'indicateurs sans latence cumulative, "
        "et de distribuer instantanément ces informations aux clients connectés sans bloquer le serveur applicatif exige une maîtrise "
        "rigoureuse des mécanismes de programmation asynchrone concurrente.",
        styles['Bullet']
    ))

    story.append(Paragraph("4. Motivation de la recherche empirique", styles['SectionTitle']))
    story.append(Paragraph(
        "La genèse de ce Projet de Fin d'Année repose sur une exigence de probité scientifique et d'excellence en ingénierie logicielle. "
        "Il ne s'agit nullement de concevoir un automate de passage d'ordres spéculatifs ni de formuler des promesses d'enrichissement algorithmique. "
        "La motivation centrale consiste à construire un environnement de recherche quantitative rigoureux, transparent et auditable, "
        "démontrant comment les technologies modernes du web asynchrone (FastAPI, WebSockets, Next.js) peuvent être harmonieusement couplées "
        "à un pipeline de Machine Learning intègre, où chaque résultat est étayé par des preuves tangibles et où les limites intrinsèques "
        "des modèles sont exposées avec une totale honnêteté intellectuelle.",
        styles['Body']
    ))

    story.append(Paragraph("5. Objectifs opérationnels et scientifiques", styles['SectionTitle']))
    story.append(Paragraph(
        "Pour répondre concrètement à cette problématique, le projet s'est fixé six objectifs opérationnels majeurs :<br/>"
        "1. <b>Acquisition et intégrité des données</b> : Collecter et assainir un historique volumineux de cotations XAU/USD (LiteFinance) "
        "sur trois échelles (M15, H1, H4) sans injecter de bougies artificielles et en préservant scrupuleusement les discontinuités réelles du marché.<br/>"
        "2. <b>Ingénierie causale des caractéristiques</b> : Concevoir et implémenter un pipeline de 87 indicateurs techniques multi-timeframes "
        "garantissant mathématiquement une absence absolue de fuite future via des jointures rétrogrades as-of.<br/>"
        "3. <b>Modélisation prédictive binaire stricte</b> : Formuler le problème en classification binaire pure opposant les régimes "
        "<b>BULLISH</b> et <b>BEARISH</b>, en excluant explicitement la zone morte d'indécision de l'apprentissage.<br/>"
        "4. <b>Validation temporelle walk-forward sans tricherie</b> : Évaluer comparativement quatre familles d'algorithmes selon un protocole "
        "à fenêtre expansive sur 4 plis avec embargo, et publier fidèlement les métriques réelles hors-échantillon sans embellissement.<br/>"
        "5. <b>Explicabilité et modélisation de l'incertitude</b> : Fournir pour chaque inférence des probabilités étalonnées, un indice de confiance "
        "chiffré et la décomposition linéaire des 8 variables les plus influentes.<br/>"
        "6. <b>Architecture full-stack et expérience utilisateur</b> : Réaliser un backend réactif FastAPI avec gestionnaire WebSocket persistant "
        "et un tableau de bord Next.js inspiré des terminaux professionnels, doté d'une internationalisation trilingue (Anglais, Français, Arabe avec support RTL).",
        styles['Body']
    ))

    story.append(Paragraph("6. Méthodologie scientifique adoptée", styles['SectionTitle']))
    story.append(Paragraph(
        "La conduite de ce travail s'inspire sur le plan conceptuel des cycles de vie itératifs propres aux projets de science des données "
        "(tels que formalisés dans la littérature de référence par le modèle conceptuel CRISP-DM — <i>Cross-Industry Standard Process for Data Mining</i>). "
        "Toutefois, nous précisons d'emblée que CRISP-DM est mobilisé ici uniquement comme un cadre théorique de réflexion méthodologique "
        "et non comme une procédure contractuelle formalisée dans le dépôt. "
        "L'accent a été mis sur le principe d'évaluation empirique fondée sur des preuves (<i>evidence-based research</i>) : "
        "le code source exécutable et les métriques réelles générées constituent la seule source de vérité admise.",
        styles['Body']
    ))

    story.append(Paragraph("7. Organisation détaillée du mémoire", styles['SectionTitle']))
    story.append(Paragraph(
        "Le présent mémoire est structuré en neuf chapitres thématiques progressifs :<br/>"
        "• <b>Chapitre 1 — Contexte Général et Étude de l'Existant</b> : Présente le marché de l'or, les fondements économétriques, "
        "analyse l'état de l'art des solutions logicielles et justifie le positionnement du projet.<br/>"
        "• <b>Chapitre 2 — Analyse et Spécification des Besoins</b> : Définit les acteurs, recense les exigences fonctionnelles et non fonctionnelles, "
        "et modélise les cas d'utilisation.<br/>"
        "• <b>Chapitre 3 — Analyse et Conception Système</b> : Détaille l'architecture globale multi-couches, l'organisation logicielle backend et frontend, "
        "les schémas de données MongoDB et les protocoles de communication.<br/>"
        "• <b>Chapitre 4 — Acquisition et Préparation des Données de Marché</b> : Décrit la collecte, le protocole d'assainissement, "
        "la formulation mathématique des 87 indicateurs techniques et la preuve de causalité temporelle.<br/>"
        "• <b>Chapitre 5 — Machine Learning et Prédiction Directionnelle</b> : Expose la formalisation binaire, le protocole walk-forward, "
        "la comparaison des modèles, les résultats mesurés hors-échantillon et les mécanismes d'explicabilité.<br/>"
        "• <b>Chapitre 6 — Réalisation et Développement Applicatif</b> : Documente l'implémentation concrète de FastAPI, du service WebSocket, "
        "du Dashboard Next.js et de l'internationalisation trilingue.<br/>"
        "• <b>Chapitre 7 — Tests, Validation et Assurance Qualité</b> : Présente la suite de 117 tests automatisés Pytest, les tests d'étanchéité "
        "et l'audit des composants client.<br/>"
        "• <b>Chapitre 8 — Déploiement et DevOps</b> : Traite de la conteneurisation Docker, des fichiers de configuration cloud (Railway, Vercel) "
        "et du statut d'audit des environnements.<br/>"
        "• <b>Chapitre 9 — Discussion Critique, Limites et Perspectives</b> : Analyse scientifiquement les résultats au regard de l'efficience "
        "des marchés financiers, recense les contraintes techniques et propose des perspectives de recherche future.<br/>"
        "Une conclusion générale, une bibliographie académique rigoureuse et des annexes techniques exhaustives clôturent l'ouvrage.",
        styles['Body']
    ))
    story.append(PageBreak())

    return story

