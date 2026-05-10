from __future__ import annotations

import time
import uuid
import hashlib
import json
from typing import Optional
from dataclasses import dataclass, field

from .tool import (
    ToolDescriptor, ToolTrace, ToolResult,
    RiskClass, AuthorityLevel, DdcEventType, DdcClass,
)
from .ddc import DdcCertificate, DdcLedgerRecord, LocalDdcChain
from .verifier import VerificationResult, LocalVerifier
from .atp import LocalATP, AgentTrustProfile
from .errors import (
    ToolTrustError,
    AuthorizationError,
    RiskClassBlockedError,
    QuotaExceededError,
    RelayError,
)


@dataclass
class LocalToolTrustClient:
    """Free, local Tool Trust client. Zero SCU. Zero cloud.

    All DDCs are local. Verifier is local. ATP is disk-only.
    Upgradable to RelayToolTrustClient without changing tool decorators.
    """

    ddc_chain: LocalDdcChain = field(default_factory=LocalDdcChain)
    verifier: LocalVerifier = field(default_factory=LocalVerifier)
    atp: LocalATP = field(default_factory=LocalATP)
    agent_id: str = "default"

    def execute(self, fn, *args, **kwargs) -> ToolResult:
        """Execute a @tool-decorated function with trust instrumentation."""
        descriptor: ToolDescriptor = getattr(fn, "_tool_descriptor", None)
        if descriptor is None:
            raise ToolTrustError(f"Function '{fn.__name__}' is not a @tool. Wrap it with @tool first.")

        # 1. Policy check
        if not descriptor.risk_class.allowed_in_local_mode:
            raise RiskClassBlockedError(
                risk_class=descriptor.risk_class,
                required_mode="relay",
                message=f"Risk class '{descriptor.risk_class.value}' requires relay mode. "
                        f"Use RelayToolTrustClient(api_key=...) instead."
            )

        # 2. Authority check
        current_auth = AuthorityLevel.OBSERVER  # Local mode: Observer authority
        if current_auth.value < descriptor.authority_required.value:
            raise AuthorizationError(
                current=current_auth,
                required=descriptor.authority_required,
                message=f"Authority {current_auth.name} < required {descriptor.authority_required.name}"
            )

        # 3. Execute
        input_hash = descriptor.input_hash(*args, **kwargs)
        start = time.time()
        error_msg = None
        try:
            data = fn(*args, **kwargs)
            success = True
        except Exception as e:
            data = None
            success = False
            error_msg = str(e)
        duration_ms = int((time.time() - start) * 1000)
        output_hash = descriptor.output_hash(data)

        # 4. Trace
        trace = ToolTrace(
            tool_name=descriptor.name,
            risk_class=descriptor.risk_class,
            authority_used=current_auth,
            input_hash=input_hash,
            output_hash=output_hash,
            duration_ms=duration_ms,
            success=success,
            error_message=error_msg,
        )

        return ToolResult(
            tool_name=descriptor.name,
            success=success,
            data=data,
            trace=trace,
        )

    def issue_ddc(self) -> DdcCertificate:
        """Issue a local DDC for the accumulated execution chain."""
        event = self.ddc_chain.append(
            session_id=f"local-{uuid.uuid4().hex[:8]}",
            event_type=DdcEventType.ATTESTED,
        )
        cert = self.ddc_chain.latest()
        if cert is None:
            cert = DdcCertificate(
                ddc_id=f"ddc-{uuid.uuid4().hex[:12]}",
                session_id=event.session_id,
                event_type=event.event_type,
                event_hash=event.event_hash,
                ddc_class=DdcClass.DDC_A,
                burned_at=event.timestamp,
                verification_tier="A",
            )
        return cert

    def verify(self, ddc_id: str) -> VerificationResult:
        """Verify a DDC locally."""
        return self.verifier.verify(ddc_id, self.ddc_chain)

    def get_atp(self, agent_id: Optional[str] = None) -> AgentTrustProfile:
        """Get the local Agent Trust Profile."""
        return self.atp.get(agent_id or self.agent_id)

    def update_atp(self) -> AgentTrustProfile:
        """Update ATP after a session."""
        profile = self.atp.get(self.agent_id)
        profile.total_ddcs = len(self.ddc_chain.events)
        profile.session_count = (profile.session_count or 0) + 1
        self.atp.save(profile)
        return profile


