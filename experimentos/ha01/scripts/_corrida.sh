#!/usr/bin/env bash
# Protocolo de UNA corrida (Anexo A del diseno, "Protocolo de una corrida").
# Lo comparten los tres bloques para que el procedimiento sea identico y la
# unica diferencia entre bloques sea que variable se mueve.
#
#   corrida <brazo> <run_id> <estado_degradado> [rate]
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

# Marca de tiempo del reloj de PROMETHEUS, no del host.
#
# analizar.py corta las fases consultando a Prometheus, que sella sus muestras
# con el reloj de la VM. Tomar las marcas del reloj de Windows funciona
# mientras ambos coincidan, pero el reloj de WSL2 deriva cuando el equipo
# suspende — y una corrida desatendida de nueve horas es justo ese escenario.
# Un desfase de minutos desplazaria los limites de fase sin que nada avise.
ahora() {
  curl -sf "http://localhost:9090/api/v1/query?query=time()" \
    | "${PY}" -c 'import json,sys; print(int(float(json.load(sys.stdin)["data"]["result"][1])))' \
    2>/dev/null || date +%s
}

# Escribe fases.json, que es lo que analizar.py consume. El formato es comun
# a todos los bloques: los de fases (sana/degradada/recuperacion) y el de
# escalones de carga tienen tramos distintos pero se analizan igual.
#   escribir_fases <destino> <brazo> <estado> <rate> <nombre:ini:fin> ...
escribir_fases() {
  local dest="$1" brazo="$2" estado="$3" rate="$4"; shift 4
  "${PY}" - "${dest}/fases.json" "${brazo}" "${estado}" "${rate}" "$@" <<'PY'
import json, sys
destino, brazo, estado, rate = sys.argv[1:5]
fases = []
for tramo in sys.argv[5:]:
    nombre, ini, fin = tramo.split(":")
    fases.append({"nombre": nombre, "ini": int(ini), "fin": int(fin)})
json.dump({"brazo": brazo, "estado": estado, "rate": float(rate),
           "fases": fases}, open(destino, "w"), indent=2)
PY
}

