import pandas as pd
from app.ml.advanced import evaluate_advanced,persist_model,shap_feature_contributions

def dataset():
 n=90;return pd.DataFrame({"timestamp":pd.date_range("2024-01-01",periods=n),"f1":[i%11 for i in range(n)],"f2":[(i*3)%7 for i in range(n)],"target":[i%3 for i in range(n)]})
def test_xgboost_and_lightgbm_chronological_models(tmp_path):
 for name in ("xgboost","lightgbm"):
  result=evaluate_advanced(dataset(),["f1","f2"],"target",name)
  assert set(result.metrics)=={"accuracy","precision","recall","f1","log_loss"}
  assert result.train_end==result.test_start
  persist_model(result,tmp_path/f"{name}.joblib",{"feature_version":"test"});assert (tmp_path/f"{name}.joblib").exists()
def test_shap_contributions_are_from_actual_xgboost_model():
 df=dataset();result=evaluate_advanced(df,["f1","f2"],"target","xgboost");items=shap_feature_contributions(result,df.iloc[[-1]],["f1","f2"]);assert len(items)==2 and {x["feature"] for x in items}=={"f1","f2"}