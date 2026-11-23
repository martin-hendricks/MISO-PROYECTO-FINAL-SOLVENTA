import asyncio

from aiokafka.abc import AbstractTokenProvider


class MSKTokenProvider(AbstractTokenProvider):
    """Token OAUTHBEARER firmado con IAM (IRSA) para MSK. Mismo patrón que
    notificaciones y outbox-relay; el firmador se importa de forma perezosa para que las
    pruebas no necesiten credenciales de AWS."""

    def __init__(self, region: str) -> None:
        self._region = region

    async def token(self) -> str:
        return await asyncio.get_running_loop().run_in_executor(None, self._token)

    def _token(self) -> str:
        from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

        token, _ = MSKAuthTokenProvider.generate_auth_token(self._region)
        return token
