import pytest
from pathlib import Path

from select_services import select


@pytest.mark.parametrize("branch", ["develop", "main", "release/0.1.0", "hotfix/1.0.1"])
def test_pull_request_selects_only_the_changed_gateway(tmp_path: Path, branch: str):
    result = select(
        "pull_request",
        branch,
        ["apps/backend/bff-web/app/main.py"],
        tmp_path,
    )
    assert result["run"] == ["bff-web"]
    assert result["skip"] == []


@pytest.mark.parametrize("branch", ["develop", "main", "release/0.1.0", "hotfix/1.0.1"])
def test_push_selects_both_gateways_when_neither_changed(tmp_path: Path, branch: str):
    result = select(
        "push",
        branch,
        ["apps/backend/specs/001-bff-unit-checks/spec.md"],
        tmp_path,
    )
    assert result["run"] == ["bff-web", "bff-movil"]


def test_feature_push_selects_only_the_changed_gateway(tmp_path: Path):
    result = select(
        "push",
        "feature/quote",
        ["apps/backend/bff-web/app/main.py"],
        tmp_path,
    )
    assert result["run"] == ["bff-web"]
    assert result["skip"] == []


def test_pull_request_outside_gitflow_selects_nothing(tmp_path: Path):
    result = select(
        "pull_request",
        "adding-bff-setup",
        ["apps/backend/bff-web/app/main.py", "apps/backend/bff-movil/app/main.py"],
        tmp_path,
    )
    assert result["run"] == []
    assert result["skip"] == []


def test_push_outside_gitflow_selects_nothing(tmp_path: Path):
    result = select(
        "push",
        "adding-bff-setup",
        ["apps/backend/bff-web/app/main.py"],
        tmp_path,
    )
    assert result["run"] == []
    assert result["skip"] == []
