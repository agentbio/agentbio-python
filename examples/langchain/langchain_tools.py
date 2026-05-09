"""
AgentBio.world — LangChain Integration
========================================
Drop-in AgentBio tools for LangChain agents.

Provides:
  verify_agent_tool      — verify a single agent by thumbprint
  lookup_agent_tool      — resolve an agent ID to a thumbprint
  batch_verify_tool      — verify up to 10 agents at once
  search_agents_tool     — discover trusted agents in the registry
  credit_score_tool      — get a FICO-modelled credit score

Install:
    pip install agentbio langchain langchain-openai

Run:
    export AGENTBIO_API_KEY=agentbio_yourkey
    export OPENAI_API_KEY=sk-...
    python examples/langchain/langchain_tools.py
"""

import os
from agentbio import AgentBio, AgentBioError, TrustAction

# ── Client setup ──────────────────────────────────────────────────────────────
_ab = AgentBio(api_key=os.environ.get("AGENTBIO_API_KEY"))


# ── Tool definitions ──────────────────────────────────────────────────────────
# Each function can be decorated with @tool from langchain.tools
# and added to any LangChain agent's tool list.

def verify_agent(thumbprint: str) -> str:
    """
    Verify an AI agent's identity and reputation before interacting with them.

    Call this before delegating any task to an external agent.
    Returns a machine-readable trust decision and human-readable summary.

    Args:
        thumbprint: The agent's hex thumbprint (32-64 chars).

    Returns:
        A formatted string with TRUSTED/CAUTION/BLOCKED decision and details.
    """
    try:
        result = _ab.public_verify(thumbprint.strip())
        status = {
            TrustAction.PROCEED:              "TRUSTED",
            TrustAction.PROCEED_WITH_CAUTION: "CAUTION",
            TrustAction.ABORT:                "BLOCKED",
        }[result.action]

        lines = [
            f"[{status}] {result.summary}",
            f"Agent ID    : {result.agent_id}",
            f"Score       : {result.reputation_score:.1f}/5.0",
            f"Txns        : {result.verified_transactions} verified",
            f"Risk        : {result.risk_level}",
            f"Hardware    : {'Yes' if result.hardware_backed else 'No'}",
            f"Profile     : {result.profile_url}",
        ]
        if result.flags:
            lines.append(f"Flags       : {', '.join(result.flags)}")

        return "\n".join(lines)

    except AgentBioError as e:
        if e.status_code == 404:
            return f"[UNKNOWN] Agent with thumbprint {thumbprint[:16]}... is not registered on AgentBio. Treat as untrusted."
        return f"[ERROR] AgentBio verification failed ({e.status_code}): {e}"


def lookup_agent(agent_id: str) -> str:
    """
    Look up an agent by its ID and return its thumbprint.

    Use this when you know an agent's name but need its thumbprint
    to call verify_agent.

    Args:
        agent_id: The agent's alphanumeric identifier.

    Returns:
        The agent's thumbprint and basic identity info.
    """
    try:
        info = _ab.lookup(agent_id.strip())
        return (
            f"Agent ID    : {info.agent_id}\n"
            f"Thumbprint  : {info.thumbprint}\n"
            f"Hardware    : {'Yes' if info.hardware_backed else 'No'}\n"
            f"Enrolled    : {info.enrolled_at.date()}\n"
            f"Last seen   : {info.last_seen_at.date() if info.last_seen_at else 'unknown'}\n"
            f"Verify URL  : {info.verify_url}"
        )
    except AgentBioError as e:
        if e.status_code == 404:
            return f"Agent '{agent_id}' not found in the AgentBio registry."
        return f"Lookup failed ({e.status_code}): {e}"


def batch_verify_agents(thumbprints_csv: str) -> str:
    """
    Verify multiple agents at once (up to 10) before starting a multi-agent task.

    Args:
        thumbprints_csv: Comma-separated list of agent thumbprints (max 10).

    Returns:
        Trust decision for each agent, plus an overall go/no-go recommendation.
    """
    thumbprints = [t.strip() for t in thumbprints_csv.split(",") if t.strip()]

    if not thumbprints:
        return "No thumbprints provided."
    if len(thumbprints) > 10:
        return "batch_verify supports a maximum of 10 thumbprints per call."

    try:
        batch = _ab.batch_verify(thumbprints)
        lines = [f"Verified {batch.found}/{batch.total} agents:\n"]
        blocked = []

        for item in batch.items:
            if not item.found:
                lines.append(f"  ✗ {item.thumbprint[:24]}... — not registered")
                blocked.append(item.thumbprint)
                continue

            r = item.result
            icon = {"proceed": "✅", "proceed_with_caution": "⚠️", "abort": "🚫"}[r.action.value]
            lines.append(f"  {icon} {r.agent_id} — score {r.reputation_score:.1f}/5, risk {r.risk_level}")
            if r.action == TrustAction.ABORT:
                blocked.append(r.agent_id)

        if blocked:
            lines.append(f"\n⛔ RECOMMENDATION: Do NOT proceed — blocked agents: {', '.join(blocked)}")
        else:
            lines.append("\n✅ RECOMMENDATION: Safe to proceed with all agents.")

        return "\n".join(lines)

    except AgentBioError as e:
        return f"Batch verify failed ({e.status_code}): {e}"


