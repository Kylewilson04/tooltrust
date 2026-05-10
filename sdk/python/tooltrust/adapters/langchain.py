"""
LangChain Adapter for Tool Trust.

Usage:
    from tooltrust.adapters.langchain import wrap_langchain_tool
    from .. import LocalToolTrustClient

    client = LocalToolTrustClient()
    wrapped = wrap_langchain_tool(my_langchain_tool, client)
    result = wrapped("query")
    ddc = client.issue_ddc()  # Trust certificate for this tool call
"""

from typing import Any, Callable, Optional
from ..tool import tool, ToolResult
from ..client import LocalToolTrustClient


def wrap_langchain_tool(
    lc_tool: Callable,
    client: LocalToolTrustClient,
    risk: str = "read_only",
    name: Optional[str] = None,
) -> Callable:
    """Wrap a LangChain tool with Tool Trust certification.

    Compatible with LangChain BaseTool, StructuredTool, and @tool decorators.
    Each invocation gets trust-certified with cryptographic provenance.
    """
    @tool(risk=risk, name=name or getattr(lc_tool, "name", lc_tool.__name__), adapter="langchain")
    def wrapped(*args, **kwargs) -> Any:
        return lc_tool(*args, **kwargs)

    def execute(*args, **kwargs) -> ToolResult:
        return client.execute(wrapped, *args, **kwargs)

    return execute


__all__ = ["wrap_langchain_tool"]
