# bff-web

Backend for Frontend del canal web: contrato versionado para cotizar, emitir, gestionar y siniestros (HU-72). Valida JWT y autoriza por rol en servidor (HU-74/75).

**Stack:** Python (FastAPI)

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
