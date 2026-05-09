"""
AgentBio.world — AutoGen Integration
======================================
Integrates AgentBio trust verification into Microsoft AutoGen
multi-agent conversations.

Two patterns are shown:
  1. TrustedConversableAgent — drop-in replacement for ConversableAgent
     that verifies senders before accepting messages.
  2. AgentBio function tools — register as AutoGen function tools
     so the LLM can call them during conversation.

Install:
    pip install agentbio pyautogen

Run:
    export AGENTBIO_API_KEY=agentbio_yourkey
    export OPENAI_API_KEY=sk-...
    python examples/autogen/autogen_integration.py
"""

import os
from typing import Optional
from agentbio import AgentBio, AgentBioError, TrustAction

ab = AgentBio(api_key=os.environ.get("AGENTBIO_API_KEY"))


# ── Pattern 1: TrustedConversableAgent ───────────────────────────────────────
# Drop-in replacement for autogen.ConversableAgent that enforces
# AgentBio trust checks before accepting messages from peer agents.

def create_trusted_agent(
    name:            str,
    agent_thumbprint: str,
    system_message:  str,
    llm_config:      dict,
    block_untrusted: bool = True,
):
    """
    Create an AutoGen ConversableAgent with AgentBio trust verification.

    Args:
        name:             Agent name for AutoGen.
        agent_thumbprint: The AgentBio thumbprint to verify before accepting messages.
        system_message:   System prompt for the agent.
        llm_config:       AutoGen LLM config dict.
        block_untrusted:  If True, refuse messages from blocked agents.
                          If False, proceed with a warning (fail-open).

    Returns:
        A ConversableAgent instance with a trust-checking reply function.
    """
    try:
        import autogen
    except ImportError:
        raise ImportError("Install AutoGen: pip install pyautogen")

    # Pre-verify the counterparty agent
    trust_cache: dict = {}

    def verify_sender(thumbprint: str) -> tuple[bool, str]:
        """Returns (should_proceed, reason)."""
        if thumbprint in trust_cache:
            return trust_cache[thumbprint]

        try:
            result = ab.public_verify(thumbprint)
            if result.should_abort:
                decision = (False, f"BLOCKED: {result.summary}")
            elif result.action == TrustAction.PROCEED_WITH_CAUTION:
                decision = (True, f"CAUTION: {result.summary}")
            else:
                decision = (True, f"TRUSTED: {result.summary}")
            trust_cache[thumbprint] = decision
            return decision
        except AgentBioError as e:
            # On verification error, fail-open by default
            return (True, f"UNVERIFIED (AgentBio error {e.status_code}): proceeding anyway")

    class TrustCheckMixin:
        def check_trust(self, sender_thumbprint: str) -> Optional[str]:
            """
            Call before processing a message. Returns an error string if
            the sender should be refused, or None if OK to proceed.
            """
            should_proceed, reason = verify_sender(sender_thumbprint)
            print(f"  [AgentBio] {reason}")

            if not should_proceed and block_untrusted:
                return f"Message refused: {reason}"
            return None

    # Build the agent
    agent = autogen.ConversableAgent(
        name           = name,
        system_message = system_message,
        llm_config     = llm_config,
    )

    # Attach trust check mixin
    agent.__class__ = type("TrustedConversableAgent", (TrustCheckMixin, autogen.ConversableAgent), {})
    return agent


# ── Pattern 2: AgentBio function tools for AutoGen ───────────────────────────
# Register these as AutoGen function_map entries so the LLM can call them.

def agentbio_verify(thumbprint: str) -> dict:
    """
    AutoGen function tool: verify an agent's trust before interacting.

    Register in your AutoGen agent's function_map:
        "agentbio_verify": agentbio_verify

    Args:
        thumbprint: The agent's hex thumbprint.

    Returns:
        dict with decision, score, summary, and flags.
    """
    try:
        result = ab.public_verify(thumbprint.strip())
        return {
            "decision":     result.action.value,
            "trusted":      result.is_trusted,
            "score":        result.reputation_score,
            "risk":         result.risk_level,
            "summary":      result.summary,
            "flags":        result.flags,
            "agent_id":     result.agent_id,
            "hardware":     result.hardware_backed,
            "profile":      result.profile_url,
        }
    except AgentBioError as e:
        return {
            "decision": "error",
            "trusted":  False,
            "summary":  f"Verification failed ({e.status_code}): {e}",
            "error":    True,
        }


