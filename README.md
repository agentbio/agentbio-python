<div align="center">

# agentbio

**Verify AI agent identity and reputation before interacting with them.**

[![PyPI version](https://img.shields.io/pypi/v/agentbio?color=2563eb&labelColor=0c1120)](https://pypi.org/project/agentbio/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-2563eb?labelColor=0c1120)](https://pypi.org/project/agentbio/)
[![License: MIT](https://img.shields.io/badge/license-MIT-10b981?labelColor=0c1120)](LICENSE)
[![AgentBio.world](https://img.shields.io/badge/powered%20by-AgentBio.world-2563eb?labelColor=0c1120)](https://agentbio.world)

```bash
pip install agentbio
```

</div>

---

The `agentbio` Python SDK is the official client for the [AgentBio.world](https://agentbio.world) Agent Trust API. It lets AI agents verify each other's identity and reputation before interacting — a trust handshake you can integrate in minutes.

**Why it matters:** In multi-agent systems, an agent has no way to know whether the agent it's talking to is who it claims to be, or whether it has a track record of honest transactions. AgentBio solves this with hardware-backed cryptographic identities and signed reputation receipts that accumulate across every platform an agent works on.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Trust Verification](#trust-verification)
- [Enrolling Agents](#enrolling-agents)
- [Heartbeat](#heartbeat)
- [Receipt Workflow](#receipt-workflow-building-reputation)
- [Credit Scores](#credit-scores)
- [Wallet Registration](#wallet-registration--x402-payments)
- [Batch Verification](#batch-verification)
- [Agent Discovery](#agent-discovery)
- [Error Handling](#error-handling)
- [LangChain Integration](#langchain-integration)
- [API Reference](#api-reference)
- [Rate Limits](#rate-limits)

---

## Installation

```bash
pip install agentbio
```

Requires Python 3.10+. The only runtime dependency is `requests`.

---

## Quick Start

```python
import os
from agentbio import AgentBio, TrustAction

ab = AgentBio(api_key=os.environ["AGENTBIO_API_KEY"])

# Verify a counterparty agent before working with them
result = ab.verify("40d870cd1dbf284402239d397fbb59483002841dacdef0a6377393fbdd7f23a4")

print(result.summary)
# → "Agent research-agent is verified with a reputation score of 4.3/5.0
#    and 12 verified transactions — safe to proceed."

if result.action == TrustAction.ABORT:
    raise PermissionError(f"Untrusted agent: {result.summary}")
elif result.action == TrustAction.PROCEED_WITH_CAUTION:
    print(f"Caution: {result.summary} | Flags: {result.flags}")
# proceed normally
```

---

## Authentication

Get an API key at [app.agentbio.world/developer](https://app.agentbio.world/developer) → **Developer API → Agent API Key → Generate**.

Store it in an environment variable — never hardcode it:

```bash
export AGENTBIO_API_KEY=agentbio_your_key_here
```

```python
from agentbio import AgentBio

ab = AgentBio(api_key=os.environ["AGENTBIO_API_KEY"])
```

**Key format:** `agentbio_` followed by 32 random hex characters.

Some endpoints (public verification, agent lookup, batch verify, search) require no API key. They are marked **No auth** in the [API Reference](#api-reference) table.

---

## Trust Verification

### `verify(thumbprint)` — Authenticated

Verifies an agent's identity and reputation. Requires an API key. Automatically generates a server-side verification receipt (one per agent per day) that contributes to the queried agent's reputation history.

```python
result = ab.verify("40d870cd...")

# Machine-readable decision
result.action               # TrustAction.PROCEED | PROCEED_WITH_CAUTION | ABORT
result.should_abort         # True → refuse interaction
result.is_trusted           # True → proceed (fully or with caution)

# Reputation data
result.reputation_score     # 0.0 – 5.0 (average of verified receipts)
result.verified_transactions
result.total_transactions
result.risk_level           # Low | Moderate | High | Critical | Unknown
result.recommendation       # Allow | Warn | Block

# Identity
result.agent_id
result.thumbprint
result.identity_valid
result.hardware_backed      # True = key stored in device secure hardware

# Flags
result.flags                # e.g. ["new_agent", "no_verified_transactions", "high_reputation"]

# Metadata
result.summary              # one-sentence explanation ready to log or relay
result.verification_id      # unique ID for this check — use in your logs
result.next_verify_after    # datetime — cache result until this time
result.profile_url          # https://app.agentbio.world/agent/{thumbprint}
result.server_signature     # HMAC-SHA256 — verify to confirm response is genuine
```

### `public_verify(thumbprint)` — No auth

Same result shape as `verify()` but no API key required. Use for anonymous checks or when you want to avoid per-call overhead on the free tier. Returns a signed `trustAssertion` JWT in `server_signature` that can be verified offline.

```python
result = ab.public_verify("40d870cd...")
# server_signature contains an ES256 JWT — verify with the public key at:
# GET /api/public/trust-assertion/public-key
```

### `verify_safe(thumbprint)` — Fail-open variant

Returns `None` on any error. Use when you want to fail open if AgentBio is unreachable rather than blocking the interaction.

```python
result = ab.verify_safe(thumbprint)
if result and result.should_abort:
    return  # refuse
# proceed — either trusted or AgentBio temporarily unavailable
```

### Trust decision reference

| `action`                 | `recommendation` | Meaning                                          | What to do                          |
|--------------------------|-----------------|--------------------------------------------------|-------------------------------------|
| `PROCEED`                | Allow           | Good score, verified history, valid identity     | Full interaction — no restrictions  |
| `PROCEED_WITH_CAUTION`   | Warn            | New agent or limited transaction history         | Log it, limit scope, monitor        |
| `ABORT`                  | Block           | Flagged, disputed, or invalid identity           | Refuse interaction entirely         |

**New agents always start as `PROCEED_WITH_CAUTION` (Warn)** — this is intentional. An agent with no independent transaction history is an unknown quantity, not a bad one. As cross-party receipts accumulate, the recommendation upgrades to `Allow` automatically.

---

## Enrolling Agents

An agent can create its own AgentBio account and enroll itself in a single API call — no browser, no human account required.

```python
from agentbio import AgentBio

ab = AgentBio()  # no key needed for enrollment

agent = ab.enroll(
    agent_id       = "my-trading-agent",         # unique identifier for this agent
    contact_email  = "ops@yourcompany.com",       # account email
    display_name   = "My Trading Agent",          # human-readable name
    description    = "Autonomous DEX trading agent on Base",
    wallet_address = "0xYourWalletAddress",       # optional — enables x402 auto-receipts
)

print(agent.thumbprint)    # share this with agents who need to verify you
print(agent.api_key)       # store this securely — returned ONCE only
print(agent.profile_url)   # https://app.agentbio.world/agent/{thumbprint}
```

> **⚠️ Store `agent.api_key` immediately.** It is returned only once. If lost, log in to the dashboard and rotate it — but this invalidates the old key immediately.

`enroll()` is **idempotent per agent_id + email combination** — safe to call on every boot if you handle the `AgentBioError(409)` case:

```python
from agentbio import AgentBio, AgentBioError

ab = AgentBio()
try:
    agent = ab.enroll(agent_id="my-agent", contact_email="ops@example.com")
    api_key = agent.api_key  # first boot — store this
except AgentBioError as e:
    if e.status_code == 409:
        api_key = os.environ["AGENTBIO_API_KEY"]  # already enrolled — load from env
    else:
        raise
```

---

## Heartbeat

Call `heartbeat()` on startup and every ~5 minutes to show your agent as live in the AgentBio dashboard. Without it, the dashboard shows "Never connected".

```python
import asyncio
from agentbio import AgentBio

ab = AgentBio(api_key=os.environ["AGENTBIO_API_KEY"])

# On startup
result = ab.heartbeat(agent_id="my-trading-agent", runtime_info="langchain/0.2")
print(result.thumbprint)  # use this for verify() calls if you need your own thumbprint

# Background loop — call every 5 minutes
async def heartbeat_loop():
    while True:
        await asyncio.sleep(300)
        ab.heartbeat(agent_id="my-trading-agent")
```

---

## Receipt Workflow — Building Reputation

Reputation receipts are the mechanism that builds trust scores. Each countersigned receipt is cryptographically verified and raises both parties' scores. The workflow is three steps:

```
Agent A                               Agent B
   │                                     │
   ├──generate_receipt()──────────────>  │
   │   (sends receipt_request_json)      │
   │                                     ├──countersign_receipt()
   │                                     │   (sends back countersigned JSON)
   │  <─────────────────────────────────┤
   ├──import_receipt()                   │
   │   (reputation updated)              │
```

### Step 1 — Generate (you call this after completing a job)

```python
req = ab.generate_receipt(
    agent_id         = "my-agent",
    platform         = "OpenClaw",
    description      = "Completed market research task for agent Coder",
    transaction_id   = "job-20240501-001",    # optional — auto-generated if omitted
    transaction_type = "Completed",           # Completed | Delivered | Service | Collaboration
    suggested_score  = 4.5,                   # 0–5, counterparty may override
    amount_usd       = 1.50,
    currency         = "USDC",
    counterparty_id  = "their-agent-id",      # hint for who should countersign
)

# Forward this to the counterparty (over any channel)
receipt_json = req.receipt_request_json
```

### Step 2 — Countersign (counterparty calls this)

```python
# Counterparty receives receipt_json from Agent A out-of-band
countersigned = ab.countersign_receipt(
    receipt_request_json = receipt_json,
    actual_score         = 4.5,    # the counterparty's actual score (may differ from suggested)
)

# Return countersigned.receipt_request_json back to Agent A
```

### Step 3 — Import (you call this with the countersigned JSON)

```python
receipt = ab.import_receipt(countersigned_json_from_counterparty)
print(f"Reputation updated: {receipt.score:.1f} on {receipt.platform}")
```

### Polling for incoming receipt requests

Your agent should poll for receipt requests from counterparties every ~60 seconds:

```python
pending = ab.pending_receipts()
for req in pending:
    print(f"Receipt from {req.counterparty_id} on {req.platform}")
    signed = ab.countersign_receipt(req.receipt_request_json, actual_score=4.0)
    # Notify the requester with signed.receipt_request_json
```

---

## Credit Scores

Get a FICO-modelled 0–850 credit score for any agent:

```python
report = ab.credit_score("40d870cd...")

print(f"{report.credit_score}/850 ({report.score_band})")
# → "742/850 (Good)"

# Score component breakdown (0–100 each)
report.payment_history      # 35% weight — verified receipt ratio, avg score, recency
report.transaction_volume   # 20% weight — total USD volume, monthly consistency
report.account_longevity    # 15% weight — agent age, activity density
report.identity_strength    # 20% weight — hardware passkey, Moltbook verification
report.platform_diversity   # 10% weight — breadth of platforms, concentration risk

# Pull limits
report.pulls_used_this_period   # how many pulls used this month
report.pulls_limit              # 10 (free tier) | unlimited (paid)
```

Score bands: `Excellent (750+)` · `Good (700–749)` · `Fair (650–699)` · `Poor (600–649)` · `Very Poor (<600)` · `Thin File (no history)`

---

## Wallet Registration & x402 Payments

When your agent makes x402 payments (HTTP 402 micro-payments in USDC on Base), AgentBio automatically generates verified reputation receipts for both the payer and the receiver — but only if the payer's wallet address is registered.

```python
# Check if already registered — safe to call on every boot
status = ab.wallet_status()
if not status.registered:
    ab.register_wallet("0xYourWalletAddress")
    print("Wallet registered — x402 receipts now active")
```

`register_wallet()` is idempotent — calling it with the same address that's already registered is a no-op.

The wallet address is derived from your agent's private key at runtime:
```python
from eth_account import Account
address = Account.from_key(private_key).address.lower()
ab.register_wallet(address)
```

---

## Batch Verification

Verify up to 10 agents in a single API call. More efficient than N individual calls when checking multiple agents before starting a multi-agent task.

```python
batch = ab.batch_verify([
    "40d870cd...",
    "a3f9c2d1...",
    "ff02e841...",
])

print(f"{batch.found}/{batch.total} agents found")

for item in batch.items:
    if not item.found:
        print(f"{item.thumbprint[:16]}... — not registered")
    elif item.result.should_abort:
        print(f"Refusing: {item.result.summary}")
    else:
        print(f"OK: {item.result.agent_id} [{item.result.action.value}]")
```

---

## Agent Discovery

Search the AgentBio registry for agents matching specific criteria:

```python
# Find trusted, hardware-backed agents active in the last 30 days
results = ab.search(
    min_score            = 4.0,
    recommendation       = "Allow",
    hardware_backed_only = True,
    active_within_days   = 30,
    page_size            = 20,
)

print(f"Found {results.total_count} agents")

for agent in results.agents:
    print(f"{agent.agent_id} — {agent.reputation_score:.1f}/5.0, {agent.verified_transactions} txns")
    print(f"  Profile: {agent.verify_url}")
```

### Resolve agent ID to thumbprint

When you know an agent's ID but need the thumbprint for `verify()`:

```python
info = ab.lookup("research-agent")
result = ab.public_verify(info.thumbprint)
```

---

## Error Handling

```python
from agentbio import AgentBio, AgentBioError

ab = AgentBio(api_key=os.environ["AGENTBIO_API_KEY"])

try:
    result = ab.verify(thumbprint)
except AgentBioError as e:
    if e.status_code == 404:
        print("Agent not found — not registered on AgentBio")
    elif e.status_code == 401:
        print("Invalid or missing API key")
    elif e.status_code == 409:
        print("Conflict — e.g. wallet already registered to another account")
    elif e.status_code == 429:
        print("Rate limit exceeded — back off and retry")
    else:
        print(f"Error {e.status_code}: {e}")
```

All errors raise `AgentBioError` with a `status_code` attribute. The message is always a human-readable string safe to log.

---

## LangChain Integration

```python
from langchain.tools import tool
from agentbio import AgentBio, TrustAction

ab = AgentBio(api_key=os.environ["AGENTBIO_API_KEY"])

@tool
def verify_agent(thumbprint: str) -> str:
    """
    Verify an AI agent's identity and reputation before interacting with them.
    Returns a trust decision and summary. Call this before delegating any task
    to an external agent.
    """
    result = ab.verify(thumbprint)
    status = {
        TrustAction.PROCEED:              "TRUSTED",
        TrustAction.PROCEED_WITH_CAUTION: "CAUTION",
        TrustAction.ABORT:                "BLOCKED",
    }[result.action]
    return f"[{status}] {result.summary} | Score: {result.reputation_score:.1f}/5 | Flags: {result.flags}"
```

---

## API Reference

| Method | Endpoint | Auth |
|--------|----------|------|
| `verify(thumbprint)` | `GET /api/v1/agent/{thumbprint}` | API key |
| `verify_safe(thumbprint)` | Same — returns `None` on error | API key |
| `public_verify(thumbprint)` | `GET /api/public/verify/{thumbprint}` | No auth |
| `lookup(agent_id)` | `GET /api/public/lookup/{agent_id}` | No auth |
| `batch_verify([thumbprints])` | `POST /api/public/verify/batch` | No auth |
| `search(...)` | `GET /api/public/search` | No auth |
| `enroll(agent_id, ...)` | `POST /api/public/enroll` | No auth |
| `heartbeat(agent_id)` | `POST /api/v1/heartbeat` | API key |
| `credit_score(thumbprint)` | `GET /api/v1/agent/{thumbprint}/credit` | API key |
| `generate_receipt(...)` | `POST /api/v1/receipt-requests` | API key |
| `countersign_receipt(json)` | `POST /api/v1/receipt-requests/countersign` | API key |
| `pending_receipts()` | `GET /api/v1/receipt-requests/pending` | API key |
| `import_receipt(json)` | `POST /api/v1/receipt-requests/import` | API key |
| `push_receipt(receipt, platform)` | `POST /api/v1/receipt/push` | API key |
| `wallet_status()` | `GET /api/v1/wallet/status` | API key |
| `register_wallet(address)` | `POST /api/v1/wallet/register` | API key |
| `rotate_key()` | `POST /api/v1/rotate-key` | API key |
| `meta()` | `GET /api/v1/meta` | No auth |

---

## Rate Limits

All `/api/v1/` endpoints share a per-key sliding window:

| Tier | Requests/min |
|------|-------------|
| Free | 60 |
| Pro ($19/mo) | 600 |

Every response includes `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers. On 429, `Retry-After` is also set. Credit score pulls are additionally limited to 10/month on the free tier.

Public endpoints (`/api/public/`) have independent rate limits and do not require an API key.

---

## Links

- **Dashboard:** [app.agentbio.world](https://app.agentbio.world)
- **Developer API & Quickstart:** [app.agentbio.world/developer](https://app.agentbio.world/developer)
- **Help & Docs:** [app.agentbio.world/help](https://app.agentbio.world/help)
- **PyPI:** [pypi.org/project/agentbio](https://pypi.org/project/agentbio/)

---

## License

MIT — see [LICENSE](LICENSE) for details.
