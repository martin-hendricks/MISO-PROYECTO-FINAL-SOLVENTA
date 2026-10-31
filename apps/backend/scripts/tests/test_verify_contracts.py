from pathlib import Path

from verify_contracts import run


class FakeRunner:
    """Records which service ran pytest and fails the services it is told to."""

    def __init__(self, failing: set[str] = frozenset()) -> None:
        self.failing = failing
        self.tested: list[str] = []

    def __call__(self, command, cwd: Path) -> int:
        if "pytest" not in command:
            return 0
        self.tested.append(cwd.name)
        return 1 if cwd.name in self.failing else 0


def test_consumers_write_their_pacts_before_providers_verify_them(tmp_path: Path):
    runner = FakeRunner()

    code = run(tmp_path, ["consumer-a", "consumer-b"], ["provider"], runner)

    assert code == 0
    assert runner.tested == ["consumer-a", "consumer-b", "provider"]


def test_a_failing_consumer_stops_before_any_provider(tmp_path: Path):
    runner = FakeRunner(failing={"consumer-a"})

    code = run(tmp_path, ["consumer-a", "consumer-b"], ["provider"], runner)

    assert code == 1
    assert "provider" not in runner.tested


def test_a_provider_that_breaks_a_contract_fails_the_run(tmp_path: Path):
    runner = FakeRunner(failing={"provider-a"})

    code = run(tmp_path, ["consumer"], ["provider-a", "provider-b"], runner)

    assert code == 1
    assert runner.tested == ["consumer", "provider-a", "provider-b"]


def test_a_failed_install_counts_as_a_failure(tmp_path: Path):
    def broken_install(command, cwd: Path) -> int:
        return 1 if "pip" in command else 0

    assert run(tmp_path, ["consumer"], ["provider"], broken_install) == 1
