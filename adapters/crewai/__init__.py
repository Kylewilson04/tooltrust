"""
CrewAI Adapter for Tool Trust.

Usage:
    from tooltrust.adapters.crewai import wrap_crewai_tool
    from tooltrust import LocalToolTrustClient

    client = LocalToolTrustClient()
    wrapped = wrap_crewai_tool(my_crewai_tool, client)
    result = wrapped("query")
    ddc = client.issue_ddc()
"""

from typing import Any, Callable, Optional
from tooltrust import tool, LocalToolTrustClient, ToolResult


def wrap_crewai_tool(
    crew_tool: Callable,
    client: LocalToolTrustClient,
    risk: str = "read_only",
    name: Optional[str] = None,
) -> Callable:
    """Wrap a CrewAI tool with Tool Trust certification.

    Compatible with CrewAI BaseTool and @tool decorator tools.
    """
    @tool(risk=risk, name=name or getattr(crew_tool, "name", crew_tool.__name__), adapter="crewai")
    def wrapped(*args, **kwargs) -> Any:
        return crew_tool(*args, **kwargs)

    def execute(*args, **kwargs) -> ToolResult:
        return client.execute(wrapped, *args, **kwargs)

    return execute


__all__ = ["wrap_crewai_tool"]