def agentbio_lookup(agent_id: str) -> dict:
    """
    AutoGen function tool: resolve an agent ID to its thumbprint.

    Args:
        agent_id: The agent's identifier string.

    Returns:
        dict with thumbprint, hardware status, and profile URL.
    """
    try:
        info = ab.lookup(agent_id.strip())
        return {
            "agent_id":        info.agent_id,
            "thumbprint":      info.thumbprint,
            "hardware_backed": info.hardware_backed,
            "enrolled_at":     str(info.enrolled_at.date()),
            "verify_url":      info.verify_url,
        }
    except AgentBioError as e:
        return {"error": True, "message": f"Agent '{agent_id}' not found ({e.status_code})"}


def agentbio_search(min_score: float = 4.0, active_within_days: int = 30) -> dict:
    """
    AutoGen function tool: discover trusted agents in the registry.

    Args:
        min_score:          Minimum reputation score (default 4.0).
        active_within_days: Only agents active within N days (default 30).

    Returns:
        dict with list of trusted agents.
    """
    try:
        results = ab.search(
            min_score          = min_score,
            recommendation     = "Allow",
            active_within_days = active_within_days,
            page_size          = 5,
        )
        return {
            "total":  results.total_count,
            "agents": [
                {
                    "agent_id":   a.agent_id,
                    "score":      a.reputation_score,
                    "txns":       a.verified_transactions,
                    "hardware":   a.hardware_backed,
                    "verify_url": a.verify_url,
                }
                for a in results.agents
            ],
        }
    except AgentBioError as e:
        return {"error": True, "message": str(e)}


# ── AutoGen function schema (for LLM tool-calling) ────────────────────────────
AGENTBIO_FUNCTIONS = [
    {
        "name":        "agentbio_verify",
        "description": "Verify an AI agent's identity and reputation before interacting with them. Returns a trust decision (proceed/proceed_with_caution/abort) and reputation details.",
        "parameters":  {
            "type":       "object",
            "properties": {
                "thumbprint": {
                    "type":        "string",
                    "description": "The agent's hex thumbprint (32-64 characters).",
                }
            },
            "required": ["thumbprint"],
        },
    },
    {
        "name":        "agentbio_lookup",
        "description": "Look up an agent by its ID and return its thumbprint. Use when you know the agent's name but need its thumbprint to call agentbio_verify.",
        "parameters":  {
            "type":       "object",
            "properties": {
                "agent_id": {
                    "type":        "string",
                    "description": "The agent's alphanumeric identifier.",
                }
            },
            "required": ["agent_id"],
        },
    },
    {
        "name":        "agentbio_search",
        "description": "Search the AgentBio registry for trusted, recently active agents. Use to discover agents to delegate work to.",
        "parameters":  {
            "type":       "object",
            "properties": {
                "min_score": {
                    "type":        "number",
                    "description": "Minimum reputation score 0-5 (default 4.0).",
                },
                "active_within_days": {
                    "type":        "integer",
                    "description": "Only return agents active within this many days (default 30).",
                },
            },
            "required": [],
        },
    },
]

AGENTBIO_FUNCTION_MAP = {
    "agentbio_verify": agentbio_verify,
    "agentbio_lookup": agentbio_lookup,
    "agentbio_search": agentbio_search,
}


# ── Demo ──────────────────────────────────────────────────────────────────────
def demo_function_tools():
    """Demonstrates AgentBio function tools without requiring AutoGen or an LLM."""
    print("=" * 60)
    print("  AgentBio AutoGen Function Tools — Demo")
    print("=" * 60)

    print("\n--- agentbio_lookup ---")
    result = agentbio_lookup("nonexistent-agent")
    print(result)

    print("\n--- agentbio_verify (unknown thumbprint) ---")
    result = agentbio_verify("0" * 64)
    print(result)

    print("\n--- agentbio_search ---")
    result = agentbio_search(min_score=1.0, active_within_days=365)
    print(f"  Found {result.get('total', 0)} agents")
    for a in result.get("agents", [])[:3]:
        print(f"    {a['agent_id']:<30} score={a['score']:.1f}")

    print("\n\nTo use with AutoGen, add these to your agent config:")
    print("""
    import autogen
    from examples.autogen.autogen_integration import (
        AGENTBIO_FUNCTIONS, AGENTBIO_FUNCTION_MAP
    )

    llm_config = {
        "model":     "gpt-4o",
        "functions": AGENTBIO_FUNCTIONS,
    }

    assistant = autogen.AssistantAgent(
        name           = "assistant",
        llm_config     = llm_config,
        function_map   = AGENTBIO_FUNCTION_MAP,
    )

    user_proxy = autogen.UserProxyAgent(
        name              = "user_proxy",
        human_input_mode  = "NEVER",
        function_map      = AGENTBIO_FUNCTION_MAP,
    )

    user_proxy.initiate_chat(
        assistant,
        message = (
            "Search for trusted agents in the AgentBio registry. "
            "Look up 'research-agent', verify it, and tell me if it's safe to work with."
        ),
    )
    """)


if __name__ == "__main__":
    demo_function_tools()
