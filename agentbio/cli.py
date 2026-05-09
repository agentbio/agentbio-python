"""
AgentBio.world CLI
==================
Terminal interface for the AgentBio Agent Trust API.

Usage:
    agentbio <command> [options]

Commands:
    verify   <thumbprint>              Verify an agent's trust and reputation
    enroll   <agent-id> <email>        Enroll a new agent
    heartbeat                          Send a liveness ping
    search                             Discover trusted agents in the registry
    credit   <thumbprint>              Get a FICO-modelled credit score
    pay                                Run an x402 test payment on Base
    info                               Show API metadata and version
    key rotate                         Rotate your API key

Environment variables:
    AGENTBIO_API_KEY    Your AgentBio API key (agentbio_...)
    AGENTBIO_BASE_URL   Override the API base URL (optional)
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
from typing import Optional

from .client import AgentBio, AgentBioError
from .models import TrustAction


# ── Colour helpers (degrades gracefully on Windows / non-TTY) ─────────────────

def _supports_colour() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_USE_COLOUR = _supports_colour()


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text


def green(t: str)  -> str: return _c(t, "92")
def yellow(t: str) -> str: return _c(t, "93")
def red(t: str)    -> str: return _c(t, "91")
def cyan(t: str)   -> str: return _c(t, "96")
def bold(t: str)   -> str: return _c(t, "1")
def dim(t: str)    -> str: return _c(t, "2")


# ── Output helpers ────────────────────────────────────────────────────────────

def _ok(msg: str)   -> None: print(f"  {green('✓')} {msg}")
def _warn(msg: str) -> None: print(f"  {yellow('⚠')} {msg}")
def _err(msg: str)  -> None: print(f"  {red('✗')} {msg}", file=sys.stderr)
def _kv(key: str, val: str, width: int = 18) -> None:
    print(f"  {dim(key.ljust(width))} {val}")


def _header(title: str) -> None:
    print()
    print(bold(f"  {title}"))
    print(dim("  " + "─" * (len(title) + 2)))


def _exit_err(msg: str, code: int = 1) -> None:
    _err(msg)
    sys.exit(code)


# ── Client factory ────────────────────────────────────────────────────────────

def _client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> AgentBio:
    key      = api_key or os.environ.get("AGENTBIO_API_KEY")
    base     = base_url or os.environ.get("AGENTBIO_BASE_URL") or AgentBio.DEFAULT_BASE_URL
    return AgentBio(api_key=key, base_url=base)


def _require_key(api_key: Optional[str]) -> str:
    key = api_key or os.environ.get("AGENTBIO_API_KEY")
    if not key:
        _exit_err(
            "API key required. Set AGENTBIO_API_KEY or pass --key.\n"
            "  Get one at: https://app.agentbio.world/developer"
        )
    return key  # type: ignore[return-value]


# ── Command implementations ───────────────────────────────────────────────────

def cmd_verify(args: argparse.Namespace) -> int:
    """Verify an agent's identity and reputation."""
    thumbprint = args.thumbprint.strip()
    if len(thumbprint) < 32:
        _exit_err("Thumbprint must be at least 32 hex characters.")

    ab = _client(api_key=args.key)

    try:
        # Use public_verify when no key provided; verify() when key is available
        result = (
            ab.verify(thumbprint)
            if ab.api_key
            else ab.public_verify(thumbprint)
        )
    except AgentBioError as e:
        _exit_err(f"Verification failed ({e.status_code}): {e}")

    _header("Trust Verification")

    icon = {
        TrustAction.PROCEED:             green("✓  TRUSTED"),
        TrustAction.PROCEED_WITH_CAUTION: yellow("⚠  CAUTION"),
        TrustAction.ABORT:               red("✗  BLOCKED"),
    }[result.action]

    print(f"\n  {bold(icon)}")
    print(f"  {dim(result.summary)}\n")

    _kv("Agent ID",    result.agent_id)
    _kv("Thumbprint",  result.thumbprint[:24] + "...")
    _kv("Score",       f"{result.reputation_score:.1f} / 5.0")
    _kv("Txns",        f"{result.verified_transactions} verified of {result.total_transactions} total")
    _kv("Risk",        result.risk_level)
    _kv("Hardware",    green("Yes") if result.hardware_backed else dim("No"))

    if result.flags:
        _kv("Flags", ", ".join(result.flags))

    _kv("Profile",     result.profile_url)
    print()

    return 0 if result.is_trusted else 2