corrida() {
  local ARM="${1:?brazo}" RUN_ID="${2:?run_id}" ESTADO="${3:-degradado}"
  local RATE="${4:-${K6_RATE:-100}}"

  # Duracion de cada fase. Los valores del protocolo son 120/120/60 s; se
  # parametrizan para poder correr un piloto corto que valide la tuberia
  # completa (k6 -> Prometheus -> analizar.py) sin gastar la ventana entera.
  local F_SANA="${FASE_SANA_S:-120}"
  local F_DEG="${FASE_DEGRADADA_S:-120}"
  local F_REC="${FASE_RECUPERACION_S:-60}"

  # Rodaje NO contabilizado, dentro del MISMO proceso de k6 que la ventana.
  #
  # Antes eran dos invocaciones de k6: una de calentamiento y otra de
  # medicion. Eso calentaba la API pero no a k6, cuyo arranque -asignar
  # cientos de VUs, cada una con su runtime de JS- satura el event loop de la
  # API durante unos segundos. A 200 sol/s ese transitorio producia un p95 de
  # 5 s e iteraciones descartadas, y caia DENTRO de la fase sana. Con un solo
  # proceso y las marcas tomadas despues del rodaje, el transitorio queda
  # fuera de toda ventana medida.
  local ESTAB="${ESTABILIZACION_S:-60}"
  local DUR=$((ESTAB + F_SANA + F_DEG + F_REC))

  local ETIQUETA="${ARM}_${RUN_ID}"
  local DEST="${RAIZ}/results/raw/${ETIQUETA}"
  mkdir -p "${DEST}"

  echo "############################################################"
  echo "# corrida ${ETIQUETA} | brazo=${ARM} estado=${ESTADO}"
  echo "#   acierto=${TARGET_HIT_RATE:-0.96} breaker=${BREAKER_POLICY:-rate} rate=${RATE}"
  echo "#   rodaje ${ESTAB}s + fases ${F_SANA}/${F_DEG}/${F_REC}s = ${DUR}s de carga"
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

  # -- 4. Un solo k6: rodaje + ventana de medicion ------------------------
  echo "-- carga: ${DUR}s a ${RATE} sol/s (los primeros ${ESTAB}s no se contabilizan)"
  MSYS_NO_PATHCONV=1 docker compose --profile load run --rm \
    -e RATE="${RATE}" -e DURATION="${DUR}s" \
    -e ARM="${ARM}" -e RUN_ID="${RUN_ID}" -e PROVIDER_STATE="${ESTADO}" \
    -e UNIVERSO_CLIENTES="${UNIVERSO_CLIENTES}" -e POOL_STALE="${POOL_STALE}" \
    -e POOL_COLD="${POOL_COLD}" -e TARGET_HIT_RATE="${TARGET_HIT_RATE}" \
    -e MISS_STALE_FRACTION="${MISS_STALE_FRACTION}" \
    k6 run -o experimental-prometheus-rw \
      --summary-export "/results/${ETIQUETA}/k6_summary.json" \
      /scripts/cotizacion_fase.js > "${DEST}/k6_stdout.txt" 2>&1 &
  local K6=$!

  # -- 5. Fases, con conmutacion EN CALIENTE ------------------------------
  # Los percentiles se calculan POR FASE; agregarlas produciria un percentil
  # sin significado. Las marcas delimitan cada una.
  sleep "${ESTAB}"
  ahora > "${DEST}/t_inicio"
  sleep "${F_SANA}"
  ahora > "${DEST}/t_degradado"
  "${RAIZ}/infra/toxiproxy/states.sh" "${ESTADO}"
  sleep "${F_DEG}"
  ahora > "${DEST}/t_recuperacion"
  "${RAIZ}/infra/toxiproxy/states.sh" sano
  sleep "${F_REC}"
  ahora > "${DEST}/t_fin"
  wait "${K6}" || true

  escribir_fases "${DEST}" "${ARM}" "${ESTADO}" "${RATE}"     "sana:$(cat "${DEST}/t_inicio"):$(cat "${DEST}/t_degradado")"     "degradada:$(cat "${DEST}/t_degradado"):$(cat "${DEST}/t_recuperacion")"     "recuperacion:$(cat "${DEST}/t_recuperacion"):$(cat "${DEST}/t_fin")"

  # -- 6. Recoleccion ----------------------------------------------------
  curl -s "${API}/metrics"  > "${DEST}/api_metrics.txt"
  curl -s "${API}/info"     > "${DEST}/api_info.json"
  curl -s "${PROV}/metrics" > "${DEST}/provider_metrics.txt"
  curl -s "${TOXI}/proxies/openfinance" > "${DEST}/toxiproxy.json"
  docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}}' \
    > "${DEST}/stats.csv"
  ( set -o posix; set ) \
    | grep -E '^(QUOTE_STRATEGY|BREAKER_|TARGET_HIT_RATE|MISS_STALE|HOT_AGE|RATING_|ADAPTER_|DEPENDENCY_|PROVIDER_|UNIVERSO_|POOL_|FASE_|ESTABILIZACION)' \
    > "${DEST}/env.txt" || true

  # -- 7. Verificaciones POSTERIORES -------------------------------------
  CORRIDA_DIR="${DEST}" "${RAIZ}/scripts/verify_run.sh" | tee "${DEST}/sanidad.txt" \
    || echo "AVISO: la corrida ${ETIQUETA} no paso todas las verificaciones"
  if [ "${ARM}" != "direct" ]; then
    "${RAIZ}/scripts/verify_hitrate.sh" | tee -a "${DEST}/sanidad.txt" || true
  fi

  echo "corrida ${ETIQUETA} -> ${DEST}"
  echo
}


