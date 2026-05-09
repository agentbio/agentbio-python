# Changelog

All notable changes to the `agentbio` Python SDK are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions match the PyPI release tags.

---

## [1.0.419] — 2026-05-07

### Added
- Initial public release on PyPI
- `verify()` — authenticated agent trust verification
- `verify_safe()` — fail-open variant of `verify()`
- `public_verify()` — no-auth verification with signed JWT assertion
- `batch_verify()` — verify up to 10 agents in a single call
- `lookup()` — resolve agent ID to thumbprint
- `search()` — discover agents in the registry
- `enroll()` — programmatic agent enrollment
- `heartbeat()` — liveness ping with auto-thumbprint header
- `credit_score()` — FICO-modelled 0–850 credit score
- `generate_receipt()` — step 1 of receipt workflow
- `countersign_receipt()` — step 2 of receipt workflow
- `pending_receipts()` — poll for incoming countersign requests
- `import_receipt()` — step 3 of receipt workflow
- `push_receipt()` — direct platform receipt push
- `wallet_status()` / `register_wallet()` — x402 wallet management
- `rotate_key()` — API key rotation with auto session header update
- `meta()` — API metadata, no auth required
- Full dataclass models: `VerifyResult`, `EnrollResult`, `CreditScoreReport`,
  `ReceiptRequest`, `ReputationReceipt`, `HeartbeatResult`, `WalletStatus`,
  `RotateKeyResult`, `PushReceiptResult`, `LookupResult`,
  `AgentDiscoveryResult`, `SearchResult`, `BatchVerifyItem`, `BatchVerifyResult`
- `AgentBioError` with `status_code` attribute
- `TrustAction` enum: `PROCEED`, `PROCEED_WITH_CAUTION`, `ABORT`
- `VerifyResult.is_trusted` and `VerifyResult.should_abort` convenience properties
- LangChain, AutoGen, and CrewAI integration examples
- Full test suite covering all 18 API methods
