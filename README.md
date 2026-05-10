# Tool Trust

**Wrap tools. Get trust. Free.**

[![Python](https://img.shields.io/pypi/v/tooltrust-sdk)](https://pypi.org/project/tooltrust-sdk/)
[![npm](https://img.shields.io/npm/v/@ardyn/tooltrust-sdk)](https://www.npmjs.com/package/@ardyn/tooltrust-sdk)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Tool Trust gives every AI tool a cryptographically-verifiable trust certificate. Local DDCs are free forever. Production DDCs are metered via [Ardyn](https://ardyn.ai) SCU (Sovereign Certification Units).

## Why Tool Trust?

AI agents call tools — search, query, execute, transfer. Every call is a liability event. Tool Trust wraps every tool call in cryptographic evidence so you can prove what happened, when, and under what authority.

- **Free forever:** Local DDCs, local verifier, local ATP — zero cost
- **5-minute install:** `pip install` or `npm install`, one decorator, done
- **Upgrade when ready:** Same adapter, different client — local → relay → enterprise
- **Production trust:** SCU-metered certification via [api.ardyn.ai](https://ardyn.ai)

## Install

```bash
# Python
pip install tooltrust-sdk

# TypeScript
npm install @ardyn/tooltrust-sdk
```

## 30 Seconds to Your First DDC

```python
from tooltrust import tool, LocalToolTrustClient

@tool(risk="read_only")
def search_docs(query: str) -> dict:
    return {"results": [f"Found: {query}"]}

client = LocalToolTrustClient()
result = client.execute(search_docs, "liability verification")
ddc = client.issue_ddc()
print(f"DDC: {ddc.ddc_id}")  # Free, local, verifiable
```

## Modes

| Mode | Client | DDCs | Cost | When to Use |
|------|--------|:---:|:---:|-------------|
| **Local** | `LocalToolTrustClient` | Local | Free | Development, testing |
| **Relay** | `RelayToolTrustClient` | Production | Metered | Production, audit |
| **Enterprise** | `ProductionToolTrustClient` | Production | Metered | Compliance, regulated |

## Adapters

Tool Trust provides drop-in adapters for popular AI frameworks:

| Adapter | Status | Install |
|---------|:---:|---------|
| MCP (Model Context Protocol) | ✅ | `adapters/mcp/` |
| LangChain | ✅ | `adapters/langchain/` |
| CrewAI | ✅ | `adapters/crewai/` |
| HTTP | ✅ | `adapters/http/` |
| Shell / Code Execution | ✅ | `adapters/shell/` |

## License

MIT — see [LICENSE](LICENSE)

---

Built by [Ardyn](https://ardyn.ai) — Liability Verification Substrate for Autonomous Systems.
