"""Tool Trust Adapters — plug into MCP, LangChain, CrewAI, HTTP, Shell."""

from .mcp import wrap_mcp_tool
from .langchain import wrap_langchain_tool
from .crewai import wrap_crewai_tool
from .http_adapter import wrap_http_tool
from .shell_adapter import wrap_shell_tool

__all__ = [
    "wrap_mcp_tool",
    "wrap_langchain_tool",
    "wrap_crewai_tool",
    "wrap_http_tool",
    "wrap_shell_tool",
]
