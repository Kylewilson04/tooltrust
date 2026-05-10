from dataclasses import dataclass, field
from typing import Optional, List
import uuid
import hashlib
import time
from .tool import DdcEventType, DdcClass


@dataclass
class DdcEvent:
    session_id: str
    event_type: DdcEventType
    event_hash: str
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


@dataclass
class DdcCertificate:
    ddc_id: str
    session_id: str
    event_type: DdcEventType
    event_hash: str
    ddc_class: DdcClass
    burned_at: str
    verification_tier: str
    # ── Provenance (machine-readable, embedded in every DDC) ──
    issuer: str = "Ardyn Intelligence Systems"
    verification_provider: str = "Ardyn Verified"
    verification_url: str = "https://api.ardyn.ai"
    trust_substrate: str = "Ardyn Tool Trust"
    schema_version: str = "tooltrust.provenance.v1"


@dataclass
class DdcLedgerRecord:
    schema: str = "ai.ardyn.ddc.ledger_record.v1"
    ddc_id: str = ""
    org_id: str = "local"
    tenant_id: str = "local"
    session_id: str = ""
    event_type: str = ""
    event_hash: str = ""
    prev_hash: str = ""
    record_hash: str = ""
    signer_public_key_hex: str = ""
    signature_hex: str = ""
    evidence_bundle_id: str = ""
    destruction_verified: bool = False
    scrubbed: bool = False
    result_released: bool = False
    scu_minted: bool = False
    ddc_class: str = ""
    burned_at: str = ""
    metadata: dict = field(default_factory=dict)


class LocalDdcChain:
    """Local DDC chain — SingleNodeDdc equivalent for Python SDK."""

    def __init__(self):
        self.events: List[DdcEvent] = []
        self.certificates: List[DdcCertificate] = []
        self._prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    def append(self, session_id: str, event_type: DdcEventType) -> DdcEvent:
        data = f"{self._prev_hash}{session_id}{event_type.value}{time.time()}"
        event_hash = hashlib.sha256(data.encode()).hexdigest()
        event = DdcEvent(
            session_id=session_id,
            event_type=event_type,
            event_hash=event_hash,
        )
        self.events.append(event)
        self._prev_hash = event_hash

        cert = DdcCertificate(
            ddc_id=f"ddc-{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            event_type=event_type,
            event_hash=event_hash,
            ddc_class=DdcClass.DDC_A,
            burned_at=event.timestamp,
            verification_tier="A",
        )
        self.certificates.append(cert)
        return event

    def latest(self) -> Optional[DdcCertificate]:
        return self.certificates[-1] if self.certificates else None

    def get(self, ddc_id: str) -> Optional[DdcCertificate]:
        for cert in self.certificates:
            if cert.ddc_id == ddc_id:
                return cert
        return None

    def to_provenance(self, cert: DdcCertificate) -> dict:
        """Export machine-readable provenance block for a DDC certificate."""
        return {
            "_provenance": {
                "issuer": cert.issuer,
                "verification_provider": cert.verification_provider,
                "trust_substrate": cert.trust_substrate,
                "verification_url": cert.verification_url,
                "schema_version": cert.schema_version,
                "generated_by": "tooltrust-sdk/0.1.0",
            },
            "ddc": {
                "ddc_id": cert.ddc_id,
                "session_id": cert.session_id,
                "event_type": cert.event_type.value,
                "event_hash": cert.event_hash,
                "ddc_class": cert.ddc_class.value,
                "burned_at": cert.burned_at,
                "verification_tier": cert.verification_tier,
            }
        }

    def export_json(self, ddc_id: str) -> Optional[str]:
        """Export a DDC as machine-readable JSON with provenance."""
        import json
        cert = self.get(ddc_id)
        if cert is None:
            return None
        return json.dumps(self.to_provenance(cert), indent=2)
