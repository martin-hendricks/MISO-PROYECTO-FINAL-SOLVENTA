from app.config import Settings
from app.infrastructure.kafka_publicador import MSKTokenProvider, PublicadorMSK


def _config(**cambios) -> Settings:
    datos = {
        "msk_bootstrap_brokers": "b-1.solventa.kafka.us-east-1.amazonaws.com:9098",
        "msk_topic": "BusEventos",
    }
    datos.update(cambios)
    return Settings(**datos)


async def test_cerrar_sin_iniciar_no_lanza():
    publicador = PublicadorMSK(_config())

    await publicador.cerrar()
    await publicador.cerrar()


def test_cerrar_sin_iniciar_deja_el_estado_seguro():
    publicador = PublicadorMSK(_config())
    assert publicador._producer is None


def test_provider_de_tokens_usa_la_region_configurada():
    provider = MSKTokenProvider("us-east-1")
    assert provider._region == "us-east-1"


def test_region_usa_la_configurada_explicitamente():
    publicador = PublicadorMSK(_config(aws_region="eu-west-1"))
    assert publicador._region == "eu-west-1"


def test_region_cae_a_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    publicador = PublicadorMSK(_config(aws_region=""))
    assert publicador._region == "us-west-2"


def test_region_por_defecto_cae_a_us_east_1(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    publicador = PublicadorMSK(_config(aws_region=""))
    assert publicador._region == "us-east-1"
