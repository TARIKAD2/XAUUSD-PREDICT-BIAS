# Rapport PFA — AI Market Intelligence

## Résumé exécutif

**AI Market Intelligence** est une application web de recherche et d’aide à la décision pour l’analyse de l’or **XAU/USD**. Elle combine des données de marché, des indicateurs techniques, des actualités financières, des données macro-économiques et des modèles de machine learning. L’application ne passe pas d’ordres et ne constitue pas un conseil financier.

Le système est organisé en deux parties :

- un backend Python/FastAPI qui collecte, normalise, stocke et expose les données ;
- un frontend Next.js qui affiche le dashboard d’analyse.

MongoDB assure la persistance. Les fournisseurs externes comprennent notamment Twelve Data pour les données de marché, Marketaux pour les actualités, FinanceCalendar pour le calendrier courant, ainsi que FRED, ALFRED, BLS et BEA pour les données macro-économiques et historiques. Le projet contient également une chaîne de features techniques, un pipeline ML chronologique, des prédictions, des scénarios et des explications.

L’état réel doit être interprété avec prudence : les routes et les services sont implémentés, mais la disponibilité des données, des clés API, de MongoDB et des artefacts de modèles conditionne le résultat affiché. Les données manquantes doivent être signalées comme indisponibles et non remplacées par des valeurs inventées.

## 1. Présentation du projet

| Élément | Description |
|---|---|
| Nom | AI Market Intelligence — XAUUSD |
| Type | Application web full-stack de recherche |
| Domaine | Marchés financiers, analyse quantitative et machine learning |
| Actif principal | Or contre dollar américain, XAU/USD |
| Utilisateurs ciblés | Étudiants, chercheurs, analystes et utilisateurs réalisant une analyse de marché |
| Objectif | Centraliser des données vérifiées et produire une analyse probabiliste interprétable |
| Limite | Aucun passage d’ordre et aucune garantie de rendement |

### Problématique

Les informations utiles à l’analyse de l’or sont dispersées entre plusieurs sources. Le projet cherche à les réunir dans une interface unique, à les normaliser, à éviter les fuites temporelles dans les données ML et à exposer clairement les états `loading`, `unavailable`, `NO_DATA` et `MODEL_NOT_READY`.

### Fonctionnement général

```text
Fournisseurs externes
        ↓
Collectors / Providers
        ↓
Validation et normalisation
        ↓
MongoDB
        ↓
Features techniques et dataset chronologique
        ↓
Services FastAPI
        ↓
Client REST / WebSocket Next.js
        ↓
Dashboard XAUUSD
```

## 2. Structure du dépôt

```text
AI_XAUUSD/
├── backend/
│   ├── app/
│   │   ├── api/          Routes FastAPI, middleware et erreurs
│   │   ├── collectors/   Collecte et normalisation de données
│   │   ├── core/         Configuration et logging
│   │   ├── data/         Transformations de données et features multi-timeframes
│   │   ├── db/           Client MongoDB, collections et repositories
│   │   ├── features/     Features canoniques, techniques et structurelles
│   │   ├── ml/           Dataset, labels, modèles, calibration et backtest
│   │   ├── models/       Modèles de données applicatifs
│   │   ├── providers/    FinanceCalendar et Trading Economics
│   │   ├── schemas/      Contrats Pydantic des APIs
│   │   └── services/     Logique métier
│   ├── tests/            Tests pytest
│   └── requirements.txt  Dépendances Python
├── frontend/
│   ├── app/              Routes App Router et dashboard
│   ├── components/       Composants React réutilisables
│   ├── context/          Contexte de langue
│   ├── locales/          Catalogues EN/FR/AR
│   ├── services/         Clients REST et WebSocket
│   └── styles/           Styles globaux
├── scripts/              Ingestion, backfill, construction et entraînement
├── models/               Artefacts de modèles lorsqu’ils sont disponibles
├── .env.example          Exemple de configuration sans secret
├── docker-compose.yml    Orchestration locale
├── PROJECT_ARCHITECTURE.md
└── README.md
```

## 3. Architecture logicielle

### Frontend

Le frontend utilise Next.js App Router et React. La page principale est [frontend/app/page.js](frontend/app/page.js). Elle compose les panneaux de marché, prediction, techniques, scénarios et explication. Les composants sont séparés dans `frontend/components`.

