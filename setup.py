from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name                          = "agentbio",
    version                       = "1.1.0",
    author                        = "AgentBio.world",
    author_email                  = "dev@agentbio.world",
    description                   = "Verify AI agent identity and reputation before interacting with them.",
    long_description              = long_description,
    long_description_content_type = "text/markdown",
    url                           = "https://agentbio.world",
    project_urls                  = {
        "Documentation": "https://app.agentbio.world/developer",
        "Source":        "https://github.com/agentbio/agentbio-python",
        "Tracker":       "https://github.com/agentbio/agentbio-python/issues",
    },
    packages                      = find_packages(),
    python_requires               = ">=3.10",
    install_requires              = [
        "requests>=2.28.0",
    ],
    extras_require                = {
        # Required for `agentbio pay` — derives wallet address from private key
        "pay": ["eth-account>=0.10.0"],
        # Install everything
        "all": ["eth-account>=0.10.0"],
    },
    entry_points                  = {
        "console_scripts": [
            "agentbio = agentbio.cli:main",
        ],
    },
    classifiers                   = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords = "ai agent identity trust verification reputation x402 blockchain cli",
)
