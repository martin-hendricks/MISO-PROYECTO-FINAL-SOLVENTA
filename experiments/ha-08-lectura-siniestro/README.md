# Experimento HA-08 — Modelo de lectura de baja latencia para el estado de siniestro

Evalúa si CQRS (proyección materializada + caché) permite cumplir `EC-LAT-11` (p95 ≤ 150ms) en la consulta de estado de siniestro, y determina el nivel mínimo de complejidad necesario.

Diseño completo, hipótesis, criterios de aceptación y amenazas a la validez: `Diseno_Experimento_HA-08.md` en la wiki.
Guía técnica de montaje: `Guia_Tecnica_HA-08.md` en la wiki.

Bitácora técnica de la ejecución: [`INFORME.md`](INFORME.md).
Auditoría del experimento (verificación de cifras, brechas frente al diseño y coherencia con la arquitectura de semana 5): [`AUDITORIA_EXTERNA_HA-08.md`](AUDITORIA_EXTERNA_HA-08.md).

**Estado:** pendiente de implementación (siguiente iteración).

Montaje autocontenido y aislado de las apps de producto (`apps/`) — no depende de `ms-siniestros` real. Es un spike desechable de arquitectura, no un despliegue de producto.
