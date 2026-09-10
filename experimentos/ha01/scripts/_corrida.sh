#!/usr/bin/env bash
# Protocolo de UNA corrida (Anexo A del diseno, "Protocolo de una corrida").
# Lo comparten los tres bloques para que el procedimiento sea identico y la
# unica diferencia entre bloques sea que variable se mueve.
#
#   corrida <brazo> <run_id> <estado_degradado> [rate] [duracion]
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

corrida() {
  local ARM="${1:?brazo}" RUN_ID="${2:?run_id}" ESTADO="${3:-degradado}"
  local RATE="${4:-${K6_RATE:-100}}"
  # Duracion de cada fase. Los valores del protocolo son 120/120/60 s;
  # se parametrizan para poder correr un piloto corto que valide la tuberia
  # completa (k6 -> Prometheus -> analizar.py) sin gastar la ventana entera.
  local F_SANA="${FASE_SANA_S:-120}"
  local F_DEG="${FASE_DEGRADADA_S:-120}"
  local F_REC="${FASE_RECUPERACION_S:-60}"
  local DUR="${5:-$((F_SANA + F_DEG + F_REC))s}"
  local WARMUP="${K6_WARMUP:-60s}"
  local ETIQUETA="${ARM}_${RUN_ID}"
  local DEST="${RAIZ}/results/raw/${ETIQUETA}"
  mkdir -p "${DEST}"

  echo "############################################################"
  echo "# corrida ${ETIQUETA} | brazo=${ARM} estado=${ESTADO}"
  echo "#   acierto=${TARGET_HIT_RATE:-0.96} breaker=${BREAKER_POLICY:-rate} rate=${RATE}"
  echo "#   fases: sana ${F_SANA}s | degradada ${F_DEG}s | recuperacion ${F_REC}s"
  echo "############################################################"

  # -- 1. Reiniciar el estado volatil -------------------------------------
  # El interruptor debe arrancar CERRADO: si arrastrara el estado de la
  # corrida anterior, el tiempo hasta la apertura no seria medible.
  docker compose stop api >/dev/null
  docker compose exec -T redis redis-cli FLUSHALL >/dev/null
  docker compose exec -T redis redis-cli CONFIG RESETSTAT >/dev/null
  "${RAIZ}/infra/toxiproxy/states.sh" sano >/dev/null

  # -- 2. Arrancar con el brazo y precargar la cache ----------------------
  QUOTE_STRATEGY="${ARM}" docker compose up -d api >/dev/null
  esperar_api
  precargar --verificar

  # -- 3. Verificaciones PREVIAS: sin ellas la corrida no es comparable ---
  "${RAIZ}/scripts/verify_baseline.sh"
  "${RAIZ}/scripts/verify_provider.sh"

  # -- 4. Calentamiento NO contabilizado ---------------------------------
  # `--duration` no sobrescribe un escenario declarado en el script: la
  # duracion se pasa por -e DURATION, que el escenario si respeta.
  echo "-- calentamiento ${WARMUP} (no se contabiliza)"
  MSYS_NO_PATHCONV=1 docker compose --profile load run --rm \
    -e RATE="${RATE}" -e DURATION="${WARMUP}" \
    -e ARM="${ARM}" -e PROVIDER_STATE=warmup \
    -e UNIVERSO_CLIENTES="${UNIVERSO_CLIENTES}" -e POOL_STALE="${POOL_STALE}" \
    -e POOL_COLD="${POOL_COLD}" -e TARGET_HIT_RATE="${TARGET_HIT_RATE}" \
    -e MISS_STALE_FRACTION="${MISS_STALE_FRACTION}" \
    k6 run --quiet /scripts/cotizacion_fase.js >/dev/null 2>&1 || true

  # El calentamiento repuebla claves: se vuelve a precargar para que la
  # ventana de medicion empiece exactamente en la tasa de acierto objetivo.
  precargar

  # -- 5. Ventana de medicion con conmutacion EN CALIENTE ----------------
  echo "-- ventana de medicion ${DUR} a ${RATE} sol/s"
  MSYS_NO_PATHCONV=1 docker compose --profile load run --rm \
    -e RATE="${RATE}" -e DURATION="${DUR}" \
    -e ARM="${ARM}" -e RUN_ID="${RUN_ID}" -e PROVIDER_STATE="${ESTADO}" \
    -e UNIVERSO_CLIENTES="${UNIVERSO_CLIENTES}" -e POOL_STALE="${POOL_STALE}" \
    -e POOL_COLD="${POOL_COLD}" -e TARGET_HIT_RATE="${TARGET_HIT_RATE}" \
    -e MISS_STALE_FRACTION="${MISS_STALE_FRACTION}" \
    k6 run -o experimental-prometheus-rw \
      --summary-export /results/"${ETIQUETA}"/k6_summary.json \
      /scripts/cotizacion_fase.js > "${DEST}/k6_stdout.txt" 2>&1 &
  local K6=$!

  # Fases: sana 0-2 min, degradada 2-4 min, recuperacion 4-5 min.
  # Los percentiles se calculan POR FASE; agregarlas produciria un percentil
  # sin significado. Las marcas de tiempo se guardan para poder cortar.
  date +%s > "${DEST}/t_inicio"
  sleep "${F_SANA}"
  date +%s > "${DEST}/t_degradado"
  "${RAIZ}/infra/toxiproxy/states.sh" "${ESTADO}"
  sleep "${F_DEG}"
  date +%s > "${DEST}/t_recuperacion"
  "${RAIZ}/infra/toxiproxy/states.sh" sano
  wait "${K6}" || true
  date +%s > "${DEST}/t_fin"

  # -- 6. Recoleccion ----------------------------------------------------
  curl -s "${API}/metrics"  > "${DEST}/api_metrics.txt"
  curl -s "${API}/info"     > "${DEST}/api_info.json"
  curl -s "${PROV}/metrics" > "${DEST}/provider_metrics.txt"
  curl -s "${TOXI}/proxies/openfinance" > "${DEST}/toxiproxy.json"
  docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}}' \
    > "${DEST}/stats.csv"
  ( set -o posix; set ) | grep -E '^(QUOTE_STRATEGY|BREAKER_|TARGET_HIT_RATE|MISS_STALE|RATING_|ADAPTER_|DEPENDENCY_|PROVIDER_|UNIVERSO_|POOL_)' \
    > "${DEST}/env.txt" || true

  # -- 7. Verificaciones POSTERIORES -------------------------------------
  "${RAIZ}/scripts/verify_run.sh" | tee "${DEST}/sanidad.txt" || \
    echo "AVISO: la corrida ${ETIQUETA} no paso todas las verificaciones"
  if [ "${ARM}" != "direct" ]; then
    "${RAIZ}/scripts/verify_hitrate.sh" | tee -a "${DEST}/sanidad.txt" || true
  fi

  echo "corrida ${ETIQUETA} -> ${DEST}"
  echo
}
