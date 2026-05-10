"""
Shell / Code Execution Adapter for Tool Trust.

Usage:
    from tooltrust.adapters.shell import wrap_shell_tool
    from tooltrust import LocalToolTrustClient

    client = LocalToolTrustClient()

    def run_test(command: str) -> dict:
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr, "code": result.returncode}

    wrapped = wrap_shell_tool(run_test, client, risk="write_action")
    result = wrapped("pytest tests/")
    ddc = client.issue_ddc()
"""

from typing import Any, Callable, Optional
from tooltrust import tool, LocalToolTrustClient, ToolResult


def wrap_shell_tool(
    shell_fn: Callable,
    client: LocalToolTrustClient,
    risk: str = "write_action",
    name: Optional[str] = None,
    authority_required: int = 2,
) -> Callable:
    """Wrap a shell/code execution function with Tool Trust certification.

    Shell/execution tools are classified as write_action (Risk 6) by default
    and require at least Contributor authority. Risk 6 is blocked in local mode —
    upgrade to RelayToolTrustClient for production use.
    """
    @tool(
        risk=risk,
        name=name or shell_fn.__name__,
        adapter="shell",
        authority_required=authority_required,
    )
    def wrapped(*args, **kwargs) -> Any:
        return shell_fn(*args, **kwargs)

    def execute(*args, **kwargs) -> ToolResult:
        return client.execute(wrapped, *args, **kwargs)

    return execute


__all__ = ["wrap_shell_tool"]
