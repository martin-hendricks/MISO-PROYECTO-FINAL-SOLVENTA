#!/usr/bin/env bash
# CAMPANA COMPLETA del experimento HA-01, desatendida.
#
# Encadena los cuatro bloques en el orden 3 -> 1 -> 2 -> 4 y consolida la
# evidencia al terminar cada uno, de modo que si la campana se corta a mitad
# de la noche lo ya medido esta analizado y con sus figuras.
#
# Por que el bloque 3 va primero: es el unico que ejercita el protocolo con
# los dos extremos de trafico (200 y 10 sol/s), las dos politicas del
# interruptor y los dos niveles de acierto. Funciona como compuerta: si alguna
# de sus corridas falla, la campana SE DETIENE y espera a una persona, en vez
# de gastar nueve horas mas sobre un montaje que ya dio senales de problema.
#
# Se lanza desde el Programador de tareas de Windows (lanzar_campana.ps1) para
# que no dependa de ninguna terminal ni de ninguna sesion abierta.
#
#   Estado en vivo : results/campana_estado.txt
#   Traza completa : results/campana.log
#   Corridas a repetir: results/corridas_fallidas.txt
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${RAIZ}"
ESTADO="${RAIZ}/results/campana_estado.txt"
FALLIDAS="${RAIZ}/results/corridas_fallidas.txt"
CANDADO="${RAIZ}/results/campana.lock"
ORDEN=(${CAMPANA_BLOQUES:-3 1 2 4})

marca() {  # una linea con marca de tiempo, en la traza y en el estado
  local linea="$(date '+%Y-%m-%d %H:%M:%S')  $*"
  echo "CAMPANA ${linea}"
  echo "${linea}" >> "${ESTADO}"
}

fallidas() { [ -f "${FALLIDAS}" ] && wc -l < "${FALLIDAS}" | tr -d ' ' || echo 0; }

# --- una sola campana a la vez -----------------------------------------
if [ -f "${CANDADO}" ] && kill -0 "$(cat "${CANDADO}")" 2>/dev/null; then
  echo "ya hay una campana en curso (PID $(cat "${CANDADO}")); no se lanza otra" >&2
  exit 1
fi
echo $$ > "${CANDADO}"
trap 'rm -f "${CANDADO}"' EXIT

: > "${ESTADO}"
marca "INICIO de la campana | bloques en orden: ${ORDEN[*]}"

# --- comprobaciones previas --------------------------------------------
if ! docker info >/dev/null 2>&1; then
  marca "DETENIDA: Docker no responde"; exit 1
fi
if ! curl -sf -o /dev/null http://localhost:8000/health; then
  marca "la API no responde; se levanta el montaje"
  docker compose up -d >/dev/null 2>&1
  sleep 15
  curl -sf -o /dev/null http://localhost:8000/health \
    || { marca "DETENIDA: el montaje no arranca"; exit 1; }
fi
marca "montaje verificado: Docker y API responden"

# Plan del experimento completo (lo lee estado.py) y estado inicial.
./scripts/generar_plan.sh >/dev/null 2>&1 || marca "AVISO: no se pudo generar el plan"
python scripts/estado.py >/dev/null 2>&1 || true
./scripts/subir.sh "Estado HA-01: inicio de campana (bloques ${ORDEN[*]})" results/plan.txt >/dev/null 2>&1 || true

# --- bloques -----------------------------------------------------------
for b in "${ORDEN[@]}"; do
  antes=$(fallidas)
  marca "BLOQUE ${b}: inicio"
  rc=0
  case "${b}" in
    1) ./scripts/run_block1.sh 3 || rc=$? ;;
    2) ./scripts/run_block2.sh 3 || rc=$? ;;
    3) ./scripts/run_block3.sh   || rc=$? ;;
    4) ./scripts/run_block4.sh   || rc=$? ;;
    d) ./scripts/run_decisivo.sh || rc=$? ;;   # A, B y C con proveedor lento
    r) ./scripts/run_plan_reducido.sh || rc=$? ;;   # plan de la noche
    *) marca "bloque desconocido: ${b}"; continue ;;
  esac
  nuevas=$(( $(fallidas) - antes ))
  marca "BLOQUE ${b}: fin | codigo ${rc} | corridas fallidas en el bloque: ${nuevas}"

  # Consolidar YA: si la campana se corta mas tarde, lo medido queda analizado.
  ./scripts/collect_results.sh >/dev/null 2>&1 \
    && marca "BLOQUE ${b}: evidencia consolidada (CSV y figuras)" \
    || marca "BLOQUE ${b}: AVISO, fallo la consolidacion (los datos crudos estan)"
  ./scripts/subir.sh "Resultados HA-01: CSV y figuras tras el bloque ${b}" \
    results/analysis >/dev/null 2>&1 || true

  if [ "${rc}" -ne 0 ]; then
    marca "DETENIDA: el bloque ${b} aborto por fallos seguidos; el montaje parece caido"
    exit 1
  fi
  if [ "${b}" = "3" ] && [ "${nuevas}" -gt 0 ]; then
    marca "DETENIDA en la compuerta: el bloque 3 tuvo ${nuevas} corrida(s) fallida(s). Revisar antes de seguir"
    exit 1
  fi
done

marca "FIN de la campana | corridas fallidas en total: $(fallidas)"

# Respaldo completo de las series temporales: una sola instantanea vigente.
rm -f results/prometheus/tsdb_*.tgz
./scripts/instantanea_prometheus.sh >/dev/null 2>&1 \
  && marca "instantanea de Prometheus guardada en results/prometheus" \
  || marca "AVISO: no se pudo sacar la instantanea de Prometheus"
python scripts/estado.py >/dev/null 2>&1 || true
./scripts/subir.sh "Evidencia HA-01: cierre de campana (instantanea de Prometheus y traza)" \
  results/prometheus results/campana.log results/plan.txt >/dev/null 2>&1 || true
exit 0
