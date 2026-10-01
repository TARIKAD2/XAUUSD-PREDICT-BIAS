"""STEP 5: Model Serving / Prediction Engine for XAUUSD.

Safely loads the production model artifact selected in STEP 4 (logistic_regression),
validates the feature schema, generates calibrated BULLISH / BEARISH probabilities,
and reports model status and confidence.

Never fabricates predictions. If artifacts, model, or features are invalid or missing,
returns MODEL_NOT_READY.
Preserves the STEP 4 status (WARNING) and metrics without modification.
No FastAPI/dashboard integration.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd

from ..data.litefinance import repo_root_from


class ModelStatus(str, Enum):
    READY = "READY"
    WARNING = "WARNING"
    MODEL_NOT_READY = "MODEL_NOT_READY"


class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


@dataclass
class ValidationIssue:
    field: str
    message: str
    severity: str = "ERROR"


@dataclass
class PredictionOutput:
    status: ModelStatus
    direction: Direction | None = None
    probability_bullish: float | None = None
    probability_bearish: float | None = None
    confidence: float | None = None  # distance from 0.5 decision boundary: abs(p - 0.5) * 2
    raw_score: float | None = None   # linear decision function or raw proba
    features_used: int = 0
    model_name: str | None = None
    horizon_bars: int | None = None
    threshold: float | None = None
    step4_status: str | None = None
    step4_metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["direction"] = self.direction.value if self.direction else None
        return d


class ModelServingEngine:
    """Production serving and prediction engine for STEP 4 XAUUSD models."""

    REQUIRED_ARTIFACTS = (
        "logistic_regression_final.joblib",
        "feature_schema.json",
        "label_definition.json",
        "step4_audit.json",
        "final_metrics.json",
    )

    def __init__(self, artifacts_dir: Path | str | None = None):
        if artifacts_dir is None:
            root = repo_root_from(Path(__file__))
            self.artifacts_dir = root / "models" / "xauusd"
        else:
            self.artifacts_dir = Path(artifacts_dir)

        self.model: Any = None
        self.model_metadata: dict[str, Any] = {}
        self.feature_schema: dict[str, Any] = {}
        self.feature_cols: list[str] = []
        self.feature_stats: dict[str, dict[str, float]] = {}
        self.label_def: dict[str, Any] = {}
        self.step4_audit: dict[str, Any] = {}
        self.final_metrics: dict[str, Any] = {}

        self.is_loaded: bool = False
        self.load_errors: list[str] = []
        self.load_warnings: list[str] = []

        # Attempt to load immediately upon instantiation
        self.load_artifacts()

    def load_artifacts(self) -> bool:
        """Safely load and validate all required artifacts."""
        self.load_errors = []
        self.load_warnings = []
        self.is_loaded = False

        if not self.artifacts_dir.is_dir():
            self.load_errors.append(f"Artifacts directory does not exist: {self.artifacts_dir}")
            return False

        # 1. Verify existence of required artifact files
        for fname in self.REQUIRED_ARTIFACTS:
            fpath = self.artifacts_dir / fname
            if not fpath.is_file():
                self.load_errors.append(f"Missing required artifact: {fname}")

        if self.load_errors:
            return False

        # 2. Load step4_audit.json
        try:
            audit_path = self.artifacts_dir / "step4_audit.json"
            self.step4_audit = json.loads(audit_path.read_text(encoding="utf-8"))
            if not self.step4_audit.get("ok"):
                self.load_errors.append("step4_audit.json indicates pipeline status ok=False")
            for w in self.step4_audit.get("warnings", []):
                self.load_warnings.append(f"STEP 4 audit warning: {w}")
        except Exception as e:
            self.load_errors.append(f"Failed to read step4_audit.json: {e}")

        # 3. Load feature_schema.json
        try:
            schema_path = self.artifacts_dir / "feature_schema.json"
            self.feature_schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.feature_cols = list(self.feature_schema.get("feature_cols", []))
            self.feature_stats = dict(self.feature_schema.get("stats", {}))
            if not self.feature_cols:
                self.load_errors.append("feature_schema.json contains empty feature_cols")
            if len(self.feature_cols) != self.feature_schema.get("n_features"):
                self.load_errors.append("feature_schema.json feature_cols length mismatch with n_features")
        except Exception as e:
            self.load_errors.append(f"Failed to read feature_schema.json: {e}")

        # 4. Load label_definition.json
        try:
            label_path = self.artifacts_dir / "label_definition.json"
            self.label_def = json.loads(label_path.read_text(encoding="utf-8"))
            if self.label_def.get("pos_class") != "BULLISH":
                self.load_errors.append(f"Unexpected pos_class in label_definition: {self.label_def.get('pos_class')}")
        except Exception as e:
            self.load_errors.append(f"Failed to read label_definition.json: {e}")

        # 5. Load final_metrics.json
        try:
            metrics_path = self.artifacts_dir / "final_metrics.json"
            self.final_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception as e:
            self.load_errors.append(f"Failed to read final_metrics.json: {e}")

        # 6. Load the joblib model bundle safely
        try:
            bundle_path = self.artifacts_dir / "logistic_regression_final.joblib"
            bundle = joblib.load(bundle_path)
            if not isinstance(bundle, dict):
                self.load_errors.append("Model bundle is not a valid dictionary")
                return False

            self.model = bundle.get("model")
            if self.model is None or not hasattr(self.model, "predict_proba"):
                self.load_errors.append("Loaded model object lacks predict_proba method")

            bundle_cols = bundle.get("feature_cols", [])
            if bundle_cols != self.feature_cols:
                self.load_errors.append("Model bundle feature_cols do not match feature_schema.json")

            self.model_metadata = {
                "model_name": bundle.get("model_name", "logistic_regression"),
                "horizon": bundle.get("horizon", 24),
                "threshold": bundle.get("threshold", 0.005),
                "pos_class": bundle.get("pos_class", "BULLISH"),
                "class_names": bundle.get("class_names", ["BEARISH", "BULLISH"]),
                "saved_at": bundle.get("saved_at"),
            }
        except Exception as e:
            self.load_errors.append(f"Failed to load model bundle: {e}")

        if not self.load_errors:
            self.is_loaded = True

        return self.is_loaded

    def get_status(self) -> dict[str, Any]:
        """Return engine readiness status and preserved STEP 4 metrics."""
        step4_status = "WARNING" if self.step4_audit.get("warnings") else ("PASS" if self.step4_audit.get("ok") else "ERROR")
        return {
            "ready": self.is_loaded,
            "engine_status": ModelStatus.WARNING.value if (self.is_loaded and self.load_warnings) else (ModelStatus.READY.value if self.is_loaded else ModelStatus.MODEL_NOT_READY.value),
            "step4_status": step4_status,
            "model_name": self.model_metadata.get("model_name"),
            "n_features": len(self.feature_cols),
            "horizon_bars": self.model_metadata.get("horizon"),
            "threshold": self.model_metadata.get("threshold"),
            "load_errors": list(self.load_errors),
            "load_warnings": list(self.load_warnings),
            "step4_test_metrics": self.final_metrics.get("test_metrics", {}),
            "step4_audit_summary": {
                "ok": self.step4_audit.get("ok"),
                "finished_at": self.step4_audit.get("finished_at"),
                "n_folds": self.step4_audit.get("n_folds"),
                "selected_model": self.step4_audit.get("model_selection", {}).get("selected_model"),
                "warnings": self.step4_audit.get("warnings", []),
            },
        }

    def validate_features(self, features: pd.DataFrame | Mapping[str, Any]) -> tuple[pd.DataFrame | None, list[ValidationIssue]]:
        """Validate input feature vectors against schema without fabricating values."""
        issues: list[ValidationIssue] = []

        if not self.is_loaded:
            issues.append(ValidationIssue("engine", "Engine is not ready / artifacts not loaded"))
            return None, issues

        # Convert to DataFrame
        if isinstance(features, pd.DataFrame):
            df = features.copy()
        elif isinstance(features, Mapping):
            df = pd.DataFrame([features])
        elif isinstance(features, list) and all(isinstance(x, Mapping) for x in features):
            df = pd.DataFrame(features)
        else:
            issues.append(ValidationIssue("type", f"Invalid input features type: {type(features)}"))
            return None, issues

        if df.empty:
            issues.append(ValidationIssue("shape", "Input features DataFrame is empty"))
            return None, issues

        # Check for missing required columns
        missing_cols = [c for c in self.feature_cols if c not in df.columns]
        if missing_cols:
            issues.append(ValidationIssue("columns", f"Missing required feature columns: {missing_cols[:5]} (total missing: {len(missing_cols)})"))
            return None, issues

        # Select exact schema columns in exact order
        sub_df = df[self.feature_cols].apply(pd.to_numeric, errors="coerce")

        # Check for NaNs or Infs
        nan_counts = sub_df.isna().sum()
        cols_with_nan = nan_counts[nan_counts > 0]
        if not cols_with_nan.empty:
            bad_cols = list(cols_with_nan.index[:5])
            issues.append(ValidationIssue("nan", f"NaN or non-numeric values present in features: {bad_cols}"))
            return None, issues

        inf_mask = np.isinf(sub_df.to_numpy(dtype=float))
        if np.any(inf_mask):
            issues.append(ValidationIssue("inf", "Infinite values present in feature matrix"))
            return None, issues

        # Outlier / range warnings (non-fatal)
        for c in self.feature_cols:
            stat = self.feature_stats.get(c)
            if stat:
                c_min = stat.get("min")
                c_max = stat.get("max")
                val = sub_df[c].iloc[-1]
                if c_min is not None and c_max is not None:
                    # If value is 10x beyond historical min/max, add warning
                    span = abs(c_max - c_min)
                    if span > 0 and (val < c_min - 2 * span or val > c_max + 2 * span):
                        issues.append(ValidationIssue(c, f"Value {val} severely exceeds historical bounds [{c_min}, {c_max}]", severity="WARNING"))

        return sub_df, issues

    def predict(self, features: pd.DataFrame | Mapping[str, Any]) -> PredictionOutput:
        """Run single or latest-row prediction safely.
        
        Never fabricates predictions. Returns MODEL_NOT_READY on invalid features or unready model.
        """
        step4_test_m = self.final_metrics.get("test_metrics", {})
        step4_status = "WARNING" if self.step4_audit.get("warnings") else ("PASS" if self.step4_audit.get("ok") else "ERROR")

        if not self.is_loaded:
            return PredictionOutput(
                status=ModelStatus.MODEL_NOT_READY,
                step4_status=step4_status,
                step4_metrics=step4_test_m,
                errors=list(self.load_errors) or ["Engine artifacts not loaded"],
                warnings=list(self.load_warnings),
            )

        matrix, issues = self.validate_features(features)
        err_issues = [i for i in issues if i.severity == "ERROR"]
        warn_issues = [i for i in issues if i.severity == "WARNING"]

        if err_issues or matrix is None:
            return PredictionOutput(
                status=ModelStatus.MODEL_NOT_READY,
                model_name=self.model_metadata.get("model_name"),
                features_used=0,
                horizon_bars=self.model_metadata.get("horizon"),
                threshold=self.model_metadata.get("threshold"),
                step4_status=step4_status,
                step4_metrics=step4_test_m,
                errors=[f"{i.field}: {i.message}" for i in err_issues],
                warnings=[f"{i.field}: {i.message}" for i in warn_issues] + list(self.load_warnings),
            )

        # Run inference on the latest (or single) row
        row = matrix.iloc[[-1]]

        try:
            raw_proba = self.model.predict_proba(row)
            # classes_ alignment check
            classes = list(getattr(self.model, "classes_", []))
            if not classes and hasattr(self.model, "named_steps"):
                last_step = list(self.model.named_steps.values())[-1]
                classes = list(getattr(last_step, "classes_", []))

            if classes == ["BEARISH", "BULLISH"]:
                p_bearish = float(raw_proba[0, 0])
                p_bullish = float(raw_proba[0, 1])
            elif classes == ["BULLISH", "BEARISH"]:
                p_bullish = float(raw_proba[0, 0])
                p_bearish = float(raw_proba[0, 1])
            else:
                # default assumption 0=BEARISH, 1=BULLISH
                p_bearish = float(raw_proba[0, 0])
                p_bullish = float(raw_proba[0, 1])

            # Validation of probabilities
            if not (0.0 <= p_bearish <= 1.0 and 0.0 <= p_bullish <= 1.0):
                return PredictionOutput(
                    status=ModelStatus.MODEL_NOT_READY,
                    model_name=self.model_metadata.get("model_name"),
                    errors=[f"Model produced invalid probabilities outside [0, 1]: ({p_bearish}, {p_bullish})"],
                )

            # Determine direction & confidence
            direction = Direction.BULLISH if p_bullish >= p_bearish else Direction.BEARISH
            confidence = float(abs(p_bullish - 0.5) * 2.0)  # scale 0.0 (50/50) to 1.0 (100/0)

            # Raw decision function score if available
            raw_score: float | None = None
            if hasattr(self.model, "decision_function"):
                try:
                    raw_score = float(self.model.decision_function(row)[0])
                except Exception:
                    pass

            # Combine warnings (including STEP 4 audit warnings)
            all_warnings = [f"{i.field}: {i.message}" for i in warn_issues] + list(self.load_warnings)

            return PredictionOutput(
                status=ModelStatus.WARNING if all_warnings else ModelStatus.READY,
                direction=direction,
                probability_bullish=p_bullish,
                probability_bearish=p_bearish,
                confidence=confidence,
                raw_score=raw_score,
                features_used=len(self.feature_cols),
                model_name=self.model_metadata.get("model_name"),
                horizon_bars=self.model_metadata.get("horizon"),
                threshold=self.model_metadata.get("threshold"),
                step4_status=step4_status,
                step4_metrics=step4_test_m,
                warnings=all_warnings,
                errors=[],
            )
        except Exception as e:
            return PredictionOutput(
                status=ModelStatus.MODEL_NOT_READY,
                model_name=self.model_metadata.get("model_name"),
                errors=[f"Inference runtime error: {e}"],
                warnings=list(self.load_warnings),
            )
