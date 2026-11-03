"""Run the Pact contract checks (HU-88): consumers write their pacts, then providers verify them.

Usage, from the repository root or anywhere else:

    python apps/backend/scripts/verify_contracts.py

Each service gets its own .venv with the `test` and `contract` extras, the same way the
unit workflow installs them. A consumer that fails stops the run before any provider,
so no provider is verified against a stale pact.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

# A consumer publishes pacts/<consumer>-<provider>.json; a provider verifies the pacts of
# its consumers. Add the service here when its contract tests land.
CONSUMERS = ("api-socios", "bff-web", "bff-movil")
PROVIDERS = ("ms-cotizacion",)

BACKEND = Path(__file__).resolve().parents[1]

Runner = Callable[[Sequence[str], Path], int]


def _subprocess(command: Sequence[str], cwd: Path) -> int:
    return subprocess.run(list(command), cwd=cwd).returncode


def _venv_python(service_dir: Path) -> Path:
    scripts = "Scripts" if os.name == "nt" else "bin"
    return service_dir / ".venv" / scripts / ("python.exe" if os.name == "nt" else "python")


def _group(title: str) -> None:
    print(f"::group::{title}" if os.environ.get("GITHUB_ACTIONS") else f"== {title}", flush=True)


def _end_group() -> None:
    if os.environ.get("GITHUB_ACTIONS"):
        print("::endgroup::", flush=True)


def check(service: str, backend: Path, runner: Runner) -> bool:
    """Install the service and run its `contract` tests. No collected test counts as a failure."""
    work = backend / service
    python = str(_venv_python(work))
    steps = (
        [sys.executable, "-m", "venv", ".venv"],
        [python, "-m", "pip", "install", "-q", "-e", ".[test,contract]"],
        [python, "-m", "pytest", "tests", "-m", "contract", "-p", "no:cacheprovider", "--junitxml=junit-contract.xml"],
    )
    _group(service)
    try:
        return all(runner(step, work) == 0 for step in steps)
    finally:
        _end_group()


def run(
    backend: Path = BACKEND,
    consumers: Sequence[str] = CONSUMERS,
    providers: Sequence[str] = PROVIDERS,
    runner: Runner = _subprocess,
) -> int:
    failed_consumers = [service for service in consumers if not check(service, backend, runner)]
    if failed_consumers:
        print(f"Consumer contract tests failed: {', '.join(failed_consumers)}. Providers not verified.")
        return 1

    failed_providers = [service for service in providers if not check(service, backend, runner)]
    if failed_providers:
        print(f"Providers break a consumer contract: {', '.join(failed_providers)}.")
        return 1

    print(f"Contracts verified: {', '.join(providers)} against {', '.join(consumers)}.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
