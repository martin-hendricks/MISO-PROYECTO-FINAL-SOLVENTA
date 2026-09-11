#!/usr/bin/env bash
# Sube evidencia al repositorio: commit y push de las rutas indicadas mas el
# estado del experimento. Envoltorio de `subir_evidencia` para usarlo desde el
# orquestador sin cargar alli todo el protocolo.
#
#   ./scripts/subir.sh "mensaje" ruta [ruta...]
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"
subir_evidencia "$@"