def search_trusted_agents(min_score: float = 4.0, active_within_days: int = 30) -> str:
    """
    Search the AgentBio registry for trusted, recently active agents.

    Useful for discovering agents to delegate work to.

    Args:
        min_score:          Minimum reputation score (0-5, default 4.0).
        active_within_days: Only agents active within this many days (default 30).

    Returns:
        A list of trusted agents with their scores and profiles.
    """
    try:
        results = _ab.search(
            min_score          = min_score,
            recommendation     = "Allow",
            active_within_days = active_within_days,
            page_size          = 10,
        )

        if not results.agents:
            return f"No agents found with score ≥ {min_score} active within {active_within_days} days."

        lines = [f"Found {results.total_count} trusted agents (showing {len(results.agents)}):\n"]
        for agent in results.agents:
            lines.append(
                f"  {agent.agent_id:<30} score={agent.reputation_score:.1f}  "
                f"txns={agent.verified_transactions}  hw={'✓' if agent.hardware_backed else '✗'}"
            )
            lines.append(f"    → {agent.verify_url}")

        return "\n".join(lines)

    except AgentBioError as e:
        return f"Search failed ({e.status_code}): {e}"


def get_credit_score(thumbprint: str) -> str:
    """
    Get a FICO-modelled credit score (0-850) for an agent.

    Useful for financial risk assessment before high-value interactions.
    Requires an API key. Free tier allows 10 pulls/month.

    Args:
        thumbprint: The agent's hex thumbprint.

    Returns:
        Credit score, band, and component breakdown.
    """
    try:
        report = _ab.credit_score(thumbprint.strip())
        return (
            f"Credit Score  : {report.credit_score}/850 ({report.score_band})\n"
            f"Agent         : {report.agent_id}\n"
            f"Payment Hist  : {report.payment_history}/100  (35% weight)\n"
            f"Txn Volume    : {report.transaction_volume}/100  (20% weight)\n"
            f"Longevity     : {report.account_longevity}/100  (15% weight)\n"
            f"Identity      : {report.identity_strength}/100  (20% weight)\n"
            f"Diversity     : {report.platform_diversity}/100  (10% weight)\n"
            f"Pulls used    : {report.pulls_used_this_period}/{report.pulls_limit} this period"
        )
    except AgentBioError as e:
        if e.status_code == 429:
            return "Credit score pull limit reached for this period. Upgrade at app.agentbio.world/account."
        return f"Credit score failed ({e.status_code}): {e}"


# ── LangChain tool wrappers ───────────────────────────────────────────────────
# Requires: pip install langchain

def get_langchain_tools():
    """
    Returns a list of AgentBio tools ready to add to a LangChain agent.

    Usage:
        from examples.langchain.langchain_tools import get_langchain_tools
        from langchain.agents import initialize_agent

        tools = get_langchain_tools()
        agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
    """
    try:
        from langchain.tools import Tool

        return [
            Tool(
                name        = "verify_agent",
                func        = verify_agent,
                description = (
                    "Verify an AI agent's identity and reputation before interacting with them. "
                    "Input: agent thumbprint (hex string). "
                    "Returns: TRUSTED / CAUTION / BLOCKED decision with reputation details. "
                    "Always call this before delegating a task to an external agent."
                ),
            ),
            Tool(
                name        = "lookup_agent",
                func        = lookup_agent,
                description = (
                    "Look up an agent by its agent ID and return its thumbprint. "
                    "Use this when you know the agent's name but need its thumbprint "
                    "to call verify_agent. Input: agent ID string."
                ),
            ),
            Tool(
                name        = "batch_verify_agents",
                func        = batch_verify_agents,
                description = (
                    "Verify multiple agents at once before starting a multi-agent task. "
                    "Input: comma-separated list of thumbprints (max 10). "
                    "Returns a trust decision for each and an overall go/no-go recommendation."
                ),
            ),
            Tool(
                name        = "search_trusted_agents",
                func        = lambda q: search_trusted_agents(),
                description = (
                    "Search the AgentBio registry for trusted, recently active agents. "
                    "Use this to discover agents to delegate work to. "
                    "Input: ignored — always searches for top trusted agents."
                ),
            ),
            Tool(
                name        = "get_credit_score",
                func        = get_credit_score,
                description = (
                    "Get a FICO-modelled credit score (0-850) for an agent. "
                    "Use for financial risk assessment before high-value interactions. "
                    "Input: agent thumbprint."
                ),
            ),
        ]
    except ImportError:
        raise ImportError("Install LangChain to use get_langchain_tools(): pip install langchain")


# ── Demo ──────────────────────────────────────────────────────────────────────
def demo_without_llm():
    """
    Demonstrates each tool function without requiring an LLM or API key.
    """
    print("=" * 60)
    print("  AgentBio LangChain Tools — Demo")
    print("=" * 60)

    print("\n--- verify_agent (invalid thumbprint) ---")
    print(verify_agent("0" * 64))

    print("\n--- lookup_agent (unknown agent) ---")
    print(lookup_agent("nonexistent-agent-xyz"))

    print("\n--- search_trusted_agents ---")
    print(search_trusted_agents(min_score=1.0, active_within_days=365))

    print("\n--- batch_verify_agents (empty list) ---")
    print(batch_verify_agents(""))

    print("\n\nTo use with LangChain:")
    print("""
    from examples.langchain.langchain_tools import get_langchain_tools
    from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI

    llm   = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = get_langchain_tools()
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )
    agent.run(
        "Look up the agent 'research-agent', verify its trustworthiness, "
        "and tell me if it's safe to delegate a task to it."
    )
    """)


if __name__ == "__main__":
    demo_without_llm()
