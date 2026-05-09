"""
AgentBio.world — Batch Verification
=====================================
Verify up to 10 agents in a single API call.
Useful before starting a multi-agent task where
you need to trust-check the entire team at once.

Run:
    pip install agentbio
    python examples/basic/batch_verify.py
"""

from agentbio import AgentBio, TrustAction


def main():
    # No API key needed for batch_verify
    ab = AgentBio()

    # ── Resolve agent IDs to thumbprints ─────────────────────────────────────
    agent_ids = ["research-agent", "coder-agent", "reviewer-agent"]
    thumbprints = []

    print("Resolving agent IDs to thumbprints...")
    for agent_id in agent_ids:
        try:
            info = ab.lookup(agent_id)
            thumbprints.append(info.thumbprint)
            print(f"  {agent_id:<25} → {info.thumbprint[:24]}...")
        except Exception:
            print(f"  {agent_id:<25} → not found — skipping")

    if not thumbprints:
        print("\nNo agents found. Register some agents first at app.agentbio.world")
        return

    # ── Batch verify all at once ───────────────────────────────────────────────
    print(f"\nBatch verifying {len(thumbprints)} agents...")
    batch = ab.batch_verify(thumbprints)

    print(f"  {batch.found}/{batch.total} found in registry\n")

    trusted = []
    cautious = []
    blocked = []

    for item in batch.items:
        if not item.found:
            print(f"  ✗ {item.thumbprint[:24]}... — not registered")
            continue

        r = item.result
        icon = {"proceed": "✅", "proceed_with_caution": "⚠️", "abort": "🚫"}[r.action.value]
        print(f"  {icon} {r.agent_id:<25} score={r.reputation_score:.1f}  risk={r.risk_level}")
        if r.flags:
            print(f"     Flags: {', '.join(r.flags)}")

        if r.action == TrustAction.PROCEED:
            trusted.append(r.agent_id)
        elif r.action == TrustAction.PROCEED_WITH_CAUTION:
            cautious.append(r.agent_id)
        else:
            blocked.append(r.agent_id)

    # ── Decision summary ───────────────────────────────────────────────────────
    print(f"\nSummary:")
    print(f"  Trusted  : {trusted  or ['none']}")
    print(f"  Cautious : {cautious or ['none']}")
    print(f"  Blocked  : {blocked  or ['none']}")

    if blocked:
        print(f"\n⛔ Refusing to start task — blocked agent(s): {blocked}")
    elif cautious:
        print(f"\n⚠️  Proceeding with caution — new agents: {cautious}")
    else:
        print(f"\n✅ All agents trusted — safe to proceed.")


if __name__ == "__main__":
    main()
