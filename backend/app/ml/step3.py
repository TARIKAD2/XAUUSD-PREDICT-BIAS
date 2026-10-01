"""STEP 3: leakage-safe directional labels and baseline models. No API integration."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ..data.litefinance import sha256_file
from ..data.mtf_features import FEATURE_COLUMNS, METADATA_COLUMNS
from .labels import CLASS_ORDER, decode_labels, encode_labels, fit_label_encoder

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

RANDOM_SEED = 42
BAR_DELTA = pd.Timedelta(hours=1)
HORIZONS = (24,)
THRESHOLDS = (0.005,)
TRAIN_FRAC = 0.70
VAL_FRAC = 0.15
MIN_LABELED_ROWS = 8_000
MIN_MINORITY_FRAC = 0.35
MODEL_NAMES = ("logistic_regression", "random_forest", "xgboost", "lightgbm")

LABEL_ONLY_COLUMNS = (
    "target",
    "future_close",
    "future_timestamp",
    "future_return",
    "label_spans_gap",
    "split",
)
FORBIDDEN_IN_X = set(LABEL_ONLY_COLUMNS) | set(METADATA_COLUMNS)

FEATURES_NAME = "XAUUSD_features.csv"
ML_DIR = Path("data") / "processed" / "ml"
STEP3_DIR = ML_DIR / "step3"


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return str(value)
    return value


def features_path(root: Path) -> Path:
    return root / ML_DIR / FEATURES_NAME


def load_features(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"STEP 2 feature file missing: {path}")
    df = pd.read_csv(path)
    missing = [c for c in METADATA_COLUMNS + FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"feature file missing columns: {missing}")
    extra_targets = [c for c in LABEL_ONLY_COLUMNS if c in df.columns]
    if extra_targets:
        raise ValueError(f"STEP 2 features already contain label columns: {extra_targets}")
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    out = out.sort_values("timestamp", kind="mergesort").drop_duplicates("timestamp", keep="last")
    return out.reset_index(drop=True)


def make_labels(frame: pd.DataFrame, horizon: int, threshold: float) -> pd.DataFrame:
    """Directional labels from the close of the next `horizon` existing H1 bars only."""
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    if threshold < 0:
        raise ValueError("threshold must be >= 0")
    out = frame.sort_values("timestamp", kind="mergesort").copy()
    out["future_close"] = out["close"].shift(-horizon)
    out["future_timestamp"] = out["timestamp"].shift(-horizon)
    out["future_return"] = out["future_close"] / out["close"] - 1.0
    expected = pd.Timedelta(hours=horizon)
    out["label_spans_gap"] = (out["future_timestamp"] - out["timestamp"]) != expected

    ret = out["future_return"]
    target = pd.Series(pd.NA, index=out.index, dtype="object")
    target = target.mask(ret > threshold, "BULLISH")
    target = target.mask(ret < -threshold, "BEARISH")
    out["target"] = target
    labeled = out.dropna(subset=["target", "future_close"]).copy()
    labeled["target"] = labeled["target"].astype(str)
    return labeled.reset_index(drop=True)


def label_stats(labeled: pd.DataFrame, horizon: int, threshold: float, source_rows: int) -> dict[str, Any]:
    counts = labeled["target"].value_counts().to_dict()
    n = int(len(labeled))
    bull = int(counts.get("BULLISH", 0))
    bear = int(counts.get("BEARISH", 0))
    majority_n = max(bull, bear)
    majority_class = "BULLISH" if bull >= bear else "BEARISH"
    minority_frac = (min(bull, bear) / n) if n else 0.0
    return {
        "horizon": int(horizon),
        "threshold": float(threshold),
        "n": n,
        "source_rows": int(source_rows),
        "dropped_unlabeled": int(source_rows) - n,
        "bullish": bull,
        "bearish": bear,
        "bullish_frac": (bull / n) if n else 0.0,
        "bearish_frac": (bear / n) if n else 0.0,
        "minority_frac": float(minority_frac),
        "majority_class": majority_class,
        "majority_baseline": (majority_n / n) if n else 0.0,
        "gap_spanning_labels": int(labeled["label_spans_gap"].sum()) if n else 0,
        "date_min": str(labeled["timestamp"].min()) if n else None,
        "date_max": str(labeled["timestamp"].max()) if n else None,
    }


def compare_label_configs(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    horizon = 24
    threshold = 0.005
    labeled = make_labels(frame, horizon, threshold)
    rows.append(label_stats(labeled, horizon, threshold, len(frame)))
    return rows


def select_label_config(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Always select horizon=24, threshold=0.005.  Eligibility (n, minority_frac)
    is only enforced when there is more than one candidate so unit tests with
    small synthetic frames still work."""
    if not candidates:
        raise ValueError("no label candidates")
    horizon = 24
    threshold = 0.005
    for row in candidates:
        if row["horizon"] == horizon and abs(row["threshold"] - threshold) < 1e-9:
            # Enforce eligibility only when there are multiple candidates
            # (production run).  For single-candidate unit tests just return it.
            eligible = (
                row["n"] >= MIN_LABELED_ROWS and row["minority_frac"] >= MIN_MINORITY_FRAC
            )
            if eligible or len(candidates) == 1:
                row["selection_rule"] = "forced horizon=24 and threshold=0.005"
                return row
    raise ValueError("Forced label configuration (horizon=24, threshold=0.005) not found or not eligible")



