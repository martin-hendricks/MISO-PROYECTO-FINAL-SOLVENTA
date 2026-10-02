# Infraestructura como código — Terraform

IaC de la infraestructura AWS de Solventa, alineada con la [vista de despliegue VC-003](https://github.com/martin-hendricks/MISO-PROYECTO-FINAL-SOLVENTA/wiki/Hoja-de-trabajo-semana-8#113-vista-de-despliegue--aws) de la wiki.

Cubre el **ambiente mínimo de producto** (HU-78): despliegue destructible que evidencia ambientes iguales. El **ambiente de experimentos** (HU-89) queda pendiente de una pasada posterior.

El plan de implementación, con las decisiones tomadas y la trazabilidad módulo a módulo contra el diagrama, está en [PLAN.md](PLAN.md).

## Estructura

```
infra/terraform/
├── environments/
│   └── minimo/        # HU-78 — composición de los módulos
└── modules/           # un módulo por servicio de la arquitectura
```

## Frontera con Kubernetes

Terraform crea la **plataforma**: clúster EKS, node groups, add-ons (ALB Controller, Cluster Autoscaler, External Secrets, Metrics Server), repositorios ECR, bases de datos, caché, bus de eventos y capa de borde.

Los **Deployments, Services y HPA de los 12 microservicios no viven aquí**: van en manifiestos de Kubernetes. Dos razones: HU-78 exige que `terraform destroy` deje la cuenta limpia, y redesplegar un microservicio no debería pasar por un apply de la infraestructura completa. El autoescalado de HA-10 (capacidad ampliada ≤ 60 s) se ajusta en un HPA, no reaplicando Terraform.

## Estado

El `.tfstate` es **local**. No hay backend remoto: el ambiente es destructible, de vida corta y con un solo operador. Si el equipo necesita compartirlo, `backend.tf.example` documenta la migración a S3 (`terraform init -migrate-state`, sin recrear recursos).

`.tfstate` y `.terraform/` están en el `.gitignore` de la raíz del repo.

## Uso

```bash
cd environments/minimo

cp terraform.tfvars.example terraform.tfvars   # ajustar valores
terraform init
terraform plan
terraform apply
```

Para destruir el ambiente y dejar la cuenta limpia, que es el criterio de aceptación de HU-78:

```bash
terraform destroy
```

Los defaults del ambiente mínimo (`skip_final_snapshot = true`, `deletion_protection = false`, `force_destroy = true` en los buckets) están puestos para que ese `destroy` no deje recursos huérfanos. **En un ambiente productivo real deben invertirse.**

## Costo

Varios servicios de esta arquitectura cobran por hora encendidos —EKS, las dos instancias RDS, MSK y los NAT gateways son los que más pesan. El ambiente está pensado para levantarse, evidenciar y destruirse, no para quedarse arriba.

Para bajar el gasto durante pruebas:

| Variable | Efecto |
|---|---|
| `single_nat_gateway = true` | Un solo NAT en vez de uno por AZ |
| `msk_number_of_broker_nodes` | Menos brokers de Kafka |
| `rds_*_instance_class` | Instancias más pequeñas |
| `node_group_*_desired_size` | Menos nodos de EKS |
| `enable_managed_prometheus = false` | Evita el workspace de AMP |

## Verificación

```bash
terraform fmt -check -recursive .
cd environments/minimo && terraform validate
```
