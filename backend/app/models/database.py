"""Database-domain types shared by infrastructure and API schemas."""

from enum import Enum


class DatabaseConnectionStatus(str, Enum):
    CONNECTED = "connected"
    NOT_CONFIGURED = "not_configured"
    UNAVAILABLE = "unavailable"