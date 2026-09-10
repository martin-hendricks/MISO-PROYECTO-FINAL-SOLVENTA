#!/usr/bin/env bash
# La tasa de acierto OBSERVADA debe coincidir con la CONFIGURADA dentro de
# +-2 puntos. Si no coincide, la corrida no es comparable y se descarta.
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

H=$(metrica "ha01_cache_hits_total")
M=$(metrica "ha01_cache_misses_total")
"${PY}" - "${H:-0}" "${M:-0}" "${TARGET_HIT_RATE:-0.96}" <<'PY'
import sys
h, m, obj = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
total = h + m
if total == 0:
    sys.exit("AVISO: no hubo trafico con cache. El brazo `direct` no usa "
             "cache y esta verificacion no aplica.")
obs = h / total
print("  acierto observado={:.4f} objetivo={:.4f} (aciertos={:.0f} fallos={:.0f})".format(
    obs, obj, h, m))
if abs(obs - obj) > 0.02:
    sys.exit("ERROR: la tasa de acierto se desvia mas de 2 puntos del "
             "objetivo; la corrida no es comparable")
print("  OK   tasa de acierto dentro de tolerancia")
PY
