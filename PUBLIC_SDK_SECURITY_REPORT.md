# ToolTrust SDK — Public Security Audit Report

**Date:** 2026-05-10  
**Scope:** `tooltrust-sdk` (Python v0.1.3, TypeScript v0.1.2)  
**Auditor:** Automated Hermes Agent Security Audit  
**Repo:** `~/tooltrust/`  
**PyPI:** `tooltrust-sdk` (v0.1.3)

---

## Executive Summary

A comprehensive security audit of the ToolTrust SDK (Python + TypeScript) and its published PyPI package was performed. The SDK is a lightweight trust infrastructure wrapper for AI tool execution. **Three HIGH-severity findings, five MEDIUM-severity findings, and one BLOCKER finding** were identified. The most critical issue is in the TypeScript SDK where tool execution occurs **before** cloud authorization, completely bypassing the trust gate. The Python verifier's chain integrity check is purely cosmetic and can be trivially bypassed. No secrets, credentials, or post-install hooks were found in the published package.

---

## Finding Summary

| # | Severity | Category | Component | Title |
|---|----------|----------|-----------|-------|
| 1 | **BLOCKER** | Auth Bypass | TypeScript SDK | `RelayToolTrustClient.executeRelay()` executes tool BEFORE cloud authorization |
| 2 | **HIGH** | Verification Bypass | Python + TS | Verifier chain integrity check is cosmetic — hash chain linkage never validated |
| 3 | **HIGH** | Proof Spoofing | Python + TS | `DdcCertificate` dataclass fields are mutable — provenance can be trivially spoofed |
| 4 | **HIGH** | Auth Bypass | Python SDK | Shell adapter can bypass risk class restrictions via `code_execution` risk level |
| 5 | **MEDIUM** | Docstring Danger | Python SDK | Shell adapter docstring demonstrates `shell=True` (command injection vector) |
| 6 | **MEDIUM** | Input Trust | Python + TS | Adapters trust arbitrary user-supplied callables without input sanitization |
| 7 | **MEDIUM** | Docs/Code Mismatch | Python SDK | README examples reference non-existent `result.output`; `result.ddc_id` is `None` locally |
| 8 | **MEDIUM** | Misleading Label | Python SDK | `ReplayResult.deterministic` is aliased to `match` — nondeterministic fn → misleading label |
| 9 | **MEDIUM** | Offline Fallback | Python SDK | Relay client falls back to local execution on HTTP 500 (design choice, but exploitable) |
| 10 | **LOW** | Stale Build | Python SDK | `build/lib/` directory contains stale v0.1.0 code — should be cleaned from distribution |
| 11 | **INFO** | No Secrets | PyPI Package | No API keys, tokens, credentials, or internal URLs found in published package |
| 12 | **INFO** | No Post-Install | PyPI Package | No `post_install`, `pre_install`, or `cmdclass` hooks in setup.py/pyproject.toml |
| 13 | **INFO** | Clean Artifacts | PyPI Package | No `__pycache__`, `.git`, `.env`, or `.pyc` files in published tar.gz |
| 14 | **INFO** | No Dangerous Imports | Python SDK | No `eval()`, `exec()`, `os.system()`, `pickle`, or `yaml.load()` in source |
| 15 | **INFO** | No Dangerous Functions | TypeScript SDK | No `eval()`, `new Function()`, `Function()`, or dynamic imports in source |
| 16 | **INFO** | Zero Third-Party Deps | Python SDK | setup.py has no `install_requires`; only stdlib modules used |
| 17 | **INFO** | Zero Third-Party Deps | TypeScript SDK | `package.json` has no `dependencies` or `devDependencies` |
| 18 | **INFO** | Doc Risk Class Drift | QUICKSTART.md | Documents risk classes (`read_filter`, `generate`, `financial`) not in actual code |

---

## Detailed Findings

### Finding 1 — BLOCKER: TypeScript Relay Executes Tool Before Authorization

**File:** `sdk/typescript/src/client.ts`, lines 165–167  
**Severity:** BLOCKER

```typescript
async executeRelay(fn: (...args: any[]) => any, ...args: any[]): Promise<ToolResult> {
    const localResult = this.execute(fn, ...args);  // ⚠️ Tool runs HERE
    // ...
    const authResp = await fetch(`${this.baseUrl}/v1/tools/authorize`, {  // Auth runs AFTER
```

The tool function is executed unconditionally at line 166, **before** the cloud authorization call at line 170. This means:
- A tool with `riskClass = FinancialAction` executes its side effects even if authorization is denied.
- The authorization denial only prevents the *certificate* from being issued — the damage is already done.
- This is the opposite of the Python implementation, which calls `authorize` first, then `execute`.