Le client REST centralisé se trouve dans `frontend/services/api.js`. Le flux temps réel est géré par `frontend/services/liveMarket.js`. Le contexte de langue dans `frontend/context/LanguageContext.js` fournit les traductions anglaise, française et arabe.

### Backend

Le point d’entrée est [backend/app/main.py](backend/app/main.py). Il crée l’application FastAPI, configure CORS, enregistre les routes, connecte MongoDB et démarre les services de worker et de marché live dans le cycle de vie ASGI.

Les routes délèguent la logique aux services. Les services utilisent les repositories MongoDB et les collectors/providers. Les schémas Pydantic valident les contrats entrants et sortants.

### Temps réel

Le service de marché live se connecte au fournisseur Twelve Data et expose un flux WebSocket consommé par le frontend. Le dashboard met à jour le prix, le statut de connexion et les informations de fraîcheur. La reconnexion et les états indisponibles sont représentés par le client live.

### Authentification

**NON TROUVÉE dans le code actuel.** L’API utilise CORS et des secrets côté backend, mais aucun système utilisateur, JWT, session ou contrôle d’autorisation n’est identifié.

## 4. Technologies réellement configurées

| Technologie | Version/configuration | Utilisation |
|---|---|---|
| Python | Version déterminée par l’environnement `.venv` | Backend, ingestion et ML |
| FastAPI | `>=0.115,<1.0` | API HTTP et WebSocket |
| Uvicorn | `>=0.30,<1.0` | Serveur ASGI |
| Pydantic Settings | `>=2.6,<3.0` | Configuration par variables d’environnement |
| MongoDB | Motor/PyMongo | Persistance asynchrone et repositories |
| Next.js | `^15.0.0` | Application frontend |
| React | `^19.0.0` | Interface utilisateur |
| NumPy / pandas / SciPy | Configurés dans requirements | Manipulation et analyse de données |
| scikit-learn | `>=1.5,<2.0` | Modèles, calibration et métriques |
| XGBoost / LightGBM | Configurés dans requirements | Modèles avancés |
| SHAP | `>=0.46,<1.0` | Explicabilité des modèles supportés |
| pytest / httpx | Configurés dans requirements | Tests backend et clients HTTP |
| Docker Compose | Présent dans le dépôt | Exécution conteneurisée |

## 5. Fonctionnalités

| Fonctionnalité | Backend | Frontend | Statut |
|---|---|---|---|
| Santé de l’application | `/api/health` | Ruban d’état | COMPLET sous réserve de MongoDB |
| Marché XAUUSD | `/api/market` et `/api/market/{symbol}` | MarketCard, graphique | PARTIEL selon provider/données |
| Flux live | `/ws/market` et statut live | `liveMarket.js` | PARTIEL selon disponibilité Twelve Data |
| Prédiction | `/api/predictions/{symbol}` | PredictionCard | PARTIEL si artefact absent |
| Explication | `/api/explanations/{symbol}` | ExplanationPanel | PARTIEL selon modèle et données |
| Scénarios | Données de prédiction | ScenarioPanel | PARTIEL selon données |
| Indicateurs techniques | `features/technical.py` | TechnicalPanel | PARTIEL selon candles |
| Actualités | `/api/news` | NewsCard | PARTIEL selon Marketaux/API key |
| Calendrier économique | `/api/economic-events` | Service et composants conservés | BACKEND COMPLET, affichage dashboard masqué |
| Qualité des données | `/api/data-quality` | QualityPanel conservé | BACKEND COMPLET, affichage dashboard masqué |
| Performance OOS | `/api/model-performance` | PerformancePanel conservé | PARTIEL selon métriques stockées, affichage masqué |
| Internationalisation | Catalogues EN/FR/AR | LanguageContext | COMPLET pour les surfaces intégrées |

## 6. Frontend

### Routes

| Route | Rôle |
|---|---|
| `/` | Dashboard principal XAUUSD |
| `/war-room/[eventId]` | Vue War Room associée à un événement |
| `/_not-found` | Page de route inconnue |

Le dashboard visible conserve les sections de marché live, prédiction, techniques, scénarios et explication. Les sections Economic Calendar, Market News & Sentiment, Model Performance et Data Quality & Health ne sont plus rendues dans le dashboard principal, mais leurs composants, appels backend et clés de traduction restent présents dans le dépôt.

