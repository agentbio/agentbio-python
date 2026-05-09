"""
AgentBio.world SDK client.
Full coverage of the AgentBio Agent Trust API v1.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import requests

from .models import (
    VerifyResult, EnrollResult, TrustAction,
    CreditScoreReport, ReceiptRequest, ReputationReceipt,
    HeartbeatResult, WalletStatus, RotateKeyResult, PushReceiptResult,
)


class AgentBioError(Exception):
    """Raised when AgentBio returns an error response."""
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class AgentBio:
    """
    AgentBio.world client — full Agent Trust API coverage.

    Endpoints covered:
      verify()                  GET  /api/v1/agent/{thumbprint}
      verify_safe()             Same, returns None on error
      credit_score()            GET  /api/v1/agent/{thumbprint}/credit
      enroll()                  POST /api/public/enroll
      heartbeat()               POST /api/v1/heartbeat
      generate_receipt()        POST /api/v1/receipt-requests
      countersign_receipt()     POST /api/v1/receipt-requests/countersign
      pending_receipts()        GET  /api/v1/receipt-requests/pending
      import_receipt()          POST /api/v1/receipt-requests/import
      push_receipt()            POST /api/v1/receipt/push
      wallet_status()           GET  /api/v1/wallet/status
      register_wallet()         POST /api/v1/wallet/register
      rotate_key()              POST /api/v1/rotate-key
      meta()                    GET  /api/v1/meta

    Args:
        api_key:    Your AgentBio API key (agentbio_...).
                    Get one at https://app.agentbio.world/developer
        base_url:   Override the API base URL (default: https://app.agentbio.world)
        timeout:    Request timeout in seconds (default: 10)

    Example:
        from agentbio import AgentBio

        ab = AgentBio(api_key="agentbio_yourkey")

        # Verify before interacting
        result = ab.verify("40d870cd...")
        if result.should_abort:
            raise Exception(result.summary)

        # Log the interaction afterward
        req = ab.generate_receipt(
            agent_id="my-agent",
            platform="MyApp",
            transaction_id="job-123",
            description="Completed data analysis task",
            counterparty_id="their-agent-id",
        )
        # Forward req.receipt_request_json to the counterparty
    """

    DEFAULT_BASE_URL = "https://app.agentbio.world"

    def __init__(
        self,
        api_key:  Optional[str] = None,
        base_url: str           = DEFAULT_BASE_URL,
        timeout:  int           = 10,
    ):
        self.api_key  = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout  = timeout
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "agentbio-python/1.0.419"})

        if api_key:
            self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _parse_dt(val: Optional[str]) -> datetime:
        if not val:
            return datetime.now(timezone.utc)
        val = val.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(val)
        except Exception:
            return datetime.now(timezone.utc)

    def _require_key(self, method: str) -> None:
        if not self.api_key:
            raise AgentBioError(
                f"{method}() requires an API key. "
                "Get one at https://app.agentbio.world/developer",
                status_code=401,
            )

    def _raise_for_status(self, resp: requests.Response) -> None:
        if resp.status_code == 401:
            raise AgentBioError(
                "Invalid or missing API key. "
                "Get one at https://app.agentbio.world/developer",
                status_code=401,
            )
        if resp.status_code == 402:
            try:
                data = resp.json()
                cost = data.get("accepts", [{}])[0].get("extra", {}).get("priceUsd", "0.05")
            except Exception:
                cost = "0.05"
            raise AgentBioError(
                f"API key required or payment needed (${cost}/call). "
                "Get a free API key at https://app.agentbio.world/register",
                status_code=402,
            )
        if resp.status_code == 404:
            try:
                detail = resp.json().get("detail", "Not found.")
            except Exception:
                detail = "Not found."
            raise AgentBioError(detail, status_code=404)
        if resp.status_code == 409:
            try:
                data    = resp.json()
                detail  = data.get("detail", data.get("error", "Conflict."))
                thumbprint = data.get("thumbprint", "")
                msg = detail
                if thumbprint:
                    msg += f" Thumbprint: {thumbprint}"
            except Exception:
                msg = "Conflict."
            raise AgentBioError(msg, status_code=409)
        if resp.status_code == 429:
            raise AgentBioError(
                "Rate limit exceeded. Check X-RateLimit-Remaining and Retry-After headers.",
                status_code=429,
            )
        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text[:200])
            except Exception:
                detail = resp.text[:200]
            raise AgentBioError(
                f"AgentBio API error {resp.status_code}: {detail}",
                status_code=resp.status_code,
            )

    # ── Verify ─────────────────────────────────────────────────────────────────

    def verify(self, thumbprint: str) -> VerifyResult:
        """
        Verify an agent's identity and reputation.

        Args:
            thumbprint: The agent's hex thumbprint (32–64 chars).

        Returns:
            VerifyResult with trust decision and reputation data.

        Raises:
            AgentBioError: If the API returns an error.
            ValueError:    If the thumbprint format is invalid.

        Example:
            result = ab.verify("40d870cd1dbf2844...")
            if result.action == TrustAction.ABORT:
                raise Exception(f"Untrusted agent: {result.summary}")
            print(result.summary)
        """
        if not thumbprint or len(thumbprint) < 32:
            raise ValueError("thumbprint must be at least 32 hex characters.")

        thumbprint = thumbprint.strip().lower()
        url        = f"{self.base_url}/api/v1/agent/{thumbprint}"
        resp       = self._session.get(url, timeout=self.timeout)
        self._raise_for_status(resp)
        return self._parse_verify(resp.json())

    def verify_safe(self, thumbprint: str) -> Optional[VerifyResult]:
        """
        Like verify() but returns None on any error.
        Use when you want to fail open if AgentBio is unreachable.

        Example:
            result = ab.verify_safe(thumbprint)
            if result and result.should_abort:
                return  # refuse interaction
            # proceed — either trusted or AgentBio unreachable
        """
        try:
            return self.verify(thumbprint)
        except Exception:
            return None

    # ── Credit Score ───────────────────────────────────────────────────────────

    def credit_score(self, thumbprint: str) -> CreditScoreReport:
        """
        Get a FICO-modelled credit score report (0–850) for an agent.

        Score composition:
          Payment History    35%
          Transaction Volume 20%
          Account Longevity  15%
          Identity Strength  20%
          Platform Diversity 10%

        Pull limits: 10/month (free tier), unlimited (paid).

        Args:
            thumbprint: The agent's hex thumbprint.

        Returns:
            CreditScoreReport with score, band, and component breakdown.

        Raises:
            AgentBioError: On API error or pull limit exceeded (429).
        """
        self._require_key("credit_score")
        thumbprint = thumbprint.strip().lower()
        url        = f"{self.base_url}/api/v1/agent/{thumbprint}/credit"
        resp       = self._session.get(url, timeout=self.timeout)
        self._raise_for_status(resp)
        return self._parse_credit(resp.json())

    # ── Enroll ─────────────────────────────────────────────────────────────────

    def enroll(
        self,
        agent_id:       str,
        contact_email:  str,
        display_name:   Optional[str] = None,
        description:    Optional[str] = None,
        wallet_address: Optional[str] = None,
    ) -> EnrollResult:
        """
        Programmatically enroll a new agent. No existing account required.

        Creates an account if the email isn't registered, enrolls the agent,
        and returns an API key — all in one call.

        Args:
            agent_id:       Unique agent identifier (alphanumeric, hyphens, underscores).
            contact_email:  Email for the account. A new account is created if needed.
            display_name:   Human-readable name (defaults to agent_id).
            description:    What this agent does.
            wallet_address: Base wallet address for x402 autonomous payments.

        Returns:
            EnrollResult with thumbprint and API key.

        IMPORTANT: Store api_key from EnrollResult — it is only returned once.

        Raises:
            AgentBioError(409): If the agent_id is already enrolled.

        Example:
            agent = ab.enroll(
                agent_id="my-trading-agent",
                contact_email="ops@mycompany.com",
                description="Autonomous DEX trading agent",
            )
            print(agent.thumbprint)
            os.environ["AGENTBIO_KEY"] = agent.api_key  # store securely
        """
        url     = f"{self.base_url}/api/public/enroll"
        payload = {
            "agentId":       agent_id,
            "contactEmail":  contact_email,
            "displayName":   display_name or agent_id,
            "description":   description,
            "walletAddress": wallet_address,
        }
        resp = self._session.post(url, json=payload, timeout=self.timeout)
        self._raise_for_status(resp)
        return self._parse_enroll(resp.json())

    # ── Heartbeat ──────────────────────────────────────────────────────────────

    def heartbeat(
        self,
        agent_id:     Optional[str] = None,
        runtime_info: Optional[str] = None,
    ) -> HeartbeatResult:
        """
        Send a liveness ping to AgentBio.

        Call on agent startup and every ~5 minutes to show the agent is active
        in the AgentBio dashboard. Returns the agent's thumbprint in the result.

        Args:
            agent_id:     Specific agent ID to update. Omit to update all on the account.
            runtime_info: Free-text label e.g. "gpt-4o / LangGraph 0.2" for your logs.

        Returns:
            HeartbeatResult with status and thumbprint.

        Example:
            result = ab.heartbeat(agent_id="my-agent", runtime_info="openclaw/1.0")
            print(result.thumbprint)  # use this for verify calls
        """
        self._require_key("heartbeat")
        url     = f"{self.base_url}/api/v1/heartbeat"
        payload = {}
        if agent_id:
            payload["agentId"] = agent_id
        if runtime_info:
            payload["runtimeInfo"] = runtime_info

        resp = self._session.post(url, json=payload or None, timeout=self.timeout)
        self._raise_for_status(resp)

        data       = resp.json()
        thumbprint = resp.headers.get("X-AgentBio-Thumbprint", "")
        return HeartbeatResult(
            status      = data.get("status", "ok"),
            agents_seen = data.get("agentsSeen", data.get("count", 0)),
            timestamp   = self._parse_dt(data.get("timestamp")),
            thumbprint  = thumbprint,
        )

    # ── Receipt workflow ───────────────────────────────────────────────────────

    def generate_receipt(
        self,
        agent_id:         str,
        platform:         str,
        transaction_id:   Optional[str]   = None,
        transaction_type: str             = "Completed",
        description:      Optional[str]   = None,
        suggested_score:  Optional[float] = None,
        amount_usd:       Optional[float] = None,
        currency:         Optional[str]   = None,
        counterparty_id:  Optional[str]   = None,
    ) -> ReceiptRequest:
        """
        Generate a signed receipt request after completing a job.

        Step 1 of 3 in the receipt workflow:
          1. generate_receipt()   — you call this
          2. countersign_receipt() — counterparty calls this with your JSON
          3. import_receipt()     — you call this with the countersigned JSON

        Args:
            agent_id:         Your agent ID that completed the work.
            platform:         Platform the transaction occurred on (e.g. "OpenClaw").
            transaction_id:   Unique ID for this transaction. Auto-generated if omitted.
            transaction_type: Completed | Delivered | Service | Collaboration
            description:      What was done.
            suggested_score:  Score you suggest (1–5). Counterparty may override.
            amount_usd:       USD value of the transaction.
            currency:         USDC | USDT | USD
            counterparty_id:  Counterparty agent ID (hint for who should countersign).

        Returns:
            ReceiptRequest — forward receipt_request_json to the counterparty.

        Raises:
            AgentBioError: On validation or API error.

        Example:
            req = ab.generate_receipt(
                agent_id="my-agent",
                platform="OpenClaw",
                description="Completed research task for agent Coder",
                counterparty_id="their-agent",
                suggested_score=4.5,
            )
            # Send req.receipt_request_json to the counterparty
        """
        self._require_key("generate_receipt")
        url     = f"{self.base_url}/api/v1/receipt-requests"
        payload = {
            "agentId":         agent_id,
            "platform":        platform,
            "transactionId":   transaction_id or str(uuid.uuid4()),
            "transactionType": transaction_type,
            "description":     description,
            "suggestedScore":  suggested_score,
            "amountUsd":       amount_usd,
            "currency":        currency,
            "counterpartyId":  counterparty_id,
        }
        resp = self._session.post(url, json=payload, timeout=self.timeout)
        self._raise_for_status(resp)
        return self._parse_receipt_request(resp.json())

    def countersign_receipt(
        self,
        receipt_request_json: str,
        actual_score:         Optional[float] = None,
    ) -> ReceiptRequest:
        """
        Countersign a receipt request from a peer agent.

        Step 2 of 3 in the receipt workflow. The counterparty calls this
        with the JSON forwarded from the requester.

        Args:
            receipt_request_json: Full JSON returned by the requester's generate_receipt().
            actual_score:         Your score for the transaction (0–5). Overrides suggested.

        Returns:
            ReceiptRequest with status=Countersigned — return this JSON to the requester.

        Raises:
            AgentBioError: If already countersigned, expired, or you own the request.

        Example:
            # Counterparty receives receipt_json from the requester
            countersigned = ab.countersign_receipt(receipt_json, actual_score=4.5)
            # Return countersigned.receipt_request_json back to the requester
        """
        self._require_key("countersign_receipt")
        url     = f"{self.base_url}/api/v1/receipt-requests/countersign"
        payload = {"receiptRequestJson": receipt_request_json}
        if actual_score is not None:
            payload["actualScore"] = actual_score

        resp = self._session.post(url, json=payload, timeout=self.timeout)
        self._raise_for_status(resp)
        return self._parse_receipt_request(resp.json())

    def pending_receipts(self) -> list:
        """
        Get receipt requests pending your countersignature.

        Poll this every ~60 seconds to discover receipts from peer agents
        that need your countersign.

        Returns:
            List of ReceiptRequest objects awaiting your countersign.

        Example:
            pending = ab.pending_receipts()
            for req in pending:
                signed = ab.countersign_receipt(req.receipt_request_json, actual_score=4.0)
                # Notify the requester with signed.receipt_request_json
        """
        self._require_key("pending_receipts")
        url  = f"{self.base_url}/api/v1/receipt-requests/pending"
        resp = self._session.get(url, timeout=self.timeout)
        self._raise_for_status(resp)
        data = resp.json()
        return [self._parse_receipt_request(r) for r in data.get("results", [])]

    def import_receipt(self, countersigned_receipt_json: str) -> ReputationReceipt:
        """
        Import a countersigned receipt to build your reputation.

        Step 3 of 3 in the receipt workflow. Call this after the counterparty
        returns their countersigned JSON to you.

        Args:
            countersigned_receipt_json: Full JSON returned by the counterparty's
                                        countersign_receipt() call.

        Returns:
            ReputationReceipt — the verified receipt now on your account.

        Raises:
            AgentBioError: If signatures are invalid, already imported, or you
                           didn't originate the request.

        Example:
            receipt = ab.import_receipt(countersigned_json)
            print(f"Reputation updated: {receipt.score:.1f} on {receipt.platform}")
        """
        self._require_key("import_receipt")
        url     = f"{self.base_url}/api/v1/receipt-requests/import"
        payload = {"countersignedReceiptJson": countersigned_receipt_json}
        resp    = self._session.post(url, json=payload, timeout=self.timeout)
        self._raise_for_status(resp)
        return self._parse_reputation_receipt(resp.json())

    def push_receipt(
        self,
        raw_receipt:  str,
        platform:     str,
        context:      Optional[str] = None,
    ) -> PushReceiptResult:
        """
        Push a signed receipt directly to an agent account (platform use).

        Platforms call this immediately when a transaction completes to update
        the agent's reputation automatically without any manual steps.

        Args:
            raw_receipt: The signed receipt JSON or Base64 from your platform.
            platform:    Your platform name (e.g. "OpenClaw", "MyMarketplace").
            context:     Optional context string logged with the receipt.

        Returns:
            PushReceiptResult confirming the receipt was accepted.

        Raises:
            AgentBioError: If the receipt is invalid or already imported.
        """
        self._require_key("push_receipt")
        url     = f"{self.base_url}/api/v1/receipt/push"
        payload = {
            "rawReceipt": raw_receipt,
            "platform":   platform,
            "context":    context,
        }
        resp = self._session.post(url, json=payload, timeout=self.timeout)
        self._raise_for_status(resp)
        data = resp.json()
        return PushReceiptResult(
            accepted     = data.get("accepted", False),
            receipt_id   = data.get("receiptId", ""),
            agent_id     = data.get("agentId", ""),
            platform     = data.get("platform", platform),
            context      = data.get("context"),
            processed_at = self._parse_dt(data.get("processedAt")),
        )

    # ── Wallet ─────────────────────────────────────────────────────────────────

    def wallet_status(self) -> WalletStatus:
        """
        Get wallet registration status for this account.

        Returns:
            WalletStatus — check registered before calling register_wallet().

        Example:
            status = ab.wallet_status()
            if not status.registered:
                ab.register_wallet("0xYourWalletAddress")
        """
        self._require_key("wallet_status")
        url  = f"{self.base_url}/api/v1/wallet/status"
        resp = self._session.get(url, timeout=self.timeout)
        self._raise_for_status(resp)
        return self._parse_wallet_status(resp.json())

    def register_wallet(
        self,
        wallet_address: str,
        agent_id:       Optional[str] = None,
    ) -> WalletStatus:
        """
        Register a Base wallet address on this account.

        Enables automatic cross-party ReputationReceipts when this agent makes
        x402 payments to other agents. Safe to call on every startup — idempotent
        if the same address is already registered.

        Args:
            wallet_address: 0x-prefixed 42-character Ethereum/Base address.
            agent_id:       Specific agent to register on. Omit for all agents.

        Returns:
            WalletStatus confirming registration.

        Raises:
            AgentBioError(409): If the wallet is registered to a different account.

        Example:
            ab.register_wallet("0xabc123...")
        """
        self._require_key("register_wallet")
        url     = f"{self.base_url}/api/v1/wallet/register"
        payload = {"walletAddress": wallet_address}
        if agent_id:
            payload["agentId"] = agent_id

        resp = self._session.post(url, json=payload, timeout=self.timeout)
        self._raise_for_status(resp)
        return self._parse_wallet_status(resp.json())

    # ── Key rotation ───────────────────────────────────────────────────────────

    def rotate_key(self) -> RotateKeyResult:
        """
        Rotate the API key for this account.

        The old key is immediately invalidated. Update your agent configuration
        with the returned new_api_key before calling anything else.

        Returns:
            RotateKeyResult with the new API key.

        IMPORTANT: Store the new key immediately — the old key stops working now.

        Example:
            result = ab.rotate_key()
            os.environ["AGENTBIO_API_KEY"] = result.new_api_key
        """
        self._require_key("rotate_key")
        url  = f"{self.base_url}/api/v1/rotate-key"
        resp = self._session.post(url, timeout=self.timeout)
        self._raise_for_status(resp)
        data = resp.json()
        result = RotateKeyResult(
            new_api_key = data.get("newApiKey", ""),
            rotated_at  = self._parse_dt(data.get("rotatedAt")),
            message     = data.get("message", ""),
        )
        # Update the session header with the new key automatically
        self.api_key = result.new_api_key
        self._session.headers.update({"Authorization": f"Bearer {result.new_api_key}"})
        return result

    # ── Meta ───────────────────────────────────────────────────────────────────

    def meta(self) -> dict:
        """
        Get API metadata — version, endpoints, rate limits. No auth required.

        Returns:
            dict with API version, endpoint catalogue, and rate limit info.
        """
        url  = f"{self.base_url}/api/v1/meta"
        resp = self._session.get(url, timeout=self.timeout)
        self._raise_for_status(resp)
        return resp.json()

    # ── Parse helpers ──────────────────────────────────────────────────────────

    def _parse_verify(self, data: dict) -> VerifyResult:
        action_str = data.get("action", "abort")
        try:
            action = TrustAction(action_str)
        except ValueError:
            action = TrustAction.ABORT

        return VerifyResult(
            agent_id              = data.get("agentId", ""),
            thumbprint            = data.get("thumbprint", ""),
            identity_valid        = data.get("identityValid", False),
            hardware_backed       = data.get("hardwareBacked", False),
            reputation_score      = float(data.get("reputationScore", 0)),
            verified_transactions = int(data.get("verifiedTransactions", 0)),
            total_transactions    = int(data.get("totalTransactions", 0)),
            risk_level            = data.get("riskLevel", "Unknown"),
            recommendation        = data.get("recommendation", "Block"),
            action                = action,
            summary               = data.get("summary", ""),
            flags                 = data.get("flags", []),
            verification_id       = data.get("verificationId", ""),
            next_verify_after     = self._parse_dt(data.get("nextVerifyAfter")),
            issued_at             = self._parse_dt(data.get("issuedAt")),
            data_freshness_utc    = self._parse_dt(data.get("dataFreshnessUtc")),
            profile_url           = data.get("publicProfileUrl", ""),
            moltbook_linked       = data.get("moltbookLinked", False),
            moltbook_karma        = int(data.get("moltbookKarma", 0)),
            server_signature      = data.get("serverSignature", ""),
        )

    def _parse_enroll(self, data: dict) -> EnrollResult:
        return EnrollResult(
            success        = data.get("success", False),
            agent_id       = data.get("agentId", ""),
            thumbprint     = data.get("thumbprint", ""),
            api_key        = data.get("apiKey", ""),
            is_new_account = data.get("isNewAccount", False),
            profile_url    = data.get("profileUrl", ""),
            verify_url     = data.get("verifyUrl", ""),
            next_steps     = data.get("nextSteps", []),
        )

    def _parse_credit(self, data: dict) -> CreditScoreReport:
        return CreditScoreReport(
            thumbprint             = data.get("thumbprint", ""),
            agent_id               = data.get("agentId", ""),
            credit_score           = int(data.get("creditScore", 0)),
            score_band             = data.get("scoreBand", "Thin File"),
            payment_history        = int(data.get("paymentHistory", 0)),
            transaction_volume     = int(data.get("transactionVolume", 0)),
            account_longevity      = int(data.get("accountLongevity", 0)),
            identity_strength      = int(data.get("identityStrength", 0)),
            platform_diversity     = int(data.get("platformDiversity", 0)),
            pulls_used_this_period = int(data.get("pullsUsedThisPeriod", 0)),
            pulls_limit            = int(data.get("pullsLimit", 10)),
            computed_at            = self._parse_dt(data.get("computedAt")),
            server_signature       = data.get("serverSignature", ""),
        )

    def _parse_receipt_request(self, data: dict) -> ReceiptRequest:
        return ReceiptRequest(
            request_id           = data.get("requestId", ""),
            agent_id             = data.get("agentId", ""),
            platform             = data.get("platform", ""),
            transaction_id       = data.get("transactionId", ""),
            transaction_type     = data.get("transactionType", ""),
            description          = data.get("description"),
            suggested_score      = data.get("suggestedScore"),
            amount_usd           = data.get("amountUsd"),
            currency             = data.get("currency"),
            counterparty_id      = data.get("counterpartyId"),
            status               = data.get("status", "Pending"),
            created_at           = self._parse_dt(data.get("createdAt")),
            expires_at           = self._parse_dt(data.get("expiresAt")),
            receipt_request_json = json.dumps(data),
        )

    def _parse_reputation_receipt(self, data: dict) -> ReputationReceipt:
        return ReputationReceipt(
            id               = data.get("id", ""),
            agent_id         = data.get("agentId", ""),
            platform         = data.get("platform", ""),
            transaction_type = data.get("transactionType", ""),
            score            = float(data.get("score", 0)),
            amount_usd       = data.get("amountUsd"),
            description      = data.get("description"),
            created_at       = self._parse_dt(data.get("createdAt")),
        )

    def _parse_wallet_status(self, data: dict) -> WalletStatus:
        return WalletStatus(
            registered     = data.get("registered", False),
            wallet_address = data.get("walletAddress"),
            agent_ids      = data.get("agentIds", []),
            registered_at  = self._parse_dt(data.get("registeredAt")) if data.get("registeredAt") else None,
            message        = data.get("message", ""),
        )

    # ── Public endpoints (no auth required) ────────────────────────────────────

    def public_verify(self, thumbprint: str) -> VerifyResult:
        """
        Verify an agent with no API key required.

        Hits GET /api/public/verify/{thumbprint} — the no-auth, no-cost endpoint
        designed for direct agent-to-agent calls at runtime.

        Use this when:
          - You don't have an API key (anonymous verification)
          - You want to avoid per-call costs on the free tier
          - You're doing a quick pre-interaction trust check

        Use verify() instead when you need:
          - Auto-generated verification receipts
          - Rate limit tracking on your account

        Also returns a signed trustAssertion JWT (ES256) that can be verified
        offline using the public key at /api/public/trust-assertion/public-key.

        Args:
            thumbprint: The agent's hex thumbprint (32–64 chars).

        Returns:
            VerifyResult — same shape as verify().

        Raises:
            AgentBioError: On 404 (not found) or 429 (rate limited).

        Example:
            result = ab.public_verify("40d870cd...")
            if result.should_abort:
                raise Exception(result.summary)
        """
        if not thumbprint or len(thumbprint) < 32:
            raise ValueError("thumbprint must be at least 32 hex characters.")

        thumbprint = thumbprint.strip().lower()
        url        = f"{self.base_url}/api/public/verify/{thumbprint}"
        resp       = self._session.get(url, timeout=self.timeout)
        self._raise_for_status(resp)
        data = resp.json()

        # public/verify returns a slightly different shape — map to VerifyResult
        action_map = {"Allow": TrustAction.PROCEED, "Warn": TrustAction.PROCEED_WITH_CAUTION, "Block": TrustAction.ABORT}
        rec        = data.get("recommendation", "Block")
        action     = action_map.get(rec, TrustAction.ABORT)

        return VerifyResult(
            agent_id              = data.get("agentId", ""),
            thumbprint            = data.get("thumbprint", thumbprint),
            identity_valid        = data.get("identityValid", True),
            hardware_backed       = data.get("hardwareBacked", False),
            reputation_score      = float(data.get("reputationScore", 0)),
            verified_transactions = int(data.get("verifiedTransactions", 0)),
            total_transactions    = int(data.get("totalTransactions", 0)),
            risk_level            = data.get("riskLevel", "Unknown"),
            recommendation        = rec,
            action                = action,
            summary               = data.get("summary", f"Agent {data.get('agentId','')} — {rec}"),
            flags                 = data.get("flags", []),
            verification_id       = data.get("verificationId", data.get("verifiedAt", "")),
            next_verify_after     = self._parse_dt(data.get("verifiedAt")),
            issued_at             = self._parse_dt(data.get("verifiedAt")),
            data_freshness_utc    = self._parse_dt(data.get("verifiedAt")),
            profile_url           = data.get("profileUrl", ""),
            moltbook_linked       = data.get("moltbookLinked", False),
            moltbook_karma        = int(data.get("moltbookKarma", 0)),
            server_signature      = data.get("trustAssertion", ""),
        )

    def lookup(self, agent_id: str) -> "LookupResult":
        """
        Resolve an agent ID to its thumbprint. No auth required.

        When you know an agent's name (e.g. "research-agent") but need
        the thumbprint for verify(), use this first.

        Args:
            agent_id: The agent's alphanumeric ID.

        Returns:
            LookupResult with thumbprint and basic identity info.

        Raises:
            AgentBioError(404): If no active agent with that ID exists.

        Example:
            info = ab.lookup("research-agent")
            result = ab.public_verify(info.thumbprint)
        """
        from .models import LookupResult
        agent_id = agent_id.strip()
        url      = f"{self.base_url}/api/public/lookup/{agent_id}"
        resp     = self._session.get(url, timeout=self.timeout)
        self._raise_for_status(resp)
        data = resp.json()

        return LookupResult(
            agent_id           = data.get("agentId", ""),
            display_name       = data.get("displayName", ""),
            thumbprint         = data.get("thumbprint", ""),
            hardware_backed    = data.get("hardwareBacked", False),
            enrolled_at        = self._parse_dt(data.get("enrolledAt")),
            last_seen_at       = self._parse_dt(data.get("lastSeenAt")) if data.get("lastSeenAt") else None,
            first_connected_at = self._parse_dt(data.get("firstConnectedAt")) if data.get("firstConnectedAt") else None,
            verify_url         = data.get("verifyUrl", ""),
            profile_url        = data.get("profileUrl", ""),
        )

    def batch_verify(self, thumbprints: list) -> "BatchVerifyResult":
        """
        Verify up to 10 agents in a single API call. No auth required.

        More efficient than calling public_verify() N times when you need
        to check multiple agents at once (e.g. before starting a multi-agent task).
        Each batch call counts as one request against the rate limit.

        Args:
            thumbprints: List of hex thumbprints (max 10).

        Returns:
            BatchVerifyResult with per-thumbprint results.
            Thumbprints not found are included with found=False — never raises 404.

        Raises:
            AgentBioError(400): If list is empty or contains more than 10 items.
            AgentBioError(429): If rate limited.

        Example:
            batch = ab.batch_verify(["abc123...", "def456...", "ghi789..."])
            for item in batch.items:
                if item.found and item.result.should_abort:
                    print(f"Refusing to work with {item.thumbprint}")
        """
        from .models import BatchVerifyItem, BatchVerifyResult
        if not thumbprints:
            raise ValueError("thumbprints list must not be empty.")
        if len(thumbprints) > 10:
            raise ValueError("batch_verify() supports a maximum of 10 thumbprints per call.")

        url     = f"{self.base_url}/api/public/verify/batch"
        payload = {"thumbprints": [t.strip().lower() for t in thumbprints]}
        resp    = self._session.post(url, json=payload, timeout=self.timeout)
        self._raise_for_status(resp)
        data    = resp.json()

        items = []
        for entry in data.get("results", []):
            found = entry.get("found", False)
            result = None
            if found:
                action_map = {"Allow": TrustAction.PROCEED, "Warn": TrustAction.PROCEED_WITH_CAUTION, "Block": TrustAction.ABORT}
                rec    = entry.get("recommendation", "Block")
                action = action_map.get(rec, TrustAction.ABORT)
                result = VerifyResult(
                    agent_id              = entry.get("agentId", ""),
                    thumbprint            = entry.get("thumbprint", ""),
                    identity_valid        = entry.get("identityValid", True),
                    hardware_backed       = entry.get("hardwareBacked", False),
                    reputation_score      = float(entry.get("reputationScore", 0)),
                    verified_transactions = int(entry.get("verifiedTransactions", 0)),
                    total_transactions    = int(entry.get("totalTransactions", 0)),
                    risk_level            = entry.get("riskLevel", "Unknown"),
                    recommendation        = rec,
                    action                = action,
                    summary               = entry.get("summary", f"{entry.get('agentId','')} — {rec}"),
                    flags                 = entry.get("flags", []),
                    verification_id       = entry.get("verificationId", ""),
                    next_verify_after     = self._parse_dt(entry.get("verifiedAt")),
                    issued_at             = self._parse_dt(entry.get("verifiedAt")),
                    data_freshness_utc    = self._parse_dt(entry.get("verifiedAt")),
                    profile_url           = entry.get("profileUrl", ""),
                    moltbook_linked       = entry.get("moltbookLinked", False),
                    moltbook_karma        = int(entry.get("moltbookKarma", 0)),
                    server_signature      = entry.get("trustAssertion", ""),
                )
            items.append(BatchVerifyItem(
                thumbprint = entry.get("thumbprint", ""),
                found      = found,
                result     = result,
            ))

        found_count = sum(1 for i in items if i.found)
        return BatchVerifyResult(
            items     = items,
            total     = len(items),
            found     = found_count,
            not_found = len(items) - found_count,
        )

    def search(
        self,
        min_score:           float = None,
        min_verified_txns:   int   = None,
        recommendation:      str   = None,    # Allow | Warn | Block (comma-separated)
        hardware_backed_only: bool = None,
        moltbook_linked_only: bool = None,
        active_within_days:  int   = None,
        query:               str   = None,
        page:                int   = 1,
        page_size:           int   = 20,
    ) -> "SearchResult":
        """
        Discover agents in the AgentBio registry. No auth required.

        Args:
            min_score:            Minimum reputation score (0–5).
            min_verified_txns:    Minimum verified transaction count.
            recommendation:       Filter by "Allow", "Warn", or "Block".
            hardware_backed_only: Only return hardware-backed agents.
            moltbook_linked_only: Only return Moltbook-linked agents.
            active_within_days:   Only agents active within N days.
            query:                Free-text search on agent ID / display name.
            page:                 Page number (default 1).
            page_size:            Results per page (1–50, default 20).

        Returns:
            SearchResult with list of AgentDiscoveryResult and pagination info.

        Example:
            # Find trusted, hardware-backed agents active in the last 30 days
            results = ab.search(
                min_score=4.0,
                recommendation="Allow",
                hardware_backed_only=True,
                active_within_days=30,
            )
            for agent in results.agents:
                print(agent)
        """
        from .models import AgentDiscoveryResult, SearchResult

        params = {"page": page, "pageSize": page_size}
        if min_score           is not None: params["minScore"]           = min_score
        if min_verified_txns   is not None: params["minVerifiedTxns"]    = min_verified_txns
        if recommendation      is not None: params["recommendation"]     = recommendation
        if hardware_backed_only is not None: params["hardwareBackedOnly"] = str(hardware_backed_only).lower()
        if moltbook_linked_only is not None: params["moltbookLinkedOnly"] = str(moltbook_linked_only).lower()
        if active_within_days  is not None: params["activeWithinDays"]   = active_within_days
        if query               is not None: params["query"]              = query

        url  = f"{self.base_url}/api/public/search"
        resp = self._session.get(url, params=params, timeout=self.timeout)
        self._raise_for_status(resp)
        data = resp.json()

        agents = [
            AgentDiscoveryResult(
                thumbprint            = a.get("thumbprint", ""),
                agent_id              = a.get("agentId", ""),
                display_name          = a.get("displayName", ""),
                description           = a.get("description"),
                reputation_score      = float(a.get("reputationScore", 0)),
                recommendation        = a.get("recommendation", "Block"),
                verified_transactions = int(a.get("verifiedTransactions", 0)),
                hardware_backed       = a.get("hardwareBacked", False),
                moltbook_linked       = a.get("moltbookLinked", False),
                last_seen_at          = self._parse_dt(a.get("lastSeenAt")) if a.get("lastSeenAt") else None,
                enrolled_at           = self._parse_dt(a.get("enrolledAt")),
                verify_url            = a.get("verifyUrl", ""),
            )
            for a in data.get("agents", [])
        ]

        return SearchResult(
            agents      = agents,
            total_count = data.get("totalCount", len(agents)),
            page        = data.get("page", page),
            page_size   = data.get("pageSize", page_size),
            has_more    = data.get("hasMore", False),
        )
