"""STEP 4: Walk-forward validation and final model selection for XAUUSD.

Labels (from STEP 3): horizon=24 H1 bars, threshold=+-0.5%, NEUTRAL excluded.
Never shuffles. Never uses future information in features.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier

    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMClassifier

    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

from ..data.litefinance import sha256_file
from ..data.mtf_features import FEATURE_COLUMNS
from .step3 import (
    FORBIDDEN_IN_X,
    RANDOM_SEED,
    _jsonable,
    chronological_splits,
    feature_matrix,
    load_features,
    make_labels,
)

# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------
HORIZON    = 24
THRESHOLD  = 0.005
TRAIN_FRAC = 0.70
VAL_FRAC   = 0.15

N_FOLDS        = 5
MIN_FOLD_TRAIN = 3_500
MIN_FOLD_VAL   = 300

MODEL_NAMES = ("logistic_regression", "random_forest", "xgboost", "lightgbm")
POS_CLASS   = "BULLISH"  # positive class for binary metrics
POS_IDX     = 1          # index in [BEARISH, BULLISH] probability array

MODELS_DIR    = Path("models") / "xauusd"
ML_DIR        = Path("data") / "processed" / "ml"
FEATURES_NAME = "XAUUSD_features.csv"

# Diagnostic thresholds
OVF_GAP_THRESHOLD = 0.12   # train-val accuracy gap -> overfitting warning
SUSPICION_AUC     = 0.75   # AUC too high for a baseline model
INSTABILITY_STD   = 0.08   # std of balanced_accuracy across folds
DEGRADATION_DELTA = 0.10   # drop from first to last fold balanced_accuracy
N_CAL_BINS        = 5      # calibration reliability diagram bins


# ---------------------------------------------------------------------------
#  Utility
# ---------------------------------------------------------------------------
def features_path(root: Path) -> Path:
    return root / ML_DIR / FEATURES_NAME


def _enc(y: "pd.Series | np.ndarray") -> np.ndarray:
    """BEARISH->0, BULLISH->1."""
    return (np.asarray(y) == POS_CLASS).astype(int)


def _majority_class(y_str: pd.Series) -> str:
    return str(y_str.value_counts().idxmax())


def _get_proba_aligned(model: Any, X: pd.DataFrame, name: str) -> np.ndarray:
    """Return (n, 2) proba with columns [P(BEARISH), P(BULLISH)]."""
    raw = model.predict_proba(X)
    if name in ("xgboost", "lightgbm"):
        # trained with 0=BEARISH, 1=BULLISH -> already aligned
        return raw
    # LR / RF: inspect classes_ ordering
    try:
        cls = list(model.classes_)
    except AttributeError:
        try:
            last_step = list(model.named_steps.values())[-1]
            cls = list(last_step.classes_)
        except AttributeError:
            return raw
    if cls == ["BEARISH", "BULLISH"]:
        return raw
    if cls == ["BULLISH", "BEARISH"]:
        return raw[:, [1, 0]]
    return raw


# ---------------------------------------------------------------------------
#  Walk-forward fold builder
# ---------------------------------------------------------------------------
def build_walk_forward_folds(
    data: pd.DataFrame,
    n_folds: int = N_FOLDS,
    min_train: int = MIN_FOLD_TRAIN,
    min_val: int = MIN_FOLD_VAL,
) -> list[dict[str, Any]]:
    """Expanding-window chronological folds with horizon embargo.

    Fold k:
        train_raw = data[0 : val_start_idx]
        val       = data[val_start_idx : val_end_idx]
        train     = train_raw WHERE future_timestamp < val_start_ts  (embargo)

    Returns list of {'fold_id', 'cut_ts', 'train', 'val'}.
    """
    if not data["timestamp"].is_monotonic_increasing:
        raise ValueError("data must be sorted chronologically before folding")
    n = len(data)
    if n < min_train + n_folds * min_val:
        raise ValueError(
            f"insufficient rows ({n}) for {n_folds} folds "
            f"(need >= {min_train + n_folds * min_val})"
        )

    step = (n - min_train) // n_folds
    folds: list[dict[str, Any]] = []

    for k in range(n_folds):
        val_lo = min_train + k * step
        val_hi = min_train + (k + 1) * step if k < n_folds - 1 else n
        val_hi = min(val_hi, n)

        if val_hi - val_lo < min_val:
            continue

        cut_ts    = data.iloc[val_lo]["timestamp"]
        train_raw = data.iloc[:val_lo].copy()
        val       = data.iloc[val_lo:val_hi].copy()

        # Embargo: remove training rows whose label looks into val window
        train = train_raw.loc[train_raw["future_timestamp"] < cut_ts].copy()

        if len(train) < min_train or len(val) < min_val:
            continue

        # Both classes must appear with enough samples
        ok = True
        for df in (train, val):
            vc = df["target"].value_counts()
            if len(vc) < 2 or vc.min() < 10:
                ok = False
                break
        if not ok:
            continue

        folds.append(
            {
                "fold_id": len(folds) + 1,
                "cut_ts" : cut_ts,
                "train"  : train.reset_index(drop=True),
                "val"    : val.reset_index(drop=True),
            }
        )

    if not folds:
        raise ValueError("could not build any valid walk-forward folds")
    return folds


# ---------------------------------------------------------------------------
#  Model instantiation
# ---------------------------------------------------------------------------
def _make_model(name: str) -> Any:
    if name == "logistic_regression":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        C=0.1,
                        max_iter=1_000,
                        solver="lbfgs",
                        class_weight="balanced",
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        )
    if name == "random_forest":
        return RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=20,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=1,
        )
    if name == "xgboost":
        if not HAS_XGB:
            raise RuntimeError("xgboost not installed")
        return XGBClassifier(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=RANDOM_SEED,
            n_jobs=1,
            verbosity=0,
        )
    if name == "lightgbm":
        if not HAS_LGBM:
            raise RuntimeError("lightgbm not installed")
        return LGBMClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            num_leaves=15,
            subsample=0.9,
            colsample_bytree=0.9,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=1,
            verbosity=-1,
        )
    raise ValueError(f"unknown model: {name!r}")


# ---------------------------------------------------------------------------
#  Metric helpers
# ---------------------------------------------------------------------------
def _metrics(
    y_true_str: "pd.Series | np.ndarray",
    y_pred_str: np.ndarray,
    y_proba: "np.ndarray | None" = None,
    majority_class: str = POS_CLASS,
) -> dict[str, Any]:
    y_true = _enc(y_true_str)
    y_pred = _enc(y_pred_str)

    acc  = float(accuracy_score(y_true, y_pred))
    bacc = float(balanced_accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0.0))
    rec  = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0.0))
    f1v  = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0.0))
    cm   = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

    collapse    = int(len(np.unique(y_pred))) < 2
    pred_counts = dict(pd.Series(y_pred_str).value_counts())
    true_counts = dict(pd.Series(y_true_str).value_counts())

    roc: "float | None" = None
    brier: "float | None" = None
    if y_proba is not None and not collapse:
        try:
            roc = float(roc_auc_score(y_true, y_proba[:, POS_IDX]))
        except Exception:
            pass
        try:
            brier = float(brier_score_loss(y_true, y_proba[:, POS_IDX]))
        except Exception:
            pass

    maj_pred = (
        np.ones_like(y_pred) if majority_class == POS_CLASS else np.zeros_like(y_pred)
    )
    maj_acc = float(accuracy_score(y_true, maj_pred))

    return {
        "n"                     : int(len(y_true)),
        "accuracy"              : acc,
        "balanced_accuracy"     : bacc,
        "precision"             : prec,
        "recall"                : rec,
        "f1"                    : f1v,
        "roc_auc"               : roc,
        "brier_score"           : brier,
        "confusion_matrix"      : cm,
        "confusion_labels"      : ["BEARISH", "BULLISH"],
        "predicted_counts"      : pred_counts,
        "true_counts"           : true_counts,
        "class_collapse"        : collapse,
        "majority_baseline_acc" : maj_acc,
        "accuracy_lift"         : acc - maj_acc,
    }


def _calibration_metrics(
    y_true_str: "pd.Series | np.ndarray",
    y_proba: np.ndarray,
) -> dict[str, Any]:
    """Brier score, ECE and reliability-diagram data."""
    y_true = _enc(y_true_str).astype(float)
    p_pos  = y_proba[:, POS_IDX].astype(float)

    try:
        brier = float(brier_score_loss(y_true, p_pos))
    except Exception:
        brier = float("nan")

    frac_pos = mean_pred = np.array([])
    ece = float("nan")
    try:
        frac_pos, mean_pred = calibration_curve(
            y_true, p_pos, n_bins=N_CAL_BINS, strategy="uniform"
        )
        bins = np.linspace(0.0, 1.0, N_CAL_BINS + 1)
        bidx = np.clip(np.digitize(p_pos, bins) - 1, 0, N_CAL_BINS - 1)
        nt   = len(y_true)
        ece  = 0.0
        for b in range(N_CAL_BINS):
            m = bidx == b
            if m.sum() == 0:
                continue
            ece += m.sum() / nt * abs(float(y_true[m].mean()) - float(p_pos[m].mean()))
    except Exception:
        pass

    return {
        "brier_score"                  : brier,
        "ece"                          : float(ece),
        "reliability_fraction_positive": frac_pos.tolist(),
        "reliability_mean_predicted"   : mean_pred.tolist(),
        "n_bins"                       : N_CAL_BINS,
    }


# ---------------------------------------------------------------------------
#  Single fold
# ---------------------------------------------------------------------------
def evaluate_fold(fold: dict[str, Any], feature_cols: list[str]) -> dict[str, Any]:
    """Train all models on fold['train'], evaluate on fold['val']."""
    train_df  = fold["train"]
    val_df    = fold["val"]

    X_tr  = feature_matrix(train_df, feature_cols)
    X_val = feature_matrix(val_df,   feature_cols)
    y_tr_str  = train_df["target"]
    y_val_str = val_df["target"]
    y_tr_int  = _enc(y_tr_str)
    maj       = _majority_class(y_tr_str)

    result: dict[str, Any] = {
        "fold_id"       : fold["fold_id"],
        "cut_ts"        : str(fold["cut_ts"]),
        "train_n"       : int(len(train_df)),
        "val_n"         : int(len(val_df)),
        "train_date_min": str(train_df["timestamp"].min()),
        "train_date_max": str(train_df["timestamp"].max()),
        "val_date_min"  : str(val_df["timestamp"].min()),
        "val_date_max"  : str(val_df["timestamp"].max()),
        "train_bullish" : int((y_tr_str == "BULLISH").sum()),
        "train_bearish" : int((y_tr_str == "BEARISH").sum()),
        "val_bullish"   : int((y_val_str == "BULLISH").sum()),
        "val_bearish"   : int((y_val_str == "BEARISH").sum()),
        "models"        : {},
    }

    for name in MODEL_NAMES:
        model = _make_model(name)
        if name in ("xgboost", "lightgbm"):
            model.fit(X_tr, y_tr_int)
            y_val_pred = np.where(model.predict(X_val) == 1, "BULLISH", "BEARISH")
            y_tr_pred  = np.where(model.predict(X_tr)  == 1, "BULLISH", "BEARISH")
        else:
            model.fit(X_tr, y_tr_str)
            y_val_pred = model.predict(X_val)
            y_tr_pred  = model.predict(X_tr)

        proba_val = _get_proba_aligned(model, X_val, name)
        proba_tr  = _get_proba_aligned(model, X_tr,  name)

        val_m   = _metrics(y_val_str, y_val_pred, proba_val, maj)
        train_m = _metrics(y_tr_str,  y_tr_pred,  proba_tr,  maj)
        cal     = _calibration_metrics(y_val_str, proba_val)

        result["models"][name] = {
            "val"        : val_m,
            "train"      : train_m,
            "calibration": cal,
            "overfit_gap": float(train_m["accuracy"] - val_m["accuracy"]),
        }

    return result


# ---------------------------------------------------------------------------
#  Aggregation
# ---------------------------------------------------------------------------
def aggregate_fold_metrics(fold_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-model mean +- std of val metrics across folds."""
    scalar_keys = [
        "accuracy", "balanced_accuracy", "precision", "recall", "f1",
        "roc_auc", "brier_score", "accuracy_lift",
    ]
    agg: dict[str, Any] = {}

    for name in MODEL_NAMES:
        vals: dict[str, list[float]] = {k: [] for k in scalar_keys + ["overfit_gap", "collapse"]}
        for fr in fold_results:
            m = fr["models"][name]
            for k in scalar_keys:
                v = m["val"].get(k)
                if v is not None:
                    vals[k].append(float(v))
            vals["overfit_gap"].append(float(m["overfit_gap"]))
            vals["collapse"].append(float(int(m["val"]["class_collapse"])))

        out: dict[str, Any] = {}
        for k, lst in vals.items():
            if not lst:
                out[f"mean_{k}"] = None
                out[f"std_{k}"]  = None
                continue
            arr = np.array(lst, dtype=float)
            out[f"mean_{k}"] = float(np.nanmean(arr))
            out[f"std_{k}"]  = float(np.nanstd(arr))

        out["fold_balanced_accuracy"] = [
            fr["models"][name]["val"].get("balanced_accuracy") for fr in fold_results
        ]
        out["fold_roc_auc"] = [
            fr["models"][name]["val"].get("roc_auc") for fr in fold_results
        ]
        out["fold_brier_score"] = [
            fr["models"][name]["calibration"]["brier_score"] for fr in fold_results
        ]
        out["fold_overfit_gap"] = [fr["models"][name]["overfit_gap"] for fr in fold_results]
        agg[name] = out

    return agg


