# Plan de implementación — Terraform ambiente mínimo (HU-78)

Trazabilidad: [Vista de despliegue — AWS](https://github.com/martin-hendricks/MISO-PROYECTO-FINAL-SOLVENTA/wiki/Hoja-de-trabajo-semana-5#13-vista-de-despliegue--aws) (VC-003) · HU-78 *Red y clúster cloud (mínimo)*.

## Decisiones tomadas

| Decisión | Valor | Razón |
| --- | --- | --- |
| Alcance | Solo ambiente mínimo (HU-78) | El ambiente de experimentos (HU-89) queda para una pasada posterior |
| Frontera Terraform / Kubernetes | Terraform hasta los add-ons del clúster; los 12 microservicios en manifiestos `k8s/` | `terraform destroy` debe dejar la cuenta limpia; redesplegar un microservicio no debe pasar por un apply de infraestructura; el autoescalado de HA-10 se ajusta en un HPA |
| Backend de estado | Local, con `backend.tf.example` documentado | Ambiente destructible de vida corta con un solo dueño; migrar a S3 es `terraform init -migrate-state`, sin recrear nada |
| Ejecución | Escribir + `fmt` + `validate`; **no se toca AWS** | `plan`/`apply` consumen créditos; esa decisión es del equipo |
| Cómputo | EKS, **no** ECS Fargate | Estrategia de pruebas §4.4: *"Alineado al modelo de despliegue; no se usa ECS Fargate"* |

## Estructura

```
infra/terraform/
├── README.md
├── PLAN.md
├── environments/
│   └── minimo/              # HU-78
│       ├── main.tf          # composición de módulos
│       ├── variables.tf
│       ├── outputs.tf
│       ├── providers.tf
│       ├── versions.tf
│       ├── backend.tf.example
│       └── terraform.tfvars.example
└── modules/
    ├── network/             # VPC, subredes pública/privadas/datos, IGW, NAT, rutas
    ├── security_groups/     # SG por tier: ALB, nodos EKS, RDS, Redis, MSK
    ├── kms/                 # llaves CMK: RDS, MSK, Redis, S3, Secrets
    ├── secrets/             # Secrets Manager: credenciales de BD y de terceros
    ├── eks/                 # control plane, node groups A y B, IRSA, OIDC
    ├── eks_addons/          # ALB Controller, Cluster Autoscaler, External Secrets (helm_release)
    ├── ecr/                 # un repositorio por microservicio
    ├── rds_polizas/         # PostgreSQL + réplica de lectura ACTIVA (sirve tráfico)
    ├── rds_siniestros/      # PostgreSQL Multi-AZ, standby PASIVO (no sirve tráfico)
    ├── elasticache/         # Redis: CacheOF / CacheOD
    ├── msk/                 # Kafka: BusEventos, ColaPagos, TopicoTelemetria
    ├── alb/                 # Application Load Balancer en subred pública
    ├── edge/                # WAF, CloudFront, API Gateway, S3 hosting SPA
    ├── s3_evidencias/       # bucket de evidencia de siniestros
    └── observability/       # CloudWatch log groups, alarmas, base para Prometheus/Grafana
```

## Correspondencia con el diagrama de despliegue

| Nodo del diagrama | Módulo | Nota de arquitectura |
| --- | --- | --- |
| VPC Solventa, subred pública, subredes privadas AZ-a/AZ-b, subred de datos | `network` | Multi-AZ activo-activo (EC-DISP-06, RTO ≤ 10 min) |
| Application Load Balancer | `alb` | En subred pública |
| EKS Node Group AZ-a + réplica AZ-b | `eks` | **Grupo A**: `ms-cotizacion` (MotorRating) + `ms-perfilamiento` (MotorRiesgo), curvas de carga independientes, escalamiento vertical, warm pool, capacidad ≤ 60 s (EC-ESC-02). **Grupo B**: resto de microservicios, BFFs y adaptadores |
| `DBPolizas` — RDS PostgreSQL | `rds_polizas` | Redundancia **ACTIVA**: réplica de lectura sirve tráfico, RPO ≤ 30 s (EC-LAT-10) |
| `DBSiniestros` — RDS PostgreSQL | `rds_siniestros` | Redundancia **PASIVA**: standby Multi-AZ que no sirve tráfico (EC-DISP-06 / EC-DISP-07) |
| ElastiCache Redis | `elasticache` | `CacheOF` y `CacheOD`, TTL por fuente |
| MSK (Kafka) | `msk` | `BusEventos`, `ColaPagos`, `TopicoTelemetria`; contrapresión, retención duradera, grupos de consumidores (EC-ESC-03) |
| API Gateway, AWS WAF, CloudFront, S3 hosting SPA Angular | `edge` | Borde fuera de la VPC |
| AWS KMS | `kms` | Cifrado de RDS, MSK, Redis, S3 y Secrets |
| Secrets Manager | `secrets` | Credenciales de BD y de terceros |
| CloudWatch + Prometheus/Grafana | `observability` | CloudWatch nativo; Prometheus/Grafana se instalan como add-on |
| S3 evidencia de siniestros | `s3_evidencias` | Versionado y cifrado con CMK |

Los 12 microservicios, los 6 adaptadores y el `Sincronizador` **no** son recursos de Terraform: van en `k8s/` como manifiestos, según la frontera acordada.

## Bloques de implementación

Cada bloque lo escribe un agente con modelo Sonnet; la integración y revisión es de esta sesión.

| Bloque | Módulos | Depende de |
| --- | --- | --- |
| **1 · Base** | `network`, `security_groups`, `kms`, `secrets` | — |
| **2 · Datos** | `rds_polizas`, `rds_siniestros`, `elasticache`, `msk` | Bloque 1 |
| **3 · Cómputo** | `eks`, `eks_addons`, `ecr` | Bloque 1 |
| **4 · Edge y observabilidad** | `alb`, `edge`, `s3_evidencias`, `observability` | Bloques 1 y 3 |
| **5 · Composición** | `environments/minimo/*`, README | Todos |

## Convenciones

Heredadas del patrón del repo de DevOps (`Universidad/devops/MISW-4304-DevOps/terraform`), adaptadas a estos servicios:

- Nombres: `${var.project_name}-${var.environment}-<recurso>`, con `project_name = "solventa"`.
- `locals.common_tags` en cada módulo: `Project`, `Environment`, `ManagedBy = "terraform"`, más `var.tags`.
- Cada módulo con `main.tf`, `variables.tf`, `outputs.tf`; `versions.tf` solo donde haga falta un provider extra.
- Toda variable con `type` y `description`; `sensitive = true` en credenciales.
- `terraform { required_version = ">= 1.5.0" }`, provider AWS `~> 5.0`.
- Cifrado en reposo activado en todo servicio que lo soporte, con CMK del módulo `kms`.
- Flags de costo (`single_nat_gateway`, tamaños de instancia, `msk_broker_count`) parametrizados para poder bajar el ambiente a mínimo gasto.
- Destructibilidad (HU-78): `skip_final_snapshot` y `deletion_protection = false` por defecto en el ambiente mínimo, de modo que `terraform destroy` deje la cuenta limpia.

## Criterio de terminado

- [x] `terraform fmt -check -recursive` sin diferencias.
- [x] `terraform validate` en `environments/minimo` sin errores.
- [x] Cada nodo del diagrama de despliegue tiene módulo correspondiente y está trazado en la tabla de arriba.
- [x] `README.md` documenta cómo levantar y destruir el ambiente.
- [x] No se ejecutó `plan` ni `apply`: el ambiente no se creó en esta pasada.

## Estado — implementado

15 módulos y 62 archivos `.tf`. `terraform init -backend=false` resuelve los 15 módulos y `terraform validate` pasa limpio.

Pendientes conocidos, a resolver antes del primer `apply`:

| Pendiente | Detalle |
| --- | --- |
| Versiones de charts de Helm | `eks_addons` fija ALB Controller 1.8.1, Cluster Autoscaler 9.37.0, External Secrets 0.9.20, Metrics Server 3.12.1. Contrastar con Artifact Hub: no se verificaron contra el registro real |
| `.terraform.lock.hcl` | El `.gitignore` de la raíz lo excluye (línea 26). Debería versionarse para que el equipo comparta versiones de provider |
| Brokers de MSK | `msk_number_of_broker_nodes` debe ser múltiplo del número de AZs de las subredes de datos |
| Endpoint público de EKS | `eks_public_access_cidrs` viene abierto (`0.0.0.0/0`); restringir antes de dejar el ambiente arriba |
| Versiones de EKS y RDS | `kubernetes_version = "1.31"` y `engine_version = "16.4"` no se validaron contra la API de AWS, porque no se corrió `plan` |

## Workloads — `infra/k8s/`

Implementados en la misma pasada, del otro lado de la frontera. Chart Helm genérico (`charts/microservicio/`) instanciado por 14 archivos de `values/`, más los manifiestos transversales de `platform/`. `helm lint --strict` pasa y los 14 componentes renderizan y parsean.

El contrato con esta infraestructura quedó verificado: `nodeSelector` sobre `solventa.io/scaling-group`, toleration al taint **solo** en el Grupo A, `topologySpreadConstraints` sobre zona (sin ellos el multi-AZ de EC-DISP-06 sería nominal), y los nombres de Secrets Manager coinciden con los que crea `modules/secrets`.

### IRSA de aplicación — `modules/irsa_aplicacion`

Cinco componentes hablan con AWS y necesitan un rol propio: `ms-siniestros` (escribe evidencia en S3) y `ms-parametrico`, `ms-pagos`, `analitica`, `notificaciones` (consumen MSK con autenticación IAM). `modules/eks_addons` solo cubre los add-ons del clúster, así que se añadió un módulo aparte.

Cada rol lleva una *trust policy* atada a `system:serviceaccount:<namespace>:<componente>`, de modo que un componente no puede asumir el rol de otro. Las políticas son mínimas y acotadas por recurso:

| Componente | Permisos |
| --- | --- |
| `ms-siniestros` | `PutObject`/`GetObject` sobre el bucket de evidencias (sin borrado: la evidencia es auditable y su expiración la gobierna la lifecycle policy), más `kms:GenerateDataKey` sobre la CMK del bucket |
| `ms-parametrico` | MSK acotado al tópico `TopicoTelemetria` y a su grupo de consumidores |
| `ms-pagos` | Idem, sobre `ColaPagos` |
| `analitica` y `notificaciones` | Idem, sobre `BusEventos` |

El output `irsa_role_arns` alimenta `serviceAccount.roleArn` de los values correspondientes. Como el ARN incluye el account id, solo se conoce tras el `apply`; los cinco values indican el comando exacto para obtenerlo.

## Fuera de alcance de esta pasada

- **HU-89 — ambiente de experimentos**: VPC aislada, EKS acotado 1→4 réplicas, K6 apuntando a cotización.
- **Pipeline de CI/CD**: los `values/` dejan el tag de imagen como TODO, a resolver en el pipeline.
