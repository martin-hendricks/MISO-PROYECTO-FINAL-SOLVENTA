# Backend · Solventa

Python 3.12 + FastAPI. Cada carpeta es un servicio independiente en build y despliegue. Arquitectura: [Hoja de trabajo semana 8 §1.1–1.2](https://github.com/martin-hendricks/MISO-PROYECTO-FINAL-SOLVENTA/wiki/Hoja-de-trabajo-semana-8).

```
 App Android ──► bff-movil ─┐
 Web cliente ─┐             ├──► ms-identidad, ms-cotizacion, ms-polizas, ms-siniestros, ms-pagos …
 Back-office ─┴► bff-web  ──┘            (núcleo: dominio + almacén propio + eventos)
      canal        BORDE                 ──► adaptadores OF/OD/KYC/pasarela, Kafka (solo el núcleo)
```

| Capa | Carpetas | Qué hace |
| --- | --- | --- |
| **Borde** (BFF) | `bff-web`, `bff-movil` | Expone la API del canal; valida JWT y rol; compone llamadas al núcleo. Sin BD |
| **Núcleo** | `ms-*` | Reglas de negocio, su propio schema (`db/schema/`), eventos por outbox |
| **Canal socio** | `api-socios` | API embebida para socios (fuera del alcance de los BFF) |
| **Arquetipos** | `ms-arquetipo`, `bff-arquetipo` | Plantillas probadas; no se despliegan |

## Crear un servicio

```bash
apps/backend/scripts/nuevo-servicio.sh ms  ms-cotizacion
apps/backend/scripts/nuevo-servicio.sh bff bff-web
```

Copia el arquetipo, lo renombra y conserva el `README.md` que ya tenga la carpeta. Si la carpeta ya tiene código, aborta.

## Ambiente de integración con dobles (HU-88)

`docker compose up -d --build` levanta el backend completo sin ningún tercero real: Open Finance, Open Data, perfil de riesgo, KYC y pasarela son dobles detrás de sus adaptadores, y el núcleo solo conoce el puerto. Por defecto responden de inmediato. Su demora y su caída se fuerzan desde el entorno:

| Variable | Servicio | Efecto |
| --- | --- | --- |
| `DOBLE_OPEN_FINANCE_LATENCIA_MS` / `_FALLAR` | `ms-perfilamiento` | Atributos degradados con valor de respaldo (HU-56) |
| `DOBLE_OPEN_DATA_LATENCIA_MS` / `_FALLAR` | `ms-perfilamiento` | Ídem |
| `DOBLE_PERFIL_RIESGO_LATENCIA_MS` / `_FALLAR` | `ms-cotizacion` | Factor de riesgo de respaldo (HU-5) |
| `DOBLE_KYC_LATENCIA_MS` / `_FALLAR` | `ms-identidad` | Alta en 503 |
| `DOBLE_KYC_DOCUMENTOS_RECHAZADOS` | `ms-identidad` | Lista separada por comas; esos documentos se rechazan en el alta (422 `identidad_no_verificada`). Vacía por defecto: el KYC aprueba todo |
| `DOBLE_PASARELA_LATENCIA_MS` / `_FALLAR` | `ms-pagos` | Cobro en 503; el token `tok_rechazo` siempre se rechaza |

```bash
DOBLE_OPEN_FINANCE_LATENCIA_MS=1000 DOBLE_KYC_FALLAR=true docker compose up -d
```

Sin ninguna variable, los dobles no alteran el comportamiento funcional: es el mismo ambiente que se despliega. Para volver a ese estado, `docker compose up -d` sin variables recrea solo los servicios que cambiaron.

## Pruebas y CI

Cada proyecto: `pip install -e ".[test]" && pytest -m "not integration and not contract" --allow-hosts=127.0.0.1,::1 --cov`.

El CI de backend es el workflow `backend-unit-tests.yml` del PR #10: corre las pruebas unitarias de los servicios que cambiaron, con cobertura y reporte JUnit. Un test rojo falla el pipeline (HU-85).

| Marcador | Corre en |
| --- | --- |
| *(sin marcador)* | Workflow unitario: sin red ni BD |
| `integration` | En local, contra un PostgreSQL con el DDL del servicio (aún no corre en CI) |
| `contract` | Workflow `backend-contract-tests.yml`: Pact, consumidores y luego proveedores (HU-88) |

Contratos (PI-01): `python apps/backend/scripts/verify_contracts.py` corre lo mismo que el CI. Cada consumidor genera su pacto en `<consumidor>/pacts/` y después cada proveedor del núcleo lo verifica; si un cambio del núcleo rompe un pacto, el job `backend-pact` falla y el PR no se integra. Los servicios participantes se declaran en `CONSUMERS` y `PROVIDERS` del script. Requiere Python 3.12 (`pact-python` no publica wheels para 3.14).

## Estado

| Servicio | Estado |
| --- | --- |
| `bff-web`, `bff-movil` | Solo README; se implementan sobre `bff-arquetipo` en sus HU |
| `ms-*` restantes | Solo README; generar con el script al tomar su HU |
