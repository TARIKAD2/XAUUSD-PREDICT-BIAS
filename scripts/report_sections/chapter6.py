"""Chapitre 6 — Réalisation et Développement Applicatif."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, BORDER_COLOR, HIGHLIGHT, LIGHT_BG

def get_chapter6_story(styles):
    story = []

    story.append(Paragraph("Chapitre 6 — Réalisation et Développement Applicatif", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("6.1 Implémentation du backend FastAPI et cycle de vie lifespan", styles['SectionTitle']))
    story.append(Paragraph(
        "Le développement du backend tire pleinement parti des capacités asynchrones offertes par Python 3.13 et FastAPI. "
        "L'organisation du code source respecte une architecture en couches épurée, isolant strictement la couche de transport HTTP, "
        "la couche de logique métier et la couche d'accès aux données :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Typage rigoureux et contrats d'échange Pydantic V2 :</b><br/>"
        "Tous les modèles de données échangés sur l'API héritent de <code>APIModel</code> (défini dans <code>backend/app/schemas/base.py</code>). "
        "Ce modèle de base configure la sérialisation automatique des objets temporels en chaînes ISO 8601 et applique une validation "
        "stricte au moment de l'instanciation. Le schéma <code>ProbabilityBreakdown</code> intègre un validateur post-construction "
        "<code>probabilities_sum_to_one</code> vérifiant que la somme des probabilités <code>bullish</code> et <code>bearish</code> "
        "est égale à 1.0 à $10^{-3}$ près, levant une exception de validation dans le cas contraire.",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Gestion centralisée et typée des exceptions applicatives :</b><br/>"
        "Les erreurs opérationnelles sont gérées par des intercepteurs dédiés dans <code>backend/app/api/errors.py</code>. "
        "Lorsqu'une requête d'inférence intervient alors que le volume de bougies fermées en base est insuffisant pour alimenter "
        "les fenêtres glissantes de 200 périodes, le service lève une exception typée <code>FeatureNotReadyError</code>. "
        "Celle-ci est immédiatement convertie en une réponse HTTP 503 documentée avec payload JSON standardisé, évitant tout plantage inopiné.",
        styles['Body']
    ))

    # Extrait de code Lifespan
    code_lifespan = (
        '@asynccontextmanager\n'
        'async def lifespan(app: FastAPI):\n'
        '    # 1. Initialisation asynchrone du pool MongoDB\n'
        '    mongo_manager = MongoClientManager(settings)\n'
        '    await mongo_manager.connect()\n'
        '    await ensure_indexes(mongo_manager.database)\n'
        '    \n'
        '    # 2. Démarrage de la supervision WebSocket temps réel (Singleton)\n'
        '    live_service = LiveMarketService.get_instance(settings)\n'
        '    supervisor_task = asyncio.create_task(live_service.start())\n'
        '    \n'
        '    # 3. Démarrage du worker périodique de collecte des bougies fermées\n'
        '    ingestion_worker = XAUUSDIngestionWorker(settings, mongo_manager)\n'
        '    ingestion_task = asyncio.create_task(ingestion_worker.run_loop())\n'
        '    \n'
        '    yield\n'
        '    \n'
        '    # 4. Phase de fermeture gracieuse\n'
        '    supervisor_task.cancel()\n'
        '    ingestion_task.cancel()\n'
        '    await live_service.shutdown()\n'
        '    await mongo_manager.disconnect()\n'
    )
    t_cl = Table([[Paragraph(f"<pre>{code_lifespan}</pre>", styles['CodeSnippet'])]], colWidths=[170 * mm])
    t_cl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_cl)
    story.append(Paragraph("Listing 6.1 : Gestionnaire asynchrone de cycle de vie (ASGI Lifespan dans app/main.py)", styles['Caption']))

    story.append(Paragraph("6.2 Gestionnaire temps réel WebSocket singleton et distribution", styles['SectionTitle']))
    story.append(Paragraph(
        "Le composant <code>LiveMarketService</code> (défini dans <code>backend/app/services/live_market.py</code>) constitue l'élément "
        "clé de la distribution des cours en streaming. Il est conçu selon le patron Singleton :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Boucle de supervision asynchrone (<code>_supervisor_loop</code>) :</b><br/>"
        "Exécutée en tâche d'arrière-plan dès le lancement du serveur ASGI. Elle établit et maintient la connexion WebSocket client "
        "vers les serveurs de Twelve Data (<code>wss://ws.twelvedata.com/v1/quotes/price</code>). En cas d'interruption réseau "
        "ou d'expiration du socket, la boucle applique une stratégie de reconnexion automatique avec temporisation exponentielle (<i>exponential backoff</i>), "
        "tout en marquant temporairement le statut du symbole à <code>DELAYED</code> ou <code>OFFLINE</code>.<br/>"
        "• <b>Mécanisme de distribution non-bloquante aux clients web :</b><br/>"
        "Dès qu'un client navigateur se connecte au point de terminaison <code>/api/ws/market</code>, le gestionnaire enregistre "
        "une file asynchrone <code>asyncio.Queue</code> dédiée à cette session. Le service lui transmet instantanément un premier message "
        "de type <code>initial_state</code> contenant le dernier cours connu en cache (évitant au client d'attendre l'arrivée du prochain tick). "
        "Par la suite, chaque message de cotation reçu de Twelve Data est poussé dans toutes les files clientes abonnées sans aucun verrou bloquant.",
        styles['Body']
    ))

    story.append(Paragraph("6.3 Développement du frontend Next.js 15 et Dashboard Terminal", styles['SectionTitle']))
    story.append(Paragraph(
        "L'interface utilisateur (hébergée dans <code>frontend/app/page.js</code>) a été conçue pour offrir l'ergonomie, "
        "la lisibilité et la sobriété visuelle caractéristiques des terminaux financiers institutionnels professionnels "
        "(palette sombre anthracite <code>#0B0E14</code>, contrastes accentués, bordures fines <code>#1E293B</code>, absence d'éléments de distraction).",
        styles['Body']
    ))
    story.append(Paragraph(
        "La page principale est structurée selon une grille analytique hiérarchisée :<br/>"
        "1. <b>Barre d'en-tête supérieure (Header Terminal)</b> : Affiche le titre de la plateforme, l'indicateur d'état du système "
        "(point vert clignotant 'SYSTEM ONLINE'), l'horloge universelle UTC en direct et le sélecteur de langue <code>LanguageSwitcher</code>.<br/>"
        "2. <b>Ligne principale d'exécution</b> : Juxtaposition de deux blocs majeurs de même importance :<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• <i>À gauche : Bloc Marché Spot</i> : Regroupe la carte de cours <code>MarketCard</code> (prix d'achat, prix de vente, "
        "spread instantané, variation sur 24H) et le graphique vectoriel <code>PriceChart</code> traçant les dernières bougies fermées.<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;• <i>À droite : Bloc Intelligence Artificielle</i> : Composant <code>PredictionCard</code> présentant le verdict "
        "du modèle ML avec sa jauge de probabilité, sa confiance et ses facteurs explicatifs.<br/>"
        "3. <b>Ligne analytique intermédiaire</b> : Présente le panneau des oscillateurs techniques <code>TechnicalPanel</code> "
        "(RSI 14, histogramme MACD, volatilité ATR) et le panneau des scénarios probabilistes <code>ScenarioPanel</code>.<br/>"
        "4. <b>Pied de page de métrologie</b> : Affiche l'empreinte de version du modèle actif, l'état de la connexion MongoDB "
        "et la latence mesurée du flux WebSocket.",
        styles['Body']
    ))

    story.append(Paragraph("6.4 Composants d'interface, bascule d'horizon et visualisation", styles['SectionTitle']))
    story.append(Paragraph(
        "Le composant <code>PredictionCard.js</code> concentre une ergonomie analytique avancée :<br/>"
        "• <b>Bascule dynamique d'horizon prévisionnel :</b> Deux boutons à bascule intégrés permettent à l'utilisateur de passer "
        "instantanément du mode <b>Daily (24H)</b> au mode <b>Weekly (120H)</b>. Cette action déclenche l'appel asynchrone "
        "vers le modèle correspondant sans recharger la page, actualisant les métriques et les facteurs explicatifs associés.<br/>"
        "• <b>Bannière de statut directionnel :</b> Présentation stylisée du régime de marché : badge vert doré <b>BULLISH</b> "
        "ou badge bordeaux <b>BEARISH</b>, accompagné de l'affichage en pourcentage de l'indice de confiance numérique.<br/>"
        "• <b>Barre de probabilité binaire complémentaire :</b> Barre de progression horizontale segmentée visualisant "
        "la part respective de $P(\\text{BULLISH})$ et $P(\\text{BEARISH})$.<br/>"
        "• <b>Facteurs explicatifs linéaires ordonnés :</b> Liste hiérarchisée des 8 caractéristiques ayant le plus fort impact logit, "
        "avec étiquette d'impact positive (favorable à la hausse) ou negative (favorable à la baisse) et valeur brute observée.<br/>"
        "• <b>Graphique vectoriel PriceChart :</b> Tracé vectoriel SVG natif calculant dynamiquement les échelles de prix et de temps "
        "à partir des bougies H1, garantissant un rendu graphique immédiat à 60 images par seconde sans surcharge mémoire.",
        styles['Body']
    ))

    story.append(Paragraph("6.5 Internationalisation trilingue (EN / FR / AR) et support RTL natif", styles['SectionTitle']))
    story.append(Paragraph(
        "L'internationalisation (i18n) a été intégralement implémentée sans bibliothèque tierce lourde afin de préserver "
        "la légèreté du bundle client :<br/>"
        "• <b>Catalogues de traduction JSON structurés :</b> Définis dans <code>frontend/locales/en.json</code>, "
        "<code>frontend/locales/fr.json</code> et <code>frontend/locales/ar.json</code>, couvrant l'intégralité des libellés de l'interface.<br/>"
        "• <b>Gestionnaire de contexte global (<code>LanguageContext.js</code>) :</b> Fournit le hook <code>useTranslation()</code> "
        "à l'ensemble des composants, mémorise le choix de l'utilisateur dans le stockage local (<code>localStorage</code>) "
        "et applique automatiquement les traductions au montage.<br/>"
        "• <b>Support bidirectionnel Right-to-Left (RTL) natif :</b><br/>"
        "Lors de la sélection de la langue arabe (AR), le contexte injecte dynamiquement l'attribut standard <code>dir=\"rtl\"</code> "
        "et la classe <code>rtl</code> sur les balises racines du document HTML. L'ensemble des grilles Flexbox et CSS Grid "
        "s'inverse automatiquement de droite à gauche : le bandeau de cours spot se positionne à droite, les jauges de probabilité "
        "progressent vers la gauche et les typographies arabes bénéficient d'un alignement et d'un espacement adaptés.",
        styles['Body']
    ))
    story.append(PageBreak())

    return story

