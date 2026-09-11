"""Shared Pydantic conventions for public API schemas."""

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Forbid unknown fields and normalize accidental surrounding whitespace."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)