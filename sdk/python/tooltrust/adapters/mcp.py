"""
MCP (Model Context Protocol) Adapter for Tool Trust.

Wraps MCP tools with Tool Trust cryptographic certification.
Supports manual wrapping, auto-discovery, and bulk wrapping of
entire MCP servers.

Usage:
    from tooltrust.adapters.mcp import wrap_mcp_tool, auto_wrap_mcp_server
    from tooltrust import RelayToolTrustClient

    client = RelayToolTrustClient()
    tools = auto_wrap_mcp_server(mcp_server, client)
    result = tools["search"](query="legal precedent")
"""

import re
from typing import Any, Callable, Optional, Dict, List

from ..tool import tool, RiskClass, ToolResult
from ..client import LocalToolTrustClient

# ─── Risk inference heuristics ────────────────────────────────────────────

_RISK_PATTERNS: list[tuple[str, RiskClass]] = [
    # Financial / regulated first (highest risk)
    (r"\b(pay|payment|charge|bill|transfer|refund|invoice|purchase|credit_card|stripe)\b", RiskClass.FINANCIAL_ACTION),
    (r"\b(phi|hipaa|medical|patient|diagnosis|prescription)\b", RiskClass.REGULATED_DATA_ACTION),
    # Infrastructure mutation
    (r"\b(delete|remove|destroy|wipe|purge|drop|truncate)\b", RiskClass.INFRASTRUCTURE_MUTATION),
    (r"\b(deploy|provision|terraform|apply.*infra)\b", RiskClass.INFRASTRUCTURE_MUTATION),
    # External communication
    (r"\b(send.*email|send.*sms|notify|webhook|publish|post.*api)\b", RiskClass.EXTERNAL_COMMUNICATION),
    (r"\b(http|fetch|request|curl|api.*call)\b", RiskClass.EXTERNAL_COMMUNICATION),
    # Write actions
    (r"\b(write|create|insert|update|save|upload|put|patch)\b", RiskClass.WRITE_ACTION),
    # Code execution — only match "run" when paired with code context
    (r"\b(exec\b|eval\b|shell|bash|script|compile|python|node|run_code|run_script)\b", RiskClass.CODE_EXECUTION),
    # Data access
    (r"\b(query|select|read.*db|sql|database|connect)\b", RiskClass.DATA_ACCESS),
    # Default: read_only
]


def infer_risk_class(
    tool_name: str,
    tool_description: str = "",
    risk_map: Optional[Dict[str, RiskClass]] = None,
) -> RiskClass:
    """Infer a Tool Trust risk class from a tool's name and description.

    Priority: explicit risk_map > name-only patterns > name+description patterns > read_only default.

    Args:
        tool_name: The MCP tool name (e.g., "search_documents")
        tool_description: Optional tool description for richer matching
        risk_map: Optional dict mapping tool_name → RiskClass overrides

    Returns:
        Best-guess RiskClass for the tool
    """
    # 1. Explicit override wins
    if risk_map and tool_name in risk_map:
        return risk_map[tool_name]

    # 2. Pattern match against name + description
    search_text = f"{tool_name} {tool_description}".lower()
    for pattern, risk_class in _RISK_PATTERNS:
        if re.search(pattern, search_text):
            return risk_class

    # 3. Default: read_only
    return RiskClass.READ_ONLY


# ─── Manual wrapping ──────────────────────────────────────────────────────

def wrap_mcp_tool(
    mcp_tool: Callable,
    client: LocalToolTrustClient,
    risk: str = "read_only",
    name: Optional[str] = None,
) -> Callable:
    """Wrap a single MCP tool with Tool Trust certification.

    Args:
        mcp_tool: The MCP tool function to wrap
        client: ToolTrustClient (local or relay)
        risk: Risk class name
        name: Tool name (defaults to function name)

    Returns:
        Wrapped function that produces trust-certified DDCs
    """
    @tool(risk=risk, name=name or mcp_tool.__name__, adapter="mcp")
    def wrapped(*args, **kwargs) -> Any:
        return mcp_tool(*args, **kwargs)

    def execute(*args, **kwargs) -> ToolResult:
        return client.execute(wrapped, *args, **kwargs)

    execute._tool_descriptor = wrapped._tool_descriptor
    return execute


