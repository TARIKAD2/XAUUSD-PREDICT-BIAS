"""Chapitre 3 — Analyse et Conception Système."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, BORDER_COLOR, HIGHLIGHT, LIGHT_BG

def get_chapter3_story(styles):
    story = []

    story.append(Paragraph("Chapitre 3 — Analyse et Conception Système", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("3.1 Architecture globale en couches micro-services", styles['SectionTitle']))
    story.append(Paragraph(
        "Pour concilier les exigences divergentes de débit temps réel, de calcul analytique lourd et de réactivité "
        "d'interface utilisateur, la plateforme <b>AI Market Intelligence</b> est articulée selon un patron d'architecture "
        "découplé en couches logiques indépendantes (<i>Layered & Service-Oriented Architecture</i>). "
        "Ce découpage assure une séparation stricte des responsabilités (<i>Separation of Concerns</i>), "
        "maximise la testabilité unitaire et permet une extensibilité horizontale sans friction.",
        styles['Body']
    ))
    story.append(Paragraph(
        "L'infrastructure générale se compose de cinq sous-systèmes fonctionnels majeurs :<br/>"
        "1. <b>Sous-système d'ingestion et passerelles externes</b> : Encapsule la communication avec les serveurs de Twelve Data. "
        "Il gère simultanément un client WebSocket asynchrone pour la réception haute fréquence des ticks spot et un client HTTP REST "
        "pour la collecte périodique des séries de bougies OHLCV fermées.<br/>"
        "2. <b>Sous-système de persistance (MongoDB)</b> : Couche de stockage non relationnelle optimisée pour les séries temporelles. "
        "Elle héberge les bougies validées, les prédictions archivées, les métriques d'évaluation et les états d'ingestion.<br/>"
        "3. <b>Moteur de calcul et d'inférence (ML Serving Engine)</b> : Moteur Python autonome chargé de charger en mémoire "
        "les artefacts sérialisés, de transformer les données de marché en matrice de 87 caractéristiques causales, d'exécuter "
        "l'inférence probabiliste et de dériver les explications linéaires.<br/>"
        "4. <b>Couche applicative Backend (FastAPI / ASGI)</b> : Cœur névralgique du système. Il expose l'API REST sécurisée, "
        "héberge le gestionnaire de connexions WebSocket et supervise le cycle de vie applicatif global.<br/>"
        "5. <b>Couche de présentation Frontend (Next.js 15 / React 19)</b> : Interface graphique riche exécutée côté client, "
        "assurant le rendu dynamique des cours, des graphiques vectoriels, des jauges de probabilité et la gestion trilingue.",
        styles['Body']
    ))

    story.append(Paragraph("3.2 Conception logicielle Backend FastAPI", styles['SectionTitle']))
    story.append(Paragraph(
        "Le backend repose sur le framework <b>FastAPI</b>, couplé au serveur ASGI haute performance <b>Uvicorn</b>. "
        "Le point d'entrée unique de l'application est formalisé dans <code>backend/app/main.py</code> via un patron usine "
        "(<code>create_app()</code>). Cette conception favorise l'isolation des contextes d'exécution lors des tests automatisés.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Cycle de vie asynchrone (ASGI Lifespan) :</b><br/>"
        "La gestion du démarrage et de l'arrêt gracieux du serveur s'effectue via un gestionnaire de contexte asynchrone moderne "
        "<code>lifespan(app: FastAPI)</code> :<br/>"
        "• <i>Phase de démarrage (Startup)</i> : Initialisation du pool de connexions asynchrones Motor/MongoDB via <code>MongoClientManager</code> ; "
        "vérification et création idempotente des index de collections (<code>ensure_indexes()</code>) ; instanciation du singleton "
        "<code>LiveMarketService</code> et démarrage de sa tâche de supervision d'arrière-plan (<code>asyncio.create_task</code>) ; "
        "lancement du worker périodique d'ingestion des bougies de marché.<br/>"
        "• <i>Phase d'arrêt (Shutdown)</i> : Interruption gracieuse de la boucle WebSocket Twelve Data, fermeture propre de l'ensemble "
        "des connexions clients abonnées, et libération ordonnée des sockets et du pool de connexions MongoDB.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Organisation modulaire des routeurs et middleware :</b><br/>"
        "Les points d'accès HTTP sont segmentés par domaine de responsabilité dans <code>backend/app/api/routes/</code> :<br/>"
        "• <code>health.py</code> : Surveillance de l'intégrité globale, de la base et du worker.<br/>"
        "• <code>market.py</code> : Restitution des cotations spot et des historiques de chandeliers.<br/>"
        "• <code>live_market.py</code> : Point de terminaison WebSocket <code>/api/ws/market</code> et statut de connectivité.<br/>"
        "• <code>predictions.py</code> : Inférence directionnelle binaire, double horizon et scénarios.<br/>"
        "• <code>explanations.py</code> : Décomposition des facteurs explicatifs les plus influents.<br/>"
        "• <code>performance.py</code> : Consultation des métriques réelles d'évaluation hors-échantillon.<br/>"
        "• <code>quality.py</code> : Rapport d'intégrité temporelle et de fraîcheur des bougies.<br/>"
        "Toutes les requêtes traversent un middleware de journalisation structurée qui consigne la méthode, l'URL, le temps d'exécution "
        "en millisecondes et le code de statut HTTP.",
        styles['Body']
    ))

    story.append(Paragraph("3.3 Architecture réactive Frontend Next.js 15", styles['SectionTitle']))
    story.append(Paragraph(
        "La couche de présentation est développée avec <b>Next.js 15</b> (exploitant l'architecture React 19 App Router). "
        "Elle est structurée dans <code>frontend/app/page.js</code> autour d'un ensemble de composants fonctionnels modulaires :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <code>MarketCard</code> : Affiche le cours spot courant, l'amplitude de variation absolue et en pourcentage sur 24 heures, "
        "l'horodatage UTC du dernier tick reçu et un indicateur lumineux de connectivité temps réel (vert si actif, orange si différé).<br/>"
        "• <code>PriceChart</code> : Trace l'évolution graphique des cours récents à l'aide d'un composant graphique vectoriel (SVG) "
        "léger et ultra-réactif, sans recourir à des dépendances tierces lourdes susceptibles de ralentir le navigateur.<br/>"
        "• <code>PredictionCard</code> : Affiche le biais directionnel binaire (BULLISH en vert / BEARISH en rouge), les jauges "
        "de probabilité proportionnelles, le score de confiance et le sélecteur d'horizon prévisionnel (Daily / Weekly).<br/>"
        "• <code>TechnicalPanel</code> : Tableau de bord récapitulant l'état des oscillateurs (RSI 14, MACD) et des moyennes mobiles.<br/>"
        "• <code>ScenarioPanel</code> : Présente les trois scénarios de marché (Base, Bullish, Bearish) avec leurs seuils de validation.<br/>"
        "• <code>LanguageSwitcher</code> : Composant de sélection linguistique permettant le basculement instantané entre EN, FR et AR.",
        styles['Body']
    ))

    story.append(Paragraph("3.4 Modélisation de la persistance et schémas MongoDB", styles['SectionTitle']))
    story.append(Paragraph(
        "Le choix de <b>MongoDB</b> comme système de gestion de base de données repose sur sa flexibilité documentaire "
        "et son excellente efficacité pour l'indexation de séries chronologiques. "
        "Dans le cadre strict du périmètre du PFA, cinq collections opérationnelles sont modélisées et auditées :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <code>market_data</code> : Stocke l'historique des bougies validées fermées. Chaque document enregistre le symbole "
        "(<code>XAUUSD</code>), la granularité (<code>H1</code>, <code>H4</code>, <code>M15</code>), l'horodatage UTC de clôture "
        "et les métriques numériques OHLCV (open, high, low, close, volume).<br/>"
        "2. <code>predictions</code> : Archive historique de l'ensemble des inférences produites par le système, incluant le symbole, "
        "la version du modèle, l'horizon prévisionnel, la direction (BULLISH/BEARISH), les probabilités et les contributions de features.<br/>"
        "3. <code>model_performance</code> : Consigne les métriques statistiques réelles obtenues lors des phases d'évaluation formelles "
        "(justesse, F1-score, ROC-AUC, Brier score, matrice de confusion).<br/>"
        "4. <code>ingestion_state</code> : Enregistre l'état opérationnel des workers, les horodatages des derniers cycles d'acquisition "
        "réussis et le nombre de barres collectées.<br/>"
        "5. <code>data_quality</code> : Rapports d'intégrité chronologique constatant l'absence de doublons et le statut des discontinuités de marché.",
        styles['Body']
    ))

    story.append(Paragraph("3.5 Stratégie d'indexation unique et optimisation", styles['SectionTitle']))
    story.append(Paragraph(
        "Pour prévenir tout risque de corruption de données ou de doublon lors d'écritures concurrentes ou de reprises sur incident, "
        "une stratégie d'indexation stricte est implémentée dans <code>backend/app/db/indexes.py</code> :",
        styles['Body']
    ))

    idx_data = [
        [Paragraph("Collection MongoDB", styles['TableHeader']), Paragraph("Clés d'Indexation Composées", styles['TableHeader']), Paragraph("Propriété", styles['TableHeader']), Paragraph("Justification Fonctionnelle & Performance", styles['TableHeader'])],
        [Paragraph("<code>market_data</code>", styles['TableText']), Paragraph("<code>symbol: 1, timeframe: 1, timestamp: 1</code>", styles['TableText']), Paragraph("Unique", styles['TableText']), Paragraph("Empêche l'insertion de bougies en doublon ; accélère les requêtes de fenêtres temporelles.", styles['TableText'])],
        [Paragraph("<code>predictions</code>", styles['TableText']), Paragraph("<code>symbol: 1, model_version: 1, timestamp: 1</code>", styles['TableText']), Paragraph("Unique", styles['TableText']), Paragraph("Garantit l'idempotence des enregistrements de prédiction.", styles['TableText'])],
        [Paragraph("<code>predictions</code>", styles['TableText']), Paragraph("<code>symbol: 1, timestamp: -1</code>", styles['TableText']), Paragraph("Standard", styles['TableText']), Paragraph("Optimise l'accès immédiat à la prédiction la plus récente pour l'API.", styles['TableText'])],
        [Paragraph("<code>model_performance</code>", styles['TableText']), Paragraph("<code>symbol: 1, model: 1, model_version: 1, testing_period_end: 1</code>", styles['TableText']), Paragraph("Unique", styles['TableText']), Paragraph("Historise fidèlement les métriques d'audit sans risque d'écrasement accidentel.", styles['TableText'])],
        [Paragraph("<code>ingestion_state</code>", styles['TableText']), Paragraph("<code>symbol: 1, timeframe: 1</code>", styles['TableText']), Paragraph("Unique", styles['TableText']), Paragraph("Assure un document d'état unique par flux de marché surveillé.", styles['TableText'])],
    ]
    t_idx = Table(idx_data, colWidths=[35 * mm, 45 * mm, 22 * mm, 68 * mm])
    t_idx.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_idx)
    story.append(Paragraph("Tableau 3.1 : Stratégie d'indexation MongoDB pour les collections du périmètre PFA", styles['Caption']))

    story.append(Paragraph("3.6 Conception des flux de communication (WebSocket & REST)", styles['SectionTitle']))
    story.append(Paragraph(
        "L'échange de données entre le client et le serveur articule deux mécanismes complémentaires adaptés à leurs cas d'usage :<br/>"
        "• <b>Flux de streaming réactif (WebSocket / <code>/api/ws/market</code>)</b> : Fonctionne selon un modèle Publish/Subscribe "
        "interne. Chaque client ouvrant une connexion se voit allouer une file asynchrone privée <code>asyncio.Queue</code>. "
        "Le singleton <code>LiveMarketService</code> consomme le flux de Twelve Data et dépose chaque tick dans toutes les files clientes actives. "
        "Ce mécanisme évite toute contention de verrou et isole les clients lents des clients rapides.<br/>"
        "• <b>Protocole requête/réponse synchrone (REST / HTTP)</b> : Réservé aux opérations nécessitant un calcul déterministe lourd "
        "(génération des prédictions, reconstruction de la matrice de 87 features, consultation de l'historique). "
        "Les contrats de données échangés sont rigoureusement sérialisés et validés par Pydantic V2.",
        styles['Body']
    ))

    story.append(Paragraph("3.7 Diagrammes d'architecture, de séquence et de données", styles['SectionTitle']))
    story.append(Paragraph(
        "L'ensemble des interactions conceptuelles du système a été formalisé dans le formalisme UML "
        "et archivé sous forme de fichiers sources textuels dans le répertoire <code>docs/uml/</code> :<br/>"
        "• <b>Architecture générale</b> : <code>docs/uml/architecture.puml</code> formalise les couches logicielles et protocoles.<br/>"
        "• <b>Séquence d'inférence</b> : <code>docs/uml/sequence_prediction.puml</code> détaille le cycle d'appel de prédiction.<br/>"
        "• <b>Séquence WebSocket</b> : <code>docs/uml/sequence_websocket.puml</code> retrace l'ingestion et la distribution de ticks.<br/>"
        "• <b>Modèle de données</b> : <code>docs/uml/database.puml</code> décrit les collections et contraintes d'intégrité MongoDB.",
        styles['Body']
    ))
    story.append(PageBreak())

    return story

