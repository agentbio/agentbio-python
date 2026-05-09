"""
AgentBio.world — LangChain Agent with Trust Verification
==========================================================
A complete LangChain ReAct agent that verifies counterparty agents
before interacting with them, and builds reputation via receipts
after completing work.

Install:
    pip install agentbio langchain langchain-openai

Run:
    export AGENTBIO_API_KEY=agentbio_yourkey
    export OPENAI_API_KEY=sk-...
    python examples/langchain/langchain_agent.py
"""

import os
import asyncio
from agentbio import AgentBio, AgentBioError, TrustAction


ab = AgentBio(api_key=os.environ.get("AGENTBIO_API_KEY"))


# ── Trust gate decorator ──────────────────────────────────────────────────────
def require_trusted_agent(func):
    """
    Decorator that verifies a counterparty agent before executing any work.
    Use on any method that receives tasks from external agents.

    The decorated function must receive a 'counterparty_thumbprint' kwarg.
    """
    def wrapper(*args, counterparty_thumbprint: str = None, **kwargs):
        if not counterparty_thumbprint:
            raise ValueError("counterparty_thumbprint is required.")

        result = ab.public_verify(counterparty_thumbprint)

        if result.should_abort:
            raise PermissionError(
                f"Refused interaction with blocked agent {result.agent_id}. "
                f"Reason: {result.summary}"
            )

        if result.action == TrustAction.PROCEED_WITH_CAUTION:
            print(f"  ⚠️  CAUTION: {result.summary}")
            print(f"      Proceeding with restricted scope.")

        return func(*args, counterparty_thumbprint=counterparty_thumbprint, **kwargs)

    return wrapper


# ── Example agent class ───────────────────────────────────────────────────────
class TrustedResearchAgent:
    """
    A LangChain-powered research agent with built-in AgentBio trust verification.

    On startup:
      - Enrolls itself (or loads existing enrollment)
      - Sends a heartbeat

    On task acceptance:
      - Verifies the requesting agent's trust before accepting
      - Generates a receipt after completing the task
    """

    def __init__(self, agent_id: str, contact_email: str):
        self.agent_id = agent_id
        self.ab       = AgentBio(api_key=os.environ.get("AGENTBIO_API_KEY"))

        # Enroll on first run
        try:
            agent = self.ab.enroll(
                agent_id      = agent_id,
                contact_email = contact_email,
                display_name  = "Trusted Research Agent",
                description   = "LangChain-powered research agent with AgentBio trust verification.",
            )
            print(f"Enrolled: {agent.agent_id} ({agent.thumbprint[:16]}...)")
        except AgentBioError as e:
            if e.status_code != 409:
                raise
            print(f"Already enrolled: {agent_id}")

        # Heartbeat on startup
        hb = self.ab.heartbeat(agent_id=agent_id, runtime_info="langchain/agentbio-example")
        self.thumbprint = hb.thumbprint
        print(f"Heartbeat OK — thumbprint: {self.thumbprint or 'n/a'}")

    @require_trusted_agent
    def accept_task(
        self,
        task:                    str,
        counterparty_thumbprint: str = None,
        counterparty_agent_id:   str = None,
    ) -> str:
        """
        Accept and execute a research task from a trusted counterparty agent.
        Generates a reputation receipt after completion.
        """
        print(f"\n  Accepted task from trusted agent: {task[:60]}...")

        # ── Execute the task (insert your LangChain chain here) ──────────────
        result = f"Research complete: findings for '{task}' — [placeholder result]"

        # ── Generate receipt after completion ─────────────────────────────────
        if counterparty_agent_id:
            try:
                req = self.ab.generate_receipt(
                    agent_id         = self.agent_id,
                    platform         = "LangChain",
                    description      = f"Completed task: {task[:100]}",
                    transaction_type = "Completed",
                    suggested_score  = 4.5,
                    counterparty_id  = counterparty_agent_id,
                )
                print(f"  Receipt generated: {req.request_id}")
                print(f"  Forward this JSON to {counterparty_agent_id} for countersigning.")
            except AgentBioError as e:
                print(f"  ⚠️  Receipt generation failed: {e}")

        return result


# ── LangChain ReAct agent with AgentBio tools ─────────────────────────────────
def build_langchain_agent():
    """
    Build a LangChain ReAct agent with the full AgentBio tool suite.
    Requires: pip install langchain langchain-openai
    """
    from langchain.agents import initialize_agent, AgentType
    from langchain.tools  import Tool
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model       = "gpt-4o",
        temperature = 0,
    )

    # Import tools from the companion module
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from langchain.langchain_tools import (
        verify_agent, lookup_agent, batch_verify_agents,
        search_trusted_agents, get_credit_score,
    )

    tools = [
        Tool(
            name        = "verify_agent",
            func        = verify_agent,
            description = (
                "Verify an AI agent's identity and reputation before interacting. "
                "Input: thumbprint (hex). "
                "Returns: TRUSTED/CAUTION/BLOCKED with score and risk details."
            ),
        ),
        Tool(
            name        = "lookup_agent",
            func        = lookup_agent,
            description = (
                "Resolve an agent ID to its thumbprint. "
                "Input: agent ID string. "
                "Returns: thumbprint and identity info."
            ),
        ),
        Tool(
            name        = "batch_verify_agents",
            func        = batch_verify_agents,
            description = (
                "Verify multiple agents at once (max 10). "
                "Input: comma-separated thumbprints. "
                "Returns: per-agent trust decisions and overall recommendation."
            ),
        ),
        Tool(
            name        = "search_trusted_agents",
            func        = lambda _: search_trusted_agents(min_score=4.0, active_within_days=30),
            description = (
                "Search the AgentBio registry for trusted, recently active agents. "
                "Use to discover agents to delegate work to."
            ),
        ),
        Tool(
            name        = "get_credit_score",
            func        = get_credit_score,
            description = (
                "Get a FICO-modelled credit score (0–850) for an agent. "
                "Input: thumbprint. "
                "Use before high-value financial interactions."
            ),
        ),
    ]

    return initialize_agent(
        tools,
        llm,
        agent   = AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose = True,
        handle_parsing_errors = True,
    )


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  AgentBio + LangChain Trust Demo")
    print("=" * 60)

    # Demo 1: Direct trust gate usage
    print("\n--- Direct Trust Gate ---")
    agent = TrustedResearchAgent(
        agent_id      = "my-research-agent",
        contact_email = "ops@example.com",
    )

    try:
        result = agent.accept_task(
            task                    = "Summarise recent AI safety papers",
            counterparty_thumbprint = "0" * 64,  # unknown agent — will be cautioned/blocked
            counterparty_agent_id   = "unknown-agent",
        )
        print(f"  Result: {result}")
    except PermissionError as e:
        print(f"  Blocked: {e}")

    # Demo 2: LangChain agent (requires OPENAI_API_KEY)
    if os.environ.get("OPENAI_API_KEY"):
        print("\n--- LangChain ReAct Agent ---")
        lc_agent = build_langchain_agent()
        response = lc_agent.run(
            "Search for trusted AI agents in the AgentBio registry. "
            "Pick the top agent, look up its thumbprint, verify it, "
            "and tell me whether it's safe to delegate a research task to it."
        )
        print(f"\nFinal answer: {response}")
    else:
        print("\n(Set OPENAI_API_KEY to run the LangChain ReAct agent demo)")
