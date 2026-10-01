# Rapport Technique — AI Market Intelligence (XAUUSD)
### Projet de Fin d'Études (PFE)
*Généré le 17 septembre 2026*

---

## 1. Vue d'ensemble du projet

**Nom :** AI Market Intelligence – XAUUSD  
**Objectif :** Plateforme de recherche et d'aide à la décision pour l'analyse du cours de l'or (XAU/USD) en temps réel, basée sur l'apprentissage automatique.  
**Type :** Application web full-stack (Non-commerciale, recherche uniquement)  
**Architecture :** Backend Python/FastAPI + Base de données MongoDB Atlas + Frontend Next.js

```
Twelve Data WebSocket
        │ ticks temps réel
        ▼
  LiveMarketService (Python)
        │ diffusion via WebSocket
        ▼
  FastAPI (port 8000)
        │ REST + WebSocket
        ▼
  Dashboard Next.js (port 3000)
```

---

## 2. Structure des fichiers

```
AI_XAUUSD/
├── backend/
│   ├── app/
│   │   ├── main.py                    ← Point d'entrée FastAPI
│   │   ├── core/
│   │   │   ├── config.py              ← Paramètres centralisés (Pydantic)
│   │   │   └── logging.py             ← Logging structuré
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── router.py          ← Registre des routes API
│   │   │   │   ├── health.py          ← GET /api/health
│   │   │   │   ├── market.py          ← GET /api/market, /api/market/{symbol}
│   │   │   │   ├── predictions.py     ← GET /api/predictions/{symbol}
│   │   │   │   ├── live_market.py     ← WS /ws/market, GET /api/market/live-status
│   │   │   │   ├── news.py            ← GET /api/news
│   │   │   │   ├── economic.py        ← GET /api/economic-events
│   │   │   │   ├── performance.py     ← GET /api/model-performance
│   │   │   │   ├── quality.py         ← GET /api/data-quality
│   │   │   │   └── explanations.py    ← GET /api/explanations/{symbol}
│   │   │   ├── errors.py              ← Gestionnaires d'erreurs HTTP
│   │   │   └── middleware.py          ← Logging des requêtes
│   │   ├── services/
│   │   │   ├── live_market.py         ← Connexion WebSocket Twelve Data (singleton)
│   │   │   ├── market.py              ← Lecture des bougies depuis MongoDB
│   │   │   ├── predictions.py         ← Chargement et exécution du modèle ML
│   │   │   ├── model_registry.py      ← Enregistrement des artefacts de modèle
│   │   │   ├── performance.py         ← Métriques de performance des modèles
│   │   │   ├── quality.py             ← Évaluation de la qualité des données
│   │   │   ├── economic.py            ← Données macro-économiques
│   │   │   ├── news.py                ← Actualités financières
│   │   │   ├── explanations.py        ← Explications SHAP
│   │   │   ├── ingestion_worker.py    ← Worker périodique de collecte
│   │   │   └── availability.py        ← Garde de disponibilité des features
│   │   ├── features/
│   │   │   ├── canonical.py           ← Contrat de features (v2.0)
│   │   │   ├── technical.py           ← Indicateurs techniques (SMA, RSI, MACD…)
│   │   │   └── structure.py           ← Features de structure (POC, FVG, Order Block)
│   │   ├── ml/
│   │   │   ├── training.py            ← Pipeline d'entraînement + recherche HP
│   │   │   ├── dataset.py             ← Construction du dataset (bougies fermées)
│   │   │   ├── backtest.py            ← Validation walk-forward chronologique
│   │   │   ├── calibration.py         ← Calibration des probabilités (Platt)
│   │   │   ├── labels.py              ← Encodage BEARISH/NEUTRAL/BULLISH
│   │   │   ├── baseline.py            ← Modèles de référence
│   │   │   └── advanced.py            ← XGBoost/LightGBM + SHAP
│   │   ├── collectors/
│   │   │   ├── market.py              ← Collecteur Twelve Data REST (bougies H1)
│   │   │   └── news.py                ← Collecteur d'actualités
│   │   ├── db/
│   │   │   ├── client.py              ← Client MongoDB (Motor async)
│   │   │   ├── collections.py         ← Noms des collections
│   │   │   └── repositories.py        ← Opérations upsert génériques
│   │   ├── schemas/
│   │   │   └── market.py              ← Schémas Pydantic (AssetSymbol, Timeframe…)
│   │   └── models/                    ← Modèles ORM MongoDB (non-SQL)
│   └── tests/                         ← Suite de tests pytest (27 tests)
├── frontend/
│   ├── app/
│   │   ├── page.js                    ← Dashboard principal (Next.js App Router)
│   │   └── layout.js                  ← Mise en page globale
│   ├── components/
│   │   ├── MarketCard.js              ← Affichage prix XAUUSD
│   │   ├── PredictionCard.js          ← Carte de prédiction ML
│   │   ├── TechnicalPanel.js          ← Indicateurs techniques (SMA 200, RSI…)
│   │   ├── PriceChart.js              ← Graphique des prix (SVG inline)
│   │   ├── ScenarioPanel.js           ← Scénarios Base/Bullish/Bearish
│   │   ├── ExplanationPanel.js        ← Contributions des features (SHAP)
│   │   ├── EconomicEventCard.js       ← Calendrier économique
│   │   ├── NewsCard.js                ← Actualités
│   │   ├── PerformancePanel.js        ← Métriques du modèle
│   │   ├── QualityPanel.js            ← Qualité des données
│   │   ├── ProbabilityBar.js          ← Barre de probabilité
│   │   ├── ConfidenceBadge.js         ← Badge de confiance
│   │   └── StatusPanel.js             ← Panneau état/erreur
│   └── services/
│       ├── api.js                     ← Client REST vers FastAPI
│       └── liveMarket.js              ← Client WebSocket (prix temps réel)
├── scripts/
│   ├── train_xauusd.py                ← Script d'entraînement (grid search multi-horizon)
│   ├── ingest_all_markets.py          ← Ingestion des bougies H1
│   ├── ingest_news.py                 ← Ingestion des actualités
│   ├── ingest_economic.py             ← Ingestion des données économiques
│   └── backfill_xauusd.py             ← Backfill de l'historique
├── data/
│   └── models/                        ← Artefacts .joblib des modèles entraînés
├── .env                               ← Clés API (non versionné)
├── docker-compose.yml                 ← Configuration Docker
└── README.md
```