**Recommendation:** Move `this.execute(fn, ...args)` to **after** the authorization check, matching the Python client's flow.

---

### Finding 2 — HIGH: Verifier Chain Integrity Check Is Cosmetic

**Files:** 
- `sdk/python/tooltrust/verifier.py`, lines 47–53
- `sdk/typescript/src/client.ts`, lines 128–131

**Severity:** HIGH

**Python:**
```python
# Check chain linkage — each event's hash is the prev_hash of the next
chain_valid = True
for i in range(1, len(chain.events)):
    # Simple check: all events have valid hashes
    if not chain.events[i].event_hash:
        chain_valid = False
```

**TypeScript:**
```typescript
const chainValid = this.ddcChain.events.every(e => e.eventHash.length === 64);
```

Both verifiers only check that event hashes are non-empty and 64 characters long. **Neither verifier checks hash chain linkage** — i.e., whether `event[i].event_hash` was actually computed from `prev_hash + session_id + ...` or whether `event[i].prev_hash == event[i-1].event_hash`.

The chain `_prev_hash` is stored privately in `LocalDdcChain` and is never exposed to the verifier. This means:
- A user can overwrite any event's hash to any 64-hex-char string and the verifier will still report `chain_valid: True`.
- There is no tamper-evidence in the local chain.

**Verified:** Overwriting `chain.events[0].event_hash = '0' * 64` mid-chain still yields `chain_valid: True`.

**Recommendation:** The verifier must recompute each event hash using the previous event's hash and compare against the stored hash. Alternatively, expose `_prev_hash` on each event and verify the linked list.

---

### Finding 3 — HIGH: DDC Certificate Provenance Fields Are Mutable

**Files:**
- `sdk/python/tooltrust/ddc.py`, lines 17–31 (`DdcCertificate` dataclass)
- `sdk/typescript/src/client.ts`, lines 110–126 (mutable object literal)

**Severity:** HIGH

The `DdcCertificate` dataclass stores provenance fields (`issuer`, `verification_provider`, `verification_url`) as plain mutable strings with default values:

```python
@dataclass
class DdcCertificate:
    issuer: str = "Ardyn Intelligence Systems"
    verification_provider: str = "Ardyn Verified"
    # ...
```

The `to_provenance()` method reads these fields directly at export time:
```python
"_provenance": {
    "issuer": cert.issuer,  # Mutable — can be changed before export
```

**Verified:** 
```python
cert.issuer = "Evil Corp"
chain.to_provenance(cert)  # Exports "issuer": "Evil Corp"
```

Any code with a reference to a `DdcCertificate` object can silently overwrite provenance fields before export. There is no digital signature or integrity check over the provenance block.

**Recommendation:** Either:
1. Make provenance fields `frozen=True` on the dataclass and set at construction time only.
2. Or cryptographically sign the provenance block at creation time and verify at export.

---

### Finding 4 — HIGH: Shell Adapter Risk Class Bypass

**File:** `sdk/python/tooltrust/adapters/shell_adapter.py`  
**Severity:** HIGH

The shell adapter defaults to `risk="write_action"` (level 5), which is correctly blocked in local mode. However, a user can set `risk="code_execution"` (level 3, allowed in local mode) and the adapter will execute arbitrary shell commands with `shell=True`:

```python
@tool(risk='code_execution')  # ← Bypasses local mode block (level 3 ≤ 4)
def shell_wrapper(cmd):
    import subprocess
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

client = LocalToolTrustClient()
result = client.execute(shell_wrapper, 'rm -rf /')  # Executes!
```

**Verified:** The test confirmed this executes successfully in local mode.

The SDK trusts the user to classify tools correctly, but nothing prevents misclassification (accidental or malicious). The risk class system is self-reported with no enforcement mechanism.

**Recommendation:** The adapter wrapper should validate that the declared risk class is appropriate for shell execution. At minimum, document this footgun prominently.

---

### Finding 5 — MEDIUM: Shell Adapter Docstring Shows Command Injection Vector

**File:** `sdk/python/tooltrust/adapters/shell_adapter.py`, lines 10–13  
**Severity:** MEDIUM

```python
def run_test(command: str) -> dict:
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
```

This is only a docstring example, not executed code. However, it serves as copy-paste guidance for users. `shell=True` with unsanitized user input is a classic command injection vector.

**Recommendation:** Replace the docstring example with a safer pattern (e.g., `subprocess.run(command.split(), shell=False, ...)`).

