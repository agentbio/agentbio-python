# Changelog

All notable changes to the `agentbio` Python SDK are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions match the PyPI release tags.

---

## [1.1.5] — 2026-05-12

### Added
- `get_auto_countersign_policy()` — read auto-countersign enabled/minScore settings.
- `set_auto_countersign_policy(enabled, min_score)` — configure autonomous receipt countersigning threshold.
- `get_auto_dispute_policy()` — read auto-dispute enabled setting.
- `set_auto_dispute_policy(enabled)` — enable/disable automatic dispute filing against High-severity anomaly flags.
- `get_succession_policy(agent_id)` — read an agent's auto-succession configuration including offline days.
- `set_succession_policy(agent_id, enabled, successor_agent_id, trigger_days)` — configure autonomous succession: when the agent goes offline for `trigger_days` consecutive days, reputation lineage is automatically transferred to the designated successor.

---

## [1.1.4] — 2026-05-11

### Fixed
- Removed SVG robot and `<style>` block from README — PyPI strips these tags causing raw HTML to display instead of the intended layout. README now renders correctly on both PyPI and GitHub.

---

## [1.1.3] — 2026-05-09

### Added
- `enroll_or_load(agent_id, contact_email, key_env, ...)` — enroll on first boot, load existing key on every subsequent boot. Eliminates the most common beginner error (crashing on 409 when already enrolled).
- `start_heartbeat(agent_id, interval_minutes, ...)` → `HeartbeatHandle` — starts a daemon background thread that pings AgentBio automatically every N minutes. No polling loop required. Call `.stop()` for clean shutdown.
- `HeartbeatHandle` model — returned by `start_heartbeat()`. Has `.is_running` property and `.stop(timeout)` method.

---

## [1.1.2] — 2026-05-09

### Added
- `get_auto_countersign_policy()` — read the current auto-countersign policy
- `set_auto_countersign_policy(enabled, min_score)` — configure server-side autonomous receipt countersigning. Enabled by default — agents build reputation with zero extra code.

---

## [1.1.1] — 2026-05-08

### Fixed
- `agentbio info` CLI command now formats rate limits cleanly instead of displaying raw JSON objects.

---

## [1.1.0] — 2026-05-08

### Added
- Full CLI: `agentbio verify`, `enroll`, `heartbeat`, `search`, `credit`, `pay`, `info`, `key rotate`
- `agentbio pay --thumbprint ... --key ... --testnet` — full x402 test payment flow on Base Sepolia
- `python -m agentbio` module entry point
- `console_scripts` entry point — `agentbio` command available after `pip install agentbio`
- `eth-account` optional dependency via `pip install agentbio[pay]`

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