### États d’interface

Les composants utilisent des états de chargement et d’erreur. Le composant `StatusPanel` affiche les messages correspondants quand une API est indisponible ou qu’aucune donnée n’est disponible.

### Localisation

Les fichiers `frontend/locales/en.json`, `fr.json` et `ar.json` contiennent les catalogues. Le changement de langue est géré par `LanguageContext` et le mode arabe conserve la direction RTL prévue. Les clés de traduction des sections masquées ne sont pas supprimées.

## 7. Backend et API

Les routes sont assemblées dans [backend/app/api/routes/router.py](backend/app/api/routes/router.py).

| Méthode | Endpoint | Rôle |
|---|---|---|
| GET | `/api/health` | État API, base et worker |
| GET | `/api/market` | Dernières données de marché |
| GET | `/api/market/{symbol}` | Bougies d’un symbole |
| GET | `/api/news` | Actualités filtrées |
| GET | `/api/economic-events` | Calendrier économique et statuts fournisseurs |
| GET | `/api/predictions/{symbol}` | Prédiction du modèle |
| GET | `/api/model-performance` | Métriques enregistrées |
| GET | `/api/data-quality` | Qualité des données |
| GET | `/api/explanations/{symbol}` | Explications de prédiction |
| GET | `/api/war-room/{event_id}` | Données War Room |
| WebSocket | `/ws/market` | Flux de prix live |

Les routes retournent des erreurs explicites lorsque les données, la base ou le modèle ne sont pas disponibles. Le projet n’utilise pas de fallback silencieux pour fabriquer des valeurs.

## 8. Base de données

La base configurée est MongoDB, généralement nommée `ai_market_intelligence`.

| Collection | Usage |
|---|---|
| `market_data` | Bougies de marché |
| `news` | Actualités financières |
| `economic_events` | Événements macro-économiques |
| `features` | Features calculées |
| `predictions` | Résultats de prédiction |
| `model_metrics` | Métriques techniques |
| `model_performance` | Résultats walk-forward/OOS |
| `model_registry` | Métadonnées d’artefacts |
| `ingestion_state` | État des collectes |
| `data_quality` | Contrôles de qualité |
| `datasets` | Jeux de données |
| `system_logs` | Journaux applicatifs |
| `war_rooms` | Données de vues War Room |

Les repositories effectuent des opérations d’upsert. Les indexes sont définis dans `backend/app/db/indexes.py`; l’architecture documente notamment l’unicité des candles par symbole, timeframe et timestamp, ainsi que la déduplication des news et événements.

## 9. Fournisseurs externes

| Fournisseur | Données | Configuration |
|---|---|---|
| Twelve Data | Candles, marché et flux live | `TWELVE_DATA_API_KEY` |
| Marketaux | News financières et sentiment | `MARKETAUX_API_KEY` |
| FinanceCalendar | Calendrier courant programmé | Activé sans clé, attribution requise |
| Trading Economics | Fallback calendrier optionnel | `TRADING_ECONOMICS_API_KEY` |
| FRED / ALFRED | Séries macro et vintages historiques | `FRED_API_KEY` |
| BLS | CPI, emploi et statistiques US | `BLS_API_KEY` si nécessaire |
| BEA | PIB, PCE et comptes nationaux | `BEA_API_KEY` si nécessaire |

FinanceCalendar est utilisé en priorité pour le calendrier courant. Les événements du jour sont filtrés avec le jour et le fuseau configurés. Un décalage de date fournisseur produit `NO_DATA` plutôt qu’un affichage de données anciennes. ALFRED reste séparé pour les usages point-in-time et backtesting.

## 10. Données et machine learning

Le pipeline ML comprend :

- construction de datasets à partir de bougies clôturées ;
- features techniques et structurelles ;
- labels directionnels `BEARISH`, `NEUTRAL`, `BULLISH` ;
- séparation chronologique ;
- backtesting walk-forward ;
- calibration de probabilités ;
- modèles scikit-learn, XGBoost et LightGBM lorsqu’ils sont configurés ;
- explicabilité SHAP pour les estimateurs compatibles ;
- registre et chargement d’artefacts.

