import pandas as pd
def build_technical_features(frame):
    if not {"timestamp","open","high","low","close"}<=set(frame.columns): raise ValueError("Missing OHLC columns.")
    df=frame.sort_values("timestamp").copy();df["return_1"]=df.close.pct_change();df["sma_20"]=df.close.rolling(20,min_periods=20).mean();df["ema_20"]=df.close.ewm(span=20,adjust=False).mean();d=df.close.diff();g=d.clip(lower=0).rolling(14,min_periods=14).mean();l=(-d.clip(upper=0)).rolling(14,min_periods=14).mean();df["rsi_14"]=100-100/(1+g/l.replace(0,float("nan")));df["range"]=df.high-df.low;df["volatility_20"]=df.return_1.rolling(20,min_periods=20).std();return df
