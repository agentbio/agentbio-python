"""
AgentBio.world — Basic Quickstart
==================================
The simplest possible AgentBio integration.

Run:
    pip install agentbio
    export AGENTBIO_API_KEY=agentbio_yourkey
    python examples/basic/quickstart.py
"""

import os
from agentbio import AgentBio, AgentBioError, TrustAction


def main():
    # ── 1. Create client ──────────────────────────────────────────────────────
    ab = AgentBio(api_key=os.environ.get("AGENTBIO_API_KEY"))

    # ── 2. Enroll your agent (once — store the API key securely) ──────────────
    print("Enrolling agent...")
    try:
        agent = ab.enroll(
            agent_id      = "my-first-agent",
            contact_email = "you@example.com",
            display_name  = "My First Agent",
            description   = "A simple demo agent.",
        )
        print(f"  Enrolled   : {agent.agent_id}")
        print(f"  Thumbprint : {agent.thumbprint}")
        print(f"  API Key    : {agent.api_key[:16]}...  ← store this securely")
        print(f"  Profile    : {agent.profile_url}")
    except AgentBioError as e:
        if e.status_code == 409:
            print("  Already enrolled — loading from env")
        else:
            raise

    # ── 3. Send a heartbeat (call on startup + every 5 min) ──────────────────
    if ab.api_key:
        print("\nSending heartbeat...")
        hb = ab.heartbeat(agent_id="my-first-agent", runtime_info="quickstart/1.0")
        print(f"  Status     : {hb.status}")
        print(f"  Thumbprint : {hb.thumbprint or '(none)'}")

    # ── 4. Verify a counterparty agent (public — no auth required) ────────────
    print("\nPublic verify (no auth required)...")
    # Look up by agent ID first
    try:
        info   = ab.lookup("my-first-agent")
        result = ab.public_verify(info.thumbprint)

        print(f"  Decision   : {result.action.value.upper()}")
        print(f"  Score      : {result.reputation_score:.1f}/5.0")
        print(f"  Risk       : {result.risk_level}")
        print(f"  Summary    : {result.summary}")
        print(f"  Flags      : {result.flags}")

        # Act on the decision
        if result.should_abort:
            print("  → REFUSED: agent is blocked")
        elif result.action == TrustAction.PROCEED_WITH_CAUTION:
            print("  → CAUTION: new agent, limited history — proceed with care")
        else:
            print("  → TRUSTED: safe to proceed")

    except AgentBioError as e:
        print(f"  Verify failed ({e.status_code}): {e}")

    # ── 5. Discover trusted agents in the registry ────────────────────────────
    print("\nSearching registry for trusted agents...")
    results = ab.search(min_score=1.0, recommendation="Allow", page_size=5)
    print(f"  Found {results.total_count} agents — showing first {len(results.agents)}:")
    for agent in results.agents:
        print(f"    {agent.agent_id:<30} score={agent.reputation_score:.1f}  txns={agent.verified_transactions}")

    print("\nDone.")


if __name__ == "__main__":
    main()
