# Validación de Kafka R6: outbox → BusEventos → notificaciones

Runbook para comprobar, contra el clúster real, que un evento de dominio
escrito en el outbox de un microservicio llega hasta `notificaciones`.

## Arquitectura del circuito

```
ms-* (transacción) ──INSERT──▶ <esquema>.outbox_evento
                                        │  publicado_en IS NULL
                                        ▼
                              outbox-relay (polling, 1 réplica)
                                        │  SASL/IAM (IRSA)
                                        ▼
                              MSK · tópico BusEventos
                                        │  consumer group "notificaciones"
                                        ▼
                              notificaciones ──▶ notificaciones.notificacion
```

`outbox-relay` lee seis esquemas: `ms_cotizacion`, `ms_suscripcion`,
`ms_pagos`, `ms_perfilamiento` (base compartida), `ms_polizas` y
`ms_siniestros` (instancias propias). Publica en un único tópico, con la key
del mensaje igual a `agregado_id` para preservar el orden por agregado.

## Estado verificado el 2026-11-11 (antes de este cambio)

| Comprobación | Resultado |
| --- | --- |
| `kubectl -n solventa get deploy outbox-relay` | no existe |
| `infra/k8s/values/outbox-relay.yaml` | no existía (el job `discover` lo omitía) |
| `aws iam get-role --role-name solventa-minimo-outbox-relay-irsa` | no existía |
| Tópicos en MSK (`AWS/Kafka` en CloudWatch) | solo `__amazon_msk_canary` y `__consumer_offsets` |
| `MSK_BOOTSTRAP_BROKERS` en el pod de `notificaciones` | vacío → consumidor nunca arrancó |
| IRSA en la ServiceAccount de `notificaciones` | sin `role-arn` |
| `MSK_CONSUMER_GROUP` vs grupo autorizado por IAM | `notificaciones-cg` vs `notificaciones` |

`auto.create.topics.enable=false`, así que ningún tópico se crea solo.

## Pasos (en orden)

### 1. Aplicar Terraform (crea el rol IRSA del relay)

```bash
cd infra/terraform/environments/minimo
terraform plan   # revisar: aws_iam_role/policy de solventa-minimo-outbox-relay-irsa
terraform apply
```

El rol existe solo después del apply. Sin él, el pod arranca pero no puede
autenticarse contra MSK (falla `publicador_msk_iniciado`).

### 2. Desplegar (CI o manual)

Por CI: merge a `develop`/`main` toca `apps/backend/**` e `infra/k8s/values/**`,
así que el workflow `Deploy` lo incluye automáticamente en la matrix.

Por manual, replicando lo que hace el workflow:

```bash
SERVICE=outbox-relay
IMAGE="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/solventa-minimo-$SERVICE"
docker build --target runtime -f apps/backend/$SERVICE/Dockerfile \
  -t "$IMAGE:$GIT_SHA" apps/backend/$SERVICE
docker push "$IMAGE:$GIT_SHA"

BROKERS=$(aws kafka get-bootstrap-brokers \
  --cluster-arn "$(aws kafka list-clusters --cluster-name-filter solventa-minimo-msk \
    --query 'ClusterInfoList[0].ClusterArn' --output text)" \
  --query BootstrapBrokerStringSaslIam --output text)

helm upgrade --install $SERVICE infra/k8s/charts/microservicio \
  --namespace solventa \
  --values infra/k8s/values/$SERVICE.yaml \
  --set imagen.repositorio="$IMAGE" \
  --set imagen.tag="$GIT_SHA" \
  --set "serviceAccount.roleArn=arn:aws:iam::$AWS_ACCOUNT_ID:role/solventa-minimo-$SERVICE-irsa" \
  --set-string "variablesEntorno[0].valor=${BROKERS//,/\\,}" \
  --timeout 3m
```

El índice `0` corresponde a `MSK_BOOTSTRAP_BROKERS` en
`infra/k8s/values/outbox-relay.yaml`; el workflow lo resuelve por nombre con
`yq`, no a mano. Las comas del string de brokers se escapan porque Helm las
trata como separador de asignaciones en `--set-string`.

### 3. Crear el tópico (automático, una sola vez)

El deploy de `outbox-relay` aplica
`infra/k8s/platform/crear-topico-buseventos.yaml` justo después del
`helm upgrade`. Ese Job:

- usa la imagen que acaba de construir CI y la ServiceAccount `outbox-relay`
  (la única con `kafka-cluster:CreateTopic`);
- solo se aplica si no existe o si existe sin haber completado;
- un Job en estado `Complete` es el registro de que el tópico ya se creó, así
  que los deploys siguientes **no lo vuelven a ejecutar**.

```bash
kubectl -n solventa get job crear-topico-buseventos
kubectl -n solventa logs job/crear-topico-buseventos
```

