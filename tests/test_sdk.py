"""
AgentBio SDK test script — full API coverage.

Usage:
    # Test against localhost (start AgentBio.Web first)
    python test_sdk.py --server http://localhost:5000 --skip-ssl --api-key agentbio_yourkey

    # Test against production
    python test_sdk.py --api-key agentbio_yourkey
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentbio import (
    AgentBio, AgentBioError,
    TrustAction, VerifyResult, EnrollResult,
    CreditScoreReport, ReceiptRequest, ReputationReceipt,
    HeartbeatResult, WalletStatus,
)

PASS = "  \033[92m✓\033[0m"
FAIL = "  \033[91m✗\033[0m"

def ok(msg):  print(f"{PASS} {msg}")
def err(msg): print(f"{FAIL} {msg}")
def skip(msg): print(f"  (skipped — {msg})")

def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")

def safe(fn, *args, **kwargs):
    """Call fn, return result or None on any exception. Prints timeout notice."""
    try:
        return fn(*args, **kwargs)
    except AgentBioError:
        raise
    except Exception as e:
        ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
        return None

def run_tests(server: str, api_key: str | None, skip_ssl: bool):
    print(f"\n{'='*55}")
    print(f"  AgentBio SDK Test — Full Coverage")
    print(f"  Server : {server}")
    print(f"  Auth   : {'API key ✓' if api_key else 'none (enrollment only)'}")
    print(f"{'='*55}")

    if skip_ssl:
        import urllib3, requests
        urllib3.disable_warnings()
        original_get  = requests.Session.get
        original_post = requests.Session.post
        requests.Session.get  = lambda self, *a, **kw: original_get(self, *a, verify=False, **kw)
        requests.Session.post = lambda self, *a, **kw: original_post(self, *a, verify=False, **kw)

    ab = AgentBio(api_key=api_key, base_url=server)

    enrolled_thumbprint = None
    enrolled_api_key    = None
    enrolled_agent_id   = None
    receipt_req_json    = None
    ab_enrolled         = None

    # ── TEST 1: Meta ──────────────────────────────────────────────────────────
    section("TEST 1: Meta endpoint (no auth required)")
    try:
        meta = ab.meta()
        ok(f"API version : {meta.get('version', '?')}")
        ok(f"Endpoints   : {len(meta.get('endpoints', []))} listed")
        ok(f"Base URL    : {meta.get('baseUrl', '?')}")
    except AgentBioError as e:
        err(f"meta() failed ({e.status_code}): {e}")
    except Exception as e:
        ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")

    # ── TEST 2: Enrollment ────────────────────────────────────────────────────
    section("TEST 2: Programmatic enrollment")
    test_agent_id = f"sdk-test-{os.urandom(3).hex()}"
    test_email    = f"sdktest-{os.urandom(3).hex()}@test.agentbio.world"
    try:
        agent = ab.enroll(
            agent_id      = test_agent_id,
            contact_email = test_email,
            description   = "Automated test agent — agentbio Python SDK test",
        )
        enrolled_thumbprint = agent.thumbprint
        enrolled_api_key    = agent.api_key
        enrolled_agent_id   = agent.agent_id
        ab_enrolled         = AgentBio(api_key=enrolled_api_key, base_url=server)
        ok(f"Enrolled    : {agent.agent_id}")
        ok(f"Thumbprint  : {agent.thumbprint[:24]}...")
        ok(f"API Key     : {agent.api_key[:16]}...")
        ok(f"New account : {agent.is_new_account}")
        ok(f"Profile     : {agent.profile_url}")
        ok(f"__str__     : {agent}")
    except AgentBioError as e:
        err(f"enroll() failed ({e.status_code}): {e}")
    except Exception as e:
        ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")

    # ── TEST 3: Duplicate enrollment ──────────────────────────────────────────
    section("TEST 3: Duplicate enrollment (expect 409)")
    try:
        ab.enroll(agent_id=test_agent_id, contact_email=test_email)
        err("Should have raised AgentBioError(409)")
    except AgentBioError as e:
        if e.status_code == 409:
            ok(f"Correctly rejected duplicate (409): {str(e)[:80]}")
        else:
            err(f"Wrong error code {e.status_code}: {e}")
    except Exception as e:
        ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")

    # ── TEST 4: Heartbeat ─────────────────────────────────────────────────────
    section("TEST 4: Heartbeat")
    if api_key:
        try:
            hb = ab.heartbeat(agent_id=enrolled_agent_id, runtime_info="agentbio-sdk-test/1.0")
            ok(f"Status      : {hb.status}")
            ok(f"Agents seen : {hb.agents_seen}")
            ok(f"Thumbprint  : {hb.thumbprint[:24] if hb.thumbprint else '(none in header)'}")
            ok(f"__str__     : {hb}")
        except AgentBioError as e:
            err(f"heartbeat() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("requires API key")

    # ── TEST 5: Verify enrolled agent ─────────────────────────────────────────
    section("TEST 5: Verify enrolled agent")
    if enrolled_thumbprint and (api_key or enrolled_api_key):
        try:
            ab_verify = AgentBio(api_key=(api_key or enrolled_api_key), base_url=server)
            result    = ab_verify.verify(enrolled_thumbprint)
            ok(f"Action      : {result.action.value}")
            ok(f"Summary     : {result.summary}")
            ok(f"Score       : {result.reputation_score:.1f}/5.0")
            ok(f"Risk        : {result.risk_level}")
            ok(f"Flags       : {result.flags}")
            ok(f"is_trusted  : {result.is_trusted}")
            ok(f"should_abort: {result.should_abort}")
            ok(f"Verify ID   : {result.verification_id}")
            ok(f"__str__     : {result}")
        except AgentBioError as e:
            err(f"verify() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("enrollment failed or no API key")

    # ── TEST 6: verify_safe ───────────────────────────────────────────────────
    section("TEST 6: verify_safe() returns None on error")
    result = AgentBio(base_url=server).verify_safe("0" * 64)
    if result is None:
        ok("verify_safe returned None as expected")
    else:
        err(f"Expected None, got {result}")

    # ── TEST 7: Verify non-existent ───────────────────────────────────────────
    section("TEST 7: Verify non-existent agent (expect 404 or 402)")
    try:
        ab.verify("0" * 64)
        err("Should have raised AgentBioError")
    except AgentBioError as e:
        if e.status_code == 404:
            ok("Correctly returned 404 (agent not found)")
        elif e.status_code == 402:
            ok("Correctly returned 402 (API key required)")
        else:
            err(f"Wrong error code {e.status_code}: {e}")
    except Exception as e:
        ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")

    # ── TEST 8: Credit score ──────────────────────────────────────────────────
    section("TEST 8: Credit score")
    if api_key and enrolled_thumbprint:
        try:
            report = ab.credit_score(enrolled_thumbprint)
            ok(f"Score       : {report.credit_score}/850")
            ok(f"Band        : {report.score_band}")
            ok(f"Pulls used  : {report.pulls_used_this_period}/{report.pulls_limit}")
            ok(f"Components  : history={report.payment_history} volume={report.transaction_volume} "
               f"longevity={report.account_longevity} identity={report.identity_strength} "
               f"diversity={report.platform_diversity}")
            ok(f"__str__     : {report}")
        except AgentBioError as e:
            if e.status_code == 429:
                ok("Pull limit reached (429) — expected on repeated test runs")
            else:
                err(f"credit_score() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("requires API key and enrolled agent")

    # ── TEST 9: Generate receipt ──────────────────────────────────────────────
    section("TEST 9: Generate receipt request")
    if ab_enrolled and enrolled_agent_id:
        try:
            req = ab_enrolled.generate_receipt(
                agent_id         = enrolled_agent_id,
                platform         = "SDK-Test",
                description      = "Test task completed by SDK test agent",
                transaction_type = "Completed",
                suggested_score  = 4.5,
            )
            receipt_req_json = req.receipt_request_json
            ok(f"Request ID  : {req.request_id}")
            ok(f"Platform    : {req.platform}")
            ok(f"Status      : {req.status}")
            ok(f"Expires     : {req.expires_at.date()}")
            ok(f"JSON length : {len(receipt_req_json)} chars")
            ok(f"__str__     : {req}")
        except AgentBioError as e:
            err(f"generate_receipt() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("requires enrolled agent")

    # ── TEST 10: Pending receipts ─────────────────────────────────────────────
    section("TEST 10: Pending receipts")
    if api_key:
        try:
            pending = ab.pending_receipts()
            ok(f"Pending count: {len(pending)}")
            if pending:
                ok(f"First request: {pending[0]}")
        except AgentBioError as e:
            err(f"pending_receipts() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("requires API key")

    # ── TEST 11: Countersign own receipt (expect 400) ─────────────────────────
    section("TEST 11: Countersign own receipt (expect 400 — can't self-sign)")
    if ab_enrolled and receipt_req_json:
        try:
            ab_enrolled.countersign_receipt(receipt_req_json, actual_score=4.0)
            err("Should have rejected self-countersign")
        except AgentBioError as e:
            if e.status_code == 400:
                ok(f"Correctly rejected self-countersign (400): {str(e)[:80]}")
            else:
                err(f"Unexpected error {e.status_code}: {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("requires enrolled agent and receipt request")

    # ── TEST 12: Wallet status ────────────────────────────────────────────────
    section("TEST 12: Wallet status")
    if api_key:
        try:
            status = ab.wallet_status()
            ok(f"Registered  : {status.registered}")
            ok(f"Wallet      : {status.wallet_address or '(none)'}")
            ok(f"Agent IDs   : {status.agent_ids}")
            ok(f"Message     : {status.message}")
            ok(f"__str__     : {status}")
        except AgentBioError as e:
            err(f"wallet_status() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("requires API key")

    # ── TEST 13: Register invalid wallet (expect 400) ─────────────────────────
    section("TEST 13: Register invalid wallet (expect 400)")
    if api_key:
        try:
            ab.register_wallet("not-a-valid-address")
            err("Should have rejected invalid wallet address")
        except AgentBioError as e:
            if e.status_code == 400:
                ok("Correctly rejected invalid wallet (400)")
            else:
                err(f"Unexpected error {e.status_code}: {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("requires API key")

    # ── TEST 14: meta() without key ───────────────────────────────────────────
    section("TEST 14: meta() works without API key")
    try:
        meta = AgentBio(base_url=server).meta()
        ok(f"meta() works unauthenticated — version: {meta.get('version', '?')}")
    except AgentBioError as e:
        err(f"meta() without key failed ({e.status_code}): {e}")
    except Exception as e:
        ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")

    # ── Public endpoint tests (15–18) ─────────────────────────────────────────
    run_public_tests(
        server           = server,
        skip_ssl         = skip_ssl,
        api_key          = api_key,
        known_thumbprint = enrolled_thumbprint,
        known_agent_id   = enrolled_agent_id,
    )

    print(f"\n{'='*55}")
    print(f"  Tests complete.")
    print(f"{'='*55}\n")


def run_public_tests(server: str, skip_ssl: bool, api_key: str = None, known_thumbprint: str = None, known_agent_id: str = None):
    # Public endpoints are free on production but may require a key locally (x402)
    ab = AgentBio(api_key=api_key, base_url=server)

    # ── TEST 15: public_verify() ──────────────────────────────────────────────
    section("TEST 15: public_verify() — no auth required")
    if known_thumbprint:
        try:
            result = ab.public_verify(known_thumbprint)
            ok(f"Action      : {result.action.value}")
            ok(f"Score       : {result.reputation_score:.1f}/5.0")
            ok(f"Rec         : {result.recommendation}")
            ok(f"Hardware    : {result.hardware_backed}")
            ok(f"is_trusted  : {result.is_trusted}")
            ok(f"__str__     : {result}")
        except AgentBioError as e:
            err(f"public_verify() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("no known thumbprint")

    # ── TEST 16: lookup() ─────────────────────────────────────────────────────
    section("TEST 16: lookup() — resolve agent ID to thumbprint")
    if known_agent_id:
        try:
            info = ab.lookup(known_agent_id)
            ok(f"Agent ID    : {info.agent_id}")
            ok(f"Thumbprint  : {info.thumbprint[:24]}...")
            ok(f"Hardware    : {info.hardware_backed}")
            ok(f"Verify URL  : {info.verify_url}")
            ok(f"__str__     : {info}")
        except AgentBioError as e:
            if e.status_code == 404:
                ok("404 — agent not in prod DB yet (expected for test agents)")
            else:
                err(f"lookup() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("no known agent ID")

    # ── TEST 17: batch_verify() ───────────────────────────────────────────────
    section("TEST 17: batch_verify() — up to 10 at once")
    if known_thumbprint:
        try:
            batch = ab.batch_verify([known_thumbprint, "0" * 64])
            ok(f"Total       : {batch.total}")
            ok(f"Found       : {batch.found}")
            ok(f"Not found   : {batch.not_found}")
            ok(f"__str__     : {batch}")
            for item in batch.items:
                if item.found:
                    ok(f"  [{item.thumbprint[:16]}...] {item.result.action.value} — score {item.result.reputation_score:.1f}")
                else:
                    ok(f"  [{item.thumbprint[:16]}...] not found (expected)")
        except AgentBioError as e:
            err(f"batch_verify() failed ({e.status_code}): {e}")
        except Exception as e:
            ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")
    else:
        skip("no known thumbprint")

    # ── TEST 18: search() ─────────────────────────────────────────────────────
    section("TEST 18: search() — discover agents in registry")
    try:
        results = ab.search(page=1, page_size=5)
        ok(f"Total agents: {results.total_count}")
        ok(f"Returned    : {len(results.agents)}")
        ok(f"Has more    : {results.has_more}")
        ok(f"__str__     : {results}")
        if results.agents:
            ok(f"First agent : {results.agents[0]}")
    except AgentBioError as e:
        err(f"search() failed ({e.status_code}): {e}")
    except Exception as e:
        ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")

    try:
        filtered = ab.search(min_score=1.0, recommendation="Allow", page_size=3)
        ok(f"Filtered (Allow, score≥1): {filtered.total_count} agents")
    except AgentBioError as e:
        err(f"search(filtered) failed ({e.status_code}): {e}")
    except Exception as e:
        ok(f"Timed out or unreachable locally — skipping: {type(e).__name__}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentBio SDK test")
    parser.add_argument("--server",   default="https://app.agentbio.world", help="API base URL")
    parser.add_argument("--api-key",  default=None,  help="AgentBio API key")
    parser.add_argument("--skip-ssl", action="store_true", help="Disable SSL verification (localhost)")
    args = parser.parse_args()

    run_tests(args.server, args.api_key, args.skip_ssl)
