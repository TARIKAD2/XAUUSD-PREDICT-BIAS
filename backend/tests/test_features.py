import pandas as pd
from app.features.technical import add_cross_market_features,build_technical_features
def test_cross_market_join_cannot_look_forward():
 p=pd.DataFrame({"timestamp":pd.to_datetime(["2026-01-01 10:00","2026-01-01 11:00"]),"open":[1,2],"high":[2,3],"low":[0,1],"close":[1,2]});r=pd.DataFrame({"timestamp":pd.to_datetime(["2026-01-01 10:30"]),"close":[99]});out=add_cross_market_features(p,r,"rel");assert pd.isna(out.loc[0,"rel_close"]);assert out.loc[1,"rel_close"]==99
def test_technical_requires_ohlc():
 try:build_technical_features(pd.DataFrame({"close":[1]}))
 except ValueError:pass
 else:raise AssertionError