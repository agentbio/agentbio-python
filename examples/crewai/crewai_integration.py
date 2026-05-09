"""
AgentBio.world — CrewAI Integration
=====================================
Integrates AgentBio trust verification into CrewAI multi-agent pipelines.

Two patterns:
  1. AgentBio CrewAI Tools — add to any CrewAI agent's tool list.
  2. TrustedCrew — a CrewAI Crew subclass that verifies all agents
     before the crew kicks off.

Install:
    pip install agentbio crewai crewai-tools

Run:
    export AGENTBIO_API_KEY=agentbio_yourkey
    export OPENAI_API_KEY=sk-...
    python examples/crewai/crewai_integration.py
"""

import os
from agentbio import AgentBio, AgentBioError, TrustAction

ab = AgentBio(api_key=os.environ.get("AGENTBIO_API_KEY"))


# ── Pattern 1: CrewAI Tools ───────────────────────────────────────────────────
# Each function can be wrapped with @tool from crewai_tools.

def verify_agent_tool(thumbprint: str) -> str:
    """
    Verify an AI agent's identity and reputation before working with them.

    Use this tool before delegating any task to an external agent.
    Returns a TRUSTED / CAUTION / BLOCKED decision.

    Args:
        thumbprint: The agent's hex thumbprint (32-64 characters).
    """
    try:
        result = ab.public_verify(thumbprint.strip())

        status = {
            TrustAction.PROCEED:              "✅ TRUSTED",
            TrustAction.PROCEED_WITH_CAUTION: "⚠️  CAUTION",
            TrustAction.ABORT:                "🚫 BLOCKED",
        }[result.action]

        output = [
            f"[{status}] {result.summary}",
            f"Agent        : {result.agent_id}",
            f"Score        : {result.reputation_score:.1f}/5.0",
            f"Transactions : {result.verified_transactions} verified",
            f"Risk         : {result.risk_level}",
            f"Hardware key : {'Yes' if result.hardware_backed else 'No'}",
        ]
        if result.flags:
            output.append(f"Flags        : {', '.join(result.flags)}")

        output.append(f"\nRECOMMENDATION: {'Do NOT interact — agent is blocked.' if result.should_abort else 'Safe to proceed.'}")
        return "\n".join(output)

    except AgentBioError as e:
        if e.status_code == 404:
            return f"🚫 Agent not registered on AgentBio. Thumbprint: {thumbprint[:24]}... Treat as untrusted."
        return f"⚠️  Verification error ({e.status_code}): {e}"


def lookup_agent_tool(agent_id: str) -> str:
    """
    Look up an agent by its name and return its thumbprint.

    Use this when you know an agent's ID but need its thumbprint
    to call verify_agent_tool.

    Args:
        agent_id: The agent's alphanumeric identifier.
    """
    try:
        info = ab.lookup(agent_id.strip())
        return (
            f"Found agent '{info.agent_id}':\n"
            f"  Thumbprint  : {info.thumbprint}\n"
            f"  Hardware    : {'Yes' if info.hardware_backed else 'No'}\n"
            f"  Enrolled    : {info.enrolled_at.date()}\n"
            f"  Last active : {info.last_seen_at.date() if info.last_seen_at else 'unknown'}\n"
            f"  Profile     : {info.profile_url}"
        )
    except AgentBioError as e:
        if e.status_code == 404:
            return f"Agent '{agent_id}' is not registered on AgentBio."
        return f"Lookup error ({e.status_code}): {e}"


def search_trusted_agents_tool(query: str = "") -> str:
    """
    Search the AgentBio registry for trusted, recently active agents.

    Use this to find agents you can safely collaborate with.

    Args:
        query: Optional search query to filter by agent name or description.
    """
    try:
        kwargs = dict(min_score=3.5, recommendation="Allow", active_within_days=60, page_size=8)
        if query.strip():
            kwargs["query"] = query.strip()

        results = ab.search(**kwargs)

        if not results.agents:
            return "No trusted agents found matching your criteria."

        lines = [f"Found {results.total_count} trusted agents:\n"]
        for a in results.agents:
            hw = "🔒" if a.hardware_backed else "  "
            lines.append(
                f"  {hw} {a.agent_id:<30} score={a.reputation_score:.1f}  "
                f"txns={a.verified_transactions}"
            )
            if a.description:
                lines.append(f"      {a.description[:80]}")

        return "\n".join(lines)

    except AgentBioError as e:
        return f"Search error ({e.status_code}): {e}"


def credit_score_tool(thumbprint: str) -> str:
    """
    Get a FICO-modelled credit score (0-850) for an agent.

    Use before high-value financial interactions to assess risk.

    Args:
        thumbprint: The agent's hex thumbprint.
    """
    try:
        r = ab.credit_score(thumbprint.strip())
        band_emoji = {
            "Excellent": "🟢",
            "Good":      "🟢",
            "Fair":      "🟡",
            "Poor":      "🔴",
            "Very Poor": "🔴",
            "Thin File": "⚪",
        }.get(r.score_band, "⚪")

        return (
            f"{band_emoji} Credit Score: {r.credit_score}/850 ({r.score_band})\n"
            f"  Agent         : {r.agent_id}\n"
            f"  Payment Hist  : {r.payment_history}/100\n"
            f"  Txn Volume    : {r.transaction_volume}/100\n"
            f"  Longevity     : {r.account_longevity}/100\n"
            f"  Identity      : {r.identity_strength}/100\n"
            f"  Diversity     : {r.platform_diversity}/100"
        )
    except AgentBioError as e:
        if e.status_code == 429:
            return "Credit score pull limit reached. Upgrade at app.agentbio.world/account."
        return f"Credit score error ({e.status_code}): {e}"