Salida esperada: `topicos_creados=BusEventos` (o `topicos_sin_cambios=...` si
ya existía).

Si hay que recrearlo (por ejemplo, cambió el número de particiones):

```bash
kubectl -n solventa delete job crear-topico-buseventos
```

y el próximo deploy lo vuelve a ejecutar. También se puede correr a mano, sin
esperar al pipeline (el comando es idempotente):

```bash
kubectl -n solventa run crear-topico --rm -it --restart=Never \
  --image="$IMAGE:$GIT_SHA" \
  --overrides='{"spec":{"serviceAccountName":"outbox-relay"}}' \
  -- python -m app.crear_topico --brokers "$BROKERS" BusEventos
```


### 4. Sembrar un evento de prueba

`PolizaEmitida` es el único tipo que hoy produce notificación real (ver
limitaciones). Se inserta directo en el outbox, que es exactamente lo que hace
ms-polizas dentro de su transacción:

```bash
kubectl -n solventa exec -i deploy/ms-polizas -- python - <<'PY'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    motor = create_async_engine(os.environ["DATABASE_URL"])
    async with motor.begin() as c:
        await c.execute(text("""
            INSERT INTO ms_polizas.outbox_evento (id, tipo, agregado_id, payload)
            VALUES (gen_random_uuid(), 'PolizaEmitida', gen_random_uuid(),
              '{"poliza_id":"22222222-2222-2222-2222-222222222222",
                "usuario_id":"33333333-3333-3333-3333-333333333333",
                "numero":"POL-E2E-1","fin_vigencia":"2027-01-01"}')
        """))
    await motor.dispose()

asyncio.run(main())
PY
```

### 5. Verificar

**a) El relay publicó** (la fila deja de estar pendiente en ≤ 5 s por ciclo):

```bash
kubectl -n solventa exec -i deploy/outbox-relay -- python - <<'PY'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    motor = create_async_engine(os.environ["DATABASE_URL_MS_POLIZAS"])
    async with motor.connect() as c:
        for f in (await c.execute(text("""
            SELECT id, tipo, creado_en, publicado_en
            FROM ms_polizas.outbox_evento ORDER BY creado_en DESC LIMIT 5
        """))).all():
            print(f)
    await motor.dispose()

asyncio.run(main())
PY
```

`publicado_en` no nulo ⇒ salió hacia MSK.

**b) Notificaciones lo consumió:**

```bash
kubectl -n solventa exec -i deploy/notificaciones -- python - <<'PY'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    motor = create_async_engine(os.environ["DATABASE_URL"])
    async with motor.connect() as c:
        for f in (await c.execute(text("""
            SELECT notificacion_id, usuario_id, tipo, estado, creada_en
            FROM notificaciones.notificacion
            ORDER BY creada_en DESC LIMIT 5
        """))).all():
            print(f)
    await motor.dispose()

asyncio.run(main())
PY
```

`estado='enviada'` ⇒ circuito completo. `estado='fallida'` es esperado si el
usuario no tiene `dispositivo_push` registrado: el mensaje sí se consumió y
persistió.

**c) Señales en logs:**

```bash
kubectl -n solventa logs deploy/outbox-relay --since=10m \
  | grep -E 'publicador_msk_iniciado|fuente_outbox_sin_configurar|Falló la publicación|Ciclo de relay falló'
kubectl -n solventa logs deploy/notificaciones --since=10m \
  | grep -E 'consumidor_msk_iniciado|evento_ignorado|mensaje_msk_invalido|error_procesando'
```

## Limitaciones conocidas (no bloquean el circuito, sí el alcance funcional)

- `notificaciones` solo maneja `PolizaEmitida`, `PolizaRenovada`,
  `PolizaModificada` y `PolizaCancelada`, y exige `payload.usuario_id`.
  `PolizaRenovada/Modificada/Cancelada` no lo incluyen; `PolizaPorVencer` no
  está en `TIPOS_SOPORTADOS`. Los eventos de `ms_siniestros`
  (`EventoParametricoRecibido`, `SiniestroCambioEstado`, …) tampoco se manejan.
- Ninguno de los dos servicios emite un log por evento procesado; la prueba
  duradera es el estado en base de datos.
- El productor no fija `acks=all` ni idempotencia, pese a lo que describe el
  módulo MSK. La entrega es al-menos-una-vez y el consumidor deduplica por
  `UNIQUE (evento_origen_id, canal)`.
- `db/schema/07_ms_polizas.sql` define `outbox_id`/`tipo_evento`, mientras que
  el código y las migraciones de servicio usan `id`/`tipo`. En el clúster se
  aplican las de servicio, así que funciona; un bootstrap local desde
  `db/schema/` rompería el relay.
