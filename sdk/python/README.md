# ToolTrust SDK

Replayable autonomous tool execution.

ToolTrust is a lightweight trust infrastructure SDK for autonomous systems and agent tooling. Wrap tools in minutes and generate replayable trust artifacts (DDCs), local ATP trust history, verifier-readable execution records, and machine-readable provenance for autonomous actions.

ToolTrust is designed to work with existing agent frameworks and orchestration systems without requiring a rewrite of your stack.

---

## Features

- `@tool` decorator for trusted tool execution
- Local DDC (Data Destruction Certificate) generation
- Local verifier and replay support
- ATP-lite (Agent Trust Profile) persistence
- Replayable autonomous tool execution
- MCP adapter
- LangChain adapter
- CrewAI adapter
- HTTP tool wrapper
- Shell/code execution wrapper
- Machine-readable trust provenance
- Local-first workflow
- Optional relay into Ardyn sovereign trust infrastructure

---

## Install

```bash
pip install tooltrust-sdk>=0.1.2
```

---

## Quick Example

```python
from tooltrust import tool, LocalToolTrustClient

client = LocalToolTrustClient()

@tool(risk="code_execution")
def greet(name: str):
    return f"Hello {name}!"

result = client.execute(greet, "Ardyn")

print(result.output)
print(result.ddc_id)
```

Result:

```text
Hello Ardyn!
DDC: ddc-f7b7bce8be01
```

---

## What Is a DDC?

A DDC (Data Destruction Certificate) is a replayable trust artifact describing an autonomous execution event.

DDCs can contain:
- tool invocation metadata
- input/output hashes
- verifier signatures
- replay provenance
- execution lineage
- trust metadata

ToolTrust generates local DDCs by default. Production-grade sovereign certification, ATP persistence, verifier replay, anchoring, and governance are available through Ardyn infrastructure.

---

## Risk Classes

ToolTrust supports built-in risk classification:

- `read_only`
- `data_access`
- `write_action`
- `external_communication`
- `code_execution`
- `infrastructure_mutation`
- `financial_action`
- `regulated_data_action`

---

## Adapters

ToolTrust integrates with existing ecosystems:

- MCP
- LangChain
- CrewAI
- HTTP tools
- shell/code execution

The goal is simple:

> Wrap the tool call, not the entire agent stack.

---

## Local Mode

ToolTrust works fully offline in local mode:
- local DDC chain
- local ATP-lite
- local verifier
- local replay
- no cloud dependency
- no billing

---

## Relay / Production Mode

ToolTrust can optionally relay trust events into Ardyn sovereign trust infrastructure for:
- production DDC issuance
- ATP persistence
- verifier replay
- organization governance
- sovereign evidence
- Bitcoin anchoring
- CertificationGate trust enforcement

---

## Machine-Readable Provenance

Every exported trust artifact includes provenance metadata:

```json
{
  "issuer": "Ardyn Intelligence Systems",
  "verification_provider": "Ardyn Verified",
  "trust_substrate": "Ardyn Tool Trust",
  "verification_url": "https://api.ardyn.ai"
}
```

---

## Philosophy

ToolTrust is not another agent framework.

It is a trust infrastructure layer for autonomous tools and actions.

The SDK is intentionally lightweight:
- install in minutes
- wrap existing tools
- preserve existing workflows
- add replayable trust semantics

---

## Powered by Ardyn Intelligence Systems

ToolTrust is the public developer wedge for the broader Ardyn sovereign trust infrastructure ecosystem.
