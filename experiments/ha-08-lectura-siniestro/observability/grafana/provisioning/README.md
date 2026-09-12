# Provisioning de Grafana

Directorio montado en `/etc/grafana/provisioning` dentro del contenedor. Pendiente de agregar `datasources/prometheus.yml` (apuntando a `http://prometheus:9090`) y un dashboard con p95/p99 de `ha08_estado_duration` por brazo, `ha08_projection_lag_seconds` y `ha08_cache_hits_total` / `ha08_cache_misses_total`, al momento de ejecutar el experimento.
