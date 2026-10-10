# bff-arquetipo

Plantilla de **Backend for Frontend** de Solventa (`bff-web`, `bff-movil`). No se despliega: se copia con `scripts/nuevo-servicio.sh bff <nombre>`.

Un BFF es el **borde de un canal**: expone la API que necesitan las pantallas de ese canal ([Contratos-BFF](https://github.com/martin-hendricks/MISO-PROYECTO-FINAL-SOLVENTA/wiki/Contratos-BFF)) y la arma llamando a los microservicios del núcleo.

| Sí hace | No hace |
| --- | --- |
| Compone varias llamadas **en paralelo** y degrada partes opcionales | Reglas de negocio (son del núcleo) |
| Recorta y renombra el payload para la vista (camelCase) | Tener base de datos propia |
| Versiona el contrato (`/v1`) | Llamar a OF/OD/KYC/pasarela o publicar en el bus |
| Reenvía `Idempotency-Key` y `X-Correlation-Id` al núcleo | Mostrar al canal qué servicio interno falló |

La validación del JWT y la autorización por rol se agregan en sus HU (HU-74, HU-75, HU-76).

## Estructura

```
app/
├── main.py              crear_app(): clientes httpx, mapeo de fallas → 404/409/422/503
├── config.py            URLs del núcleo, timeouts
├── dependencies.py      raíz de composición de los clientes
├── observabilidad.py    /health, /metrics, X-Correlation-Id
├── api/v1/rutas.py      contrato del canal
├── api/v1/schemas.py    payloads de la vista (camelCase, campos nuevos opcionales)
├── clients/             un cliente por microservicio (solo operaciones del canal)
└── aggregators/         componer(): fuente principal + opcionales en paralelo
tests/                   rutas y composición; núcleo simulado con httpx.MockTransport
tests/contract/          verificación Pact (HU-88), excluida del workflow unitario
```

<!-- desarrollo -->

## Desarrollo

**Requisitos:** Python 3.12+ (o solo Docker).

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[test]"
uvicorn app.main:app --reload --port 8080          # http://localhost:8080/docs
```

| Variable | Default | Uso |
| --- | --- | --- |
| `MS_EJEMPLO_URL` | `http://localhost:8000` | Una variable `MS_<NOMBRE>_URL` por microservicio |
| `TIMEOUT_NUCLEO_S` | `1.0` | Timeout por llamada al núcleo |
| `TIMEOUT_OPCIONAL_S` | `0.3` | Corte de fuentes opcionales en vistas agregadas |

## Pruebas (HU-85)

```bash
pytest -m "not integration and not contract" --cov
```

El núcleo se simula con `httpx.MockTransport`: sin red.

En la imagen (contexto `apps/backend`):

```bash
docker build -f Dockerfile --target test -t bff-arquetipo:test .. && docker run --rm bff-arquetipo:test
```

## Ejecutar con Docker (HU-71)

```bash
docker compose up --build          # BFF :8080 + núcleo de ejemplo (ms-arquetipo + PostgreSQL)
```

El contexto de build es `apps/backend`, para que las imágenes de los BFF puedan incluir código compartido del backend.

## Despliegue

Imagen `runtime` detrás del `:ApiGateway` (ALB + WAF) hacia EKS (§1.1.3). El canal solo conoce la URL del gateway.

La imagen corre con uid 1000 en :8080, como espera el chart `infra/k8s/charts/microservicio`. En el Compose local el núcleo de ejemplo se levanta en :8000 para conservar `MS_EJEMPLO_URL`.

Las dependencias de la imagen se instalan con `requirements.lock` como *constraints*: dos construcciones del mismo commit instalan las mismas versiones. Si cambia `pyproject.toml`, se regenera el lock (sin Docker):

```bash
uv pip compile pyproject.toml --extra test --python-version 3.12.7 --python-platform x86_64-unknown-linux-gnu -o requirements.lock
```
