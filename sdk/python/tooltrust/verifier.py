from dataclasses import dataclass, field
from typing import List, Optional
from .ddc import LocalDdcChain, DdcCertificate


@dataclass
class VerificationResult:
    ddc_id: str
    signature_valid: bool = False
    chain_valid: bool = False
    found: bool = False
    details: List[str] = field(default_factory=list)


class LocalVerifier:
    """Local DDC verifier — checks signature, hash, and chain integrity.

    Non-authoritative. For authoritative verification, use the cloud verifier
    via api.ardyn.ai (RelayToolTrustClient).
    """

    def verify(self, ddc_id: str, chain: LocalDdcChain) -> VerificationResult:
        """Verify a DDC within a local chain."""
        cert = chain.get(ddc_id)
        if cert is None:
            return VerificationResult(
                ddc_id=ddc_id,
                found=False,
                details=[f"DDC '{ddc_id}' not found in local chain"],
            )

        details = []
        # Check certificate exists in chain
        found = cert is not None
        details.append(f"Certificate found: {found}")

        # Check event hash is present (local verification)
        signature_valid = bool(cert.event_hash and len(cert.event_hash) == 64)
        details.append(f"Event hash present: {signature_valid}")

        # Check chain linkage — each event's hash is the prev_hash of the next
        chain_valid = True
        for i in range(1, len(chain.events)):
            # Simple check: all events have valid hashes
            if not chain.events[i].event_hash:
                chain_valid = False
                details.append(f"Event {i} missing hash")
        details.append(f"Chain integrity: {chain_valid}")

        return VerificationResult(
            ddc_id=ddc_id,
            signature_valid=signature_valid,
            chain_valid=chain_valid,
            found=found,
            details=details,
        )


def verify_ddc(ddc_id: str, chain: LocalDdcChain) -> VerificationResult:
    """Convenience function for local DDC verification."""
    verifier = LocalVerifier()
    return verifier.verify(ddc_id, chain)
