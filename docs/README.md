# Documentación de arquitectura

Documentación del caso Solventa. El código de cada experimento o servicio vive
fuera de aquí; esta carpeta guarda lo que se entrega y se sustenta.

| Carpeta | Contenido |
|---|---|
| `architecture/` | Vistas (funcional, información, despliegue), escenarios de calidad y ASR. |
| `architecture/decisions/` | ADRs, numerados `NNNN-titulo-en-kebab-case.md`. |
| `experiments/` | Un subdirectorio por experimento: diseño y guía técnica. |

## Experimentos

| ID | Documento de diseño | Guía técnica | Implementación |
|---|---|---|---|
| HA-08 | [Diseño](experiments/ha-08/Diseno_Experimento_HA-08.md) | [Guía técnica](experiments/ha-08/Guia_Tecnica_HA-08.md) | [`experiments/ha-08-cqrs-read-model/`](../experiments/ha-08-cqrs-read-model/) |

## Convención

Cada experimento aporta **dos documentos**: el de **diseño** (hipótesis,
variables, criterios de aceptación, amenazas a la validez) y la **guía
técnica** (montaje, código, dataset, protocolo de ejecución). Los resultados y
el informe final se agregan al mismo subdirectorio cuando existan.