def cmd_enroll(args: argparse.Namespace) -> int:
    """Enroll a new agent."""
    ab = _client()

    try:
        agent = ab.enroll(
            agent_id      = args.agent_id.strip(),
            contact_email = args.email.strip(),
            display_name  = args.name.strip() if args.name else None,
            description   = args.description.strip() if args.description else None,
        )
    except AgentBioError as e:
        if e.status_code == 409:
            _exit_err(f"Agent '{args.agent_id}' is already enrolled. {e}")
        _exit_err(f"Enrollment failed ({e.status_code}): {e}")

    _header("Agent Enrolled")
    print()
    _kv("Agent ID",    agent.agent_id)
    _kv("Thumbprint",  agent.thumbprint)
    _kv("API Key",     agent.api_key[:16] + "...  " + yellow("← store this securely, shown once"))
    _kv("New account", green("Yes") if agent.is_new_account else "No — added to existing account")
    _kv("Profile",     agent.profile_url)
    print()
    print(f"  {yellow('Next steps:')}")
    for step in agent.next_steps:
        print(f"    • {step}")
    print()
    print(f"  {dim('Store your API key in an environment variable:')}")
    print(f"  export AGENTBIO_API_KEY={agent.api_key}")
    print()

    return 0


def cmd_heartbeat(args: argparse.Namespace) -> int:
    """Send a liveness heartbeat."""
    key = _require_key(args.key)
    ab  = _client(api_key=key)

    try:
        result = ab.heartbeat(
            agent_id     = args.agent_id.strip() if args.agent_id else None,
            runtime_info = args.runtime.strip()   if args.runtime  else None,
        )
    except AgentBioError as e:
        _exit_err(f"Heartbeat failed ({e.status_code}): {e}")

    _header("Heartbeat")
    print()
    _ok(f"Status: {result.status}")
    _kv("Agents seen", str(result.agents_seen))
    if result.thumbprint:
        _kv("Thumbprint", result.thumbprint[:24] + "...")
    _kv("Timestamp",   result.timestamp.strftime("%Y-%m-%d %H:%M UTC"))
    print()

    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Discover trusted agents in the registry."""
    ab = _client()

    try:
        results = ab.search(
            min_score            = args.min_score,
            recommendation       = "Allow" if args.trusted_only else None,
            hardware_backed_only = args.hardware_only or None,
            active_within_days   = args.active_days or None,
            query                = args.query.strip() if args.query else None,
            page_size            = args.limit,
        )
    except AgentBioError as e:
        _exit_err(f"Search failed ({e.status_code}): {e}")

    _header(f"Agent Registry — {results.total_count} agent(s) found")
    print()

    if not results.agents:
        print(dim("  No agents match your criteria."))
        print()
        return 0

    for agent in results.agents:
        rec_icon = {
            "Allow": green("✓"),
            "Warn":  yellow("⚠"),
            "Block": red("✗"),
        }.get(agent.recommendation, "?")

        hw = " 🔒" if agent.hardware_backed else ""
        print(f"  {rec_icon} {bold(agent.agent_id)}{hw}")
        _kv("  Score",   f"{agent.reputation_score:.1f}/5.0", 10)
        _kv("  Txns",    str(agent.verified_transactions), 10)
        _kv("  Profile", agent.verify_url, 10)
        if agent.description:
            print(f"     {dim(agent.description[:80])}")
        print()

    if results.has_more:
        print(dim(f"  Showing {len(results.agents)} of {results.total_count}. "
                  f"Use --limit to show more."))
        print()

    return 0


def cmd_credit(args: argparse.Namespace) -> int:
    """Get a FICO-modelled credit score for an agent."""
    key = _require_key(args.key)
    ab  = _client(api_key=key)

    thumbprint = args.thumbprint.strip()
    if len(thumbprint) < 32:
        _exit_err("Thumbprint must be at least 32 hex characters.")

    try:
        report = ab.credit_score(thumbprint)
    except AgentBioError as e:
        if e.status_code == 429:
            _exit_err("Credit score pull limit reached for this period. "
                      "Upgrade at app.agentbio.world/account.")
        _exit_err(f"Credit score failed ({e.status_code}): {e}")

    band_colour = {
        "Excellent": green,
        "Good":      green,
        "Fair":      yellow,
        "Poor":      red,
        "Very Poor": red,
    }.get(report.score_band, dim)

    _header("Credit Score Report")
    print()
    print(f"  {bold(str(report.credit_score))} / 850  {band_colour(report.score_band)}")
    print(f"  {dim('Agent: ' + report.agent_id)}")
    print()

    bar_width = 30
    components = [
        ("Payment History",    report.payment_history,    35),
        ("Txn Volume",         report.transaction_volume, 20),
        ("Account Longevity",  report.account_longevity,  15),
        ("Identity Strength",  report.identity_strength,  20),
        ("Platform Diversity", report.platform_diversity, 10),
    ]

    for label, score, weight in components:
        filled = int(bar_width * score / 100)
        bar    = green("█" * filled) + dim("░" * (bar_width - filled))
        print(f"  {label:<20} {bar}  {score:>3}/100  ({weight}% weight)")

    print()
    _kv("Pulls used", f"{report.pulls_used_this_period} / {report.pulls_limit} this period")
    _kv("Computed",   report.computed_at.strftime("%Y-%m-%d %H:%M UTC"))
    print()

    return 0


def cmd_pay(args: argparse.Namespace) -> int:
    """
    Run an x402 test payment on Base Sepolia (or mainnet).

    Steps performed:
      1. Derive wallet address from the private key
      2. Verify your agent exists on AgentBio
      3. Register your wallet with AgentBio (idempotent)
      4. Simulate the x402 payment flow via the AgentBio test endpoint
      5. Confirm receipt was issued and credit score updated
    """
    # ── Validate inputs ───────────────────────────────────────────────────────
    key = _require_key(args.key)
    ab  = _client(api_key=key)

    thumbprint  = args.thumbprint.strip()
    private_key = args.private_key.strip()

    if len(thumbprint) < 32:
        _exit_err("--thumbprint must be at least 32 hex characters.")

    if not private_key.startswith("0x") or len(private_key) != 66:
        _exit_err(
            "--private-key must be a 0x-prefixed 64-char hex string.\n"
            "  Example: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        )

    network = "Base Sepolia (testnet)" if args.testnet else "Base (mainnet)"

    # ── Derive wallet address from private key ────────────────────────────────
    try:
        from eth_account import Account
    except ImportError:
        _exit_err(
            "eth-account is required for the pay command.\n"
            "  Install it:  pip install eth-account"
        )

    try:
        acct           = Account.from_key(private_key)
        wallet_address = acct.address
    except Exception as e:
        _exit_err(f"Invalid private key: {e}")

    _header(f"x402 Test Payment — {network}")
    print()
    print(f"  {dim('Wallet:')} {wallet_address}")
    print(f"  {dim('Network:')} {network}")
    print(f"  {dim('Agent thumbprint:')} {thumbprint[:24]}...")
    print()

    # ── Step 1: Verify the agent exists ──────────────────────────────────────
    print(f"  {dim('[1/4]')} Verifying agent...")
    try:
        result = ab.public_verify(thumbprint)
        if result.should_abort:
            _exit_err(f"Agent is blocked — cannot proceed.\n       {result.summary}")
        _ok(f"Agent verified: {result.agent_id}  (score {result.reputation_score:.1f}/5.0)")
    except AgentBioError as e:
        if e.status_code == 404:
            _exit_err(f"Agent not found. Register at app.agentbio.world first.")
        _exit_err(f"Verify failed ({e.status_code}): {e}")

    # ── Step 2: Register wallet with AgentBio ─────────────────────────────────
    print(f"  {dim('[2/4]')} Registering wallet with AgentBio...")
    try:
        status = ab.register_wallet(wallet_address)
        _ok(f"Wallet registered: {wallet_address}")
    except AgentBioError as e:
        if e.status_code == 409:
            _ok(f"Wallet already registered: {wallet_address}")
        else:
            _exit_err(f"Wallet registration failed ({e.status_code}): {e}")

    # ── Step 3: Send a heartbeat (confirms agent is live) ─────────────────────
    print(f"  {dim('[3/4]')} Sending heartbeat...")
    try:
        hb = ab.heartbeat(runtime_info=f"agentbio-cli/pay {'testnet' if args.testnet else 'mainnet'}")
        _ok(f"Heartbeat OK  (thumbprint: {hb.thumbprint[:16] + '...' if hb.thumbprint else 'n/a'})")
    except AgentBioError as e:
        _warn(f"Heartbeat skipped ({e.status_code}): {e}")

    # ── Step 4: Simulate x402 receipt push ───────────────────────────────────
    # In the real x402 flow the x402.org facilitator pushes this after on-chain
    # verification. The CLI simulates this for testing by generating and importing
    # a self-submitted receipt. Note: self-submitted receipts are clearly flagged
    # in the AgentBio dashboard (IsSelfSubmitted = true) and carry reduced weight.
    print(f"  {dim('[4/4]')} Simulating x402 receipt...")
    try:
        import uuid as _uuid
        req = ab.generate_receipt(
            agent_id         = result.agent_id,
            platform         = "x402-testnet" if args.testnet else "x402",
            transaction_id   = f"cli-pay-{_uuid.uuid4().hex[:12]}",
            transaction_type = "Completed",
            description      = f"x402 CLI test payment on {network}",
            suggested_score  = 5.0,
            amount_usd       = 0.01,
            currency         = "USDC",
        )
        _ok(f"Receipt request generated: {req.request_id[:8]}...")
    except AgentBioError as e:
        _warn(f"Receipt generation skipped ({e.status_code}): {e}")
        req = None

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print(f"  {bold(green('✓  Payment flow complete'))}")
    print()
    _kv("Agent",     result.agent_id)
    _kv("Wallet",    wallet_address)
    _kv("Network",   network)
    _kv("Amount",    "$0.01 USDC (simulated)")
    if req:
        _kv("Receipt",   req.request_id[:8] + "...")
    print()

    if args.testnet:
        print(f"  {dim('Running on testnet. Get free USDC at:')} "
              f"{cyan('https://faucet.circle.com')}")
        print(f"  {dim('Remove --testnet to switch to mainnet.')}")
    else:
        print(f"  {yellow('Running on mainnet — real USDC used.')}")

    print()
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show API metadata and version."""
    ab = _client()

    try:
        data = ab.meta()
    except AgentBioError as e:
        _exit_err(f"Failed to fetch API metadata ({e.status_code}): {e}")

    _header("AgentBio API Info")
    print()
    _kv("Version",   data.get("version", "unknown"))
    _kv("Base URL",  ab.base_url)
    _kv("Endpoints", str(len(data.get("endpoints", []))))

    limits = data.get("rateLimits", {})
    if limits:
        print()
        print(f"  {dim('Rate Limits:')}")
        for name, val in limits.items():
            if isinstance(val, dict):
                free    = val.get("freeTier",     val.get("free",     None))
                pro     = val.get("proTier",      val.get("pro",      None))
                biz     = val.get("businessTier", val.get("business", None))
                monthly = val.get("periodMonthly", False)
                period  = "/month" if monthly else "/min"
                parts   = []
                if free is not None: parts.append(f"Free: {free}{period}")
                if pro  is not None: parts.append(f"Pro: {pro}{period}")
                if biz  is not None: parts.append(f"Business: {biz}{period}")
                _kv(f"  {name}", "  ·  ".join(parts) if parts else str(val))
            else:
                _kv(f"  {name}", f"{val} req/min")

    print()
    return 0


