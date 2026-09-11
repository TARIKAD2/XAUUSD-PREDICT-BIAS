"""Schemas shared by API error responses."""

from typing import Literal

from .base import APIModel


class ErrorDetail(APIModel):
    """A stable machine-readable API error."""

    code: str
    message: str


class ErrorResponse(APIModel):
    """Envelope used by custom API exception handlers."""

    error: ErrorDetail


FeatureNotReadyCode = Literal["feature_not_ready"]