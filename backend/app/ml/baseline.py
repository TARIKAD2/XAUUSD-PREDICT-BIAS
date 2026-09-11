"""Reproducible chronological baseline model evaluation."""
from dataclasses import dataclass
from typing import Literal
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,precision_recall_fscore_support,confusion_matrix,log_loss
@dataclass(frozen=True)
class BaselineResult: model:object;model_name:str;metrics:dict;confusion:list;train_end:int;test_start:int

def chronological_split(df,features,target,test_fraction=.2):
 clean=df.sort_values("timestamp").dropna(subset=features+[target]).copy();split=int(len(clean)*(1-test_fraction))
 if split<20 or len(clean)-split<5:raise ValueError("Insufficient chronological samples.")
 return clean.iloc[:split],clean.iloc[split:]
def evaluate_baseline(df,features,target,model_name:Literal["logistic_regression","random_forest"]="logistic_regression",test_fraction=.2)->BaselineResult:
 train,test=chronological_split(df,features,target,test_fraction)
 base=LogisticRegression(max_iter=2000,multi_class="auto") if model_name=="logistic_regression" else RandomForestClassifier(n_estimators=300,min_samples_leaf=5,random_state=42,n_jobs=1,class_weight="balanced_subsample")
 model=CalibratedClassifierCV(base,method="sigmoid",cv=3).fit(train[features],train[target]);pred=model.predict(test[features]);prob=model.predict_proba(test[features]);p,r,f,_=precision_recall_fscore_support(test[target],pred,average="weighted",zero_division=0)
 return BaselineResult(model,model_name,{"accuracy":accuracy_score(test[target],pred),"precision":p,"recall":r,"f1":f,"log_loss":log_loss(test[target],prob,labels=model.classes_)},confusion_matrix(test[target],pred,labels=model.classes_).tolist(),len(train),len(train))
def train_baseline(df,features,target,test_fraction=.2):return evaluate_baseline(df,features,target,"logistic_regression",test_fraction)