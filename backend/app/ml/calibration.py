"""CalibratedClassifierCV helpers compatible with sklearn 1.5 and 1.6+."""
from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV


def calibrate_fitted_estimator(fitted_estimator, validation_x, validation_y):
    """Calibrate an already-fitted estimator on a chronological validation split.

    sklearn 1.6+ uses FrozenEstimator. `cv='prefit'` was removed in later 1.x
    releases, so FrozenEstimator + a numeric cv is the 1.9-compatible path.
    """
    try:
        from sklearn.frozen import FrozenEstimator

        frozen = FrozenEstimator(fitted_estimator)
        try:
            calibrated = CalibratedClassifierCV(estimator=frozen, method="sigmoid", cv=2)
        except TypeError:
            calibrated = CalibratedClassifierCV(frozen, method="sigmoid", cv=2)
    except ImportError:
        try:
            calibrated = CalibratedClassifierCV(
                estimator=fitted_estimator,
                method="sigmoid",
                cv="prefit",
            )
        except (TypeError, ValueError):
            try:
                calibrated = CalibratedClassifierCV(
                    fitted_estimator,
                    method="sigmoid",
                    cv="prefit",
                )
            except (TypeError, ValueError):
                calibrated = CalibratedClassifierCV(
                    fitted_estimator,
                    method="sigmoid",
                    cv=2,
                )
    calibrated.fit(validation_x, validation_y)
    return calibrated


def unwrap_calibrated_estimator(model):
    """Return the inner estimator used for SHAP when calibration wrappers are present."""
    if hasattr(model, "calibrated_classifiers_") and model.calibrated_classifiers_:
        inner = model.calibrated_classifiers_[0]
        estimator = getattr(inner, "estimator", getattr(inner, "base_estimator", inner))
        return getattr(estimator, "estimator", estimator)
    return model
