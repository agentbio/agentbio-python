"""
Allows running the CLI as a module:

    python -m agentbio <command> [options]

Equivalent to the `agentbio` console script installed by pip.
"""

from .cli import main

if __name__ == "__main__":
    main()