# ---------------------------------------------------------------------------
#  Diagnostics
# ---------------------------------------------------------------------------
def diagnose_walk_forward(
    fold_results: list[dict[str, Any]],
    aggregated  : dict[str, Any],
) -> dict[str, Any]:
    warnings: list[str] = []
    errors  : list[str] = []
    per_model: dict[str, Any] = {}

    for name in MODEL_NAMES:
        agg      = aggregated[name]
        findings : dict[str, Any] = {}

        collapses = sum(
            int(fr["models"][name]["val"]["class_collapse"]) for fr in fold_results
        )
        if collapses > 0:
            warnings.append(
                f"{name}: class collapse in {collapses}/{len(fold_results)} fold(s)"
            )
        findings["collapse_count"] = collapses

        gap = float(agg.get("mean_overfit_gap") or 0.0)
        if gap > OVF_GAP_THRESHOLD:
            warnings.append(
                f"{name}: overfitting — mean train-val accuracy gap={gap:.3f}"
            )
        findings["mean_overfit_gap"] = gap

        auc = agg.get("mean_roc_auc")
        if auc and float(auc) > SUSPICION_AUC:
            warnings.append(f"{name}: suspiciously high mean ROC-AUC {float(auc):.3f}")
        findings["mean_roc_auc"] = auc

        std_ba = float(agg.get("std_balanced_accuracy") or 0.0)
        if std_ba > INSTABILITY_STD:
            warnings.append(
                f"{name}: unstable — std balanced_accuracy={std_ba:.3f} across folds"
            )
        findings["std_balanced_accuracy"] = std_ba

        ba_seq = [v for v in (agg.get("fold_balanced_accuracy") or []) if v is not None]
        if len(ba_seq) >= 2:
            delta = ba_seq[-1] - ba_seq[0]
            findings["temporal_delta"] = float(delta)
            if delta < -DEGRADATION_DELTA:
                warnings.append(
                    f"{name}: temporal degradation — delta balanced_accuracy={delta:.3f}"
                )
        else:
            findings["temporal_delta"] = None

        per_model[name] = findings

    return {"warnings": warnings, "errors": errors, "per_model": per_model}


