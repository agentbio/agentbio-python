<div align="center">

<!-- Animated AgentBio Robot — renders live on GitHub -->
<svg width="180" height="220" viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;margin-bottom:8px">
  <defs>
    <linearGradient id="r-body" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#1a2744"/><stop offset="45%" stop-color="#0f1c38"/><stop offset="100%" stop-color="#060d1f"/></linearGradient>
    <linearGradient id="r-head" x1="20%" y1="0%" x2="80%" y2="100%"><stop offset="0%" stop-color="#243563"/><stop offset="50%" stop-color="#131f45"/><stop offset="100%" stop-color="#080f28"/></linearGradient>
    <linearGradient id="r-head-top" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#4f7fff" stop-opacity="0.35"/><stop offset="100%" stop-color="#4f7fff" stop-opacity="0"/></linearGradient>
    <linearGradient id="r-visor" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#050c1e"/><stop offset="100%" stop-color="#020710"/></linearGradient>
    <linearGradient id="r-visor-s" x1="10%" y1="0%" x2="90%" y2="100%"><stop offset="0%" stop-color="#4f7fff" stop-opacity="0.22"/><stop offset="100%" stop-color="#4f7fff" stop-opacity="0"/></linearGradient>
    <radialGradient id="r-eye" cx="50%" cy="40%" r="60%"><stop offset="0%" stop-color="#020916"/><stop offset="100%" stop-color="#000408"/></radialGradient>
    <radialGradient id="r-pupil" cx="38%" cy="35%" r="65%"><stop offset="0%" stop-color="#60a5fa"/><stop offset="40%" stop-color="#2563eb"/><stop offset="100%" stop-color="#1140a8"/></radialGradient>
    <linearGradient id="r-shoulder" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#3b5fc0"/><stop offset="100%" stop-color="#1a3080"/></linearGradient>
    <linearGradient id="r-neck" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#1e2f5a"/><stop offset="100%" stop-color="#0a1228"/></linearGradient>
    <linearGradient id="r-ant" x1="0%" y1="100%" x2="0%" y2="0%"><stop offset="0%" stop-color="#1d4ed8"/><stop offset="100%" stop-color="#60a5fa"/></linearGradient>
    <linearGradient id="r-mouth" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#10b981"/><stop offset="50%" stop-color="#34d399"/><stop offset="100%" stop-color="#10b981"/></linearGradient>
    <filter id="r-eglow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <filter id="r-shadow"><feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#000918" flood-opacity="0.7"/></filter>
  </defs>
  <style>
    @keyframes float{0%,100%{transform:translateY(0px)}50%{transform:translateY(-10px)}}
    .r-float{animation:float 4s ease-in-out infinite}
  </style>
  <g class="r-float">
    <ellipse cx="100" cy="234" rx="52" ry="8" fill="#000918" opacity="0.55"/>
    <rect x="58" y="193" width="30" height="28" rx="9" fill="url(#r-body)"/><rect x="58" y="193" width="30" height="6" rx="3" fill="#2563eb" opacity="0.25"/><rect x="58" y="193" width="30" height="28" rx="9" stroke="#1d4ed8" stroke-width="0.8" fill="none" opacity="0.5"/>
    <rect x="112" y="193" width="30" height="28" rx="9" fill="url(#r-body)"/><rect x="112" y="193" width="30" height="6" rx="3" fill="#2563eb" opacity="0.25"/><rect x="112" y="193" width="30" height="28" rx="9" stroke="#1d4ed8" stroke-width="0.8" fill="none" opacity="0.5"/>
    <rect x="38" y="130" width="124" height="70" rx="18" fill="url(#r-body)" filter="url(#r-shadow)"/>
    <rect x="38" y="130" width="124" height="70" rx="18" stroke="#2563eb" stroke-width="1" fill="none" opacity="0.45"/>
    <rect x="40" y="131" width="120" height="4" rx="2" fill="#3b82f6" opacity="0.18"/>
    <rect x="54" y="142" width="92" height="46" rx="10" fill="#0d1830" stroke="#1d4ed8" stroke-width="0.8"/>
    <circle cx="72" cy="158" r="4" fill="#2563eb"><animate attributeName="opacity" values="1;0.4;1" dur="2.2s" repeatCount="indefinite"/></circle>
    <circle cx="89" cy="158" r="4" fill="#10b981"><animate attributeName="opacity" values="0.9;0.3;0.9" dur="1.6s" repeatCount="indefinite"/></circle>
    <circle cx="89" cy="158" r="2" fill="#34d399" opacity="0.7"/>
    <circle cx="106" cy="158" r="4" fill="#7c3aed"><animate attributeName="opacity" values="0.85;0.35;0.85" dur="2.8s" repeatCount="indefinite"/></circle>
    <circle cx="106" cy="158" r="2" fill="#a78bfa" opacity="0.7"/>
    <circle cx="123" cy="158" r="4" fill="#d97706"><animate attributeName="opacity" values="0.7;0.2;0.7" dur="1.9s" repeatCount="indefinite"/></circle>
    <rect x="58" y="172" width="84" height="10" rx="4" fill="#050c1e" stroke="#1d4ed8" stroke-width="0.6"/>
    <rect x="60" y="174" width="0" height="6" rx="2" fill="url(#r-mouth)"><animate attributeName="width" values="10;58;22;72;38;80;16;64;28" dur="3s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1;0.4 0 0.6 1"/></rect>
    <rect x="32" y="126" width="28" height="16" rx="8" fill="url(#r-shoulder)"/><rect x="32" y="127" width="24" height="4" rx="2" fill="#60a5fa" opacity="0.2"/>
    <rect x="140" y="126" width="28" height="16" rx="8" fill="url(#r-shoulder)"/><rect x="142" y="127" width="24" height="4" rx="2" fill="#60a5fa" opacity="0.2"/>
    <rect x="14" y="134" width="22" height="52" rx="11" fill="url(#r-neck)" stroke="#1d4ed8" stroke-width="0.8"/><rect x="14" y="155" width="22" height="6" rx="3" fill="#1d4ed8" opacity="0.35"/>
    <rect x="164" y="134" width="22" height="52" rx="11" fill="url(#r-neck)" stroke="#1d4ed8" stroke-width="0.8"/><rect x="164" y="155" width="22" height="6" rx="3" fill="#1d4ed8" opacity="0.35"/>
    <rect x="82" y="116" width="36" height="18" rx="7" fill="url(#r-neck)" stroke="#1d4ed8" stroke-width="0.8"/>
    <rect x="28" y="45" width="144" height="88" rx="20" fill="url(#r-head)" filter="url(#r-shadow)"/>
    <rect x="28" y="45" width="144" height="34" rx="20" fill="url(#r-head-top)"/>
    <rect x="28" y="45" width="144" height="88" rx="20" stroke="#2563eb" stroke-width="1.2" fill="none" opacity="0.5"/>
    <rect x="32" y="46" width="136" height="5" rx="2.5" fill="#60a5fa" opacity="0.2"/>
    <rect x="14" y="72" width="18" height="36" rx="8" fill="url(#r-neck)" stroke="#1d4ed8" stroke-width="0.8"/>
    <rect x="16" y="76" width="6" height="6" rx="2" fill="#2563eb" opacity="0.5"/>
    <rect x="168" y="72" width="18" height="36" rx="8" fill="url(#r-neck)" stroke="#1d4ed8" stroke-width="0.8"/>
    <rect x="178" y="76" width="6" height="6" rx="2" fill="#2563eb" opacity="0.5"/>
    <rect x="36" y="60" width="128" height="56" rx="14" fill="url(#r-visor)"/>
    <rect x="36" y="60" width="128" height="56" rx="14" stroke="#1d4ed8" stroke-width="1" fill="none" opacity="0.7"/>
    <rect x="36" y="60" width="128" height="56" rx="14" fill="url(#r-visor-s)"/>
    <rect x="40" y="62" width="120" height="3" rx="1.5" fill="#60a5fa" opacity="0.18"/>
    <circle cx="72" cy="84" r="20" fill="url(#r-eye)"/>
    <circle cx="72" cy="84" r="20" fill="none" stroke="#2563eb" stroke-width="2" opacity="0.55" filter="url(#r-eglow)"/>
    <circle cx="72" cy="84" r="20" fill="none" stroke="#1d4ed8" stroke-width="1"/>
    <circle cx="72" cy="84" r="10" fill="url(#r-pupil)"/><circle cx="72" cy="84" r="4" fill="#020916"/>
    <circle cx="76" cy="79" r="3" fill="white" opacity="0.85"/>
    <circle cx="128" cy="84" r="20" fill="url(#r-eye)"/>
    <circle cx="128" cy="84" r="20" fill="none" stroke="#2563eb" stroke-width="2" opacity="0.55" filter="url(#r-eglow)"/>
    <circle cx="128" cy="84" r="20" fill="none" stroke="#1d4ed8" stroke-width="1"/>
    <circle cx="128" cy="84" r="10" fill="url(#r-pupil)"/><circle cx="128" cy="84" r="4" fill="#020916"/>
    <circle cx="132" cy="79" r="3" fill="white" opacity="0.85"/>
    <rect x="52" y="110" width="96" height="18" rx="8" fill="#020912" stroke="#1d4ed8" stroke-width="0.8"/>
    <rect x="56" y="113" width="12" height="10" rx="3" fill="#10b981"><animate attributeName="opacity" values="1;0.4;1" dur="1.4s" repeatCount="indefinite"/></rect>
    <rect x="82" y="113" width="14" height="10" rx="3" fill="#2563eb"><animate attributeName="opacity" values="0.9;0.3;0.9" dur="2.1s" repeatCount="indefinite"/></rect>
    <rect x="112" y="113" width="16" height="10" rx="3" fill="#10b981"><animate attributeName="opacity" values="0.8;0.25;0.8" dur="2.4s" repeatCount="indefinite"/></rect>
    <rect x="97" y="12" width="6" height="36" rx="3" fill="url(#r-ant)"/>
    <circle cx="100" cy="10" r="12" fill="#2563eb" opacity="0.12" filter="url(#r-eglow)"/>
    <circle cx="100" cy="10" r="6" fill="#60a5fa"><animate attributeName="r" values="6;7.5;6" dur="1.6s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/><animate attributeName="fill" values="#60a5fa;#93c5fd;#60a5fa" dur="1.6s" repeatCount="indefinite"/></circle>
    <circle cx="102" cy="8" r="2" fill="white" opacity="0.7"/>
  </g>
</svg>

<br/>

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
| `set_auto_countersign_policy(...)` | Configure autonomous reputation | ✓ |
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
