# Despliegue del canal de telemetría paramétrica

Runbook para llevar al clúster el cambio de `feature/telemetria-parametrica`:
`ms-parametrico` (`:ApiTelemetria`) publica en `TopicoTelemetria` y `ms-siniestros`
(`:MotorParametrico`) lo consume. Diseño y evidencia: `odd/tasks/telemetria-parametrica.md`.

> **Orden obligatorio: Terraform primero, merge después.** `ms-parametrico` ahora tiene
> `Dockerfile` y `infra/k8s/values/ms-parametrico.yaml`, así que el job `discover` de
> `deploy.yml` lo despliega en el primer merge a `develop`. Ese deploy corre el Job
> `crear-topico-telemetria` con la ServiceAccount `ms-parametrico`. Si el rol IRSA no tiene
> todavía `kafka-cluster:CreateTopic`, el Job falla (`backoffLimit: 2`) y el deploy se detiene.

## 1. Cambio en Terraform

Único archivo: `infra/terraform/modules/irsa_aplicacion/main.tf`, mapa `local.msk_consumers`.

| Componente | Antes | Después |
| --- | --- | --- |
| `ms-parametrico` | Consumidor de `TopicoTelemetria`, grupo `ms-parametrico` | **Productor y dueño** del tópico: `topics = ["TopicoTelemetria"]`, `consumer_groups = []`, `crear_topicos = true` |
| `ms-siniestros` | Solo S3 (evidencia) | Además **consume** `TopicoTelemetria` con el grupo `ms-siniestros-telemetria` |

No cambia la trust policy de ningún rol. `ms-siniestros` ya tenía rol por S3: `all_components` une los dos mapas por la misma clave, así que sigue siendo un único rol (`solventa-minimo-ms-siniestros-irsa`), ahora con dos políticas adjuntas.

### Plan esperado

```bash
cd infra/terraform/environments/minimo
terraform plan
```

Solo debe aparecer esto. Cualquier otra cosa (sobre todo un `destroy` o `replace` de roles) es una señal para detenerse y revisar:

| Recurso | Acción | Por qué |
| --- | --- | --- |
| `module.irsa_aplicacion.aws_iam_policy.msk["ms-parametrico"]` | `update in-place` | Sale el statement `ConsumerGroupAccess` (ya no tiene grupo) y entra `TopicProvisioning` (`CreateTopic`, `AlterTopic`, `DescribeTopic` sobre `TopicoTelemetria`) |
| `module.irsa_aplicacion.aws_iam_policy.msk["ms-siniestros"]` | `create` | Política `solventa-minimo-ms-siniestros-msk`: `Connect`/`DescribeCluster`, `ReadData`/`WriteData`/`DescribeTopic` sobre `TopicoTelemetria`, `AlterGroup`/`DescribeGroup` sobre `ms-siniestros-telemetria`, KMS del clúster |
| `module.irsa_aplicacion.aws_iam_role_policy_attachment.msk["ms-siniestros"]` | `create` | Adjunta esa política al rol existente de `ms-siniestros` |

`Plan: 2 to add, 1 to change, 0 to destroy.`

```bash
terraform apply
```

Validado sin estado (`hashicorp/terraform:1.9.8`: `fmt -check` y `validate` sobre el módulo); el `plan` real contra la cuenta queda por correr.

### Lo que NO hace falta tocar en Terraform

- **ECR:** `solventa-minimo-ms-parametrico` ya está en `modules/ecr/variables.tf`.
- **Security group de MSK:** la regla 9098 desde los nodos de EKS ya existe (`docs/validacion-kafka-r6.md`).
- **MSK:** el tópico no lo crea Terraform (AWS no expone API de tópicos), lo crea el Job. `num_partitions=6` del módulo es solo el default del broker; el Job pide 12 explícitamente.

## 2. Secreto del proveedor

`ms-parametrico` lee `clientId`/`clientSecret` de `solventa-minimo-telemetria_iot-credentials`. En `minimo` el módulo `secrets` los siembra con `PENDIENTE_telemetria_iot`. El servicio arranca con eso, y el proveedor debe enviar esos valores en `X-Telemetria-Cliente` / `X-Telemetria-Secreto`. Para un proveedor real:

```bash
aws secretsmanager put-secret-value \
  --secret-id solventa-minimo-telemetria_iot-credentials \
  --secret-string '{"clientId":"<id>","clientSecret":"<secreto>"}'
```

