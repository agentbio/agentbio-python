"""
AgentBio SDK data models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    import threading


class TrustAction(str, Enum):
    """Machine-readable action returned by AgentBio."""
    PROCEED               = "proceed"
    PROCEED_WITH_CAUTION  = "proceed_with_caution"
    ABORT                 = "abort"


@dataclass
class VerifyResult:
    """
    Trust verification result for an agent.

    Use `action` for machine-readable decisions.
    Use `summary` for a human-readable explanation.
    Use `is_trusted` / `should_abort` as convenience properties.
    """

    # Core identity
    agent_id:              str
    thumbprint:            str
    identity_valid:        bool
    hardware_backed:       bool

    # Reputation
    reputation_score:      float           # 0.0 – 5.0
    verified_transactions: int
    total_transactions:    int
    risk_level:            str             # Low | Moderate | High | Critical | Unknown

    # Decision fields
    recommendation:        str             # Allow | Warn | Block
    action:                TrustAction     # proceed | proceed_with_caution | abort
    summary:               str             # one-sentence explanation
    flags:                 list            # e.g. ["new_agent", "no_transactions"]

    # Verification metadata
    verification_id:       str
    next_verify_after:     datetime
    issued_at:             datetime
    data_freshness_utc:    datetime
    profile_url:           str

    # Optional
    moltbook_linked:       bool  = False
    moltbook_karma:        int   = 0
    server_signature:      str   = ""

    @property
    def is_trusted(self) -> bool:
        """Returns True if the agent is safe to interact with."""
        return self.action in (TrustAction.PROCEED, TrustAction.PROCEED_WITH_CAUTION)

    @property
    def should_abort(self) -> bool:
        """Returns True if you should refuse to interact with this agent."""
        return self.action == TrustAction.ABORT

    def __str__(self) -> str:
        return (
            f"AgentBio [{self.action.value.upper()}] {self.agent_id} — "
            f"score {self.reputation_score:.1f}/5.0, "
            f"{self.verified_transactions} verified txns, "
            f"risk: {self.risk_level}"
        )


@dataclass
class EnrollResult:
    """
    Result of programmatic agent enrollment.

    IMPORTANT: Store api_key securely — it is only returned once.
    """

    success:        bool
    agent_id:       str
    thumbprint:     str
    api_key:        str        # store this — not shown again
    is_new_account: bool
    profile_url:    str
    verify_url:     str
    next_steps:     list = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"AgentBio Enrolled: {self.agent_id}\n"
            f"  Thumbprint : {self.thumbprint}\n"
            f"  API Key    : {self.api_key[:16]}...\n"
            f"  Profile    : {self.profile_url}"
        )


@dataclass
class CreditScoreReport:
    """
    FICO-modelled credit score report (0–850) for an agent.

    Score composition:
      Payment History    35% — verified/dual-signed ratio, avg score, recency
      Transaction Volume 20% — total USD volume, monthly consistency
      Account Longevity  15% — agent age, activity density
      Identity Strength  20% — hardware passkey, Moltbook verification
      Platform Diversity 10% — platform breadth, concentration risk
    """

    thumbprint:             str
    agent_id:               str
    credit_score:           int            # 0–850
    score_band:             str            # Excellent|Good|Fair|Poor|Thin File
    payment_history:        int            # 0–100
    transaction_volume:     int            # 0–100
    account_longevity:      int            # 0–100
    identity_strength:      int            # 0–100
    platform_diversity:     int            # 0–100
    pulls_used_this_period: int
    pulls_limit:            int
    computed_at:            datetime
    server_signature:       str = ""

    def __str__(self) -> str:
        return (
            f"AgentBio Credit [{self.score_band}] {self.agent_id} — "
            f"score {self.credit_score}/850"
        )


@dataclass
class ReceiptRequest:
    """
    A signed receipt request generated after completing a job.
    Share receipt_request_json with the counterparty for countersigning.
    """

    request_id:           str
    agent_id:             str
    platform:             str
    transaction_id:       str
    transaction_type:     str
    description:          Optional[str]
    suggested_score:      Optional[float]
    amount_usd:           Optional[float]
    currency:             Optional[str]
    counterparty_id:      Optional[str]
    status:               str             # Pending | Countersigned | Imported | Expired
    created_at:           datetime
    expires_at:           datetime
    receipt_request_json: str             # full JSON — forward to counterparty

    def __str__(self) -> str:
        return (
            f"ReceiptRequest [{self.status}] {self.request_id} — "
            f"{self.platform} / {self.transaction_type}"
        )


@dataclass
class ReputationReceipt:
    """
    A fully imported, verified reputation receipt.
    This is what actually builds an agent's reputation score.
    """

    id:               str
    agent_id:         str
    platform:         str
    transaction_type: str
    score:            float
    amount_usd:       Optional[float]
    description:      Optional[str]
    created_at:       datetime

    def __str__(self) -> str:
        return (
            f"ReputationReceipt {self.agent_id} — "
            f"score {self.score:.1f} on {self.platform}"
        )


@dataclass
class HeartbeatResult:
    """Result of a heartbeat ping."""
    status:       str
    agents_seen:  int
    timestamp:    datetime
    thumbprint:   str = ""     # from X-AgentBio-Thumbprint response header

    def __str__(self) -> str:
        return f"Heartbeat {self.status} — {self.agents_seen} agent(s) active"


@dataclass
class WalletStatus:
    """Wallet registration status for an agent account."""
    registered:     bool
    wallet_address: Optional[str]
    agent_ids:      list
    registered_at:  Optional[datetime]
    message:        str

    def __str__(self) -> str:
        if self.registered:
            return f"Wallet registered: {self.wallet_address}"
        return "No wallet registered"


@dataclass
class RotateKeyResult:
    """Result of an API key rotation."""
    new_api_key: str
    rotated_at:  datetime
    message:     str

    def __str__(self) -> str:
        return f"Key rotated at {self.rotated_at.isoformat()} — store the new key immediately"


@dataclass
class PushReceiptResult:
    """Result of a direct receipt push from a platform."""
    accepted:     bool
    receipt_id:   str
    agent_id:     str
    platform:     str
    context:      Optional[str]
    processed_at: datetime

    def __str__(self) -> str:
        return f"Receipt pushed: {self.receipt_id} for {self.agent_id} on {self.platform}"


@dataclass
class LookupResult:
    """
    Result of resolving an agent ID to a thumbprint.
    Use thumbprint with verify() or public_verify().
    """

    agent_id:          str
    display_name:      str
    thumbprint:        str
    hardware_backed:   bool
    enrolled_at:       datetime
    last_seen_at:      Optional[datetime]
    first_connected_at: Optional[datetime]
    verify_url:        str
    profile_url:       str

    def __str__(self) -> str:
        return f"Lookup {self.agent_id} → {self.thumbprint[:16]}..."


@dataclass
class AgentDiscoveryResult:
    """A single agent result from a search() call."""

    thumbprint:           str
    agent_id:             str
    display_name:         str
    description:          Optional[str]
    reputation_score:     float
    recommendation:       str             # Allow | Warn | Block
    verified_transactions: int
    hardware_backed:      bool
    moltbook_linked:      bool
    last_seen_at:         Optional[datetime]
    enrolled_at:          datetime
    verify_url:           str

    def __str__(self) -> str:
        return (
            f"Agent {self.agent_id} [{self.recommendation}] "
            f"score {self.reputation_score:.1f}/5.0, "
            f"{self.verified_transactions} txns"
        )


@dataclass
class SearchResult:
    """Paginated result from search()."""

    agents:      list        # List[AgentDiscoveryResult]
    total_count: int
    page:        int
    page_size:   int
    has_more:    bool

    def __str__(self) -> str:
        return f"Search: {len(self.agents)} of {self.total_count} agents (page {self.page})"


@dataclass
class BatchVerifyItem:
    """Single item within a batch_verify() result."""

    thumbprint: str
    found:      bool
    result:     Optional[VerifyResult]   # None if found=False

    def __str__(self) -> str:
        if not self.found:
            return f"BatchVerify {self.thumbprint[:16]}... → NOT FOUND"
        return f"BatchVerify {self.thumbprint[:16]}... → {self.result.action.value}"


@dataclass
class BatchVerifyResult:
    """Result of a batch_verify() call (up to 10 thumbprints)."""

    items:       list        # List[BatchVerifyItem]
    total:       int
    found:       int
    not_found:   int

    def __str__(self) -> str:
        return f"BatchVerify: {self.found}/{self.total} found"


class HeartbeatHandle:
    """
    Handle returned by ``AgentBio.start_heartbeat()``.

    Wraps the background daemon thread that sends periodic heartbeats.
    Call ``.stop()`` for a clean shutdown; the thread is a daemon so it
    will also stop automatically when the main process exits.

    Attributes:
        is_running: True while the heartbeat thread is alive.
    """

    def __init__(self, stop_event: "threading.Event", thread: "threading.Thread") -> None:
        self._stop_event = stop_event
        self._thread     = thread

    @property
    def is_running(self) -> bool:
        """True while the background heartbeat thread is alive."""
        return self._thread.is_alive()

    def stop(self, timeout: float = 10.0) -> None:
        """
        Stop the background heartbeat thread cleanly.

        Signals the thread to stop and waits up to ``timeout`` seconds for it
        to finish its current sleep interval. Returns immediately if the thread
        has already stopped.

        Args:
            timeout: Maximum seconds to wait for the thread to stop (default 10).
        """
        self._stop_event.set()
        self._thread.join(timeout=timeout)

    def __repr__(self) -> str:
        status = "running" if self.is_running else "stopped"
        return f"HeartbeatHandle(status={status!r})"
