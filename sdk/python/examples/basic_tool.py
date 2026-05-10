"""Basic Tool Trust example — local mode, free forever."""

from tooltrust import tool, LocalToolTrustClient


@tool(risk="read_only", name="web_search")
def search_docs(query: str, limit: int = 5) -> dict:
    """Search the documentation."""
    return {"results": [f"Found: {query}"] * min(limit, 3)}


@tool(risk="read_filter", name="database_query")
def query_db(sql: str) -> list:
    """Query the internal database."""
    return [{"id": 1, "name": "Test record"}]


def main():
    client = LocalToolTrustClient()

    # Execute tools with trust
    for fn, args in [
        (search_docs, {"query": "liability verification"}),
        (query_db, {"sql": "SELECT * FROM policies"}),
    ]:
        result = client.execute(fn, **args)
        print(f"  {fn._tool_descriptor.name}: {'OK' if result.success else 'FAIL'}")
        print(f"    Risk: {result.trace.risk_class.value}")
        print(f"    Duration: {result.trace.duration_ms}ms")

    # Issue DDC
    ddc = client.issue_ddc()
    print(f"\nDDC issued: {ddc.ddc_id}")
    print(f"  Class: {ddc.ddc_class.value}")
    print(f"  Events in chain: {len(client.ddc_chain.events)}")

    # Verify
    verification = client.verify(ddc.ddc_id)
    print(f"\nVerification:")
    print(f"  Signature: {'✅' if verification.signature_valid else '❌'}")
    print(f"  Chain: {'✅' if verification.chain_valid else '❌'}")

    # Check ATP
    profile = client.get_atp()
    print(f"\nATP:")
    print(f"  Agent: {profile.agent_id}")
    print(f"  Trust score: {profile.trust_score:.2f}")
    print(f"  DDCs: {profile.total_ddcs}")


if __name__ == "__main__":
    main()
