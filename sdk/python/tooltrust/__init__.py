from __future__ import annotations

from . import config
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

__version__ = "0.1.4"


def _offer_onboarding():
    """Offer to create a free Tool Trust account on first import.

    Only prompts once. If declined, creates a '.tooltrust/opted_out'
    sentinel so we never ask again. If accepted, registers via the
    gateway and persists credentials.
    """
    import os
    import uuid
    import json
    import urllib.request

    opt_out = config.CONFIG_DIR / "opted_out"
    if opt_out.exists():
        return

    if config.get_config():
        return  # Already registered

    try:
        answer = input("\nCreate a free Tool Trust account? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return  # Non-interactive environments

    if answer and answer != "y":
        config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        opt_out.write_text("")
        return

    print("Creating your free Tool Trust account...")
    try:
        client_id = str(uuid.uuid4())
        body = json.dumps({"client_id": client_id}).encode()
        req = urllib.request.Request(
            "https://api.ardyn.ai/v1/register/tooltrust",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
    except Exception as e:
        print(f"  Registration failed: {e}")
        print(f"  You can register later via RelayToolTrustClient().execute()\n")
        return

    config.save_config({"api_key": data["api_key"], "tenant_id": data["tenant_id"]})
    print(f"  Account created: {config.mask_key(data['api_key'])}")
    print(f"  Credentials saved to ~/.tooltrust/config.json\n")


_offer_onboarding()
__all__ = [
    "config",
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