def get_crewai_tools():
    """
    Returns AgentBio tools as CrewAI Tool instances.

    Usage:
        from examples.crewai.crewai_integration import get_crewai_tools
        from crewai import Agent

        tools = get_crewai_tools()
        agent = Agent(
            role  = "Research Coordinator",
            goal  = "Find and verify trusted agents for delegation",
            tools = tools,
            ...
        )
    """
    try:
        from crewai_tools import tool as crewai_tool

        @crewai_tool("Verify Agent Trust")
        def verify_agent(thumbprint: str) -> str:
            """Verify an AI agent's identity and reputation. Input: hex thumbprint."""
            return verify_agent_tool(thumbprint)

        @crewai_tool("Lookup Agent")
        def lookup_agent(agent_id: str) -> str:
            """Look up an agent by ID. Input: agent ID string."""
            return lookup_agent_tool(agent_id)

        @crewai_tool("Search Trusted Agents")
        def search_agents(query: str = "") -> str:
            """Search the AgentBio registry for trusted agents."""
            return search_trusted_agents_tool(query)

        @crewai_tool("Agent Credit Score")
        def agent_credit_score(thumbprint: str) -> str:
            """Get a FICO-modelled credit score for an agent. Input: hex thumbprint."""
            return credit_score_tool(thumbprint)

        return [verify_agent, lookup_agent, search_agents, agent_credit_score]

    except ImportError:
        raise ImportError("Install CrewAI tools: pip install crewai crewai-tools")


# ── Pattern 2: TrustedCrew ────────────────────────────────────────────────────
def build_trusted_crew(agent_thumbprints: list[str]):
    """
    Build a CrewAI Crew that verifies all agent thumbprints before kickoff.

    Raises PermissionError if any agent is blocked by AgentBio.

    Args:
        agent_thumbprints: List of thumbprints for agents in the crew.

    Returns:
        (safe_thumbprints, blocked_thumbprints) — proceed only if blocked is empty.
    """
    if not agent_thumbprints:
        return [], []

    print(f"Pre-flight trust check for {len(agent_thumbprints)} agents...")

    batch  = ab.batch_verify(agent_thumbprints[:10])
    safe   = []
    blocked = []

    for item in batch.items:
        if not item.found:
            print(f"  ⚪ {item.thumbprint[:24]}... — not registered")
            blocked.append(item.thumbprint)
        elif item.result.should_abort:
            print(f"  🚫 {item.result.agent_id} — BLOCKED: {item.result.summary}")
            blocked.append(item.thumbprint)
        elif item.result.action == TrustAction.PROCEED_WITH_CAUTION:
            print(f"  ⚠️  {item.result.agent_id} — CAUTION: {item.result.summary}")
            safe.append(item.thumbprint)
        else:
            print(f"  ✅ {item.result.agent_id} — TRUSTED (score {item.result.reputation_score:.1f})")
            safe.append(item.thumbprint)

    return safe, blocked


# ── Demo ──────────────────────────────────────────────────────────────────────
def demo():
    print("=" * 60)
    print("  AgentBio CrewAI Integration — Demo")
    print("=" * 60)

    print("\n--- verify_agent_tool ---")
    print(verify_agent_tool("0" * 64))

    print("\n--- lookup_agent_tool ---")
    print(lookup_agent_tool("nonexistent-agent"))

    print("\n--- search_trusted_agents_tool ---")
    print(search_trusted_agents_tool())

    print("\n--- build_trusted_crew (pre-flight check) ---")
    safe, blocked = build_trusted_crew(["a" * 64, "b" * 64])
    print(f"  Safe: {len(safe)}, Blocked: {len(blocked)}")

    print("\n\nTo use AgentBio tools in a CrewAI crew:")
    print("""
    from crewai import Agent, Task, Crew, Process
    from examples.crewai.crewai_integration import get_crewai_tools

    agentbio_tools = get_crewai_tools()

    coordinator = Agent(
        role        = "Trust Coordinator",
        goal        = "Verify agent identities before delegating work",
        backstory   = "You are responsible for ensuring all agents in the pipeline are trusted.",
        tools       = agentbio_tools,
        verbose     = True,
    )

    researcher = Agent(
        role      = "Researcher",
        goal      = "Conduct research tasks assigned by trusted agents",
        backstory  = "You execute research tasks after trust is established.",
        tools     = [],
        verbose   = True,
    )

    verify_task = Task(
        description = (
            "Search for trusted agents in the AgentBio registry. "
            "Verify the top result. Report whether it's safe to collaborate with."
        ),
        agent           = coordinator,
        expected_output = "Trust verification report for the top agent.",
    )

    crew = Crew(
        agents  = [coordinator, researcher],
        tasks   = [verify_task],
        process = Process.sequential,
        verbose = True,
    )

    result = crew.kickoff()
    print(result)
    """)


if __name__ == "__main__":
    demo()
