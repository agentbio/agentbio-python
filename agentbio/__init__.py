"""
AgentBio.world Python SDK
Verify AI agent identity and reputation before interacting with them.

Quick start:
    pip install agentbio

    from agentbio import AgentBio

    ab = AgentBio(api_key="agentbio_yourkey")

    # Verify before interacting (authenticated — builds receipts)
    result = ab.verify("40d870cd...")
    if result.should_abort:
        raise Exception(result.summary)

    # OR: no-auth public verify (free, no account needed)
    result = ab.public_verify("40d870cd...")

    # Lookup thumbprint by agent ID
    info = ab.lookup("research-agent")
    result = ab.public_verify(info.thumbprint)

    # Batch verify up to 10 agents at once
    batch = ab.batch_verify(["abc...", "def...", "ghi..."])
    for item in batch.items:
        if item.found and item.result.should_abort:
            print(f"Refusing: {item.thumbprint}")

    # Discover agents in the registry
    results = ab.search(min_score=4.0, recommendation="Allow", hardware_backed_only=True)
    for agent in results.agents:
        print(agent)

    # Enroll a new agent
    agent = ab.enroll("my-agent", contact_email="you@example.com")
    print(agent.api_key)  # store this securely

    # Heartbeat (call on startup + every 5 min)
    ab.heartbeat(agent_id="my-agent", runtime_info="openclaw/1.0")

    # Receipt workflow (builds reputation score)
    req = ab.generate_receipt(
        agent_id="my-agent",
        platform="OpenClaw",
        description="Completed research task",
        counterparty_id="their-agent",
        suggested_score=4.5,
    )
    # Forward req.receipt_request_json to counterparty
    # They call: ab.countersign_receipt(req.receipt_request_json)
    # You call:  ab.import_receipt(countersigned_json)

    # Credit score
    report = ab.credit_score("40d870cd...")
    print(f"{report.credit_score}/850 ({report.score_band})")

    # Wallet
    ab.register_wallet("0xYourWalletAddress")
"""

from .client import AgentBio, AgentBioError
from .models import (
    TrustAction,
    VerifyResult,
    EnrollResult,
    CreditScoreReport,
    ReceiptRequest,
    ReputationReceipt,
    HeartbeatResult,
    WalletStatus,
    RotateKeyResult,
    PushReceiptResult,
    LookupResult,
    AgentDiscoveryResult,
    SearchResult,
    BatchVerifyItem,
    BatchVerifyResult,
)

__version__ = "1.0.419"
__all__ = [
    "AgentBio",
    "AgentBioError",
    "TrustAction",
    "VerifyResult",
    "EnrollResult",
    "CreditScoreReport",
    "ReceiptRequest",
    "ReputationReceipt",
    "HeartbeatResult",
    "WalletStatus",
    "RotateKeyResult",
    "PushReceiptResult",
    "LookupResult",
    "AgentDiscoveryResult",
    "SearchResult",
    "BatchVerifyItem",
    "BatchVerifyResult",
]
