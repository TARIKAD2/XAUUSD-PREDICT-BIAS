from dataclasses import dataclass
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,f1_score
@dataclass(frozen=True)
class BaselineResult: model: object;metrics:dict;train_end:int
def train_baseline(df,features,target,test_fraction=.2):
 clean=df.sort_values("timestamp").dropna(subset=features+[target]);split=int(len(clean)*(1-test_fraction));
 if split<20 or len(clean)-split<5:raise ValueError("Insufficient chronological samples.")
 model=LogisticRegression(max_iter=1000).fit(clean.iloc[:split][features],clean.iloc[:split][target]);pred=model.predict(clean.iloc[split:][features]);return BaselineResult(model,{"accuracy":accuracy_score(clean.iloc[split:][target],pred),"f1":f1_score(clean.iloc[split:][target],pred,zero_division=0)},split)
