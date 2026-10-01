# Architecture

Routes call services; services use collectors and Mongo repositories. Collectors validate and normalize external data before persistence. Features and ML use chronological as-of alignment so a row at time T only includes observations with timestamps <= T. Labels use a future close after T and are isolated in `target`. The Next.js app uses one centralized API client. Docker uses only relative paths.

## Data stores

MongoDB Atlas database `ai_market_intelligence`. Market candles live only in `market_data` with a unique index on `(symbol, timeframe, timestamp)`. News is unique on `url`. Economic events are unique on `(event, country, currency, timestamp)`. Walk-forward metrics persist to `model_performance`.

## Providers

- Twelve Data: OHLC. Internal symbol XAUUSD maps to provider code XAU/USD.
- Marketaux: financial news. Provider entity sentiment is stored when present; otherwise lexicon sentiment is labeled as `lexicon`.
- FRED, BLS, BEA: published US statistics. These sources do not supply market consensus forecasts, so `forecast` is null and `status` is `unavailable`.

## Machine learning

Training uses a chronological 60/20/20 split, integer labels for all estimators, `CalibratedClassifierCV` (FrozenEstimator when sklearn >= 1.6, `cv='prefit'` otherwise), and selection by F1 + Brier + log loss. SHAP is computed only for supported tree estimators.
