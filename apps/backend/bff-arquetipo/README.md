# bff-arquetipo

Plantilla de **Backend for Frontend** de Solventa (`bff-web`, `bff-movil`). No se despliega: se copia con `scripts/nuevo-servicio.sh bff <nombre>`.

Un BFF es el **borde de un canal**: expone la API que necesitan las pantallas de ese canal ([Contratos-BFF](https://github.com/martin-hendricks/MISO-PROYECTO-FINAL-SOLVENTA/wiki/Contratos-BFF)) y la arma llamando a los microservicios del núcleo.

| Sí hace | No hace |
| --- | --- |
| Valida el JWT de `ms-identidad` en **cada** petición (HU-74/76) | Emitir tokens (eso es `ms-identidad`) |
| Autoriza por **rol** en servidor (HU-75) | Confiar en un rol que mande el cliente |
| Compone varias llamadas **en paralelo** y degrada partes opcionales | Reglas de negocio (son del núcleo) |
| Recorta y renombra el payload para la vista (camelCase) | Tener base de datos propia |
| Versiona el contrato (`/v1`) | Llamar a OF/OD/KYC/pasarela o publicar en el bus |
| Reenvía `Idempotency-Key` y `X-Correlation-Id` al núcleo | Mostrar al canal qué servicio interno falló |

## Estructura

```
app/
├── main.py              crear_app(): seguridad, clientes httpx, mapeo de fallas → 404/422/503
├── config.py            URLs del núcleo, llave pública JWT, timeouts
├── dependencies.py      raíz de composición de los clientes
├── observabilidad.py    /health, /metrics, X-Correlation-Id
├── api/v1/rutas.py      contrato del canal: TODO el router exige JWT; cada ruta declara roles
├── api/v1/schemas.py    payloads de la vista (camelCase, campos nuevos opcionales)
├── clients/             un cliente por microservicio (solo operaciones del canal)
└── aggregators/         componer(): fuente principal + opcionales en paralelo
tests/                   seguridad, rutas, composición; núcleo simulado con httpx.MockTransport
tests/contract/          verificación Pact (HU-88), excluida del workflow unitario
```

La seguridad **no está aquí**: viene de `libs/solventa-seguridad`, que es un solo validador para web y móvil (HU-76).

<!-- desarrollo -->

## Desarrollo

**Requisitos:** Python 3.12+ (o solo Docker). `pip install` instala también `libs/solventa-seguridad` por ruta relativa.

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[test]"
uvicorn app.main:app --reload --port 8080          # http://localhost:8080/docs
```

Sin `JWT_PUBLIC_KEY`, las rutas `/v1` responden 503 (falla cerrada).

## Pruebas (HU-85)

```bash
pytest -m "not integration and not contract" --cov
```

Los tests firman tokens con un par de llaves efímero (`solventa_seguridad.pruebas.EmisorDePrueba`) y simulan el núcleo con `httpx.MockTransport`: sin red, sin `ms-identidad`, sin secretos. `test_ninguna_ruta_v1_responde_sin_token` recorre el OpenAPI, así que una ruta nueva sin protección rompe el build.

En la imagen (contexto `apps/backend`):

```bash
docker build -f Dockerfile --target test -t $(basename "$PWD"):test .. && docker run --rm $(basename "$PWD"):test
```

## Ejecutar con Docker

```bash
JWT_PUBLIC_KEY="$(cat llave_publica.pem)" docker compose up --build    # BFF :8080 + núcleo de ejemplo
```

| Variable | Default | Uso |
| --- | --- | --- |
| `JWT_PUBLIC_KEY` | *(vacío → 503)* | PEM de la llave **pública** de `ms-identidad` |
| `JWT_ISSUER` / `JWT_AUDIENCE` | `ms-identidad` / `solventa` | Claims `iss` / `aud` esperados |
| `MS_EJEMPLO_URL` | `http://localhost:8000` | Una variable `MS_<NOMBRE>_URL` por microservicio |
| `TIMEOUT_NUCLEO_S` | `1.0` | Timeout por llamada al núcleo |
| `TIMEOUT_OPCIONAL_S` | `0.3` | Corte de fuentes opcionales en vistas agregadas |

## Despliegue

Imagen `runtime` detrás del `:ApiGateway` (ALB + WAF) hacia EKS (§1.1.3). El canal solo conoce la URL del gateway.