Le principe anti-lookahead est documenté : une observation au temps `T` ne doit utiliser que des données disponibles à `T`, tandis que la cible est calculée sur une période future isolée. Un modèle n’est pas considéré comme prêt seulement parce que le code d’entraînement existe ; l’API vérifie la présence d’un artefact utilisable.

## 11. Sécurité et limites

### Mesures présentes

- variables d’environnement pour les secrets ;
- absence de secrets dans le frontend ;
- CORS configurable ;
- validation Pydantic ;
- logging des requêtes ;
- erreurs explicites et contrôle de disponibilité ;
- recommandations de compte MongoDB à privilèges limités.

### Éléments manquants ou à renforcer

- aucune authentification utilisateur identifiée ;
- aucune autorisation par rôle identifiée ;
- les clés API dépendent de la configuration de déploiement ;
- les limites et licences des fournisseurs doivent être respectées ;
- les données financières ne doivent pas être présentées comme une garantie de résultat.

## 12. Tests et validation

Le backend utilise pytest et httpx. Les tests couvrent les contrats, la configuration, les collectors, le marché live, les features, le ML, le calendrier économique, l’ingestion et la War Room.

La dernière validation connue de la suite backend est :

```text
113 passed, 5 warnings
```

Les warnings sont des avertissements de dépréciation de dépendances. Le frontend est construit avec :

```powershell
Set-Location frontend
npm run build
```

La validation finale doit être relancée après toute modification. Les données des fournisseurs et l’état de MongoDB peuvent modifier les résultats runtime sans modifier le code.

## 13. Déploiement

### Développement local

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
Set-Location ..\frontend
npm install
npm run dev
```

### Docker

Le dépôt contient une configuration Docker Compose. Les secrets restent dans `.env` ou dans le gestionnaire de secrets du fournisseur de déploiement.

### Déploiement possible

La documentation existante décrit un déploiement backend sur Railway, frontend sur Vercel et base sur MongoDB Atlas. Les origines CORS et `NEXT_PUBLIC_API_URL` doivent être adaptées à l’environnement réel.

## 14. Workflow d’une donnée de marché

```text
Twelve Data
    ↓
LiveMarketService / collector market
    ↓
Validation et normalisation
    ↓
MongoDB market_data
    ↓
Features techniques et structurelles
    ↓
Service de prédiction
    ↓
FastAPI
    ↓
Client REST / WebSocket Next.js
    ↓
MarketCard, PriceChart, TechnicalPanel, PredictionCard
```

## 15. Limitations connues

| Limitation | Impact | Réponse actuelle |
|---|---|---|
| Fournisseur ou clé API indisponible | Données absentes | Statut d’indisponibilité explicite |
| Artefact ML absent | Pas de prédiction fiable | `MODEL_NOT_READY` ou état indisponible |
| Date FinanceCalendar différente du jour applicatif | Calendrier vide | Exclusion stricte, `NO_DATA`, aucun fallback historique |
| Consensus absent de FRED/BLS/BEA | Surprise impossible | `forecast` et `surprise` restent nuls |
| Pas d’authentification | API non adaptée à un espace multi-utilisateur | À ajouter avant exposition publique |
| Quotas fournisseurs | Collecte limitée | Cache, retries bornés et configuration à respecter |
| Données de marché réelles indisponibles | Graphiques et features incomplets | États loading/unavailable |

## 16. Conclusion PFA

Le projet constitue une base full-stack cohérente pour une plateforme de recherche quantitative sur XAU/USD. Sa valeur principale réside dans l’intégration de plusieurs sources, la séparation des responsabilités entre routes, services, collectors et repositories, ainsi que la prise en compte de la causalité temporelle dans le pipeline ML.

Le système est fonctionnel comme plateforme de recherche lorsque MongoDB, les providers et les artefacts nécessaires sont disponibles. Les résultats doivent toujours être interprétés selon leur statut de fraîcheur et de disponibilité. Les prochaines améliorations prioritaires sont l’authentification, l’observabilité de production, la validation systématique des quotas fournisseurs et l’élargissement des tests frontend/end-to-end.

## 17. Références internes

- [README principal](README.md)
- [Architecture](PROJECT_ARCHITECTURE.md)
- [API research](README_API.md)
- [Configuration exemple](.env.example)
- [Backend](backend/)
- [Frontend](frontend/)
