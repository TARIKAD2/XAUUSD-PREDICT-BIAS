"""Advanced chronological models, persistence, and SHAP explanations."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import joblib
import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score,log_loss,precision_recall_fscore_support
from xgboost import XGBClassifier
from .baseline import chronological_split

AdvancedModelName=Literal["xgboost","lightgbm"]
@dataclass(frozen=True)
class AdvancedResult:
    model:object
    model_name:str
    metrics:dict[str,float]
    train_end:int
    test_start:int
    classes:list[int]

def _base_model(name:AdvancedModelName,classes:int):
    if name=="xgboost": return XGBClassifier(n_estimators=80,max_depth=3,learning_rate=.05,subsample=.9,colsample_bytree=.9,objective="multi:softprob",num_class=classes,random_state=42,n_jobs=1,eval_metric="mlogloss")
    return LGBMClassifier(n_estimators=80,max_depth=3,learning_rate=.05,subsample=.9,colsample_bytree=.9,objective="multiclass",num_class=classes,random_state=42,n_jobs=1,verbosity=-1)

def evaluate_advanced(df:pd.DataFrame,features:list[str],target:str,model_name:AdvancedModelName,test_fraction:float=.2)->AdvancedResult:
    train,test=chronological_split(df,features,target,test_fraction); classes=sorted(train[target].unique().tolist())
    if len(classes)<2: raise ValueError("Training target needs at least two classes.")
    model=CalibratedClassifierCV(_base_model(model_name,len(classes)),method="sigmoid",cv=3).fit(train[features],train[target])
    pred=model.predict(test[features]);prob=model.predict_proba(test[features]);p,r,f,_=precision_recall_fscore_support(test[target],pred,average="weighted",zero_division=0)
    return AdvancedResult(model,model_name,{"accuracy":float(accuracy_score(test[target],pred)),"precision":float(p),"recall":float(r),"f1":float(f),"log_loss":float(log_loss(test[target],prob,labels=model.classes_))},len(train),len(train),list(model.classes_))

def persist_model(result:AdvancedResult,path:Path,metadata:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True);joblib.dump({"model":result.model,"model_name":result.model_name,"metrics":result.metrics,"metadata":metadata},path)

def shap_feature_contributions(result:AdvancedResult,row:pd.DataFrame,features:list[str])->list[dict[str,float|str]]:
    calibrated=result.model.calibrated_classifiers_[0].estimator
    values=shap.TreeExplainer(calibrated).shap_values(row[features])
    array=np.asarray(values)
    if array.ndim==3: array=array[0].mean(axis=1)
    elif array.ndim==2: array=array[0]
    return [{"feature":feature,"contribution":float(value)} for feature,value in sorted(zip(features,array),key=lambda item:abs(item[1]),reverse=True)]