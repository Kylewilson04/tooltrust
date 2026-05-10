from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Any
import hashlib
import json
import time


class RiskClass(str, Enum):
    READ_ONLY = "read_only"
    READ_FILTER = "read_filter"
    READ_TRANSFORM = "read_transform"
    GENERATE = "generate"
    EXTERNAL_COMM = "external_comm"
    WRITE_ACTION = "write_action"
    FINANCIAL = "financial"
    REGULATED_DATA = "regulated_data"

    @property
    def level(self) -> int:
        return _RISK_LEVELS[self]

    @property
    def allowed_in_local_mode(self) -> bool:
        return self.level <= 4


_RISK_LEVELS = {
    RiskClass.READ_ONLY: 1,
    RiskClass.READ_FILTER: 2,
    RiskClass.READ_TRANSFORM: 3,
    RiskClass.GENERATE: 4,
    RiskClass.EXTERNAL_COMM: 5,
    RiskClass.WRITE_ACTION: 6,
    RiskClass.FINANCIAL: 7,
    RiskClass.REGULATED_DATA: 8,
}


class AuthorityLevel(int, Enum):
    OBSERVER = 0
    READER = 1
    CONTRIBUTOR = 2
    OPERATOR = 3
    ADMIN = 4
    ROOT = 5


class AdapterType(str, Enum):
    MCP = "mcp"
    LANGCHAIN = "langchain"
    CREWAI = "crewai"
    HTTP = "http"
    SHELL = "shell"
    CODE_EXECUTION = "code_execution"


class DdcEventType(str, Enum):
    DESTRUCTION_CONFIRMED = "DestructionConfirmed"
    ABORT_BURNED = "AbortBurned"
    DESTRUCTION_FAILED = "DestructionFailed"
    SESSION_CRASHED = "SessionCrashed"
    ATTESTED = "Attested"
    SOVEREIGNTY_VERIFIED = "SovereigntyVerified"
    CERTIFICATION_GATE_PASSED = "CertificationGatePassed"
    CERTIFICATION_GATE_REJECTED = "CertificationGateRejected"


class DdcClass(str, Enum):
    DDC_A = "DDC-A"
    DDC_S = "DDC-S"
    DDC_H = "DDC-H"


@dataclass
class ToolDescriptor:
    name: str
    description: str
    risk_class: RiskClass
    authority_required: AuthorityLevel = AuthorityLevel.OBSERVER
    adapter: AdapterType = AdapterType.HTTP
    fn: Optional[Callable] = field(default=None, repr=False)

    def input_hash(self, *args, **kwargs) -> str:
        data = json.dumps({"args": str(args), "kwargs": str(kwargs)}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def output_hash(self, result: Any) -> str:
        data = json.dumps({"result": str(result)}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class ToolTrace:
    tool_name: str
    risk_class: RiskClass
    authority_used: AuthorityLevel
    input_hash: str
    output_hash: str
    duration_ms: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    data: Any
    trace: ToolTrace
    ddc_id: Optional[str] = None
    ddc_class: Optional[DdcClass] = None
    scu_consumed: float = 0.0
    atp_updated: bool = False


def tool(
    risk: str = "read_only",
    name: Optional[str] = None,
    description: Optional[str] = None,
    authority_required: int = 0,
    adapter: str = "http",
):
    """Decorator that wraps a function as a Tool Trust instrumented tool.

    Args:
        risk: Risk class name (read_only, financial, etc.)
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        authority_required: Minimum authority level (0-5)
        adapter: Adapter type (http, shell, mcp, etc.)
    """
    risk_class = RiskClass(risk)
    authority = AuthorityLevel(authority_required)
    adapter_type = AdapterType(adapter)

    def decorator(fn: Callable):
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or "").strip()
        descriptor = ToolDescriptor(
            name=tool_name,
            description=tool_desc,
            risk_class=risk_class,
            authority_required=authority,
            adapter=adapter_type,
            fn=fn,
        )
        fn._tool_descriptor = descriptor
        return fn

    return decorator
