from __future__ import annotations

from .client import LocalToolTrustClient, RelayToolTrustClient, ProductionToolTrustClient
from .tool import tool, ToolDescriptor, RiskClass, AuthorityLevel, AdapterType
from .errors import (
    ToolTrustError,
    AuthorizationError,
    RiskClassBlockedError,
    QuotaExceededError,
    RelayError,
    VerificationError,
)
from .ddc import DdcCertificate, DdcLedgerRecord, DdcEventType, DdcClass
from .verifier import verify_ddc, VerificationResult
from .atp import LocalATP, AgentTrustProfile
from .replay import replay_ddc, ReplayResult

__version__ = "0.1.2"
__all__ = [
    # Decorator
    "tool",
    # Clients
    "LocalToolTrustClient",
    "RelayToolTrustClient",
    "ProductionToolTrustClient",
    # Types
    "ToolDescriptor",
    "RiskClass",
    "AuthorityLevel",
    "AdapterType",
    "DdcCertificate",
    "DdcLedgerRecord",
    "DdcEventType",
    "DdcClass",
    "VerificationResult",
    "AgentTrustProfile",
    # Utilities
    "LocalATP",
    "verify_ddc",
    "replay_ddc",
    "ReplayResult",
    # Errors
    "ToolTrustError",
    "AuthorizationError",
    "RiskClassBlockedError",
    "QuotaExceededError",
    "RelayError",
    "VerificationError",
]
