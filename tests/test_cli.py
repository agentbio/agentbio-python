"""
AgentBio CLI Test Suite
========================
Tests every CLI command using unittest.mock — no network calls, no API key required.

Run:
    python -m pytest tests/test_cli.py -v
    # or
    python tests/test_cli.py
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from io import StringIO

# Allow running from the repo root or from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentbio.cli  import main, _build_parser
from agentbio.models import (
    TrustAction, VerifyResult, EnrollResult, CreditScoreReport,
    HeartbeatResult, WalletStatus, RotateKeyResult, AgentDiscoveryResult,
    SearchResult,
)
from agentbio.client import AgentBioError


# ── Shared fixtures ───────────────────────────────────────────────────────────

NOW = datetime.now(timezone.utc)
THUMBPRINT = "a" * 64


def _make_verify(action: TrustAction = TrustAction.PROCEED) -> VerifyResult:
    return VerifyResult(
        agent_id              = "test-agent",
        thumbprint            = THUMBPRINT,
        identity_valid        = True,
        hardware_backed       = True,
        reputation_score      = 4.5,
        verified_transactions = 10,
        total_transactions    = 12,
        risk_level            = "Low",
        recommendation        = action.value,
        action                = action,
        summary               = f"Agent test-agent — {action.value}",
        flags                 = [],
        verification_id       = "vrf_test",
        next_verify_after     = NOW,
        issued_at             = NOW,
        data_freshness_utc    = NOW,
        profile_url           = "https://app.agentbio.world/agent/test",
    )


def _make_enroll() -> EnrollResult:
    return EnrollResult(
        success        = True,
        agent_id       = "test-agent",
        thumbprint     = THUMBPRINT,
        api_key        = "agentbio_" + "x" * 32,
        is_new_account = True,
        profile_url    = "https://app.agentbio.world/agent/test",
        verify_url     = f"https://app.agentbio.world/api/public/verify/{THUMBPRINT}",
        next_steps     = ["Publish to relay", "Send a heartbeat"],
    )


def _make_heartbeat() -> HeartbeatResult:
    return HeartbeatResult(
        status      = "ok",
        agents_seen = 3,
        timestamp   = NOW,
        thumbprint  = THUMBPRINT,
    )


def _make_credit() -> CreditScoreReport:
    return CreditScoreReport(
        thumbprint             = THUMBPRINT,
        agent_id               = "test-agent",
        credit_score           = 742,
        score_band             = "Good",
        payment_history        = 85,
        transaction_volume     = 70,
        account_longevity      = 60,
        identity_strength      = 90,
        platform_diversity     = 55,
        pulls_used_this_period = 2,
        pulls_limit            = 10,
        computed_at            = NOW,
    )


def _make_wallet(registered: bool = True) -> WalletStatus:
    return WalletStatus(
        registered     = registered,
        wallet_address = "0xabc123" if registered else None,
        agent_ids      = ["test-agent"],
        registered_at  = NOW if registered else None,
        message        = "Wallet registered" if registered else "No wallet",
    )


def _make_search() -> SearchResult:
    agent = AgentDiscoveryResult(
        thumbprint            = THUMBPRINT,
        agent_id              = "test-agent",
        display_name          = "Test Agent",
        description           = "A test agent",
        reputation_score      = 4.5,
        recommendation        = "Allow",
        verified_transactions = 10,
        hardware_backed       = True,
        moltbook_linked       = False,
        last_seen_at          = NOW,
        enrolled_at           = NOW,
        verify_url            = f"https://app.agentbio.world/api/public/verify/{THUMBPRINT}",
    )
    return SearchResult(agents=[agent], total_count=1, page=1, page_size=10, has_more=False)


def _make_rotate() -> RotateKeyResult:
    return RotateKeyResult(
        new_api_key = "agentbio_" + "n" * 32,
        rotated_at  = NOW,
        message     = "Key rotated successfully.",
    )


# ── Test class ────────────────────────────────────────────────────────────────

class TestCLIParser(unittest.TestCase):
    """Tests that the argument parser is correctly configured."""

    def setUp(self):
        self.parser = _build_parser()

    def test_verify_requires_thumbprint(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["verify"])

    def test_enroll_requires_agent_id_and_email(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["enroll"])
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["enroll", "agent-id"])

    def test_enroll_parses_correctly(self):
        args = self.parser.parse_args(["enroll", "my-agent", "ops@example.com"])
        self.assertEqual(args.agent_id, "my-agent")
        self.assertEqual(args.email, "ops@example.com")

    def test_enroll_with_optional_name(self):
        args = self.parser.parse_args(
            ["enroll", "my-agent", "ops@example.com", "--name", "My Agent"])
        self.assertEqual(args.name, "My Agent")

    def test_pay_requires_thumbprint(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["pay", "--testnet"])

    def test_pay_testnet_flag(self):
        args = self.parser.parse_args(
            ["pay", "--thumbprint", THUMBPRINT, "--testnet"])
        self.assertTrue(args.testnet)

    def test_search_defaults(self):
        args = self.parser.parse_args(["search"])
        self.assertEqual(args.limit, 10)
        self.assertFalse(args.trusted_only)
        self.assertFalse(args.hardware_only)

    def test_key_rotate_subcommand(self):
        args = self.parser.parse_args(["key", "rotate", "--yes"])
        self.assertTrue(args.yes)

    def test_global_key_flag(self):
        args = self.parser.parse_args(["--key", "agentbio_test", "info"])
        self.assertEqual(args.key, "agentbio_test")

    def test_all_commands_have_func(self):
        commands = [
            ["verify", THUMBPRINT],
            ["enroll", "agent", "email@example.com"],
            ["heartbeat"],
            ["search"],
            ["credit", THUMBPRINT],
            ["info"],
            ["key", "rotate"],
        ]
        for cmd in commands:
            args = self.parser.parse_args(cmd)
            self.assertTrue(hasattr(args, "func"), f"Missing func for: {cmd}")


class TestVerifyCommand(unittest.TestCase):

    @patch("agentbio.cli.AgentBio")
    def test_trusted_agent_exits_0(self, MockAB):
        mock = MockAB.return_value
        mock.api_key = None
        mock.public_verify.return_value = _make_verify(TrustAction.PROCEED)

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["verify", THUMBPRINT])
        self.assertEqual(ctx.exception.code, 0)

    @patch("agentbio.cli.AgentBio")
    def test_blocked_agent_exits_2(self, MockAB):
        mock = MockAB.return_value
        mock.api_key = None
        mock.public_verify.return_value = _make_verify(TrustAction.ABORT)

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["verify", THUMBPRINT])
        self.assertEqual(ctx.exception.code, 2)

    @patch("agentbio.cli.AgentBio")
    def test_caution_agent_exits_0(self, MockAB):
        mock = MockAB.return_value
        mock.api_key = None
        mock.public_verify.return_value = _make_verify(TrustAction.PROCEED_WITH_CAUTION)

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["verify", THUMBPRINT])
        self.assertEqual(ctx.exception.code, 0)

    def test_short_thumbprint_exits_1(self):
        with patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["verify", "short"])
        self.assertEqual(ctx.exception.code, 1)

    @patch("agentbio.cli.AgentBio")
    def test_api_error_404_exits_1(self, MockAB):
        mock = MockAB.return_value
        mock.api_key = None
        mock.public_verify.side_effect = AgentBioError("Not found", 404)

        with patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["verify", THUMBPRINT])
        self.assertEqual(ctx.exception.code, 1)

    @patch("agentbio.cli.AgentBio")
    def test_uses_verify_when_key_provided(self, MockAB):
        mock = MockAB.return_value
        mock.api_key = "agentbio_key"
        mock.verify.return_value = _make_verify(TrustAction.PROCEED)

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                main(["--key", "agentbio_key", "verify", THUMBPRINT])

        mock.verify.assert_called_once_with(THUMBPRINT)
        mock.public_verify.assert_not_called()


class TestEnrollCommand(unittest.TestCase):

    @patch("agentbio.cli.AgentBio")
    def test_enroll_success(self, MockAB):
        mock = MockAB.return_value
        mock.enroll.return_value = _make_enroll()

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["enroll", "test-agent", "ops@example.com"])
        self.assertEqual(ctx.exception.code, 0)

    @patch("agentbio.cli.AgentBio")
    def test_duplicate_enroll_exits_1(self, MockAB):
        mock = MockAB.return_value
        mock.enroll.side_effect = AgentBioError("Already enrolled", 409)

        with patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["enroll", "test-agent", "ops@example.com"])
        self.assertEqual(ctx.exception.code, 1)


class TestHeartbeatCommand(unittest.TestCase):

    @patch("agentbio.cli.AgentBio")
    @patch.dict(os.environ, {"AGENTBIO_API_KEY": "agentbio_test"})
    def test_heartbeat_success(self, MockAB):
        mock = MockAB.return_value
        mock.heartbeat.return_value = _make_heartbeat()

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["heartbeat"])
        self.assertEqual(ctx.exception.code, 0)

    def test_heartbeat_without_key_exits_1(self):
        env = {k: v for k, v in os.environ.items() if k != "AGENTBIO_API_KEY"}
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["heartbeat"])
        self.assertEqual(ctx.exception.code, 1)

    @patch("agentbio.cli.AgentBio")
    @patch.dict(os.environ, {"AGENTBIO_API_KEY": "agentbio_test"})
    def test_heartbeat_with_agent_id(self, MockAB):
        mock = MockAB.return_value
        mock.heartbeat.return_value = _make_heartbeat()

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                main(["heartbeat", "--agent-id", "my-agent", "--runtime", "test/1.0"])

        mock.heartbeat.assert_called_once_with(
            agent_id="my-agent", runtime_info="test/1.0"
        )


class TestSearchCommand(unittest.TestCase):

    @patch("agentbio.cli.AgentBio")
    def test_search_success(self, MockAB):
        mock = MockAB.return_value
        mock.search.return_value = _make_search()

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["search"])
        self.assertEqual(ctx.exception.code, 0)

    @patch("agentbio.cli.AgentBio")
    def test_search_empty_results(self, MockAB):
        mock = MockAB.return_value
        mock.search.return_value = SearchResult(
            agents=[], total_count=0, page=1, page_size=10, has_more=False
        )

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["search"])
        self.assertEqual(ctx.exception.code, 0)

    @patch("agentbio.cli.AgentBio")
    def test_search_passes_filters(self, MockAB):
        mock = MockAB.return_value
        mock.search.return_value = _make_search()

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                main(["search", "--trusted-only", "--hardware-only",
                      "--min-score", "4.0", "--active-days", "30", "--limit", "5"])

        mock.search.assert_called_once_with(
            min_score            = 4.0,
            recommendation       = "Allow",
            hardware_backed_only = True,
            active_within_days   = 30,
            query                = None,
            page_size            = 5,
        )


class TestCreditCommand(unittest.TestCase):

    @patch("agentbio.cli.AgentBio")
    @patch.dict(os.environ, {"AGENTBIO_API_KEY": "agentbio_test"})
    def test_credit_success(self, MockAB):
        mock = MockAB.return_value
        mock.credit_score.return_value = _make_credit()

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["credit", THUMBPRINT])
        self.assertEqual(ctx.exception.code, 0)

    @patch("agentbio.cli.AgentBio")
    @patch.dict(os.environ, {"AGENTBIO_API_KEY": "agentbio_test"})
    def test_credit_pull_limit_exits_1(self, MockAB):
        mock = MockAB.return_value
        mock.credit_score.side_effect = AgentBioError("Pull limit reached", 429)

        with patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["credit", THUMBPRINT])
        self.assertEqual(ctx.exception.code, 1)


class TestPayCommand(unittest.TestCase):

    VALID_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

    def _mock_eth(self):
        """Mock eth_account so tests pass without the package installed."""
        mock_acct   = MagicMock()
        mock_acct.from_key.return_value.address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        mock_module = MagicMock()
        mock_module.Account = mock_acct
        return patch.dict("sys.modules", {"eth_account": mock_module})

    def _run_pay(self, extra_args: list[str] = None):
        args = [
            "--key", "agentbio_test",
            "pay",
            "--thumbprint", THUMBPRINT,
            "--private-key", self.VALID_KEY,
            "--testnet",
        ] + (extra_args or [])
        main(args)

    @patch("agentbio.cli.AgentBio")
    def test_pay_testnet_success(self, MockAB):
        mock = MockAB.return_value
        mock.public_verify.return_value = _make_verify(TrustAction.PROCEED)
        mock.register_wallet.return_value = _make_wallet()
        mock.heartbeat.return_value = _make_heartbeat()
        mock.generate_receipt.return_value = MagicMock(request_id="req_test_12345678")

        with self._mock_eth(), patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                self._run_pay()
        self.assertEqual(ctx.exception.code, 0)

    @patch("agentbio.cli.AgentBio")
    def test_pay_blocked_agent_exits_1(self, MockAB):
        mock = MockAB.return_value
        mock.public_verify.return_value = _make_verify(TrustAction.ABORT)

        with self._mock_eth(), \
             patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                self._run_pay()
        self.assertEqual(ctx.exception.code, 1)

    def test_pay_invalid_private_key_exits_1(self):
        with patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main([
                    "--key", "agentbio_test",
                    "pay",
                    "--thumbprint", THUMBPRINT,
                    "--private-key", "not-a-valid-key",
                    "--testnet",
                ])
        self.assertEqual(ctx.exception.code, 1)

    def test_pay_short_thumbprint_exits_1(self):
        with patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main([
                    "--key", "agentbio_test",
                    "pay",
                    "--thumbprint", "short",
                    "--private-key", self.VALID_KEY,
                    "--testnet",
                ])
        self.assertEqual(ctx.exception.code, 1)

    def test_pay_without_private_key_exits_1(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("AGENTBIO_PRIVATE_KEY",)}
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.stdout", new_callable=StringIO), \
             patch("sys.stderr", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main([
                    "--key", "agentbio_test",
                    "pay",
                    "--thumbprint", THUMBPRINT,
                    "--testnet",
                ])
        self.assertEqual(ctx.exception.code, 1)

    @patch("agentbio.cli.AgentBio")
    def test_pay_wallet_already_registered(self, MockAB):
        """409 on wallet registration should not fail the command."""
        mock = MockAB.return_value
        mock.public_verify.return_value = _make_verify(TrustAction.PROCEED)
        mock.register_wallet.side_effect = AgentBioError("Already registered", 409)
        mock.heartbeat.return_value = _make_heartbeat()
        mock.generate_receipt.return_value = MagicMock(request_id="req_test_12345678")

        with self._mock_eth(), patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                self._run_pay()
        self.assertEqual(ctx.exception.code, 0)

    @patch("agentbio.cli.AgentBio")
    def test_pay_private_key_from_env(self, MockAB):
        """Private key should be read from AGENTBIO_PRIVATE_KEY env var."""
        mock = MockAB.return_value
        mock.public_verify.return_value = _make_verify(TrustAction.PROCEED)
        mock.register_wallet.return_value = _make_wallet()
        mock.heartbeat.return_value = _make_heartbeat()
        mock.generate_receipt.return_value = MagicMock(request_id="req_test_12345678")

        with self._mock_eth(), \
             patch.dict(os.environ, {"AGENTBIO_PRIVATE_KEY": self.VALID_KEY}), \
             patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main([
                    "--key", "agentbio_test",
                    "pay",
                    "--thumbprint", THUMBPRINT,
                    "--testnet",
                ])
        self.assertEqual(ctx.exception.code, 0)


class TestInfoCommand(unittest.TestCase):

    @patch("agentbio.cli.AgentBio")
    def test_info_success(self, MockAB):
        mock = MockAB.return_value
        mock.meta.return_value = {
            "version":    "1.0",
            "endpoints":  ["/api/v1/agent/{thumbprint}"],
            "rateLimits": {"Free": 60, "Pro": 600},
        }

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["info"])
        self.assertEqual(ctx.exception.code, 0)


class TestKeyRotateCommand(unittest.TestCase):

    @patch("agentbio.cli.AgentBio")
    @patch.dict(os.environ, {"AGENTBIO_API_KEY": "agentbio_test"})
    def test_rotate_with_yes_flag(self, MockAB):
        mock = MockAB.return_value
        mock.rotate_key.return_value = _make_rotate()

        with patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["key", "rotate", "--yes"])
        self.assertEqual(ctx.exception.code, 0)
        mock.rotate_key.assert_called_once()

    @patch("agentbio.cli.AgentBio")
    @patch.dict(os.environ, {"AGENTBIO_API_KEY": "agentbio_test"})
    def test_rotate_cancelled_at_prompt(self, MockAB):
        mock = MockAB.return_value

        with patch("builtins.input", return_value="no"), \
             patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["key", "rotate"])
        self.assertEqual(ctx.exception.code, 0)
        mock.rotate_key.assert_not_called()

    @patch("agentbio.cli.AgentBio")
    @patch.dict(os.environ, {"AGENTBIO_API_KEY": "agentbio_test"})
    def test_rotate_confirmed_at_prompt(self, MockAB):
        mock = MockAB.return_value
        mock.rotate_key.return_value = _make_rotate()

        with patch("builtins.input", return_value="rotate"), \
             patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                main(["key", "rotate"])
        self.assertEqual(ctx.exception.code, 0)
        mock.rotate_key.assert_called_once()


class TestEnvironmentVariables(unittest.TestCase):
    """Verify the CLI correctly reads from environment variables."""

    @patch("agentbio.cli.AgentBio")
    def test_api_key_from_env(self, MockAB):
        mock = MockAB.return_value
        mock.api_key = "agentbio_from_env"
        mock.verify.return_value = _make_verify(TrustAction.PROCEED)

        with patch.dict(os.environ, {"AGENTBIO_API_KEY": "agentbio_from_env"}), \
             patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                main(["verify", THUMBPRINT])

        # Verify AgentBio was constructed with the env key
        MockAB.assert_called_once()
        call_kwargs = MockAB.call_args
        self.assertEqual(call_kwargs.kwargs.get("api_key") or call_kwargs.args[0],
                         "agentbio_from_env")

    @patch("agentbio.cli.AgentBio")
    def test_base_url_from_env(self, MockAB):
        mock = MockAB.return_value
        mock.api_key = None
        mock.public_verify.return_value = _make_verify(TrustAction.PROCEED)

        with patch.dict(os.environ, {"AGENTBIO_BASE_URL": "https://custom.example.com"}), \
             patch("sys.stdout", new_callable=StringIO):
            with self.assertRaises(SystemExit):
                main(["verify", THUMBPRINT])

        MockAB.assert_called_once()
        call_kwargs = MockAB.call_args
        base = call_kwargs.kwargs.get("base_url") or (
            call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
        )
        self.assertEqual(base, "https://custom.example.com")


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
