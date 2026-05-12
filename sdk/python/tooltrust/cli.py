"""Tool Trust CLI — zero-code onboarding after pip install.

Usage:
    tooltrust onboard        Create a free account (interactive)
    tooltrust status         Show account info
    tooltrust                Print usage
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import config
from .client import RelayToolTrustClient


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "onboard":
        _onboard()
    elif cmd == "status":
        _status()
    else:
        _usage()


def _onboard() -> None:
    """Interactive onboarding — create a free Tool Trust account."""
    cfg = config.get_config()
    if cfg.get("api_key"):
        print("You already have a Tool Trust account.")
        _status()
        return

    print("Create a free Tool Trust account? [Y/n] ", end="")
    answer = input().strip().lower()
    if answer and answer != "y":
        print("Skipped. Run `tooltrust onboard` anytime.")
        return

    print("Creating account...")
    try:
        client = RelayToolTrustClient()
        # force registration by reading the config it just saved
        cfg = config.get_config()
        print()
        print("✓ Account created")
        print(f"  API key:  {config.mask_key(cfg.get('api_key'))}")
        print(f"  Tenant:   {cfg.get('tenant_id', 'unknown')}")
        print()
        print("Ready. Use the Python SDK:")
        print("  from tooltrust import RelayToolTrustClient")
        print("  client = RelayToolTrustClient()")
        print()
        print("Or upgrade to Ardyn Core for certified DDCs:")
        print("  curl -sSL https://api.ardyn.ai/install | bash")
    except Exception as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)


def _status() -> None:
    """Show current account status."""
    cfg = config.get_config()
    if not cfg.get("api_key"):
        print("No account. Run `tooltrust onboard` to create one.")
        return

    print("Tool Trust Account")
    print("──────────────────")
    print(f"  API key:  {config.mask_key(cfg.get('api_key'))}")
    print(f"  Tenant:   {cfg.get('tenant_id', 'unknown')}")
    print(f"  Agent:    {cfg.get('agent_id', 'unknown')}")
    print(f"  Config:   {config.CONFIG_FILE}")

    # show ATP if present
    agent = cfg.get("agent_id")
    if agent:
        atp_path = Path.home() / ".ardyn" / "atp" / f"{agent}.json"
        if atp_path.exists():
            import json
            atp = json.loads(atp_path.read_text())
            print(f"  Trust:    {atp.get('trust_score', '?')}")
            print(f"  DDCs:     {atp.get('total_ddcs', 0)}")


def _usage() -> None:
    """Print usage."""
    print("Tool Trust — lightweight trust infrastructure for AI tools")
    print()
    print("Commands:")
    print("  tooltrust onboard    Create a free account")
    print("  tooltrust status     Show account info")
    print()
    cfg = config.get_config()
    if cfg.get("api_key"):
        print("Account: active ✓")
    else:
        print("No account. Run `tooltrust onboard` to get started.")