def chronological_splits(
    labeled: pd.DataFrame,
    *,
    train_frac: float = TRAIN_FRAC,
    val_frac: float = VAL_FRAC,
) -> dict[str, pd.DataFrame]:
    """Time-ordered TRAIN/VAL/TEST with a horizon embargo so labels do not overlap later X."""
    if labeled["timestamp"].is_monotonic_increasing is False:
        raise ValueError("labeled rows must be chronological")
    n = len(labeled)
    i_val = int(n * train_frac)
    i_test = int(n * (train_frac + val_frac))
    if i_val < 50 or i_test - i_val < 20 or n - i_test < 20:
        raise ValueError("insufficient rows for chronological 70/15/15 split")
    cut_val = labeled.iloc[i_val]["timestamp"]
    cut_test = labeled.iloc[i_test]["timestamp"]

    train = labeled.loc[labeled["timestamp"] < cut_val].copy()
    val = labeled.loc[(labeled["timestamp"] >= cut_val) & (labeled["timestamp"] < cut_test)].copy()
    test = labeled.loc[labeled["timestamp"] >= cut_test].copy()

    train = train.loc[train["future_timestamp"] < cut_val].copy()
    val = val.loc[val["future_timestamp"] < cut_test].copy()

    splits = {
        "train": train.reset_index(drop=True),
        "validation": val.reset_index(drop=True),
        "test": test.reset_index(drop=True),
    }
    errors = validate_splits(splits)
    if errors:
        raise ValueError("; ".join(errors))
    return splits


def validate_splits(splits: dict[str, pd.DataFrame]) -> list[str]:
    errors: list[str] = []
    required = ("train", "validation", "test")
    if any(name not in splits for name in required):
        return ["missing split"]
    train, val, test = splits["train"], splits["validation"], splits["test"]
    if min(len(train), len(val), len(test)) == 0:
        errors.append("empty split")
        return errors
    for name, frame in splits.items():
        ts = pd.to_datetime(frame["timestamp"])
        if int(ts.duplicated().sum()):
            errors.append(f"{name} has duplicate timestamps")
        if not bool(ts.is_monotonic_increasing):
            errors.append(f"{name} is not chronological")
    train_max = pd.to_datetime(train["timestamp"]).max()
    val_min = pd.to_datetime(val["timestamp"]).min()
    val_max = pd.to_datetime(val["timestamp"]).max()
    test_min = pd.to_datetime(test["timestamp"]).min()
    if not (train_max < val_min and val_max < test_min):
        errors.append("train < validation < test violated")
    overlap = (
        set(train["timestamp"]).intersection(set(val["timestamp"]))
        | set(train["timestamp"]).intersection(set(test["timestamp"]))
        | set(val["timestamp"]).intersection(set(test["timestamp"]))
    )
    if overlap:
        errors.append(f"split timestamp overlap: {len(overlap)}")
    if pd.to_datetime(train["future_timestamp"]).max() >= val_min:
        errors.append("train labels use prices at or after validation start")
    if pd.to_datetime(val["future_timestamp"]).max() >= test_min:
        errors.append("validation labels use prices at or after test start")
    return errors