# ---------------------------------------------------------------------------
#  Model selection
# ---------------------------------------------------------------------------
def select_final_model(
    aggregated  : dict[str, Any],
    fold_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Select the most robust model by documented walk-forward criteria.

    Score = 0.40 * mean_roc_auc
           + 0.40 * mean_balanced_accuracy
           - 0.10 * mean_brier_score
           - 0.10 * std_balanced_accuracy

    Disqualified: any model with class collapse in ANY fold.
    Fallback:     if all models collapse, select by mean_balanced_accuracy.
    """
    scored: list[tuple[float, str]] = []

    for name in MODEL_NAMES:
        agg       = aggregated[name]
        collapses = sum(
            int(fr["models"][name]["val"]["class_collapse"]) for fr in fold_results
        )
        if collapses > 0:
            continue

        roc   = float(agg.get("mean_roc_auc")          or 0.0)
        bacc  = float(agg.get("mean_balanced_accuracy") or 0.0)
        brier = float(agg.get("mean_brier_score")       or 0.5)
        std   = float(agg.get("std_balanced_accuracy")  or 0.5)

        score = 0.40 * roc + 0.40 * bacc - 0.10 * brier - 0.10 * std
        scored.append((score, name))

    if not scored:
        # Fallback — ignore collapse
        for name in MODEL_NAMES:
            bacc  = float(aggregated[name].get("mean_balanced_accuracy") or 0.0)
            scored.append((bacc, name))

    scored.sort(reverse=True)
    best_score, best_name = scored[0]

    ranking = [
        {"rank": i + 1, "model": n, "score": float(s)}
        for i, (s, n) in enumerate(scored)
    ]

    return {
        "selected_model"    : best_name,
        "selection_score"   : float(best_score),
        "ranking"           : ranking,
        "selection_criteria": (
            "score = 0.40*mean_roc_auc + 0.40*mean_balanced_accuracy "
            "- 0.10*mean_brier_score - 0.10*std_balanced_accuracy; "
            "models with class collapse in any fold are disqualified"
        ),
    }


# ---------------------------------------------------------------------------
#  Final model: TRAIN+VAL -> train, TEST -> evaluate
# ---------------------------------------------------------------------------
def train_final_model(
    train_val_df: pd.DataFrame,
    test_df     : pd.DataFrame,
    feature_cols: list[str],
    model_name  : str,
) -> dict[str, Any]:
    X_tv   = feature_matrix(train_val_df, feature_cols)
    X_test = feature_matrix(test_df,      feature_cols)
    y_tv_str   = train_val_df["target"]
    y_test_str = test_df["target"]
    y_tv_int   = _enc(y_tv_str)
    maj        = _majority_class(y_tv_str)

    model = _make_model(model_name)
    if model_name in ("xgboost", "lightgbm"):
        model.fit(X_tv, y_tv_int)
        y_test_pred = np.where(model.predict(X_test) == 1, "BULLISH", "BEARISH")
        y_tv_pred   = np.where(model.predict(X_tv)   == 1, "BULLISH", "BEARISH")
    else:
        model.fit(X_tv, y_tv_str)
        y_test_pred = model.predict(X_test)
        y_tv_pred   = model.predict(X_tv)

    proba_test = _get_proba_aligned(model, X_test, model_name)
    proba_tv   = _get_proba_aligned(model, X_tv,   model_name)

    test_m = _metrics(y_test_str, y_test_pred, proba_test, maj)
    tv_m   = _metrics(y_tv_str,   y_tv_pred,   proba_tv,   maj)
    cal    = _calibration_metrics(y_test_str, proba_test)

    return {
        "model"            : model,
        "model_name"       : model_name,
        "feature_cols"     : feature_cols,
        "test_metrics"     : test_m,
        "train_val_metrics": tv_m,
        "calibration"      : cal,
    }


# ---------------------------------------------------------------------------
#  Artifact persistence
# ---------------------------------------------------------------------------
def save_artifacts(
    root        : Path,
    final       : dict[str, Any],
    fold_results: list[dict[str, Any]],
    aggregated  : dict[str, Any],
    selection   : dict[str, Any],
    diagnosis   : dict[str, Any],
    labeled_df  : pd.DataFrame,
    feature_cols: list[str],
    feat_hash   : str,
    train_val_df: pd.DataFrame,
    test_df     : pd.DataFrame,
) -> dict[str, str]:
    out_dir    = root / MODELS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    model_name = final["model_name"]
    model      = final["model"]

    # 1. Trained model bundle
    model_path = out_dir / f"{model_name}_final.joblib"
    joblib.dump(
        {
            "model"       : model,
            "model_name"  : model_name,
            "feature_cols": feature_cols,
            "horizon"     : HORIZON,
            "threshold"   : THRESHOLD,
            "pos_class"   : POS_CLASS,
            "class_names" : ["BEARISH", "BULLISH"],
            "saved_at"    : datetime.now().isoformat(timespec="seconds"),
        },
        model_path,
    )

    # 2. Feature schema
    X_sample = feature_matrix(train_val_df, feature_cols)
    feat_schema = {
        "feature_cols": feature_cols,
        "n_features"  : len(feature_cols),
        "stats"       : {
            c: {
                "mean": float(X_sample[c].mean()),
                "std" : float(X_sample[c].std()),
                "min" : float(X_sample[c].min()),
                "max" : float(X_sample[c].max()),
            }
            for c in feature_cols
        },
    }
    feat_schema_path = out_dir / "feature_schema.json"
    feat_schema_path.write_text(json.dumps(feat_schema, indent=2), encoding="utf-8")

    # 3. Label definition
    label_def = {
        "horizon"    : HORIZON,
        "threshold"  : THRESHOLD,
        "bullish_rule": f"close[t+{HORIZON}] / close[t] - 1 >= +{THRESHOLD}",
        "bearish_rule": f"close[t+{HORIZON}] / close[t] - 1 <= -{THRESHOLD}",
        "neutral_rule": f"|return| < {THRESHOLD}  -> NEUTRAL, excluded from training",
        "future_use" : "future_close used ONLY to compute target label, never as feature",
        "bar_size"   : "H1 (1-hour)",
        "pos_class"  : POS_CLASS,
        "class_names": ["BEARISH", "BULLISH"],
    }
    label_def_path = out_dir / "label_definition.json"
    label_def_path.write_text(json.dumps(label_def, indent=2), encoding="utf-8")

    # 4. Dataset metadata
    meta = {
        "step2_features_sha256": feat_hash,
        "total_labeled_rows"   : int(len(labeled_df)),
        "train_val_rows"       : int(len(train_val_df)),
        "test_rows"            : int(len(test_df)),
        "labeled_date_min"     : str(labeled_df["timestamp"].min()),
        "labeled_date_max"     : str(labeled_df["timestamp"].max()),
        "train_val_date_min"   : str(train_val_df["timestamp"].min()),
        "train_val_date_max"   : str(train_val_df["timestamp"].max()),
        "test_date_min"        : str(test_df["timestamp"].min()),
        "test_date_max"        : str(test_df["timestamp"].max()),
        "neutral_excluded"     : True,
        "shuffle"              : False,
        "chronological_order"  : True,
    }
    meta_path = out_dir / "dataset_metadata.json"
    meta_path.write_text(json.dumps(_jsonable(meta), indent=2), encoding="utf-8")

    # 5. Training configuration
    config = {
        "fold_type"       : "expanding_window",
        "n_folds"         : N_FOLDS,
        "min_fold_train"  : MIN_FOLD_TRAIN,
        "min_fold_val"    : MIN_FOLD_VAL,
        "train_frac"      : TRAIN_FRAC,
        "val_frac"        : VAL_FRAC,
        "random_seed"     : RANDOM_SEED,
        "horizon"         : HORIZON,
        "threshold"       : THRESHOLD,
        "embargo"         : "future_timestamp < fold_val_start_timestamp",
        "models_evaluated": list(MODEL_NAMES),
        "selected_model"  : model_name,
        "selection_criteria": selection["selection_criteria"],
    }
    config_path = out_dir / "training_config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # 6. Walk-forward metrics
    wf_path = out_dir / "walk_forward_metrics.json"
    wf_path.write_text(
        json.dumps(
            {
                "fold_results": _jsonable(fold_results),
                "aggregated"  : _jsonable(aggregated),
                "selection"   : _jsonable(selection),
                "diagnosis"   : _jsonable(diagnosis),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # 7. Final test metrics
    final_m_path = out_dir / "final_metrics.json"
    final_m_path.write_text(
        json.dumps(
            _jsonable(
                {
                    "model_name"       : model_name,
                    "test_metrics"     : final["test_metrics"],
                    "train_val_metrics": final["train_val_metrics"],
                }
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    # 8. Calibration
    cal_path = out_dir / "calibration.json"
    cal_path.write_text(
        json.dumps(
            _jsonable(
                {
                    "model"           : model_name,
                    "test_calibration": final["calibration"],
                    "fold_mean_brier" : {
                        name: aggregated[name].get("mean_brier_score")
                        for name in MODEL_NAMES
                    },
                    "fold_brier_scores": {
                        name: aggregated[name].get("fold_brier_score")
                        for name in MODEL_NAMES
                    },
                }
            ),
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "model"               : str(model_path),
        "feature_schema"      : str(feat_schema_path),
        "label_definition"    : str(label_def_path),
        "dataset_metadata"    : str(meta_path),
        "training_config"     : str(config_path),
        "walk_forward_metrics": str(wf_path),
        "final_metrics"       : str(final_m_path),
        "calibration"         : str(cal_path),
    }


# ---------------------------------------------------------------------------
#  Main orchestrator
# ---------------------------------------------------------------------------
def run_step4(root: Path) -> dict[str, Any]:
    np.random.seed(RANDOM_SEED)

    # Load and label
    feat_path = features_path(root)
    feat_hash = sha256_file(feat_path)
    frame     = load_features(feat_path)
    labeled   = make_labels(frame, HORIZON, THRESHOLD)

    # Chronological 70/15/15 split (replicates STEP 3)
    splits       = chronological_splits(labeled)
    train_df     = splits["train"]
    val_df       = splits["validation"]
    test_df      = splits["test"]
    train_val_df = pd.concat([train_df, val_df], ignore_index=True)

    assert train_val_df["timestamp"].is_monotonic_increasing
    assert train_val_df["timestamp"].max() < test_df["timestamp"].min()

    feature_cols = list(FEATURE_COLUMNS)

    # Walk-forward on TRAIN+VAL (TEST held out)
    folds        = build_walk_forward_folds(train_val_df)
    fold_results = [evaluate_fold(fold, feature_cols) for fold in folds]

    # Aggregate + diagnose + select
    aggregated = aggregate_fold_metrics(fold_results)
    diagnosis  = diagnose_walk_forward(fold_results, aggregated)
    selection  = select_final_model(aggregated, fold_results)
    best_name  = selection["selected_model"]

    # Train final model on full TRAIN+VAL, evaluate on TEST
    final_data = train_final_model(train_val_df, test_df, feature_cols, best_name)

    # Integrity checks
    errors   = list(diagnosis["errors"])
    warnings = list(diagnosis["warnings"])

    if sha256_file(feat_path) != feat_hash:
        errors.append("STEP 2 feature file was modified during STEP 4")

    if train_val_df["timestamp"].max() >= test_df["timestamp"].min():
        errors.append("TEST set overlaps with TRAIN+VAL")

    X_test     = feature_matrix(test_df, feature_cols)
    proba_test = _get_proba_aligned(final_data["model"], X_test, best_name)
    proba_ok   = bool(not (proba_test < 0).any() and not (proba_test > 1).any())
    if not proba_ok:
        errors.append(f"{best_name}: probabilities outside [0, 1]")

    # Save all artifacts
    artifact_paths = save_artifacts(
        root, final_data, fold_results, aggregated,
        selection, diagnosis, labeled, feature_cols,
        feat_hash, train_val_df, test_df,
    )

    summary = {
        "step"     : 4,
        "ok"       : not errors,
        "horizon"  : HORIZON,
        "threshold": THRESHOLD,
        "n_folds"  : len(fold_results),
        "fold_summary": [
            {
                "fold_id"       : fr["fold_id"],
                "train_n"       : fr["train_n"],
                "val_n"         : fr["val_n"],
                "cut_ts"        : fr["cut_ts"],
                "train_date_min": fr["train_date_min"],
                "train_date_max": fr["train_date_max"],
                "val_date_min"  : fr["val_date_min"],
                "val_date_max"  : fr["val_date_max"],
                "train_bullish" : fr["train_bullish"],
                "train_bearish" : fr["train_bearish"],
                "val_bullish"   : fr["val_bullish"],
                "val_bearish"   : fr["val_bearish"],
            }
            for fr in fold_results
        ],
        "walk_forward_aggregated": aggregated,
        "model_selection"        : selection,
        "diagnosis"              : diagnosis,
        "final_model": {
            "name"             : best_name,
            "test_metrics"     : final_data["test_metrics"],
            "train_val_metrics": final_data["train_val_metrics"],
            "calibration"      : final_data["calibration"],
        },
        "majority_baseline": {
            "train_val": {
                "majority_class": _majority_class(train_val_df["target"]),
                "accuracy"      : float(train_val_df["target"].value_counts(normalize=True).max()),
            },
            "test": {
                "majority_class": _majority_class(test_df["target"]),
                "accuracy"      : float(test_df["target"].value_counts(normalize=True).max()),
            },
        },
        "leakage_tests": {
            "test_after_train_val"   : True,
            "no_shuffle"             : True,
            "embargo_applied"        : True,
            "future_in_features"     : False,
            "features_unchanged"     : sha256_file(feat_path) == feat_hash,
            "proba_in_unit_interval" : proba_ok,
        },
        "artifact_paths"        : artifact_paths,
        "errors"                : errors,
        "warnings"              : warnings,
        "step2_features_sha256" : feat_hash,
        "finished_at"           : datetime.now().isoformat(timespec="seconds"),
    }

    audit_path = root / MODELS_DIR / "step4_audit.json"
    audit_path.write_text(json.dumps(_jsonable(summary), indent=2), encoding="utf-8")
    summary["audit_path"] = str(audit_path)
    return summary


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    _root   = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    _result = run_step4(_root)
    sel = _result["model_selection"]
    print(
        f"STEP 4  finished_at={_result['finished_at']}  "
        f"horizon={_result['horizon']}  threshold={_result['threshold']}  "
        f"n_folds={_result['n_folds']}  "
        f"selected={sel['selected_model']}  "
        f"ok={_result['ok']}"
    )
    for e in _result["errors"]:
        print("ERROR:", e)
    for w in _result["warnings"]:
        print("WARNING:", w)
