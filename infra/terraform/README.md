# Infraestructura como código — Terraform

IaC de la infraestructura AWS de Solventa (VPC, EKS, RDS, ElastiCache, MSK, WAF, KMS), alineada con la vista de despliegue documentada en la wiki (`Diagramas-arquitectura-semana-4`).

Cubre dos ambientes distintos:
- **Ambiente mínimo de producto** (HU-78): despliegue destructible para evidenciar ambientes iguales.
- **Ambiente de experimentos** (HU-89): separado del anterior, para no contaminar con carga de K6 la evidencia funcional del ambiente mínimo.

Pendiente de implementación.
