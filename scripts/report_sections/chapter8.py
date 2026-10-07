"""Chapitre 8 — Déploiement et DevOps."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, BORDER_COLOR, HIGHLIGHT, LIGHT_BG

def get_chapter8_story(styles):
    story = []

    story.append(Paragraph("Chapitre 8 — Déploiement et DevOps", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("8.1 Conteneurisation Docker multi-services", styles['SectionTitle']))
    story.append(Paragraph(
        "Pour éliminer toute disparité d'environnement entre les postes de développement et les infrastructures d'hébergement, "
        "l'ensemble de la plateforme est conteneurisé à l'aide de la technologie <b>Docker</b>. "
        "Deux images spécialisées et optimisées sont configurées :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Image Backend FastAPI (<code>backend/Dockerfile</code>) :</b><br/>"
        "Construite sur l'image de base officielle allégée <code>python:3.13-slim</code>. "
        "Le fichier copie les spécifications de dépendances <code>requirements.txt</code>, procède à l'installation isolée des packages "
        "Python sans conservation de cache (<code>pip install --no-cache-dir</code>), injecte l'arborescence applicative <code>app/</code> "
        "et expose le port réseau 8000. Le démarrage est confié au serveur ASGI Uvicorn : "
        "<code>uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}</code>.",
        styles['Body']
    ))

    code_docker_be = (
        'FROM python:3.13-slim\n'
        'WORKDIR /app\n'
        'COPY requirements.txt .\n'
        'RUN pip install --no-cache-dir -r requirements.txt\n'
        'COPY app ./app\n'
        'EXPOSE 8000\n'
        'CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]\n'
    )
    t_dbe = Table([[Paragraph(f"<pre>{code_docker_be}</pre>", styles['CodeSnippet'])]], colWidths=[170 * mm])
    t_dbe.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t_dbe)
    story.append(Paragraph("Listing 8.1 : Spécification Dockerfile du Backend (backend/Dockerfile)", styles['Caption']))

    story.append(Paragraph(
        "• <b>Image Frontend Next.js (<code>frontend/Dockerfile</code>) :</b><br/>"
        "Construite sur l'image ultra-légère <code>node:24-alpine</code>. "
        "Elle gère les arguments de build d'environnement (<code>ARG NEXT_PUBLIC_API_URL</code>), installe les dépendances npm, "
        "exécute la compilation de production optimisée <code>npm run build</code>, expose le port réseau 3000 "
        "et démarre le serveur de production via <code>npm start</code>.",
        styles['Body']
    ))

    code_docker_fe = (
        'FROM node:24-alpine\n'
        'WORKDIR /app\n'
        'ARG NEXT_PUBLIC_API_URL=http://localhost:8000\n'
        'ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL\n'
        'COPY package.json .\n'
        'RUN npm install\n'
        'COPY . .\n'
        'RUN npm run build\n'
        'EXPOSE 3000\n'
        'CMD ["npm", "start"]\n'
    )
    t_dfe = Table([[Paragraph(f"<pre>{code_docker_fe}</pre>", styles['CodeSnippet'])]], colWidths=[170 * mm])
    t_dfe.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t_dfe)
    story.append(Paragraph("Listing 8.2 : Spécification Dockerfile du Frontend (frontend/Dockerfile)", styles['Caption']))

    story.append(Paragraph("8.2 Orchestration locale Docker Compose et healthchecks", styles['SectionTitle']))
    story.append(Paragraph(
        "L'orchestration locale des conteneurs est définie dans le fichier <code>docker-compose.yml</code> à la racine du dépôt. "
        "Ce descripteur met en œuvre un mécanisme de dépendance conditionnelle stricte (<i>healthcheck chaining</i>) :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Surveillance de santé du Backend (<code>healthcheck</code>) :</b><br/>"
        "Le conteneur backend exécute périodiquement une sonde HTTP interrogeant le point d'accès <code>http://localhost:8000/api/health</code> "
        "(intervalle de 30 secondes, délai d'attente de 5 secondes, 3 tentatives consécutives). Le conteneur n'est déclaré sain "
        "(<code>healthy</code>) que lorsque l'API répond avec succès.<br/>"
        "• <b>Démarrage conditionnel du Frontend (<code>depends_on</code>) :</b><br/>"
        "Le service frontend déclare une dépendance sur le backend avec la clause <code>condition: service_healthy</code>. "
        "Cette disposition garantit que l'interface graphique ne démarre que lorsque le backend FastAPI est pleinement opérationnel "
        "et capable de traiter les requêtes de données et les connexions WebSocket, évitant tout affichage d'erreur réseau au chargement initial.",
        styles['Body']
    ))

    code_compose = (
        'services:\n'
        '  backend:\n'
        '    build: ./backend\n'
        '    env_file:\n'
        '      - path: .env\n'
        '        required: false\n'
        '    ports: ["8000:8000"]\n'
        '    healthcheck:\n'
        '      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen(\'http://localhost:8000/api/health\')"]\n'
        '      interval: 30s\n'
        '      timeout: 5s\n'
        '      retries: 3\n'
        '  frontend:\n'
        '    build: ./frontend\n'
        '    environment: ["NEXT_PUBLIC_API_URL=http://localhost:8000"]\n'
        '    ports: ["3000:3000"]\n'
        '    depends_on:\n'
        '      backend:\n'
        '        condition: service_healthy\n'
    )
    t_cmp = Table([[Paragraph(f"<pre>{code_compose}</pre>", styles['CodeSnippet'])]], colWidths=[170 * mm])
    t_cmp.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR), ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t_cmp)
    story.append(Paragraph("Listing 8.3 : Fichier d'orchestration multi-services (docker-compose.yml)", styles['Caption']))

    story.append(Paragraph("8.3 Configuration de déploiement cloud (Railway & Vercel)", styles['SectionTitle']))
    story.append(Paragraph(
        "Le dépôt contient les descripteurs de configuration requis pour un déploiement cloud distribué :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Déploiement Backend sur Railway :</b><br/>"
        "Configuré via <code>Dockerfile.railway</code> et <code>railway.toml</code>. "
        "Le descripteur <code>railway.toml</code> spécifie le constructeur Docker, le chemin de la sonde de vie "
        "<code>healthcheckPath = \"/api/health\"</code> et un délai d'attente de 30 secondes. "
        "Le fichier <code>Dockerfile.railway</code> embarque les répertoires de modèles sérialisés (<code>models/xauusd/</code> "
        "et <code>models/xauusd_weekly/</code>) ainsi que les données nettoyées requises pour l'inférence en production.<br/>"
        "• <b>Déploiement Frontend sur Vercel :</b><br/>"
        "Documenté dans <code>DEPLOYMENT.md</code>. La configuration prévoit le déploiement de l'application Next.js sur l'infrastructure "
        "Edge de Vercel, avec injection de la variable d'environnement <code>NEXT_PUBLIC_API_URL</code> pointant vers le nom d'hôte Railway.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Mention d'audit obligatoire concernant le déploiement cloud :</b><br/>"
        "<i>« Configuration de déploiement présente ; déploiement cloud non vérifié dans le présent audit local. »</i><br/>"
        "L'audit certifie que les fichiers de configuration (<code>Dockerfile.railway</code>, <code>railway.toml</code>, <code>DEPLOYMENT.md</code>) "
        "sont formellement présents, syntaxiquement valides et cohérents avec l'architecture. Néanmoins, l'existence d'une instance "
        "cloud distante en activité ne peut être certifiée dans le cadre d'un audit de code local statique.",
        styles['Callout']
    ))

    story.append(Paragraph("8.4 Intégration MongoDB Atlas et gestion des environnements", styles['SectionTitle']))
    story.append(Paragraph(
        "L'intégration avec le service de base de données managé <b>MongoDB Atlas</b> est documentée dans <code>DEPLOYMENT.md</code> "
        "et configurée au niveau applicatif par la variable <code>MONGODB_URI</code>. "
        "Conformément aux principes de rigueur, l'audit établit la distinction essentielle à trois niveaux :",
        styles['Body']
    ))
    story.append(Paragraph(
        "1. <b>Intégration logicielle MongoDB :</b> Pleinement implémentée dans le code source (<code>backend/app/db/client.py</code>). "
        "Le gestionnaire <code>MongoClientManager</code> assure la connexion asynchrone via Motor, la création des index uniques "
        "et la reconnexion automatique en cas de déconnexion transitoire.<br/>"
        "2. <b>Configuration Atlas :</b> Présente dans les fichiers de configuration d'exemple (<code>.env.example</code>) "
        "et la documentation de déploiement.<br/>"
        "3. <b>État runtime vérifié :</b> Lors de l'exécution de la suite de tests et de l'audit local, le système fonctionne "
        "avec une instance MongoDB locale accessible, ou gère gracieusement le statut dégradé <code>DISCONNECTED</code> "
        "sans interruption du serveur. L'activité opérationnelle réelle d'un cluster distant Atlas n'a pas fait l'objet "
        "d'une vérification runtime externe.",
        styles['Body']
    ))

    story.append(Paragraph("8.5 Variables d'environnement et matrice de déploiement", styles['SectionTitle']))
    story.append(Paragraph(
        "Le Tableau 8.1 récapitule les variables d'environnement configurées dans le système et leur statut :",
        styles['Body']
    ))

    env_table = [
        [Paragraph("Variable d'Environnement", styles['TableHeader']), Paragraph("Rôle Fonctionnel", styles['TableHeader']), Paragraph("Exemple / Valeur par Défaut", styles['TableHeader']), Paragraph("Environnement Cible", styles['TableHeader'])],
        [Paragraph("<code>TWELVE_DATA_API_KEY</code>", styles['TableText']), Paragraph("Clé d'authentification Twelve Data REST & WebSocket", styles['TableText']), Paragraph("Chaîne secrète (32 caractères)", styles['TableText']), Paragraph("Backend (Railway / Local)", styles['TableText'])],
        [Paragraph("<code>MONGODB_URI</code>", styles['TableText']), Paragraph("Chaîne de connexion MongoDB / Motor", styles['TableText']), Paragraph("<code>mongodb://localhost:27017</code>", styles['TableText']), Paragraph("Backend (Railway / Atlas)", styles['TableText'])],
        [Paragraph("<code>DATABASE_NAME</code>", styles['TableText']), Paragraph("Nom de la base de données MongoDB", styles['TableText']), Paragraph("<code>market_intelligence</code>", styles['TableText']), Paragraph("Backend (Tous)", styles['TableText'])],
        [Paragraph("<code>PORT</code>", styles['TableText']), Paragraph("Port d'écoute HTTP du serveur ASGI", styles['TableText']), Paragraph("<code>8000</code>", styles['TableText']), Paragraph("Backend (Railway dyn.)", styles['TableText'])],
        [Paragraph("<code>NEXT_PUBLIC_API_URL</code>", styles['TableText']), Paragraph("URL d'accès public à l'API FastAPI", styles['TableText']), Paragraph("<code>http://localhost:8000</code>", styles['TableText']), Paragraph("Frontend (Vercel / Local)", styles['TableText'])],
    ]
    t_env = Table(env_table, colWidths=[45 * mm, 50 * mm, 45 * mm, 30 * mm])
    t_env.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_env)
    story.append(Paragraph("Tableau 8.1 : Spécification des variables d'environnement applicatives", styles['Caption']))

    story.append(Spacer(1, 4 * mm))

    deploy_summary = [
        [Paragraph("Composant Applicatif", styles['TableHeader']), Paragraph("Cible d'Hébergement", styles['TableHeader']), Paragraph("Fichiers Descripteurs Présents", styles['TableHeader']), Paragraph("Statut Formel de l'Audit Local", styles['TableHeader'])],
        [Paragraph("<b>Backend API & WS</b>", styles['TableText']), Paragraph("Railway Cloud", styles['TableText']), Paragraph("<code>Dockerfile.railway</code><br/><code>railway.toml</code>", styles['TableText']), Paragraph("Configuration présente ; déploiement cloud non vérifié dans le présent audit local.", styles['TableText'])],
        [Paragraph("<b>Frontend Next.js</b>", styles['TableText']), Paragraph("Vercel Edge", styles['TableText']), Paragraph("<code>frontend/package.json</code><br/><code>DEPLOYMENT.md</code>", styles['TableText']), Paragraph("Configuration présente ; déploiement cloud non vérifié dans le présent audit local.", styles['TableText'])],
        [Paragraph("<b>Base de données</b>", styles['TableText']), Paragraph("MongoDB Atlas", styles['TableText']), Paragraph("<code>app/db/client.py</code><br/><code>.env.example</code>", styles['TableText']), Paragraph("Intégration logicielle implémentée ; cluster distant non vérifié dans le présent audit local.", styles['TableText'])],
        [Paragraph("<b>Conteneurisation Locale</b>", styles['TableText']), Paragraph("Docker Engine", styles['TableText']), Paragraph("<code>docker-compose.yml</code><br/><code>backend/Dockerfile</code><br/><code>frontend/Dockerfile</code>", styles['TableText']), Paragraph("<font color='#1B4D3E'><b>Vérifié et conforme</b> (Orchestration locale fonctionnelle avec healthchecks).</font>", styles['TableText'])],
    ]
    t_ds = Table(deploy_summary, colWidths=[35 * mm, 30 * mm, 50 * mm, 55 * mm])
    t_ds.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_ds)
    story.append(Paragraph("Tableau 8.2 : Matrice de configuration et statut d'audit des environnements de déploiement", styles['Caption']))
    story.append(PageBreak())

    return story

