"""
HTTP Tool Adapter for Tool Trust.

Usage:
    from tooltrust.adapters.http import wrap_http_tool
    from tooltrust import LocalToolTrustClient

    client = LocalToolTrustClient()

    def fetch_api(url: str) -> dict:
        import requests
        return requests.get(url).json()

    wrapped = wrap_http_tool(fetch_api, client, risk="read_filter")
    result = wrapped("https://api.example.com/data")
    ddc = client.issue_ddc()
"""

from typing import Any, Callable, Optional
from tooltrust import tool, LocalToolTrustClient, ToolResult


def wrap_http_tool(
    http_fn: Callable,
    client: LocalToolTrustClient,
    risk: str = "external_comm",
    name: Optional[str] = None,
    authority_required: int = 1,
) -> Callable:
    """Wrap an HTTP-calling function with Tool Trust certification.

    HTTP tools are classified as external_comm (Risk 5) by default
    and require at least Reader authority.
    """
    @tool(
        risk=risk,
        name=name or http_fn.__name__,
        adapter="http",
        authority_required=authority_required,
    )
    def wrapped(*args, **kwargs) -> Any:
        return http_fn(*args, **kwargs)

    def execute(*args, **kwargs) -> ToolResult:
        # HTTP tools require relay mode for risk 5+
        return client.execute(wrapped, *args, **kwargs)

    return execute


__all__ = ["wrap_http_tool"]