---

### Finding 6 — MEDIUM: Adapters Pass User Arguments to Arbitrary Callables

**Files:** All adapter wrappers (`shell_adapter.py`, `http_adapter.py`, `crewai.py`, `langchain.py`, `mcp.py`)  
**Severity:** MEDIUM

Every adapter pattern follows:
```python
def wrapped(*args, **kwargs) -> Any:
    return user_supplied_fn(*args, **kwargs)  # No input validation
```

The `client.execute(wrapped, *args, **kwargs)` call only checks the **risk class** and **authority level**. It does not validate, sanitize, or constrain the arguments passed to the wrapped function. This is by design (the SDK wraps arbitrary tool functions), but it means:
- Any tool marked `risk="read_only"` could still have destructive side effects through its arguments.
- The `RiskClass` is purely advisory — the SDK trusts the developer to classify correctly.

**Recommendation:** Document this trust model clearly. Consider adding an optional input validator hook to the `@tool` decorator.

---

### Finding 7 — MEDIUM: README Code Examples Don't Match Actual API

**File:** `sdk/python/README.md`, lines 48–52  
**Severity:** MEDIUM

```python
print(result.output)    # ❌ ToolResult has no 'output' attribute
print(result.ddc_id)    # ❌ None in LocalToolTrustClient (only set in relay mode)
```

**Verified:**
- `ToolResult` has `data`, not `output`.
- `execute()` in `LocalToolTrustClient` never sets `ddc_id` — only cloud relay sets it.
- The README implies `client.execute(...)` produces a DDC, but the DDC is separate: `client.issue_ddc()`.

The **QUICKSTART.md** example correctly shows `client.issue_ddc()` after execute, which is the proper pattern.

Additionally, QUICKSTART.md risk class names (`read_filter`, `read_transform`, `generate`, `external_comm`, `financial`) don't match the actual enum values (`data_access`, `code_execution`, `external_communication`, `financial_action`).

**Recommendation:** Fix README to use `result.data` and `client.issue_ddc().ddc_id`. Fix QUICKSTART risk class names.

---

### Finding 8 — MEDIUM: ReplayResult.deterministic Is Misleading

**File:** `sdk/python/tooltrust/replay.py`, line 48  
**Severity:** MEDIUM

```python
match = output_hash == expected_output_hash
deterministic = match  # Misleading variable name
```

The `deterministic` field is always set equal to `match`. A non-deterministic function like `time.time()` correctly produces `match=False`, which then sets `deterministic=False`. This is technically correct in that "if it didn't match, it's not deterministic" — but the label is misleading because:
- A deterministic function called with different arguments would also produce `match=False`.
- The field doesn't actually measure determinism — it measures replay match.

**Recommendation:** Rename to `replay_matched` or similar, or remove the `deterministic` field since it's redundant with `match`.

---

### Finding 9 — MEDIUM: Relay Client Falls Back to Local on HTTP 500

**File:** `sdk/python/tooltrust/client.py`, lines 186–189  
**Severity:** MEDIUM

```python
except urllib.error.HTTPError as e:
    # Offline fallback
    if e.code >= 500:
        return self._local_client.execute(fn, *args, **kwargs)
```

When the cloud relay returns HTTP 5xx, the client silently falls back to local execution with **no DDC minting, no cloud verification, no SCU metering**. This is a design choice for resilience, but it creates a potential attack vector:
- An attacker who can cause 500 errors (SSRF, DoS on api.ardyn.ai) can force tools into unverified local mode.
- The caller receives a `ToolResult` indistinguishable from a successful relay execution (only `ddc_id` is missing).

**Recommendation:** Make the offline fallback opt-in via a flag. When it triggers, raise a warning or set a flag on the `ToolResult`.

---

### Finding 10 — LOW: Stale Build Artifacts in build/lib/

**File:** `sdk/python/build/lib/tooltrust/ddc.py`  
**Severity:** LOW

The `build/lib/` directory contains v0.1.0 code (note: `generated_by: "tooltrust-sdk/0.1.0"` vs `0.1.3` in the source). The `.gitignore` excludes `build/`, but the directory persists in the working copy. While not shipped in the tar.gz, it indicates a stale build environment.

**Recommendation:** Run `rm -rf build/ dist/ *.egg-info` and rebuild clean.

---

### Finding 11–18 — INFO: Clean Supply Chain

**Severity:** INFO