---

## 3. Ce qui fonctionne ✅

### 3.1 Connexion données temps réel (Twelve Data WebSocket)
| Élément | État |
|---------|------|
| Connexion `wss://ws.twelvedata.com` | ✅ Opérationnel |
| Abonnement XAU/USD uniquement | ✅ Configuré |
| Réception des ticks en temps réel | ✅ Vérifié (13+ ticks en 30s) |
| Reconnexion automatique (backoff exponentiel) | ✅ Implémenté |
| Diffusion vers les clients WebSocket frontend | ✅ Fonctionne |
| Timestamps en millisecondes | ✅ ISO 8601 avec ms |
| Calcul de la latence (provider → backend → browser) | ✅ `latency_ms` dans chaque tick |
| Endpoint `/ws/market` | ✅ WebSocket FastAPI |
| Endpoint `/api/market/live-status` | ✅ Statut LIVE/DELAYED/STALE |

### 3.2 Backend FastAPI
| Endpoint | État |
|----------|------|
| `GET /api/health` | ✅ Fonctionne |
| `GET /api/market` | ✅ Bougies H1 XAUUSD depuis MongoDB |
| `GET /api/market/{symbol}` | ✅ Détail + bougies pour graphique |
| `GET /api/predictions/XAUUSD` | ✅ Fonctionne (si modèle entraîné) |
| `GET /api/explanations/XAUUSD` | ✅ Contributions SHAP |
| `GET /api/economic-events` | ✅ Calendrier économique |
| `GET /api/news` | ✅ Actualités financières |
| `GET /api/model-performance` | ✅ Métriques de validation |
| `GET /api/data-quality` | ✅ Rapport qualité des données |
| `WS /ws/market` | ✅ Stream temps réel |

### 3.3 Pipeline ML
| Composant | État |
|-----------|------|
| Dataset : bougies fermées uniquement | ✅ Règle stricte (`candle_is_closed`) |
| Labellisation BULLISH/NEUTRAL/BEARISH | ✅ Horizon configurable (1h, 2h, 4h) |
| Absence de fuite de données (leakage) | ✅ Splits chronologiques stricts |
| Validation walk-forward (expanding window) | ✅ Implémentée dans `backtest.py` |
| Calibration des probabilités (Platt Scaling) | ✅ `CalibratedClassifierCV` |
| 4 modèles candidats | ✅ LR, RF, XGBoost, LightGBM |
| Recherche d'hyperparamètres (grid search WF-safe) | ✅ Nouveau (session actuelle) |
| Multi-horizon (1h, 2h, 4h) | ✅ Nouveau (session actuelle) |
| Sélection sur OOS composite score | ✅ `selection_score = (1-F1) + Brier + LogLoss/5` |
| Métriques : accuracy, F1, precision, recall, ROC-AUC, Brier, LogLoss | ✅ Toutes calculées |
| Sauvegarde `.joblib` | ✅ `data/models/` |
| Enregistrement dans MongoDB (`model_performance`) | ✅ |

