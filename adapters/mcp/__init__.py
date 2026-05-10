"""
MCP (Model Context Protocol) Adapter for Tool Trust.

Wraps MCP tools with Tool Trust cryptographic certification.
Each tool call gets a local DDC (free) or production DDC (relay mode).

Usage:
    from tooltrust.adapters.mcp import wrap_mcp_tool
    from tooltrust import LocalToolTrustClient

    client = LocalToolTrustClient()
    wrapped = wrap_mcp_tool(mcp_tool, client)
    result = wrapped(args)
"""

from typing import Any, Callable, Optional
from tooltrust import tool, LocalToolTrustClient, ToolResult, RiskClass


def wrap_mcp_tool(
    mcp_tool: Callable,
    client: LocalToolTrustClient,
    risk: str = "read_only",
    name: Optional[str] = None,
) -> Callable:
    """Wrap an MCP tool with Tool Trust certification.

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


# Stub — full MCP adapter requires mcp package
# pip install mcp  (when available)

__all__ = ["wrap_mcp_tool"]
