"""Choose which backend services the unit-check workflow runs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REQUIRED = ("bff-web", "bff-movil")
IGNORED = {"scripts", "specs"}
BACKEND_PREFIX = "apps/backend/"
HISTORICAL = {"develop", "main"}
PUBLISHED_PREFIXES = ("release/", "hotfix/")
FEATURE_PREFIX = "feature/"


def _touches(service: str, changed_paths: list[str]) -> bool:
    prefix = f"{BACKEND_PREFIX}{service}/"
    exact = f"{BACKEND_PREFIX}{service}"
    return any(path == exact or path.startswith(prefix) for path in changed_paths)


def _has_test_file(service_dir: Path) -> bool:
    tests = service_dir / "tests"
    if not tests.is_dir():
        return False
    return any(tests.rglob("test_*.py")) or any(tests.rglob("*_test.py"))


def _skip_reason(service_dir: Path) -> str | None:
    if not _has_test_file(service_dir):
        return "no test file"
    if not (service_dir / "pyproject.toml").is_file():
        return "no pyproject.toml"
    if not (service_dir / "app" / "main.py").is_file():
        return "no app/main.py"
    return None


def _is_published(branch: str) -> bool:
    return branch in HISTORICAL or branch.startswith(PUBLISHED_PREFIXES)


def _is_pull_request_base(branch: str) -> bool:
    return _is_published(branch)


def _always_runs_gateways(event: str, branch: str) -> bool:
    return event == "push" and _is_published(branch)


def _uses_path_filter(event: str, branch: str) -> bool:
    if event == "push" and branch.startswith(FEATURE_PREFIX):
        return True
    return event == "pull_request" and _is_pull_request_base(branch)


def select(
    event: str,
    branch: str,
    changed_paths: list[str],
    backend_root: Path,
) -> dict:
    if not _always_runs_gateways(event, branch) and not _uses_path_filter(event, branch):
        return {"run": [], "skip": []}

    run: list[str] = []
    skip: list[dict[str, str]] = []
    if _always_runs_gateways(event, branch):
        run.extend(REQUIRED)
    else:
        run.extend(name for name in REQUIRED if _touches(name, changed_paths))

    if backend_root.is_dir():
        for child in sorted(backend_root.iterdir()):
            if (
                not child.is_dir()
                or child.name.startswith(".")
                or child.name in IGNORED
                or child.name in REQUIRED
            ):
                continue
            if not _touches(child.name, changed_paths):
                continue
            reason = _skip_reason(child)
            if reason:
                skip.append({"service": child.name, "reason": reason})
            else:
                run.append(child.name)

    return {"run": run, "skip": skip}


def _changed_paths_from_git(event: str, repo_root: Path) -> list[str]:
    if event == "pull_request":
        base = os.environ.get("GITHUB_BASE_REF", "main")
        command = ["git", "diff", "--name-only", f"origin/{base}...HEAD"]
    else:
        before = os.environ.get("GITHUB_EVENT_BEFORE", "")
        if before and set(before) != {"0"}:
            command = ["git", "diff", "--name-only", before, "HEAD"]
        else:
            command = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
    completed = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line]


def _write_output(result: dict) -> None:
    print(json.dumps(result))
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with open(output, "a", encoding="utf-8") as handle:
        for key in ("matrix", "skip"):
            payload = result["run"] if key == "matrix" else result["skip"]
            handle.write(f"{key}<<EOF\n{json.dumps(payload)}\nEOF\n")


def main() -> None:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event == "pull_request":
        branch = os.environ.get("GITHUB_BASE_REF", "")
    else:
        branch = os.environ.get("GITHUB_REF_NAME", "")
    script_dir = Path(__file__).resolve().parent
    backend_root = script_dir.parent
    repo_root = backend_root.parent
    paths = _changed_paths_from_git(event, repo_root)
    _write_output(select(event, branch, paths, backend_root))


if __name__ == "__main__":
    main()