@dataclass
class RelayToolTrustClient:
    """Production relay client. Meters SCU via api.ardyn.ai.

    Same @tool decorator as LocalToolTrustClient.
    Upgrades: authorize → execute → complete → production DDC.
    """

    api_key: str
    base_url: str = "https://api.ardyn.ai"
    offline_grace_period_hours: int = 24
    agent_id: str = "default"
    _local_client: LocalToolTrustClient = field(default_factory=LocalToolTrustClient)

    def execute(self, fn, *args, **kwargs) -> ToolResult:
        """Execute with cloud relay — authorize, execute, complete."""
        descriptor: ToolDescriptor = getattr(fn, "_tool_descriptor", None)
        if descriptor is None:
            raise ToolTrustError(f"Function '{fn.__name__}' is not a @tool.")

        # 1. Local policy check
        input_hash = descriptor.input_hash(*args, **kwargs)

        # 2. Authorize via cloud (placeholder — requires HTTP client)
        try:
            import urllib.request
            auth_body = json.dumps({
                "tool_name": descriptor.name,
                "risk_class": descriptor.risk_class.value,
                "authority_level": descriptor.authority_required.value,
                "input_hash": input_hash,
                "agent_id": self.agent_id,
                "client_version": "tooltrust-sdk/0.1.3",
            }).encode()
            req = urllib.request.Request(
                f"{self.base_url}/v1/tools/authorize",
                data=auth_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "X-ToolTrust-SDK-Version": "tooltrust-sdk/0.1.3",
                },
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=10)
            auth_result = json.loads(resp.read())
            if not auth_result.get("authorized"):
                raise AuthorizationError(
                    current=AuthorityLevel.OBSERVER,
                    required=descriptor.authority_required,
                    message=auth_result.get("reason", "Authorization denied"),
                )
            call_id = auth_result["call_id"]
        except urllib.error.HTTPError as e:
            # Offline fallback
            if e.code >= 500:
                return self._local_client.execute(fn, *args, **kwargs)
            raise RelayError(f"Authorization failed: HTTP {e.code}")

        # 3. Execute locally
        local_result = self._local_client.execute(fn, *args, **kwargs)

        # 4. Complete via cloud
        try:
            complete_body = json.dumps({
                "call_id": call_id,
                "output_hash": local_result.trace.output_hash,
                "traces": [{
                    "tool_name": local_result.trace.tool_name,
                    "risk_class": local_result.trace.risk_class.value,
                    "input_hash": local_result.trace.input_hash,
                    "output_hash": local_result.trace.output_hash,
                    "duration_ms": local_result.trace.duration_ms,
                    "success": local_result.trace.success,
                }],
                "duration_ms": local_result.trace.duration_ms,
            }).encode()
            req = urllib.request.Request(
                f"{self.base_url}/v1/tools/complete",
                data=complete_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=10)
            complete_result = json.loads(resp.read())
            local_result.ddc_id = complete_result.get("ddc_id")
            local_result.ddc_class = DdcClass(complete_result.get("ddc_class", "DDC-A"))
            local_result.scu_consumed = complete_result.get("scu_consumed", 0)
            local_result.atp_updated = complete_result.get("atp_updated", False)
        except urllib.error.HTTPError:
            # Return local result without cloud completion
            pass

        return local_result


@dataclass
class ProductionToolTrustClient(RelayToolTrustClient):
    """Enterprise production client with full trust stack.

    Adds: Bitcoin anchoring, CertificationGate, sovereign evidence.
    """

    enable_bitcoin_anchor: bool = False
    enable_certification_gate: bool = False
    enable_sovereign_evidence: bool = False