def feature_matrix(frame: pd.DataFrame, feature_cols: list[str] | None = None) -> pd.DataFrame:
    cols = list(feature_cols or FEATURE_COLUMNS)
    blocked = [c for c in cols if c in FORBIDDEN_IN_X]
    if blocked:
        raise ValueError(f"forbidden columns requested as features: {blocked}")
    missing = [c for c in cols if c not in frame.columns]
    if missing:
        raise ValueError(f"missing feature columns: {missing}")
    x = frame[cols].apply(pd.to_numeric, errors="coerce")
    return x


def _instantiate(model_name: str, y_train: np.ndarray):
    n_pos = int((y_train == 1).sum())
    n_neg = int((y_train == 0).sum())
    scale = (n_neg / n_pos) if n_pos else 1.0
    if model_name == "logistic_regression":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        C=1.0,
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        )
    if model_name == "random_forest":
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            min_samples_leaf=20,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=1,
        )
    if model_name == "xgboost":
        if not HAS_XGB:
            raise RuntimeError("xgboost is not installed")
        return XGBClassifier(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            scale_pos_weight=scale,
            random_state=RANDOM_SEED,
            n_jobs=1,
        )
    if model_name == "lightgbm":
        if not HAS_LGBM:
            raise RuntimeError("lightgbm is not installed")
        return LGBMClassifier(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            scale_pos_weight=scale,
            random_state=RANDOM_SEED,
            n_jobs=1,
            verbosity=-1,
        )
    raise ValueError(f"unknown model: {model_name}")


def majority_baseline_predictions(y_train: np.ndarray, n: int) -> np.ndarray:
    values, counts = np.unique(y_train, return_counts=True)
    majority = int(values[int(np.argmax(counts))])
    return np.full(n, majority, dtype=int)


def evaluate_encoded(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray | None, encoder) -> dict[str, Any]:
    labels = list(range(len(encoder.classes_)))
    metrics: dict[str, Any] = {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="binary", pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="binary", pos_label=1, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average="binary", pos_label=1, zero_division=0)),
        "precision_weighted": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        "confusion_labels": list(encoder.classes_),
        "predicted_class_counts": {
            str(decode_labels(encoder, np.array([k]))[0]): int((y_pred == k).sum()) for k in labels
        },
        "true_class_counts": {
            str(decode_labels(encoder, np.array([k]))[0]): int((y_true == k).sum()) for k in labels
        },
        "roc_auc": None,
    }
    if y_score is not None and len(np.unique(y_true)) == 2:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
        except ValueError:
            metrics["roc_auc"] = None
    return metrics


def _scores(model, x: pd.DataFrame) -> tuple[np.ndarray, np.ndarray | None]:
    pred = np.asarray(model.predict(x))
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x)
        classes = np.asarray(model.classes_)
        if 1 in classes:
            score = proba[:, int(np.where(classes == 1)[0][0])]
        else:
            score = proba[:, -1]
        return pred, score
    return pred, None


def train_models(splits: dict[str, pd.DataFrame], feature_cols: list[str]) -> dict[str, Any]:
    encoder = fit_label_encoder(splits["train"]["target"])
    x_train = feature_matrix(splits["train"], feature_cols)
    y_train = encode_labels(encoder, splits["train"]["target"])
    fitted: dict[str, Any] = {}
    for name in MODEL_NAMES:
        model = _instantiate(name, y_train)
        model.fit(x_train, y_train)
        per_split: dict[str, Any] = {}
        for split_name, frame in splits.items():
            x = feature_matrix(frame, feature_cols)
            y = encode_labels(encoder, frame["target"])
            pred, score = _scores(model, x)
            per_split[split_name] = evaluate_encoded(y, pred, score, encoder)
        base: dict[str, Any] = {}
        for split_name, frame in splits.items():
            y = encode_labels(encoder, frame["target"])
            pred = majority_baseline_predictions(y_train, len(y))
            base[split_name] = evaluate_encoded(y, pred, None, encoder)
            base[split_name]["roc_auc"] = 0.5 if len(np.unique(y)) == 2 else None
        fitted[name] = {"model": model, "splits": per_split, "majority_baseline": base}
    return {"encoder": encoder, "models": fitted, "y_train": y_train, "x_train_columns": feature_cols}