### 3.4 Features techniques (v2.0)
| Feature | Description |
|---------|-------------|
| `return_1`, `log_return_1` | Rendements 1-période |
| `momentum_5/10/20` | Momentum multi-horizon |
| `sma_20/50/200` | Moyennes mobiles simples |
| `ema_20/50` | Moyennes mobiles exponentielles |
| `macd`, `macd_signal`, `macd_hist` | MACD complet (12/26/9) |
| `rsi_14` | RSI 14 périodes |
| `atr_14`, `atr_pct` | ATR + ATR normalisé |
| `bb_upper/lower/width` | Bandes de Bollinger (20, 2σ) |
| `close_vs_sma50/200` | Distance normalisée aux moyennes |
| `volatility_5/20/50` | Volatilité multi-fenêtre |
| `range`, `high_low_ratio` | Forme de la bougie |
| `body`, `upper_wick`, `lower_wick` | Structure de la bougie |
| `rolling_high/low_20/50` | Canaux de prix |
| `poc`, `bullish_fvg`, `bearish_fvg` | Structures de marché XAUUSD |
| `order_block`, `market_structure` | Blocs d'ordre, structure |
| `hour_utc`, `day_of_week`, `session` | Temporalité et session |
| `econ_actual`, `econ_surprise` | Données macro (si disponibles) |
| `news_sentiment_score` | Sentiment actualités (si disponibles) |

### 3.5 Frontend Next.js
| Composant | État |
|-----------|------|
| Dashboard principal | ✅ Fonctionne (port 3000) |
| Prix XAUUSD (MarketCard) | ✅ Affiché |
| Prédiction AI (PredictionCard) | ✅ Direction + probabilités |
| Barre de probabilités (ProbabilityBar) | ✅ BULLISH/NEUTRAL/BEARISH |
| Indicateurs techniques (TechnicalPanel) | ✅ SMA 200, RSI, MACD, ATR |
| Explication SHAP (ExplanationPanel) | ✅ Top features |
| Scénarios (ScenarioPanel) | ✅ Base/Bullish/Bearish |
| Calendrier économique (EconomicEventCard) | ✅ Affiché |
| Graphique de prix SVG (PriceChart) | ✅ Bougies H1 |
| Panneau qualité (QualityPanel) | ✅ |
| Client WebSocket temps réel (liveMarket.js) | ✅ Reconnexion automatique |
| Polling REST de secours (60s) | ✅ Configurable via env |

### 3.6 Base de données
| Collection MongoDB | État |
|-------------------|------|
| `market_data` (bougies XAUUSD H1) | ✅ 10 242 bougies stockées |
| `news` | ✅ Actualités financières |
| `economic_events` | ✅ Calendrier macro |
| `model_performance` | ✅ Métriques walk-forward |

### 3.7 Tests
```
27 passed ✅  (8 warnings mineurs)
```

### 3.8 Modèles entraînés (session actuelle)
| Modèle | Artefact | Horizon |
|--------|----------|---------|
| **LightGBM (production)** | `xauusd_lightgbm-20260917T182128Z-production.joblib` | 1h |
| LightGBM candidate h1 | `...-candidate_h1.joblib` | 1h |
| LightGBM candidate h2 | `...-candidate_h2.joblib` | 2h |
| LightGBM candidate h4 | `...-candidate_h4.joblib` | 4h |
| Logistic Regression (×6) | candidats h1/h2/h4 | 1h/2h/4h |
| Random Forest (×6) | candidats h1/h2/h4 | 1h/2h/4h |
| XGBoost (×6) | candidats h1/h2/h4 | 1h/2h/4h |

---

## 4. Ce qui est limité ⚠️

| Limitation | Explication |
|------------|-------------|
| **Précision OOS réaliste 45–60 %** | XAU/USD H1 est un marché bruit dominant. Les métriques sont honnêtes, non gonflées. |
| **Données macro optionnelles** | Les features `econ_actual/surprise` et `news_sentiment` sont vides si les clés FRED/BEA/BLS/Marketaux ne sont pas configurées. |
| **SMA 200 sur TechnicalPanel** | Nécessite ≥ 200 bougies fermées en base pour afficher la tendance. Si les données sont insuffisantes, affiche "N/A". |
| **Volume XAUUSD absent** | Twelve Data ne fournit pas de volume pour XAUUSD H1. Le POC (Point of Control) affiche NaN. |
| **Walk-forward lent** | Sur 10 000 bougies, le grid search complet (4 modèles × 3 horizons × 8 params) prend ~5–10 min. |
| **Données fraîches STALE pendant les heures creuses** | En dehors des heures de marché, le statut devient STALE ; la reconnexion est maintenue mais les ticks s'arrêtent (comportement normal). |
| **`penalty='l2'` FutureWarning sklearn** | Avertissement de dépréciation sklearn ≥ 1.8. N'affecte pas les résultats. Corrigé pour les prochains runs. |