# ---------------------------------------------------------------------
# Corrida de ESCALONES de carga (bloque 4).
#
# El estado del proveedor se fija de entrada y NO se conmuta: aqui la
# variable que se mueve es la tasa de llegada, y mover dos a la vez haria
# imposible atribuir el efecto.
#
#   corrida_escalones <brazo> <run_id> <estado>
# ---------------------------------------------------------------------
corrida_escalones() {
  local ARM="${1:?brazo}" RUN_ID="${2:?run_id}" ESTADO="${3:-sano}"
  local ESCALONES="${ESCALONES:-20,50,100,200}"
  local ESCALON_S="${ESCALON_S:-120}"
  local ESTAB="${ESTABILIZACION_S:-60}"

  local ETIQUETA="${ARM}_${RUN_ID}"
  local DEST="${RAIZ}/results/raw/${ETIQUETA}"
  mkdir -p "${DEST}"

  echo "############################################################"
  echo "# corrida ${ETIQUETA} | brazo=${ARM} estado=${ESTADO}"
  echo "#   escalones ${ESCALONES} de ${ESCALON_S}s | acierto=${TARGET_HIT_RATE}"
  echo "############################################################"

  docker compose stop api >/dev/null
  docker compose exec -T redis redis-cli FLUSHALL >/dev/null
  docker compose exec -T redis redis-cli CONFIG RESETSTAT >/dev/null
  "${RAIZ}/infra/toxiproxy/states.sh" sano >/dev/null

  QUOTE_STRATEGY="${ARM}" docker compose up -d api >/dev/null
  esperar_api
  precargar --verificar
  "${RAIZ}/scripts/verify_baseline.sh"
  "${RAIZ}/scripts/verify_provider.sh"

  # El estado se fija ANTES de arrancar la carga y no se toca.
  "${RAIZ}/infra/toxiproxy/states.sh" "${ESTADO}"

  local n; n=$(echo "${ESCALONES}" | tr ',' ' ' | wc -w)
  local total=$((ESTAB + n * ESCALON_S))
  echo "-- carga: ${total}s (rodaje ${ESTAB}s + ${n} escalones de ${ESCALON_S}s)"

  MSYS_NO_PATHCONV=1 docker compose --profile load run --rm     -e ESCALONES="${ESCALONES}" -e ESCALON_S="${ESCALON_S}"     -e ESTABILIZACION_S="${ESTAB}"     -e ARM="${ARM}" -e RUN_ID="${RUN_ID}" -e PROVIDER_STATE="${ESTADO}"     -e UNIVERSO_CLIENTES="${UNIVERSO_CLIENTES}" -e POOL_STALE="${POOL_STALE}"     -e POOL_COLD="${POOL_COLD}" -e TARGET_HIT_RATE="${TARGET_HIT_RATE}"     -e MISS_STALE_FRACTION="${MISS_STALE_FRACTION}"     k6 run -o experimental-prometheus-rw       --summary-export "/results/${ETIQUETA}/k6_summary.json"       /scripts/cotizacion.js > "${DEST}/k6_stdout.txt" 2>&1 &
  local K6=$!

  sleep "${ESTAB}"
  local marcas=() ini fin
  for r in $(echo "${ESCALONES}" | tr ',' ' '); do
    ini=$(ahora)
    sleep "${ESCALON_S}"
    fin=$(ahora)
    marcas+=("r${r}:${ini}:${fin}")
    echo "   escalon ${r} sol/s: ${ini} -> ${fin}"
  done
  wait "${K6}" || true

  escribir_fases "${DEST}" "${ARM}" "${ESTADO}" 0 "${marcas[@]}"

  curl -s "${API}/metrics"  > "${DEST}/api_metrics.txt"
  curl -s "${API}/info"     > "${DEST}/api_info.json"
  curl -s "${PROV}/metrics" > "${DEST}/provider_metrics.txt"
  docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}}'     > "${DEST}/stats.csv"

  CORRIDA_DIR="${DEST}" "${RAIZ}/scripts/verify_run.sh" | tee "${DEST}/sanidad.txt"     || echo "AVISO: la corrida ${ETIQUETA} no paso todas las verificaciones"

  echo "corrida ${ETIQUETA} -> ${DEST}"
  echo
}
