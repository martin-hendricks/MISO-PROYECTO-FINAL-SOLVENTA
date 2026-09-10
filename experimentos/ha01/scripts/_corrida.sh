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
  # Margen: k6 corre mas de lo que duran las fases. El reloj de las fases
  # arranca cuando la carga EMPIEZA A LLEGAR de verdad, no cuando se lanza el
  # contenedor, y entre una cosa y otra pasa un tiempo variable.
  # 20 s cubren la variabilidad de creacion del contenedor de k6 sin encarecer
  # la campana: son 27 minutos sobre las 81 corridas.
  local MARGEN="${MARGEN_CARGA_S:-20}"
  local DUR=$((ESTAB + F_SANA + F_DEG + F_REC + MARGEN))

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
  # El pool vencido se dimensiona con la aritmetica de la corrida: las fases
  # SANAS son las que repueblan claves vencidas y hacen derivar el acierto.
  # La degradada no cuenta, porque ahi el refresco falla.
  export RATE_ESPERADA="${RATE}"
  export SEGUNDOS_SANOS=$((ESTAB + F_SANA + F_REC))
  POOL_STALE="$(pool_vencido "${RATE}" "${SEGUNDOS_SANOS}")"
  export POOL_STALE

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
  # Esperar a que la carga LLEGUE, no a que el contenedor se lance.
  #
  # Antes se hacia `sleep ESTAB` desde el lanzamiento. Entre lanzar
  # `docker compose run` y que k6 empiece a emitir pasa un tiempo variable
  # -crear el contenedor, contencion de la maquina-, y en una traza medida ese
  # `sleep 10` tardo 62 s: la ventana entera quedo FUERA de la carga. Las tres
  # fases sin una sola peticion, y todas las verificaciones diciendo que la
  # corrida era valida.
  esperar_carga || fallar "la carga no arranco: la corrida no es valida"
  sleep "${ESTAB}"

  # Segunda comprobacion, ya con la ventana a punto de abrirse: la carga debe
  # seguir viva. Si k6 termino durante el rodaje -porque su contenedor tardo
  # en crearse y el margen no alcanzo- la ventana caeria fuera de la carga y
  # las tres fases saldrian vacias. Vale mas abortar aqui que descubrirlo seis
  # minutos despues.
  carga_viva || fallar "la carga no sigue viva al abrir la ventana"
  ahora > "${DEST}/t_inicio"
  sleep "${F_SANA}"
  ahora > "${DEST}/t_degradado"
  "${RAIZ}/infra/toxiproxy/states.sh" "${ESTADO}"
  sleep "${F_DEG}"
  ahora > "${DEST}/t_recuperacion"
  "${RAIZ}/infra/toxiproxy/states.sh" sano
  sleep "${F_REC}"
  ahora > "${DEST}/t_fin"

  # Se deja terminar a k6 en vez de matarlo. Matarlo ahorraba el margen pero
  # costaba dos cosas: `--summary-export` no llegaba a escribirse -y con el se
  # perdia la comprobacion de `dropped_iterations`- y quedaban peticiones en
  # vuelo, que hacian fallar la deteccion de fugas del adaptador. La carga
  # sobrante cae fuera de la ventana y no contamina ninguna fase.
  wait "${K6}" || true

  # Drenaje: las invocaciones en curso pueden durar hasta el timeout duro.
  # Sin esta espera, `ha01_adapter_inflight` se lee antes de que bajen y la
  # comprobacion de fugas del brazo C daria un falso positivo.
  sleep 3

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

  # Con el proveedor SANO todos los escalones repueblan; se dimensiona con el
  # escalon mas alto y la corrida entera, que es el peor caso.
  local n_esc; n_esc=$(echo "${ESCALONES}" | tr ',' ' ' | wc -w)
  local rate_max; rate_max=$(echo "${ESCALONES}" | tr ',' '
' | sort -n | tail -1)
  export RATE_ESPERADA="${rate_max}"
  export SEGUNDOS_SANOS=$((ESTAB + n_esc * ESCALON_S))
  POOL_STALE="$(pool_vencido "${rate_max}" "${SEGUNDOS_SANOS}")"
  export POOL_STALE

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


# ---------------------------------------------------------------------
# Ejecuta una corrida SIN que su fallo tumbe el bloque entero.
#
# Los scripts de bloque llevan `set -e`, asi que un fallo en la corrida 40 de
# 45 se llevaria por delante las cinco restantes -y a las cuatro horas y media
# de una ejecucion desatendida nadie esta mirando-.
#
# La corrida se lanza en un PROCESO APARTE, no en un subshell. Bash desarma
# `set -e` para todo lo que cuelga de la condicion de un `if` o del lado
# izquierdo de un `||`, y ese desarme se HEREDA en los subshells: ni
# `( f )`, ni `( set -e; f )`, ni `rc=0; ( set -e; f ) || rc=$?` detienen la
# funcion en el punto que falla. Comprobado: las tres siguen ejecutando los
# pasos posteriores al fallo, que es peor que abortar, porque la corrida
# continuaria con la cache mal precargada o el proveedor en el estado que no es.
#
# Con `bash -c` el contexto no se hereda: dentro rige `set -e` y la corrida
# aborta donde debe, mientras el bloque sigue vivo.
#
# La corrida siguiente reinicia el estado volatil en su paso 1 -para la API,
# vacia Redis y quita las toxinas-, asi que la recuperacion es automatica.
#
# Si fallan tres seguidas se aborta: eso ya no es una corrida mala, es el
# montaje caido, y seguir nueve horas contra un Docker muerto no sirve de nada.
#
#   corrida_segura <corrida|corrida_escalones> <args...>
# ---------------------------------------------------------------------
FALLOS_SEGUIDOS=0
FALLOS_DEL_BLOQUE=()
# Registro persistente de toda la campana; el resumen de cada bloque usa el
# array, para no repetir los fallos de bloques anteriores.
REGISTRO_FALLOS="${RAIZ}/results/corridas_fallidas.txt"

corrida_segura() {
  local fn="$1"; shift
  local rc=0
  bash -c 'set -euo pipefail; source "$1"; shift; "$@"'        _ "${RAIZ}/scripts/_corrida.sh" "${fn}" "$@" || rc=$?
  if [ "${rc}" -eq 0 ]; then
    FALLOS_SEGUIDOS=0
    return 0
  fi

  FALLOS_SEGUIDOS=$((FALLOS_SEGUIDOS + 1))
  local linea="$(date '+%Y-%m-%d %H:%M:%S')  ${fn} $*"
  FALLOS_DEL_BLOQUE+=("${linea}")
  echo "${linea}" >> "${REGISTRO_FALLOS}"
  echo "!! CORRIDA FALLIDA: ${fn} $* — registrada, el bloque continua" >&2

  if [ "${FALLOS_SEGUIDOS}" -ge 3 ]; then
    echo >&2
    echo "!! TRES CORRIDAS SEGUIDAS FALLIDAS — se aborta el bloque." >&2
    echo "   Eso no es una corrida mala sino el montaje caido; revisar" >&2
    echo "   'docker compose ps' y ${REGISTRO_FALLOS}" >&2
    exit 1
  fi
  return 0
}

resumen_bloque() {
  echo "============================================================"
  if [ "${#FALLOS_DEL_BLOQUE[@]}" -eq 0 ]; then
    echo "BLOQUE COMPLETO — ninguna corrida fallo"
  else
    echo "BLOQUE COMPLETO — ${#FALLOS_DEL_BLOQUE[@]} corrida(s) fallida(s):"
    printf '  %s
' "${FALLOS_DEL_BLOQUE[@]}"
    echo
    echo "Repetir esas corridas antes de dar el bloque por valido."
  fi
  echo "============================================================"
}
