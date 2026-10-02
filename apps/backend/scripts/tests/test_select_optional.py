from pathlib import Path

from select_services import select


def _file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# marker\n", encoding="utf-8")


def test_domain_without_tests_is_skipped(tmp_path: Path):
    (tmp_path / "api-socios").mkdir()
    result = select(
        "pull_request",
        "main",
        ["apps/backend/api-socios/README.md"],
        tmp_path,
    )
    assert result["run"] == []
    assert result["skip"] == [{"service": "api-socios", "reason": "no test file"}]


def test_domain_with_tests_but_no_package_is_skipped(tmp_path: Path):
    _file(tmp_path / "ms-pagos" / "tests" / "test_pago.py")
    result = select(
        "pull_request",
        "main",
        ["apps/backend/ms-pagos/tests/test_pago.py"],
        tmp_path,
    )
    assert result["run"] == []
    assert result["skip"][0]["service"] == "ms-pagos"
    assert "pyproject.toml" in result["skip"][0]["reason"]


def test_domain_with_tests_but_no_app_main_is_skipped(tmp_path: Path):
    _file(tmp_path / "ms-identidad" / "tests" / "test_token.py")
    _file(tmp_path / "ms-identidad" / "pyproject.toml")
    result = select(
        "pull_request",
        "main",
        ["apps/backend/ms-identidad/pyproject.toml"],
        tmp_path,
    )
    assert result["run"] == []
    assert "app/main.py" in result["skip"][0]["reason"]


def test_later_directory_with_the_same_markers_is_selected(tmp_path: Path):
    _file(tmp_path / "ms-futuro" / "tests" / "test_ok.py")
    _file(tmp_path / "ms-futuro" / "pyproject.toml")
    _file(tmp_path / "ms-futuro" / "app" / "main.py")
    result = select(
        "pull_request",
        "main",
        ["apps/backend/ms-futuro/app/main.py"],
        tmp_path,
    )
    assert result["run"] == ["ms-futuro"]
    assert result["skip"] == []
