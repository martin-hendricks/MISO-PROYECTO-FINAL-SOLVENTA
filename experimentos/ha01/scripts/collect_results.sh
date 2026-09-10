#!/usr/bin/env bash
# Consolida las corridas y produce las tablas del Anexo C.
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

echo "== consolidacion de resultados =="
curl -sf -o /dev/null "http://localhost:9090/-/healthy" \
  || fallar "Prometheus no responde: el analisis por fase lo necesita"

"${PY}" "${RAIZ}/scripts/analizar.py" \
  "${RAIZ}/results/raw" -o "${RAIZ}/results/analysis"

echo
echo "== figuras del informe =="
MSYS_NO_PATHCONV=1 docker compose --profile tools run --rm   figuras /work/scripts/graficas.py

echo
echo "Evidencia consolidada en results/analysis:"
ls -1 "${RAIZ}/results/analysis"
echo
echo "  resultados_por_fase.csv  todas las metricas, una fila por fase"
echo "  figuras/                 PNG a 200 ppp para pegar en el informe"
echo "  enlaces_grafana.md       un enlace por corrida, ya acotado a su ventana"
echo
echo "Evidencia cruda por corrida en results/raw/<brazo>_<run_id>/"