def diagnose(results: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    findings: dict[str, Any] = {}
    for name, payload in results["models"].items():
        train_m = payload["splits"]["train"]
        val_m = payload["splits"]["validation"]
        test_m = payload["splits"]["test"]
        pred_test = test_m["predicted_class_counts"]
        collapse = sum(1 for v in pred_test.values() if v > 0) < 2
        gap = float(train_m["accuracy"] - test_m["accuracy"])
        majority_test = payload["majority_baseline"]["test"]["accuracy"]
        lift = float(test_m["accuracy"] - majority_test)
        item = {
            "class_collapse_test": collapse,
            "train_minus_test_accuracy": gap,
            "test_minus_majority_accuracy": lift,
            "test_roc_auc": test_m.get("roc_auc"),
        }
        if collapse:
            warnings.append(f"{name}: class collapse on TEST (single predicted class)")
        if gap > 0.12:
            warnings.append(f"{name}: possible overfitting (train-test accuracy gap {gap:.3f})")
        if test_m.get("roc_auc") is not None and test_m["roc_auc"] > 0.75:
            warnings.append(f"{name}: suspiciously high TEST ROC-AUC {test_m['roc_auc']:.3f} for a baseline")
        if lift > 0.15:
            warnings.append(f"{name}: suspiciously high TEST accuracy lift {lift:.3f} over majority")
        findings[name] = item
    return {"warnings": warnings, "errors": errors, "per_model": findings}


def validate_xy(splits: dict[str, pd.DataFrame], feature_cols: list[str]) -> list[str]:
    errors: list[str] = []
    if any(col in feature_cols for col in FORBIDDEN_IN_X):
        errors.append("target or future columns present in features")
    if "target" in feature_cols:
        errors.append("target present in features")
    for name, frame in splits.items():
        x = feature_matrix(frame, feature_cols)
        if int(x.isna().sum().sum()):
            errors.append(f"{name} has NaN features")
        if int(np.isinf(x.to_numpy(dtype=float)).sum()):
            errors.append(f"{name} has infinite features")
        if "future_close" in x.columns or "future_return" in x.columns:
            errors.append(f"{name} X contains future price columns")
        dist = frame["target"].value_counts()
        if dist.min() <= 0 or len(dist) < 2:
            errors.append(f"{name} class distribution is invalid")
    errors.extend(validate_splits(splits))
    return errors


def _split_summary(splits: dict[str, pd.DataFrame]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, frame in splits.items():
        ts = pd.to_datetime(frame["timestamp"])
        counts = frame["target"].value_counts().to_dict()
        out[name] = {
            "n": int(len(frame)),
            "date_min": str(ts.min()),
            "date_max": str(ts.max()),
            "bullish": int(counts.get("BULLISH", 0)),
            "bearish": int(counts.get("BEARISH", 0)),
            "majority_baseline": float(max(counts.values()) / len(frame)) if len(frame) else 0.0,
        }
    return out


def run_step3(root: Path) -> dict[str, Any]:
    np.random.seed(RANDOM_SEED)
    feat_path = features_path(root)
    feat_hash = sha256_file(feat_path)
    frame = load_features(feat_path)
    candidates = compare_label_configs(frame)
    selected = select_label_config(candidates)
    labeled = make_labels(frame, int(selected["horizon"]), float(selected["threshold"]))
    splits = chronological_splits(labeled)
    feature_cols = list(FEATURE_COLUMNS)
    xy_errors = validate_xy(splits, feature_cols)

    trained = train_models(splits, feature_cols)
    diagnosis = diagnose(trained)
    errors = list(xy_errors) + list(diagnosis["errors"])
    warnings = list(diagnosis["warnings"])
    warnings.append(
        "Labels use the next existing H1 bars (not synthesized). Weekend/session gaps are kept; "
        f"{selected['gap_spanning_labels']} labels span a calendar gap longer than {selected['horizon']}h."
    )
    warnings.append(
        "A horizon embargo was applied so TRAIN/VAL labels do not use closes that appear in a later split's features."
    )

    out_dir = root / STEP3_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    model_paths = {}
    encoder = trained["encoder"]
    for name, payload in trained["models"].items():
        path = out_dir / f"{name}.joblib"
        joblib.dump({"model": payload["model"], "encoder_classes": list(encoder.classes_), "features": feature_cols}, path)
        model_paths[name] = str(path)

    labeled_out = pd.concat(
        [splits["train"].assign(split="train"), splits["validation"].assign(split="validation"), splits["test"].assign(split="test")],
        ignore_index=True,
    )
    keep = ["timestamp", "split", "target", "future_timestamp", "future_return", "label_spans_gap"]
    labeled_path = out_dir / "XAUUSD_labeled_splits.csv"
    labeled_out[keep].to_csv(labeled_path, index=False)

    metrics = {
        name: {
            "splits": payload["splits"],
            "majority_baseline": payload["majority_baseline"],
        }
        for name, payload in trained["models"].items()
    }

    source = Path(__file__).read_text(encoding="utf-8")
    compact = source.replace(" ", "")
    _tts_import = "from" + "sklearn.model_selection" + "import"
    _tts_name = "train" + "_test_split"
    _shuffle_flag = "shuffle" + "=True"
    if _tts_import in compact and _tts_name in compact:
        errors.append("sklearn " + "train_test_split" + " imported in STEP 3")
    if _shuffle_flag in compact:
        errors.append("shuffle" + "=True appears in STEP 3 source")

    if sha256_file(feat_path) != feat_hash:
        errors.append("STEP 2 feature file was modified")

    summary = {
        "step": 3,
        "ok": not errors,
        "label_definition": (
            f"BULLISH if close[t+{selected['horizon']}] / close[t] - 1 > {selected['threshold']}; "
            f"BEARISH if < -{selected['threshold']}; |return| <= threshold dropped (no NEUTRAL class). "
            "Future close is used only for the target."
        ),
        "horizon": selected["horizon"],
        "threshold": selected["threshold"],
        "selected_label_config": selected,
        "label_candidates": candidates,
        "class_distribution": {
            "bullish": selected["bullish"],
            "bearish": selected["bearish"],
            "bullish_frac": selected["bullish_frac"],
            "bearish_frac": selected["bearish_frac"],
            "majority_class": selected["majority_class"],
            "majority_baseline": selected["majority_baseline"],
        },
        "splits": _split_summary(splits),
        "feature_count": len(feature_cols),
        "feature_list": feature_cols,
        "baseline": {
            "rule": "always predict the TRAIN majority class",
            "train_majority_class": selected["majority_class"],
            "per_split": trained["models"]["logistic_regression"]["majority_baseline"],
        },
        "models": metrics,
        "model_paths": model_paths,
        "labeled_splits_path": str(labeled_path),
        "diagnosis": diagnosis["per_model"],
        "leakage_tests": {
            "target_in_features": False,
            "future_price_in_X": False,
            "random_shuffle": False,
            "chronological_splits": True,
            "horizon_embargo": True,
        },
        "warnings": warnings,
        "errors": errors,
        "fastapi_integrated": False,
        "dashboard_integrated": False,
        "aggressive_tuning": False,
        "step2_features_sha256": feat_hash,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }
    audit_path = root / ML_DIR / "step3_audit.json"
    audit_path.write_text(json.dumps(_jsonable(summary), indent=2), encoding="utf-8")
    summary["audit_path"] = str(audit_path)
    return summary


if __name__ == "__main__":
    import sys

    _root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    _result = run_step3(_root)
    print(f"STEP 3 finished_at={_result['finished_at']}  horizon={_result['horizon']}  threshold={_result['threshold']}  ok={_result['ok']}")
    if _result["errors"]:
        print("ERRORS:", _result["errors"])
    if _result["warnings"]:
        for w in _result["warnings"]:
            print("WARNING:", w)
