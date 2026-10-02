from pathlib import Path

from select_services import select


def test_pull_request_into_main_selects_only_the_changed_gateway(tmp_path: Path):
    result = select(
        "pull_request",
        "main",
        ["apps/backend/bff-web/app/main.py"],
        tmp_path,
    )
    assert result["run"] == ["bff-web"]
    assert result["skip"] == []


def test_push_to_main_selects_both_gateways_when_neither_changed(tmp_path: Path):
    result = select(
        "push",
        "main",
        ["apps/backend/specs/001-bff-unit-checks/spec.md"],
        tmp_path,
    )
    assert result["run"] == ["bff-web", "bff-movil"]


def test_pull_request_that_does_not_target_main_selects_nothing(tmp_path: Path):
    result = select(
        "pull_request",
        "adding-bff-setup",
        ["apps/backend/bff-web/app/main.py", "apps/backend/bff-movil/app/main.py"],
        tmp_path,
    )
    assert result["run"] == []
    assert result["skip"] == []
