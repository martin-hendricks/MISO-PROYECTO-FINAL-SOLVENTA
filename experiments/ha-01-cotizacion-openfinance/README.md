# Experimento HA-01 — Protección del presupuesto de latencia de la cotización embebida

Evalúa si tratar la llamada a Open Finance como una **actualización oportunista** (en vez de una dependencia bloqueante) permite cumplir `EC-LAT-01`/`EC-LAT-02` (p95 ≤ 250ms, p99 ≤ 500ms extremo a extremo) incluso con el proveedor externo degradado o caído (`EC-LAT-09`).

Diseño completo, hipótesis, criterios de aceptación y amenazas a la validez: `Diseno_Experimento_HA-01.md` en la wiki.
Guía técnica de montaje: `Guia_Tecnica_HA-01.md` en la wiki (pendiente, análoga a la de HA-08).

**Estado:** pendiente de implementación (código base generado; falta guía técnica detallada, ejecución y evidencia).

Reutiliza el patrón de infraestructura de `experiments/ha-08-lectura-siniestro/` (Docker Compose, Prometheus/Grafana, protocolo de corridas contrabalanceadas), pero es un montaje independiente y autocontenido — no depende de que HA-08 esté corriendo.