External Secrets lo sincroniza al secreto `ms-parametrico-telemetria-iot` del namespace. Si el secreto quedara vacío, `ms-parametrico` responde 500 a toda ingesta, por diseño: sin credenciales configuradas no acepta nada.

## 3. Merge y deploy

Al mergear a `develop`, `deploy.yml`:

1. Construye y publica la imagen de `ms-parametrico` y despliega su chart (`kafka.necesitaMsk: true` inyecta `MSK_BOOTSTRAP_BROKERS`).
2. Paso **"Crear el tópico TopicoTelemetria (una sola vez)"**: aplica `infra/k8s/platform/crear-topico-telemetria.yaml` (`python -m app.crear_topico`, 12 particiones, factor de replicación 2) y espera que el Job termine (`Complete`). Si ya está `Complete` de un deploy anterior, se lo salta.
3. Redespliega `ms-siniestros`, ahora con `MSK_BOOTSTRAP_BROKERS` y el consumidor activo.

El orden entre servicios de la matrix no importa. Si `ms-siniestros` arranca antes de que exista el tópico, el consumidor espera la metadata y reintenta en segundo plano sin tumbar el pod. Si `ms-parametrico` recibe un evento antes de que exista el tópico, responde 503 y el proveedor reintenta.

## 4. Verificación en el clúster

```bash
kubectl -n solventa get job crear-topico-telemetria        # COMPLETIONS 1/1
kubectl -n solventa logs job/crear-topico-telemetria       # topico_creado=TopicoTelemetria
kubectl -n solventa logs deploy/ms-siniestros | grep consumidor_telemetria_iniciado
kubectl -n solventa logs deploy/ms-parametrico | grep publicador_telemetria_iniciado
```

Evento de prueba desde dentro del clúster (el servicio no está expuesto por el ALB):

```bash
kubectl -n solventa port-forward svc/ms-parametrico 8013:8080 &
curl -s localhost:8013/v1/telemetria/vuelos/eventos \
  -H 'Content-Type: application/json' \
  -H 'X-Telemetria-Cliente: <clientId>' -H 'X-Telemetria-Secreto: <clientSecret>' \
  -d '{"reporte_id":"DEPLOY-1","vuelo":"AV234","fecha":"2026-11-20","retraso_minutos":190,
       "reportado_en":"2026-11-20T14:00:00Z","cobertura":{"umbral":"120","monto":"1000.00"}}'
# 202 {"evento_id":"vuelos:DEPLOY-1","aceptado":true}
```

Debe aparecer el siniestro `vuelos:DEPLOY-1` en `ms_siniestros.siniestro` con estado `pagado`, y la métrica `solventa_siniestros_telemetria_mensajes_total{resultado="procesado"}` en 1.

## Fallas probables

| Síntoma | Causa | Acción |
| --- | --- | --- |
| Job `crear-topico-telemetria` en `Error`, log `TopicAuthorizationFailed` o `Access denied` | No se aplicó Terraform antes del merge | `terraform apply`, `kubectl -n solventa delete job crear-topico-telemetria` y relanzar el workflow |
| `ms-siniestros` loguea `consumidor_telemetria_sin_conexion` en bucle | Sin `kafka-cluster:Connect` (falta la política nueva) o sin regla 9098 | Revisar el apply; el resto de `ms-siniestros` sigue sirviendo |
| `GroupAuthorizationFailed` en `ms-siniestros` | `MSK_CONSUMER_GROUP_TELEMETRIA` no coincide con el grupo del rol | Debe ser `ms-siniestros-telemetria` en ambos |
| `ms-parametrico` responde 500 `Credenciales de telemetría no configuradas` | Secreto vacío o External Secrets sin sincronizar | Paso 2 |
| `ms-parametrico` responde 503 `topico_no_disponible` | Tópico sin crear o MSK inaccesible | Paso 3.2 y la regla 9098 |

## Reversión

Revertir el merge saca el consumidor de `ms-siniestros` y deja `ms-parametrico` sin imagen nueva. El Deployment viejo de `ms-parametrico` hay que borrarlo a mano con `helm uninstall ms-parametrico -n solventa`, porque el pipeline no desinstala. El tópico y los permisos IAM pueden quedarse: no los usa nadie más. Para revertir Terraform, `git revert` del cambio en `irsa_aplicacion` y `terraform apply`.
