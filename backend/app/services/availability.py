"""Explicit service boundary for capabilities implemented in later phases."""

from __future__ import annotations

from typing import NoReturn


class FeatureNotReadyError(RuntimeError):
    """Raised when an API capability has no verified data pipeline yet."""

    def __init__(self, feature: str, available_in_phase: int) -> None:
        self.feature = feature
        self.available_in_phase = available_in_phase
        super().__init__(f"{feature} will be available after Phase {available_in_phase}.")


def require_feature(feature: str, available_in_phase: int) -> NoReturn:
    """Prevent route stubs from manufacturing unverified information."""
    raise FeatureNotReadyError(feature, available_in_phase)