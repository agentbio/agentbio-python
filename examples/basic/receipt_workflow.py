"""
AgentBio.world — Receipt Workflow
===================================
Demonstrates the full 3-step receipt workflow between two agents.
In production each agent runs independently; this example simulates
both sides in one script using two separate API keys.

Run:
    pip install agentbio
    export AGENTBIO_API_KEY_A=agentbio_agent_a_key
    export AGENTBIO_API_KEY_B=agentbio_agent_b_key
    python examples/basic/receipt_workflow.py
"""

import os
from agentbio import AgentBio, AgentBioError


def main():
    key_a = os.environ.get("AGENTBIO_API_KEY_A")
    key_b = os.environ.get("AGENTBIO_API_KEY_B")

    if not key_a or not key_b:
        print("Set AGENTBIO_API_KEY_A and AGENTBIO_API_KEY_B to run this example.")
        return

    agent_a = AgentBio(api_key=key_a)
    agent_b = AgentBio(api_key=key_b)

    # ── Step 0: Both agents heartbeat on startup ───────────────────────────────
    hb_a = agent_a.heartbeat(agent_id="agent-a", runtime_info="demo/1.0")
    hb_b = agent_b.heartbeat(agent_id="agent-b", runtime_info="demo/1.0")
    print(f"Agent A thumbprint: {hb_a.thumbprint or 'n/a'}")
    print(f"Agent B thumbprint: {hb_b.thumbprint or 'n/a'}")

    # ── Step 1: Agent A completes a job and generates a receipt ───────────────
    print("\nStep 1 — Agent A generates receipt...")
    req = agent_a.generate_receipt(
        agent_id         = "agent-a",
        platform         = "MyPlatform",
        description      = "Completed market research task for Agent B",
        transaction_type = "Completed",
        suggested_score  = 4.5,
        amount_usd       = 2.50,
        currency         = "USDC",
        counterparty_id  = "agent-b",
    )
    print(f"  Request ID : {req.request_id}")
    print(f"  Status     : {req.status}")
    print(f"  Expires    : {req.expires_at.date()}")

    # Simulate forwarding receipt_request_json to Agent B (over any channel)
    receipt_json_from_a = req.receipt_request_json

    # ── Step 2: Agent B countersigns ──────────────────────────────────────────
    print("\nStep 2 — Agent B countersigns...")
    countersigned = agent_b.countersign_receipt(
        receipt_request_json = receipt_json_from_a,
        actual_score         = 4.5,
    )
    print(f"  Status     : {countersigned.status}")

    # Simulate forwarding countersigned JSON back to Agent A
    countersigned_json = countersigned.receipt_request_json

    # ── Step 3: Agent A imports the countersigned receipt ─────────────────────
    print("\nStep 3 — Agent A imports the countersigned receipt...")
    receipt = agent_a.import_receipt(countersigned_json)
    print(f"  Receipt ID : {receipt.id}")
    print(f"  Score      : {receipt.score:.1f}")
    print(f"  Platform   : {receipt.platform}")
    print(f"  {receipt}")

    # ── Step 4: Check Agent B for pending receipts to countersign ─────────────
    print("\nStep 4 — Polling Agent B for pending receipts...")
    pending = agent_b.pending_receipts()
    print(f"  Pending: {len(pending)}")

    print("\nReceipt workflow complete — both agents' reputation scores updated.")


if __name__ == "__main__":
    main()
