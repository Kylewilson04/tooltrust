"""DDC Replay Engine — replayable autonomous tool execution.

Replay replays a DDC execution event to verify it produces
the same output hash, confirming the execution was deterministic
and tamper-free.
"""
from dataclasses import dataclass, field
from typing import Any, Callable
import hashlib
import json

from .ddc import DdcCertificate, LocalDdcChain


@dataclass
class ReplayResult:
    ddc_id: str
    original_output_hash: str
    replayed_output_hash: str
    match: bool
    deterministic: bool
    details: list = field(default_factory=list)


def replay_ddc(
    fn: Callable,
    args: tuple,
    expected_output_hash: str,
    ddc: DdcCertificate | None = None,
) -> ReplayResult:
    """Replay a DDC — re-execute and verify output hash matches.

    Args:
        fn: The function to replay
        args: Arguments to pass to the function
        expected_output_hash: The original output hash to compare against
        ddc: Optional DDC certificate for metadata
    """
    ddc_id = ddc.ddc_id if ddc else "local-replay"

    # Re-execute
    data = fn(*args)
    output_hash = hashlib.sha256(
        json.dumps({"result": str(data)}, sort_keys=True).encode()
    ).hexdigest()

    match = output_hash == expected_output_hash
    deterministic = match

    return ReplayResult(
        ddc_id=ddc_id,
        original_output_hash=expected_output_hash,
        replayed_output_hash=output_hash,
        match=match,
        deterministic=deterministic,
        details=[
            f"DDC: {ddc_id}",
            f"Original hash: {expected_output_hash[:16]}...",
            f"Replayed hash: {output_hash[:16]}...",
            f"Match: {match}",
            f"Deterministic: {deterministic}",
        ],
    )


__all__ = ["replay_ddc", "ReplayResult"]