---

## 5. Ce qui ne fonctionne pas / non implémenté ❌

| Élément | État | Raison |
|---------|------|--------|
| **Prédiction sans modèle entraîné** | ❌ → HTTP 503 `MODEL_NOT_READY` | Normal : nécessite un artefact `.joblib` |
| **Écriture de chaque tick en MongoDB** | ❌ Désactivé intentionnellement | Trop coûteux en performance |
| **Cross-market features** | ❌ Désactivé dans `dataset.py` | Contrat de feature en ligne non établi |
| **News sentiment** | ❌ Vide sans clé Marketaux/NewsAPI | Clé API requise dans `.env` |
| **Données macro FRED/BEA/BLS** | ❌ Vide sans clés | Clés API requises dans `.env` |
| **Authentification utilisateur** | ❌ Non implémentée | Hors périmètre PFE (lecture seule) |
| **Alertes / notifications push** | ❌ Non implémentées | Non prévu |
| **Backtesting de stratégie de trading** | ❌ Non implémenté | Outil de recherche uniquement |
| **Déploiement cloud automatisé** | ⚠️ Documenté pas testé | Railway + Vercel documentés dans README |

---

## 6. Pipeline de données – Diagramme de flux

```
Twelve Data REST API (H1 candles)
         │
         ▼
  collectors/market.py
         │  upsert
         ▼
  MongoDB : market_data (10 242 bougies)
         │
         ▼
  ml/dataset.py (bougies fermées uniquement)
         │
         ▼
  features/canonical.py → technical.py + structure.py
  (35+ features, aucune fuite temporelle)
         │
         ▼
  ml/training.py → search_and_train_best()
  [4 modèles × 3 horizons × grid HP → walk-forward → sélection OOS]
         │
         ▼
  data/models/xauusd_*.joblib  ←  production model
         │
         ▼
  services/predictions.py → FastAPI GET /api/predictions/XAUUSD
         │
         ▼
  Frontend → PredictionCard + ExplanationPanel + ScenarioPanel

  ══════════════════════════
  Parallèlement (temps réel) :
  ══════════════════════════
  Twelve Data WebSocket (ticks XAU/USD)
         │
         ▼
  services/live_market.py (singleton, reconnexion auto)
         │  broadcast
         ▼
  FastAPI WS /ws/market
         │
         ▼
  liveMarket.js → MarketCard (prix + latence + timestamp ms)
```

---

## 7. Qualité du code

| Critère | Évaluation |
|---------|-----------|
| Séparation des responsabilités | ✅ Services / Routes / Features / ML distincts |
| Gestion des erreurs | ✅ Handlers HTTP 503 par domaine |
| Pas de fake data | ✅ Garanti par architecture |
| Tests automatisés | ✅ 27 tests (pytest) |
| Logging structuré | ✅ JSON (structlog) |
| Configuration centralisée | ✅ Pydantic Settings |
| Pas de fuite de données ML | ✅ Validé par tests chronologiques |
| CORS sécurisé | ✅ Origines explicites uniquement |
| WebSocket persistant | ✅ Backoff exponentiel 1→30s |

---

## 8. Résumé pour PFE

> **Ce projet implémente une plateforme complète de recherche financière IA pour le cours de l'or (XAUUSD).**
>
> Il couvre :
> - La collecte de données réelles (Twelve Data, MongoDB Atlas)
> - Un pipeline ML rigoureux (walk-forward, calibration, anti-leakage)
> - Une architecture microservices moderne (FastAPI + Next.js + WebSocket)
> - Un dashboard interactif avec prix temps réel, prédiction probabiliste, indicateurs techniques (SMA 200, RSI, MACD, Bollinger), explication SHAP, calendrier économique
>
> **Modèle en production :** `LightGBM` — sélectionné par grid search multi-horizon sur 10 242 bougies H1 réelles.  
> **Précision OOS honnête :** 45–60 % (3 classes : BULLISH / NEUTRAL / BEARISH)  
> **Tests :** 27 passés ✅

---

*Rapport généré automatiquement — 17 septembre 2026*
