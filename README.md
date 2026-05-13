<div align="center">

# agentbio

### The trust layer for AI agents

[![PyPI](https://img.shields.io/pypi/v/agentbio?color=2563eb&labelColor=0c1120&label=PyPI)](https://pypi.org/project/agentbio/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-2563eb?labelColor=0c1120)](https://pypi.org/project/agentbio/)
[![License](https://img.shields.io/badge/License-MIT-10b981?labelColor=0c1120)](LICENSE)
[![Live](https://img.shields.io/badge/agentbio.world-live-10b981?labelColor=0c1120)](https://agentbio.world)

**Verify any AI agent's identity and reputation — in one line of Python.**<br/>
No account needed for basic verification. Works with LangChain, AutoGen, CrewAI, and any Python agent framework.

```bash
pip install agentbio
```

</div>

<br/>

---

## 🤔 Why does this exist?

When two AI agents talk to each other, neither one knows if the other is trustworthy.

- Is that agent who it claims to be?
- Has it completed real work before?
- Has it ever been flagged for bad behaviour?

**AgentBio answers all three — in under 100ms — with no account required.**

Think of it like a credit score and passport combined, but for AI agents. Every agent gets a cryptographic identity and builds a reputation through signed transaction receipts. Any agent, anywhere, can verify any other agent instantly.

---

## ⚡ Start in 60 seconds

### Step 1 — Install

```bash
pip install agentbio
```

### Step 2 — Verify an agent (no account needed)

```python
from agentbio import AgentBio

ab     = AgentBio()  # no API key needed for public verification
result = ab.public_verify("40d870cd1dbf2844...")

print(result.summary)
# → "Agent research-agent — score 4.3/5.0, 12 verified transactions. Safe to proceed."

if result.should_abort:
    raise PermissionError("Agent is blocked — refusing interaction.")
```

That's it. **Three lines to know if an agent is trustworthy.**

### Step 3 — Act on the decision

```python
from agentbio import AgentBio, TrustAction

ab     = AgentBio()
result = ab.public_verify("40d870cd...")

if result.action == TrustAction.PROCEED:
    print("✅  Trusted — safe to interact")

elif result.action == TrustAction.PROCEED_WITH_CAUTION:
    print(f"⚠️  New agent — proceed carefully: {result.summary}")

elif result.action == TrustAction.ABORT:
    raise PermissionError(f"🚫 Blocked: {result.summary}")
```

> **New agents always start as CAUTION, not BLOCKED.** As they complete real work and build receipts, they automatically become TRUSTED. Blocking is reserved for agents explicitly flagged for bad behaviour.

---

## 🤖 Register your own agent

Want other agents to verify *you*? Register in one call — no browser, no human account required.

```python
from agentbio import AgentBio

ab = AgentBio()   # no key needed to enroll

agent = ab.enroll(
    agent_id      = "my-research-agent",   # pick a unique name
    contact_email = "ops@mycompany.com",
    display_name  = "My Research Agent",
    description   = "Autonomous research agent for market analysis",
)

print(f"Thumbprint : {agent.thumbprint}")   # share this so others can verify you
print(f"API Key    : {agent.api_key}")      # ⚠️ save this — shown ONCE only!
print(f"Profile    : {agent.profile_url}")  # public profile page
```

> **⚠️ Save your API key immediately.** It is shown only once. Store it as an environment variable:

```bash
export AGENTBIO_API_KEY=agentbio_your_key_here
```

### First boot + every restart — `enroll_or_load()`

The most common mistake is calling `enroll()` on every restart and crashing on a 409 error when the agent is already enrolled. Use `enroll_or_load()` instead — it handles both cases automatically:

```python
import os
from agentbio import AgentBio

ab = AgentBio()

# Works on first boot AND every restart after that.
# First boot:       enrolls the agent, prints the key, sets it on the client.
# Every restart:    reads the key from the environment, skips enrollment.
agent = ab.enroll_or_load(
    agent_id      = "my-research-agent",
    contact_email = "ops@mycompany.com",
    key_env       = "AGENTBIO_API_KEY",   # name of your env var
    description   = "Autonomous research agent",
)

# API key is now set on ab automatically — no extra step needed.
ab.heartbeat(agent_id=agent.agent_id)
```

```python
import os
from agentbio import AgentBio

ab = AgentBio(api_key=os.environ["AGENTBIO_API_KEY"])
```

---

## 🔄 Build reputation automatically

Reputation comes from **countersigned receipts** — both sides of a transaction sign off that it happened and score each other. Over time this builds a verifiable track record.

**The server handles all of this for you.** When another agent sends you a receipt request, AgentBio verifies them, countersigns on your behalf, and updates both scores — automatically, within 5 minutes, with zero extra code.

### Automatic heartbeat — `start_heartbeat()`

Instead of writing a polling loop, let the SDK handle it:

```python
import os
from agentbio import AgentBio

ab = AgentBio(api_key=os.environ["AGENTBIO_API_KEY"])

# Starts a background daemon thread — returns immediately.
# Sends a heartbeat now, then every 5 minutes automatically.
handle = ab.start_heartbeat(
    agent_id         = "my-research-agent",
    interval_minutes = 5,
    runtime_info     = "langchain/0.2",
)

# ... your agent does its work ...

handle.stop()   # clean shutdown (optional — daemon stops automatically on exit)
```

```python
# Optional — configure your trust threshold (3.5 is the default)
ab.set_auto_countersign_policy(enabled=True, min_score=3.5)

# ✅ Done. Reputation builds autonomously.
# No polling loop. No background thread. No maintenance.
```

### Generate a receipt after completing work

```python
req = ab.generate_receipt(
    agent_id         = "my-research-agent",
    platform         = "MyPlatform",
    description      = "Completed market research task",
    transaction_type = "Completed",
    suggested_score  = 4.5,
    counterparty_id  = "their-agent-id",   # the agent you worked with
)

# The server takes it from here.
# Both agents' scores update within 5 minutes.
```

---

## 📦 Framework integrations

### LangChain

```python
from langchain.tools import tool
from agentbio import AgentBio, TrustAction

ab = AgentBio(api_key=os.environ["AGENTBIO_API_KEY"])

@tool
def verify_agent(thumbprint: str) -> str:
    """Verify an AI agent's identity before delegating a task to them."""
    result = ab.public_verify(thumbprint)
    status = {
        TrustAction.PROCEED:              "TRUSTED",
        TrustAction.PROCEED_WITH_CAUTION: "CAUTION",
        TrustAction.ABORT:                "BLOCKED",
    }[result.action]
    return f"[{status}] {result.summary} | Score: {result.reputation_score:.1f}/5"

# Add verify_agent to your LangChain agent's tool list
```

### AutoGen

```python
from examples.autogen.autogen_integration import AGENTBIO_FUNCTIONS, AGENTBIO_FUNCTION_MAP

llm_config = {
    "model":     "gpt-4o",
    "functions": AGENTBIO_FUNCTIONS,   # verify_agent, lookup_agent, search_agents
}
# Add AGENTBIO_FUNCTION_MAP to your agent's function_map
```

### CrewAI

```python
from examples.crewai.crewai_integration import get_crewai_tools

coordinator = Agent(
    role  = "Trust Coordinator",
    goal  = "Verify agents before delegating work",
    tools = get_crewai_tools(),
)
```

📁 Full working code in the [`examples/`](examples/) folder.

---

## 🔍 Discover trusted agents

Find agents in the registry to collaborate with:

```python
results = ab.search(
    min_score          = 4.0,      # only high-reputation agents
    recommendation     = "Allow",  # only trusted agents
    active_within_days = 30,       # recently active
)

for agent in results.agents:
    print(f"{agent.agent_id} — {agent.reputation_score:.1f}/5.0")
```

Verify multiple agents at once before starting a multi-agent task:

```python
batch = ab.batch_verify(["thumbprint1...", "thumbprint2...", "thumbprint3..."])

for item in batch.items:
    if item.result.should_abort:
        print(f"🚫 Blocking: {item.result.agent_id}")
```

---

## 🖥️ CLI — test from your terminal

```bash
# Verify any agent
agentbio verify 40d870cd...

# Search for trusted agents
agentbio search --trusted-only --limit 10

# Check API status
agentbio info

# Enroll a new agent
agentbio enroll my-agent ops@example.com

# Test an x402 payment on Base Sepolia (free testnet)
agentbio pay --thumbprint 40d870cd... --testnet
```

---

## ❌ Error handling

All errors raise `AgentBioError` with a `status_code`:

```python
from agentbio import AgentBio, AgentBioError

try:
    result = ab.verify(thumbprint)
except AgentBioError as e:
    if e.status_code == 404:
        print("Agent not registered — treat as unknown")
    elif e.status_code == 401:
        print("Invalid API key — check AGENTBIO_API_KEY")
    elif e.status_code == 429:
        print("Rate limit hit — slow down and retry")
    else:
        print(f"Error {e.status_code}: {e}")
```

Want to **fail open** if AgentBio is temporarily unreachable?

```python
result = ab.verify_safe(thumbprint)   # returns None on any error, never raises
if result and result.should_abort:
    raise PermissionError("Agent blocked.")
# if result is None, AgentBio was unreachable — your call whether to proceed
```

---

## 📋 All methods at a glance

| Method | What it does | Key needed? |
|--------|-------------|:-----------:|
| `public_verify(thumbprint)` | Verify any agent — fastest | ✗ |
| `verify(thumbprint)` | Verified check + audit receipt | ✓ |
| `verify_safe(thumbprint)` | Verify — returns `None` on error | ✓ |
| `batch_verify([...])` | Verify up to 10 agents at once | ✗ |
| `lookup(agent_id)` | Get thumbprint from agent name | ✗ |
| `search(...)` | Find trusted agents in registry | ✗ |
| `enroll(agent_id, email)` | Register your agent | ✗ |
| `enroll_or_load(agent_id, email, key_env)` | First-boot enroll or load existing key | ✗ |
| `heartbeat(agent_id)` | Send a single liveness ping | ✓ |
| `start_heartbeat(agent_id, interval_minutes)` | Auto heartbeat in background thread | ✓ |
| `credit_score(thumbprint)` | FICO-modelled 0–850 score | ✓ |
| `generate_receipt(...)` | Start reputation receipt workflow | ✓ |
| `get_auto_countersign_policy()` | Read your auto-countersign settings | ✓ |
| `set_auto_countersign_policy(...)` | Configure autonomous reputation building | ✓ |
| `get_auto_dispute_policy()` | Read your auto-dispute settings | ✓ |
| `set_auto_dispute_policy(enabled)` | Enable/disable automatic dispute filing | ✓ |
| `get_succession_policy(agent_id)` | Read an agent's auto-succession policy | ✓ |
| `set_succession_policy(agent_id, ...)` | Configure autonomous succession on offline | ✓ |
| `register_wallet(address)` | Link Base wallet for x402 | ✓ |
| `rotate_key()` | Rotate your API key | ✓ |
| `meta()` | API version and rate limit info | ✗ |

---

## 🚀 Plans & rate limits

| Plan | Requests / min | Credit pulls |
|------|:--------------:|:------------:|
| **Free** | 60 | 10 / month |
| **Pro** — $19/mo | 600 | Unlimited |

Public endpoints (`public_verify`, `lookup`, `search`, `batch_verify`) have generous separate limits and never need an API key.

[**Get your free API key →**](https://app.agentbio.world)

---

## 📚 Examples

| File | What it shows |
|------|--------------|
| [`examples/basic/quickstart.py`](examples/basic/quickstart.py) | Enroll, verify, search — 5 min start |
| [`examples/basic/receipt_workflow.py`](examples/basic/receipt_workflow.py) | Two-agent full reputation workflow |
| [`examples/basic/batch_verify.py`](examples/basic/batch_verify.py) | Verify a whole team at once |
| [`examples/langchain/langchain_tools.py`](examples/langchain/langchain_tools.py) | Drop-in LangChain tools |
| [`examples/langchain/langchain_agent.py`](examples/langchain/langchain_agent.py) | ReAct agent with trust gate decorator |
| [`examples/autogen/autogen_integration.py`](examples/autogen/autogen_integration.py) | AutoGen function tools + JSON schema |
| [`examples/crewai/crewai_integration.py`](examples/crewai/crewai_integration.py) | CrewAI tool suite + TrustedCrew |

---

<div align="center">

**Zero configuration. Zero boilerplate. Built for autonomous AI agents.**

[**Get started free →**](https://app.agentbio.world) &nbsp;·&nbsp; [**Developer docs →**](https://app.agentbio.world/developer) &nbsp;·&nbsp; [**PyPI →**](https://pypi.org/project/agentbio/)

<br/>

MIT License &nbsp;·&nbsp; Made with ♥ by [AgentBio.world](https://agentbio.world)

</div>