- **No secrets found:** Grep for `BEGIN`, `private_key`, `api_key=`, `token=`, passwords, `.internal` URLs in the PyPI tar.gz returned only the expected `api_key=...` in a docstring/usage message.
- **No post-install hooks:** No `cmdclass`, `post_install`, `pre_install`, `entry_points.console_scripts` in `setup.py` or `pyproject.toml`.
- **Clean package:** The published `tooltrust_sdk-0.1.3.tar.gz` contains no `__pycache__/`, `.git/`, `.env`, `.pyc`, or `.DS_Store` files.
- **No dangerous code patterns:** No `eval()`, `exec()`, `os.system()`, `pickle.load()`, `yaml.load()`, `__import__()` in any Python source file.
- **No dangerous JS patterns:** No `eval()`, `new Function()`, `Function()`, dynamic `import()`, or `__proto__` manipulation in TypeScript source.
- **Zero dependencies:** The Python SDK uses only stdlib (`hashlib`, `json`, `uuid`, `time`, `urllib`, `os`, `dataclasses`). TypeScript SDK only uses Node.js `crypto` module via `require()`.
- **Hardcoded URL:** `https://api.ardyn.ai` appears in source code (Python + TS) as the production API endpoint — this is a public endpoint, not a secret.
- **Import safety:** `import tooltrust` triggers no network calls, no subprocess calls, no file writes beyond normal Python module loading.
- **TypeScript `require("crypto")`:** Uses CommonJS `require()` inside TypeScript modules — works in Node.js but would break in pure ESM or browser environments.

---

## Supply Chain Checklist

| Check | Status |
|-------|--------|
| Secrets/keys/tokens in published package | ✅ Clean |
| Internal/hardcoded URLs (non-public) | ✅ Clean |
| `__pycache__`, `.pyc` in tarball | ✅ Clean |
| `.git/` in tarball | ✅ Clean |
| `.env` or credential files | ✅ Clean |
| Post-install hooks | ✅ Clean |
| Dependency vulnerabilities | ✅ No dependencies |
| `eval()`/`exec()`/`os.system()` | ✅ None found |
| `pickle`/`yaml.load` deserialization | ✅ None found |
| `subprocess` with `shell=True` in code | ✅ Only in docstring example |
| `new Function()` in TypeScript | ✅ None found |
| Dynamic imports from user input | ✅ None found |
| Prototype pollution | ✅ None found |

---

## Risk Class Matrix

| Risk Class | Level | Allowed in Local | Notes |
|-----------|-------|------------------|-------|
| `read_only` | 1 | ✅ | Safe |
| `data_access` | 2 | ✅ | Safe |
| `code_execution` | 3 | ✅ | **Potential bypass vector** for shell adapter |
| `external_communication` | 4 | ✅ | Edge of local mode |
| `write_action` | 5 | ❌ | Requires relay |
| `infrastructure_mutation` | 6 | ❌ | Requires relay |
| `financial_action` | 7 | ❌ | Requires relay |
| `regulated_data_action` | 8 | ❌ | Requires relay |

---

## Recommendations (Priority Order)

1. **BLOCKER:** Fix TypeScript `executeRelay()` to call `authorize` **before** `execute`.
2. **HIGH:** Implement actual hash chain linkage verification in both Python and TypeScript verifiers.
3. **HIGH:** Make `DdcCertificate` provenance fields immutable or add cryptographic signature.
4. **HIGH:** Add risk-class validation in shell adapter to prevent `code_execution` bypass.
5. **MEDIUM:** Fix README code examples to use correct attribute names (`data` not `output`).
6. **MEDIUM:** Replace `shell=True` in shell adapter docstring with safe example.
7. **MEDIUM:** Add input validation hooks to the `@tool` decorator.
8. **MEDIUM:** Make relay offline fallback opt-in.
9. **LOW:** Clean stale `build/` artifacts.
10. **INFO:** Fix QUICKSTART.md risk class names to match actual enum values.

---

## Methodology

- Static analysis of all `.py` and `.ts` source files in `sdk/`
- Extraction and inspection of PyPI tarball (`tooltrust_sdk-0.1.3.tar.gz`)
- Dynamic testing: import, execution, replay, verification, and spoofing attacks
- Pattern search for dangerous APIs (`eval`, `exec`, `os.system`, `subprocess`, `pickle`, `yaml.load`, `new Function`, prototype pollution)
- Supply chain checks: secrets, credentials, `.git`, `__pycache__`, post-install hooks
- Dependency analysis: zero third-party packages in both Python and TypeScript SDKs
- README/code cross-validation

---

*Report generated by automated security audit. No secrets were extracted, modified, or exfiltrated during this audit.*