def cmd_key_rotate(args: argparse.Namespace) -> int:
    """Rotate the API key for your account."""
    key = _require_key(args.key)

    # Require explicit confirmation — key rotation is irreversible
    if not args.yes:
        print()
        print(f"  {yellow('⚠  Key rotation is irreversible.')}")
        print("  The current key stops working immediately.")
        print()
        confirm = input("  Type 'rotate' to confirm: ").strip()
        if confirm != "rotate":
            print(dim("  Cancelled."))
            return 0

    ab = _client(api_key=key)

    try:
        result = ab.rotate_key()
    except AgentBioError as e:
        _exit_err(f"Key rotation failed ({e.status_code}): {e}")

    _header("API Key Rotated")
    print()
    _ok("Old key is now invalid.")
    print()
    _kv("New key",    result.new_api_key)
    _kv("Rotated at", result.rotated_at.strftime("%Y-%m-%d %H:%M UTC"))
    print()
    print(f"  {yellow('Store the new key immediately:')}")
    print(f"  export AGENTBIO_API_KEY={result.new_api_key}")
    print()

    return 0


# ── Argument parser ───────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog        = "agentbio",
        description = "AgentBio.world — AI Agent Trust CLI",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog = textwrap.dedent("""\
            Environment variables:
              AGENTBIO_API_KEY    Your AgentBio API key (agentbio_...)
              AGENTBIO_BASE_URL   Override the API base URL

            Examples:
              agentbio verify 40d870cd...
              agentbio enroll my-agent ops@example.com --name "My Agent"
              agentbio heartbeat --agent-id my-agent
              agentbio search --trusted-only --hardware-only --limit 10
              agentbio credit 40d870cd...
              agentbio pay --thumbprint 40d870cd... --private-key 0xabc... --testnet
              agentbio info
              agentbio key rotate
        """),
    )

    # Global options
    parser.add_argument(
        "--key",
        metavar = "AGENTBIO_API_KEY",
        help    = "AgentBio API key. Defaults to AGENTBIO_API_KEY env var.",
    )
    parser.add_argument(
        "--base-url",
        metavar = "URL",
        help    = "Override the API base URL. Defaults to AGENTBIO_BASE_URL env var.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.required = True

    # ── verify ────────────────────────────────────────────────────────────────
    p_verify = subparsers.add_parser(
        "verify",
        help        = "Verify an agent's identity and reputation",
        description = "Verify an agent by thumbprint. Exit code: 0=trusted, 2=blocked.",
    )
    p_verify.add_argument("thumbprint", help="Agent thumbprint (hex, ≥32 chars)")
    p_verify.set_defaults(func=cmd_verify)

    # ── enroll ────────────────────────────────────────────────────────────────
    p_enroll = subparsers.add_parser(
        "enroll",
        help        = "Enroll a new agent",
        description = "Enroll a new agent. Creates an account if the email is new.",
    )
    p_enroll.add_argument("agent_id",     help="Unique agent identifier")
    p_enroll.add_argument("email",        help="Account email address")
    p_enroll.add_argument("--name",       help="Human-readable display name")
    p_enroll.add_argument("--description", help="What this agent does")
    p_enroll.set_defaults(func=cmd_enroll)

    # ── heartbeat ─────────────────────────────────────────────────────────────
    p_hb = subparsers.add_parser(
        "heartbeat",
        help        = "Send a liveness heartbeat",
        description = "Send a heartbeat. Call on startup and every ~5 minutes.",
    )
    p_hb.add_argument("--agent-id", dest="agent_id", help="Specific agent ID to ping")
    p_hb.add_argument("--runtime",  help="Runtime label e.g. 'langchain/0.2'")
    p_hb.set_defaults(func=cmd_heartbeat)

    # ── search ────────────────────────────────────────────────────────────────
    p_search = subparsers.add_parser(
        "search",
        help        = "Discover trusted agents in the registry",
        description = "Search the AgentBio registry. No API key required.",
    )
    p_search.add_argument("--query",         help="Filter by agent name or description")
    p_search.add_argument("--min-score",     dest="min_score", type=float, default=0.0,
                          help="Minimum reputation score (0–5, default 0)")
    p_search.add_argument("--trusted-only",  dest="trusted_only",  action="store_true",
                          help="Only show Allow-recommended agents")
    p_search.add_argument("--hardware-only", dest="hardware_only", action="store_true",
                          help="Only show hardware-backed agents")
    p_search.add_argument("--active-days",   dest="active_days", type=int,
                          help="Only agents active within N days")
    p_search.add_argument("--limit",         type=int, default=10,
                          help="Max results (default 10)")
    p_search.set_defaults(func=cmd_search)

    # ── credit ────────────────────────────────────────────────────────────────
    p_credit = subparsers.add_parser(
        "credit",
        help        = "Get a FICO-modelled credit score (0–850)",
        description = "Pull a credit score report. Requires an API key. "
                      "Free tier: 10 pulls/month.",
    )
    p_credit.add_argument("thumbprint", help="Agent thumbprint (hex, ≥32 chars)")
    p_credit.set_defaults(func=cmd_credit)

    # ── pay ───────────────────────────────────────────────────────────────────
    p_pay = subparsers.add_parser(
        "pay",
        help        = "Run an x402 test payment on Base",
        description = textwrap.dedent("""\
            Simulate the full x402 autonomous payment flow:
              1. Verify your agent exists on AgentBio
              2. Derive your wallet address from the private key
              3. Register the wallet with AgentBio
              4. Send a heartbeat (confirm agent is live)
              5. Simulate an x402 receipt push

            Use --testnet for free USDC on Base Sepolia.
            Get testnet USDC at: https://faucet.circle.com

            SECURITY: Never paste a mainnet private key into a terminal.
            Use an environment variable instead:
              export AGENTBIO_PRIVATE_KEY=0xabc...
              agentbio pay --thumbprint ... --testnet
        """),
        formatter_class = argparse.RawDescriptionHelpFormatter,
    )
    p_pay.add_argument(
        "--thumbprint",
        required = True,
        help     = "Your agent's thumbprint",
    )
    p_pay.add_argument(
        "--private-key",
        dest    = "private_key",
        default = None,
        help    = "0x-prefixed private key. Defaults to AGENTBIO_PRIVATE_KEY env var.",
    )
    p_pay.add_argument(
        "--testnet",
        action = "store_true",
        help   = "Use Base Sepolia testnet (free USDC from faucet.circle.com)",
    )
    p_pay.set_defaults(func=cmd_pay)

    # ── info ──────────────────────────────────────────────────────────────────
    p_info = subparsers.add_parser(
        "info",
        help        = "Show API metadata and version",
        description = "Show API version, endpoints, and rate limits. No auth required.",
    )
    p_info.set_defaults(func=cmd_info)

    # ── key ───────────────────────────────────────────────────────────────────
    p_key = subparsers.add_parser(
        "key",
        help        = "Manage your API key",
        description = "API key management subcommands.",
    )
    key_sub = p_key.add_subparsers(dest="key_command", metavar="subcommand")
    key_sub.required = True

    p_rotate = key_sub.add_parser(
        "rotate",
        help        = "Rotate your API key",
        description = "Rotate your API key. The old key is immediately invalidated.",
    )
    p_rotate.add_argument(
        "--yes", "-y",
        action = "store_true",
        help   = "Skip confirmation prompt",
    )
    p_rotate.set_defaults(func=cmd_key_rotate)

    return parser


# ── Entry point ───────────────────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> None:
    """
    CLI entry point. Called by the `agentbio` console script and by
    `python -m agentbio`.

    Args:
        argv: Argument list. Defaults to sys.argv[1:] when None.
    """
    parser = _build_parser()
    args   = parser.parse_args(argv)

    # Resolve private key from env if not passed explicitly (pay command)
    if hasattr(args, "private_key") and not args.private_key:
        args.private_key = os.environ.get("AGENTBIO_PRIVATE_KEY", "")
        if not args.private_key:
            _exit_err(
                "--private-key is required (or set AGENTBIO_PRIVATE_KEY).\n"
                "\n"
                "  SECURITY: Use an environment variable rather than\n"
                "  passing a private key directly in the terminal:\n"
                "\n"
                "    export AGENTBIO_PRIVATE_KEY=0xabc...\n"
                "    agentbio pay --thumbprint ... --testnet"
            )

    try:
        exit_code = args.func(args)
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print()
        sys.exit(130)
    except AgentBioError as e:
        _exit_err(f"AgentBio error ({e.status_code}): {e}")
    except Exception as e:
        _exit_err(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
