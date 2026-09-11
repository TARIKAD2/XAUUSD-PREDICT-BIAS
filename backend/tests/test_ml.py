import pandas as pd
from app.ml.baseline import evaluate_baseline
from app.ml.backtest import walk_forward_splits
def test_chronological_models_return_calibrated_metrics():
 n=80;df=pd.DataFrame({"timestamp":pd.date_range("2024-01-01",periods=n),"a":[i%7 for i in range(n)],"b":[i%5 for i in range(n)],"target":[i%3 for i in range(n)]});r=evaluate_baseline(df,["a","b"],"target","random_forest");assert set(("accuracy","precision","recall","f1","log_loss"))<=set(r.metrics);assert r.train_end==r.test_start
def test_walk_forward_never_trains_on_future():
 for train,test in walk_forward_splits(30,10,5):assert max(train)<min(test)