# ─── Auto-discovery and bulk wrapping ─────────────────────────────────────

def discover_mcp_tools(mcp_server) -> List[dict]:
    """Discover all tools exposed by an MCP server.

    Works with any object that has a list_tools() or tools attribute.

    Args:
        mcp_server: An MCP server object (stdio proxy, client session, etc.)

    Returns:
        List of dicts with keys: name, description, fn (callable)
    """
    tools: List[dict] = []

    # Try list_tools() method (MCP SDK pattern)
    if hasattr(mcp_server, "list_tools"):
        try:
            result = mcp_server.list_tools()
            # result may be a list of Tool objects or a ListToolsResult
            if hasattr(result, "tools"):
                result = result.tools
            for t in result:
                name = t.name if hasattr(t, "name") else str(t)
                desc = t.description if hasattr(t, "description") else ""
                fn = getattr(mcp_server, "call_tool", None)
                if fn:
                    tools.append({
                        "name": name,
                        "description": desc,
                        "fn": lambda *a, tool_name=name, **kw: fn(tool_name, *a, **kw),
                    })
        except Exception:
            pass

    # Try tools dict (stdio transport pattern)
    if not tools and hasattr(mcp_server, "tools"):
        tool_attr = mcp_server.tools
        if isinstance(tool_attr, dict):
            for name, fn in tool_attr.items():
                tools.append({
                    "name": name,
                    "description": getattr(fn, "__doc__", "") or "",
                    "fn": fn,
                })
        elif callable(tool_attr):
            # tools might be a method that returns a dict
            try:
                result = tool_attr()
                if isinstance(result, dict):
                    for name, fn in result.items():
                        tools.append({
                            "name": name,
                            "description": getattr(fn, "__doc__", "") or "",
                            "fn": fn,
                        })
            except Exception:
                pass

    return tools


def wrap_mcp_tools_bulk(
    mcp_tools: List[dict],
    client: LocalToolTrustClient,
    risk_map: Optional[Dict[str, RiskClass]] = None,
) -> Dict[str, Callable]:
    """Wrap a list of discovered MCP tools with Tool Trust certification.

    Args:
        mcp_tools: List of dicts from discover_mcp_tools()
        client: ToolTrustClient (local or relay)
        risk_map: Optional dict mapping tool_name → RiskClass

    Returns:
        Dict mapping tool_name → wrapped callable
    """
    wrapped: Dict[str, Callable] = {}
    for tool_def in mcp_tools:
        name = tool_def["name"]
        desc = tool_def.get("description", "")
        fn = tool_def["fn"]

        risk_class = infer_risk_class(name, desc, risk_map).value
        wrapped[name] = wrap_mcp_tool(fn, client, risk=risk_class, name=name)

    return wrapped


def auto_wrap_mcp_server(
    mcp_server,
    client: LocalToolTrustClient,
    risk_map: Optional[Dict[str, RiskClass]] = None,
) -> Dict[str, Callable]:
    """Auto-discover and wrap all tools from an MCP server in one call.

    Discovers every tool exposed by the MCP server, infers risk classes,
    and wraps each one with Tool Trust certification.

    Args:
        mcp_server: Any MCP server (stdio proxy, client session, etc.)
        client: ToolTrustClient (local or relay)
        risk_map: Optional dict mapping tool_name → RiskClass overrides

    Returns:
        Dict mapping tool_name → wrapped callable

    Example:
        from tooltrust.adapters.mcp import auto_wrap_mcp_server
        from tooltrust import RelayToolTrustClient

        client = RelayToolTrustClient()
        tools = auto_wrap_mcp_server(mcp_server, client)
        result = tools["search_documents"](query="contracts")
    """
    discovered = discover_mcp_tools(mcp_server)
    if not discovered:
        raise ValueError(
            "No tools discovered from MCP server. "
            "Ensure the server has a list_tools() method or tools dict."
        )
    return wrap_mcp_tools_bulk(discovered, client, risk_map)


# Stub — full MCP adapter requires mcp package
# pip install mcp  (when available)

__all__ = [
    "wrap_mcp_tool",
    "discover_mcp_tools",
    "wrap_mcp_tools_bulk",
    "auto_wrap_mcp_server",
    "infer_risk_class",
]
