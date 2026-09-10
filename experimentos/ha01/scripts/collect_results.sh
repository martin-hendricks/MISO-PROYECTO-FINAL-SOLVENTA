#!/usr/bin/env bash
# Consolida las corridas y produce las tablas del Anexo C.
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

echo "== consolidacion de resultados =="
curl -sf -o /dev/null "http://localhost:9090/-/healthy" \
  || fallar "Prometheus no responde: el analisis por fase lo necesita"

"${PY}" "${RAIZ}/scripts/analizar.py" \
  "${RAIZ}/results/raw" -o "${RAIZ}/results/analysis"

echo
echo "Archivos en results/analysis:"
ls -1 "${RAIZ}/results/analysis"
