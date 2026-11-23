import pytest

from .dobles import PublicadorDoble, RepositorioOutboxDoble


@pytest.fixture
def publicador() -> PublicadorDoble:
    return PublicadorDoble()


@pytest.fixture
def repositorio() -> RepositorioOutboxDoble:
    return RepositorioOutboxDoble("ms_cotizacion")
