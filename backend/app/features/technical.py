"""Leakage-safe technical and cross-market feature construction."""
import pandas as pd

def build_technical_features(frame:pd.DataFrame)->pd.DataFrame:
    if not {"timestamp","open","high","low","close"}<=set(frame.columns):raise ValueError("Missing OHLC columns.")
    df=frame.sort_values("timestamp").drop_duplicates("timestamp").copy();df["return_1"]=df.close.pct_change();df["sma_20"]=df.close.rolling(20,min_periods=20).mean();df["ema_20"]=df.close.ewm(span=20,adjust=False).mean();d=df.close.diff();g=d.clip(lower=0).rolling(14,min_periods=14).mean();l=(-d.clip(upper=0)).rolling(14,min_periods=14).mean();df["rsi_14"]=100-100/(1+g/l.replace(0,float("nan")));fast=df.close.ewm(span=12,adjust=False).mean();slow=df.close.ewm(span=26,adjust=False).mean();df["macd"]=fast-slow;df["atr_14"]=(df.high-df.low).rolling(14,min_periods=14).mean();df["range"]=df.high-df.low;df["momentum_10"]=df.close.pct_change(10);df["volatility_20"]=df.return_1.rolling(20,min_periods=20).std();return df

def add_cross_market_features(primary:pd.DataFrame,related:pd.DataFrame,prefix:str)->pd.DataFrame:
    """Backward-only as-of join; a primary row can only receive earlier related data."""
    left=primary.sort_values("timestamp").copy();right=related.sort_values("timestamp")[["timestamp","close"]].rename(columns={"close":f"{prefix}_close"});out=pd.merge_asof(left,right,on="timestamp",direction="backward",allow_exact_matches=True);out[f"{prefix}_return_1"]=out[f"{prefix}_close"].pct_change();return out