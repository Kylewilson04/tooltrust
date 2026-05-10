# Quickstart — 5 Minutes to First DDC

## 1. Install (10 seconds)

```bash
pip install tooltrust-sdk
```

## 2. Wrap a Tool (20 seconds)

```python
from tooltrust import tool

@tool(risk="read_only", name="hello_world")
def greet(name: str) -> str:
    """Say hello and get a trust certificate."""
    return f"Hello, {name}!"
```

## 3. Execute + Get DDC (20 seconds)

```python
from tooltrust import LocalToolTrustClient

client = LocalToolTrustClient()
result = client.execute(greet, "World")
ddc = client.issue_ddc()

print(f"✅ DDC issued: {ddc.ddc_id}")
print(f"   Class: {ddc.ddc_class}")
print(f"   Hash: {ddc.event_hash[:16]}...")
```

## 4. Verify (10 seconds)

```python
verification = client.verify(ddc.ddc_id)
print(f"   Signature: {'✅' if verification.signature_valid else '❌'}")
print(f"   Chain: {'✅' if verification.chain_valid else '❌'}")
```

## 5. Check Your ATP (10 seconds)

```python
from tooltrust.atp import LocalATP

atp = LocalATP()
profile = atp.get("default")
print(f"   Trust score: {profile.trust_score:.2f}")
print(f"   DDCs issued: {profile.total_ddcs}")
```

---

## You Just Did This (Free, Local, Forever)

```
┌─────────────────────────────────────────┐
│  Tool Execution                          │
│  greet("World") → "Hello, World!"       │
│       │                                  │
│       ▼                                  │
│  Policy Check (risk=read_only ✓)        │
│       │                                  │
│       ▼                                  │
│  DDC Minted (ddc-a1b2c3...)             │
│       │                                  │
│       ▼                                  │
│  Local Verifier (signature ✓)           │
│       │                                  │
│       ▼                                  │
│  ATP Updated (trust score: 0.92)        │
└─────────────────────────────────────────┘
```

**Cost:** $0.00. **SCU:** 0. **Cloud:** None.

---

## Next: Upgrade to Relay Mode

When you need production DDCs (third-party verifiable), swap one line:

```python
# Before (local, free)
client = LocalToolTrustClient()

# After (relay, metered)
client = RelayToolTrustClient(api_key="ardyn_key_xxx")

# Same tools, same decorators, same code
result = client.execute(greet, "World")
ddc = client.issue_ddc()  # Now a production DDC
```

---

## Risk Classes

```python
@tool(risk="read_only")        # ✅ Always OK locally
@tool(risk="read_filter")      # ✅ Always OK locally
@tool(risk="read_transform")   # ✅ Always OK locally
@tool(risk="generate")         # ✅ Always OK locally
@tool(risk="external_comm")    # ⚠️ Requires relay mode
@tool(risk="write_action")     # ⚠️ Requires relay mode
@tool(risk="financial")        # 🚫 Enterprise only
@tool(risk="regulated_data")   # 🚫 Enterprise only
```
