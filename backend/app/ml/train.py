"""Executable script to train and select the best binary model."""
import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.db.client import MongoClientManager
from app.ml.dataset import fetch_raw_candles_async
from app.ml.training import search_and_train_best
from app.schemas.market import AssetSymbol, Timeframe
from app.services.model_registry import ModelRegistryService

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def run():
    settings = get_settings()
    manager = MongoClientManager(settings)
    await manager.connect()
    try:
        logger.info("Fetching raw historical data...")
        df = await fetch_raw_candles_async(manager, AssetSymbol.XAUUSD, Timeframe.H1, limit=5000)
        if df.empty:
            logger.error("No raw data found in DB.")
            return

        logger.info(f"Loaded {len(df)} real historical H1 candles.")
        logger.info("Training binary models across horizons [1, 2, 4]...")
        
        result = search_and_train_best(
            raw_ohlc=df,
            symbol="XAUUSD",
            models_dir="data/models",
            candidates=["logistic_regression", "random_forest", "xgboost", "lightgbm"],
            horizons=[1, 2, 4],
            bullish_threshold=0.0,
            bearish_threshold=-0.000000001
        )
        
        selected = result["selected"]
        horizon = result["selected_horizon"]
        production = result["production"]
        
        metrics = production.get("final_test_metrics") or production.get("metrics") or {}
        acc = metrics.get("accuracy", 0)
        
        logger.info(f"--- Training Complete ---")
        logger.info(f"Selected Model: {selected}")
        logger.info(f"Selected Target Horizon: {horizon}H")
        logger.info(f"Holdout Accuracy: {acc:.2%}")
        logger.info(f"Production Artifact: {production.get('path')}")
        
        if acc >= 0.85:
            logger.info("Target achieved: >=85% Out-Of-Sample accuracy.")
        else:
            logger.info("Target not achieved: <85% accuracy. Do not fabricate results.")
            
        # Register the production model
        if production.get("path"):
            registry = ModelRegistryService(manager)
            await registry.register_production(production)
            logger.info("Model registered to database successfully.")

    finally:
        await manager.disconnect()

if __name__ == "__main__":
    asyncio.run(run())
