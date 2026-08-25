# Infraestructura transversal

Infraestructura compartida entre servicios. **Vacío por ahora.**

Contenido previsto:

- Composición local de varios servicios (`docker-compose.yml` de integración).
- Observabilidad compartida: Prometheus, Grafana, dashboards.
- Manifiestos de despliegue, si se llega a esa etapa.

> La observabilidad del experimento HA-08 vive **dentro** del experimento
> (`experiments/ha-08-cqrs-read-model/observability/`) a propósito: debe ser
> reproducible de forma aislada y con límites de recursos propios. Solo se
> promueve aquí lo que efectivamente compartan varios servicios.
