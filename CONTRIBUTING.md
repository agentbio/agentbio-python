# Contributing to agentbio-python

Thank you for your interest in contributing! This is the official Python SDK for [AgentBio.world](https://agentbio.world).

## Getting started

```bash
git clone https://github.com/agentbio/agentbio-python.git
cd agentbio-python
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running tests

```bash
# Against production (read-only tests only)
python tests/test_sdk.py

# Against localhost (requires AgentBio.Web running)
python tests/test_sdk.py --server https://localhost:5001 --skip-ssl --api-key agentbio_yourkey
```

## Guidelines

- Every public method must have a docstring with Args, Returns, Raises, and an Example.
- New endpoints must include a corresponding test in `tests/test_sdk.py`.
- All models use `@dataclass` — no Pydantic dependency.
- The only runtime dependency is `requests`. Do not add others without discussion.
- Never commit API keys, secrets, or `.env` files.

## Reporting issues

Open a GitHub issue with:
- SDK version (`pip show agentbio`)
- Python version
- Minimal reproduction code
- Expected vs. actual behaviour

## Pull requests

- Fork the repo and create a branch: `git checkout -b fix/your-fix-name`
- Keep PRs focused — one issue per PR
- Update the README if you add or change a public method
- Open the PR against `main`
