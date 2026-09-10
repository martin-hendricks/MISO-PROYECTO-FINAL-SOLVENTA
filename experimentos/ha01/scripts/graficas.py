"""Figuras del informe HA-01.

Lee `results/analysis/resultados_por_fase.csv` y, para las series temporales,
consulta a Prometheus con los cortes de `fases.json`. Escribe PNG a 200 ppp en
`results/analysis/figuras/`.

Cada figura genera solo si hay datos del bloque correspondiente, asi que se
puede ejecutar con los bloques a medio correr.

Corre dentro del contenedor `figuras` (perfil tools): matplotlib no vive en la
imagen de la API porque cambiaria la huella del contenedor que se mide.

Uso:  docker compose --profile tools run --rm figuras /work/scripts/graficas.py
"""
import csv
import json
import pathlib
import sys
import urllib.parse
import urllib.request

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --- Paleta -----------------------------------------------------------
# Categorica de cuatro ranuras, validada para modo claro (banda de luminosidad,
# piso de croma, separacion CVD y piso de vision normal). Aqua y amarillo
# quedan por debajo de 3:1 contra la superficie, asi que rige la regla de
# relieve: TODA barra lleva su valor escrito. El CSV es ademas la vista de
# tabla equivalente.
SUP = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TINTA_3 = "#8b8a84"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]

SLO_P95, SLO_P99 = 225, 475
PROM = "http://localhost:9090"

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CSV = RAIZ / "results" / "analysis" / "resultados_por_fase.csv"
CRUDO = RAIZ / "results" / "raw"
FIGS = RAIZ / "results" / "analysis" / "figuras"

NOMBRE_BRAZO = {
    "direct": "A  directo",
    "cache_blocking": "B  cache bloqueante",
    "cache_opportunistic": "C  oportunista",
    "cache_singleflight": "C'  + coalescencia",
}
ORDEN_BRAZO = list(NOMBRE_BRAZO)
ORDEN_ESTADO = ["sano", "lento", "degradado", "sin_respuesta", "caido"]
ORDEN_CAMINO = ["cache", "open_finance", "fallback", "default"]

matplotlib.rcParams.update({
    "figure.facecolor": SUP,
    "axes.facecolor": SUP,
    "savefig.facecolor": SUP,
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "600",
    "axes.labelsize": 9,
    "axes.edgecolor": TINTA_3,
    "axes.labelcolor": TINTA_2,
    "text.color": TINTA,
    "xtick.color": TINTA_2,
    "ytick.color": TINTA_2,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "lines.linewidth": 2,
    "lines.markersize": 5,
})


# --- utilidades -------------------------------------------------------
def eje(ax, titulo=None, ylabel=None):
    """Rejilla y ejes recesivos: los datos mandan, el andamiaje no."""
    ax.grid(axis="y", color=TINTA_3, alpha=0.22, linewidth=0.7)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(TINTA_3)
        ax.spines[lado].set_linewidth(0.8)
    if titulo:
        ax.set_title(titulo, loc="left", pad=10)
    if ylabel:
        ax.set_ylabel(ylabel)


def umbral(ax, y, etiqueta):
    ax.axhline(y, color=TINTA_2, linestyle=(0, (5, 4)), linewidth=1.2, alpha=0.8)
    ax.annotate(etiqueta, xy=(1.0, y), xycoords=("axes fraction", "data"),
                xytext=(4, 0), textcoords="offset points",
                va="center", ha="left", fontsize=7.5, color=TINTA_2)


def etiquetar(ax, barras, fmt="{:.0f}"):
    """Valor sobre cada barra. Obligatorio: dos de las cuatro ranuras estan
    por debajo de 3:1 de contraste y rige la regla de relieve."""
    for b in barras:
        h = b.get_height()
        if h is None or h != h:
            continue
        ax.annotate(fmt.format(h), xy=(b.get_x() + b.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=7, color=TINTA_2)


def guardar(fig, nombre, nota=None):
    if nota:
        fig.text(0.01, 0.008, nota, fontsize=7, color=TINTA_3, ha="left")
    FIGS.mkdir(parents=True, exist_ok=True)
    destino = FIGS / nombre
    fig.savefig(destino, dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("  " + nombre)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def leer_csv():
    if not CSV.exists():
        return []
    with CSV.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def rango(expr, ini, fin, paso=2):
    url = PROM + "/api/v1/query_range?" + urllib.parse.urlencode(
        {"query": expr, "start": ini, "end": fin, "step": paso})
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            d = json.load(r)
    except Exception:
        return []
    if d.get("status") != "success" or not d["data"]["result"]:
        return []
    fuera = []
    for t, v in d["data"]["result"][0]["values"]:
        x = float(v)
        fuera.append((float(t), None if x != x else x))
    return fuera


def fases_de(nombre_corrida):
    f = CRUDO / nombre_corrida / "fases.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


# --- Figura 1: latencia por brazo y estado (bloque 1) -----------------
def fig_brazo_estado(filas):
    datos = {}
    for r in filas:
        if not r["corrida"].split("_", 3)[-1].startswith("b1_"):
            continue
        if r["fase"] != "degradada":
            continue
        estado = r["corrida"].rsplit("_", 1)[-1]
        if estado not in ORDEN_ESTADO:
            continue
        datos.setdefault((r["brazo"], estado), []).append(
            (num(r["p95_ms"]), num(r["p99_ms"])))
    if not datos:
        return

    brazos = [b for b in ORDEN_BRAZO if any(k[0] == b for k in datos)]
    fig, ejes = plt.subplots(2, 1, figsize=(9.5, 7.2), sharex=True)
    ancho = 0.8 / max(len(brazos), 1)

    for idx, (ax, i_metrica, slo, nombre) in enumerate([
            (ejes[0], 0, SLO_P95, "p95"), (ejes[1], 1, SLO_P99, "p99")]):
        for j, brazo in enumerate(brazos):
            alturas = []
            for e in ORDEN_ESTADO:
                vs = [x[i_metrica] for x in datos.get((brazo, e), [])
                      if x[i_metrica] is not None]
                alturas.append(sum(vs) / len(vs) if vs else float("nan"))
            x = [k + (j - (len(brazos) - 1) / 2) * ancho
                 for k in range(len(ORDEN_ESTADO))]
            barras = ax.bar(x, alturas, ancho * 0.86, color=SERIES[j],
                            label=NOMBRE_BRAZO[brazo] if idx == 0 else None,
                            edgecolor=SUP, linewidth=2)
            etiquetar(ax, barras)
        eje(ax, f"{nombre} de la cotizacion en fase degradada",
            f"{nombre} (ms)")
        umbral(ax, slo, f"{slo} ms")
        ax.set_xticks(range(len(ORDEN_ESTADO)))
        ax.set_xticklabels([e.replace("_", " ") for e in ORDEN_ESTADO])

    ejes[0].legend(loc="upper left", ncol=len(brazos))
    fig.suptitle("Bloque 1 — estrategia contra estado del proveedor",
                 x=0.012, ha="left", fontsize=13, weight="600")
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    guardar(fig, "fig1_brazo_x_estado.png",
            "Umbral del SERVICIO (250/500 ms extremo a extremo menos 25 ms de "
            "borde, Anexo G). Media de las repeticiones.")


# --- Figura 2: p95 por camino (HD-01.3) -------------------------------
def fig_camino(filas):
    datos = {}
    for r in filas:
        if r["fase"] not in ("sana", "degradada"):
            continue
        for c in ORDEN_CAMINO:
            v = num(r.get("p95_" + c + "_ms"))
            if v is not None:
                datos.setdefault((r["brazo"], r["fase"]), {}).setdefault(
                    c, []).append(v)
    if not datos:
        return

    brazos = [b for b in ORDEN_BRAZO if any(k[0] == b for k in datos)]
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    ancho = 0.8 / max(len(ORDEN_CAMINO), 1)

    for idx, (ax, fase) in enumerate([(ejes[0], "sana"), (ejes[1], "degradada")]):
        for j, camino in enumerate(ORDEN_CAMINO):
            alturas = []
            for b in brazos:
                vs = datos.get((b, fase), {}).get(camino, [])
                alturas.append(sum(vs) / len(vs) if vs else float("nan"))
            x = [k + (j - (len(ORDEN_CAMINO) - 1) / 2) * ancho
                 for k in range(len(brazos))]
            barras = ax.bar(x, alturas, ancho * 0.86, color=SERIES[j],
                            label=camino if idx == 0 else None,
                            edgecolor=SUP, linewidth=2)
            etiquetar(ax, barras)
        eje(ax, "proveedor " + fase, "p95 (ms)" if idx == 0 else None)
        umbral(ax, SLO_P95, f"{SLO_P95} ms")
        ax.set_xticks(range(len(brazos)))
        ax.set_xticklabels([NOMBRE_BRAZO[b].split(" ")[0] for b in brazos])

    ejes[0].legend(loc="upper left", ncol=2, title="camino de resolucion",
                   title_fontsize=8)
    fig.suptitle("HD-01.3 — latencia por camino de resolucion del perfil",
                 x=0.012, ha="left", fontsize=13, weight="600")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    guardar(fig, "fig2_camino.png",
            "La hipotesis predice que en el brazo C el camino degradado "
            "(fallback/default) es mas rapido que el camino frio (open_finance).")


# --- Figura 3: sensibilidad al acierto (HD-01.4) ----------------------
def fig_acierto(filas):
    datos = {}
    for r in filas:
        corrida = r["corrida"]
        if "_hr" not in corrida or r["fase"] != "degradada":
            continue
        try:
            hr = float(corrida.rsplit("hr", 1)[-1])
        except ValueError:
            continue
        datos.setdefault(r["brazo"], {}).setdefault(hr, []).append(
            (num(r["p95_ms"]), num(r["p99_ms"])))
    if not datos:
        return

    fig, ejes = plt.subplots(1, 2, figsize=(10.5, 4.4), sharex=True)
    for idx, (ax, i_m, slo, nombre) in enumerate([
            (ejes[0], 0, SLO_P95, "p95"), (ejes[1], 1, SLO_P99, "p99")]):
        for j, brazo in enumerate(b for b in ORDEN_BRAZO if b in datos):
            xs = sorted(datos[brazo])
            ys = []
            for hr in xs:
                vs = [v[i_m] for v in datos[brazo][hr] if v[i_m] is not None]
                ys.append(sum(vs) / len(vs) if vs else float("nan"))
            ax.plot([x * 100 for x in xs], ys, marker="o", color=SERIES[j],
                    label=NOMBRE_BRAZO[brazo] if idx == 0 else None,
                    markeredgecolor=SUP, markeredgewidth=1.5)
            for x, y in zip(xs, ys):
                if y == y:
                    ax.annotate(f"{y:.0f}", (x * 100, y), xytext=(0, 7),
                                textcoords="offset points", ha="center",
                                fontsize=7, color=TINTA_2)
        eje(ax, nombre + " contra tasa de acierto", nombre + " (ms)")
        umbral(ax, slo, f"{slo} ms")
        ax.set_xlabel("tasa de acierto de :CacheOF (%)")
    ejes[0].legend(loc="upper right")
    fig.suptitle("HD-01.4 — sensibilidad a la tasa de acierto "
                 "(proveedor degradado)",
                 x=0.012, ha="left", fontsize=13, weight="600")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    guardar(fig, "fig3_acierto.png",
            "El cruce con la linea de umbral marca el acierto minimo que "
            "sostiene el ASR.")


# --- Figura 4: serie temporal de una corrida (HD-01.8) ----------------
def fig_serie(nombre_corrida):
    meta = fases_de(nombre_corrida)
    if not meta or not meta.get("fases"):
        return
    ini = meta["fases"][0]["ini"]
    fin = meta["fases"][-1]["fin"]

    lat = rango("histogram_quantile(0.95, sum by (le) "
                "(rate(ha01_quote_latency_seconds_bucket[15s])))", ini, fin)
    brk = rango("ha01_breaker_state", ini, fin)
    resp = rango("rate(ha01_cotizaciones_degradadas_total[15s]) / "
                 "rate(ha01_cotizaciones_total[15s])", ini, fin)
    if not lat:
        return

    # Tres paneles apilados que comparten el eje X. NUNCA dos escalas Y en un
    # mismo panel: superponer latencia y estado del interruptor sobre ejes
    # distintos es la forma mas comun de mentir con un grafico.
    fig, ejes = plt.subplots(3, 1, figsize=(10, 7.4), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1.4, 1.8]})
    t0 = ini

    ax = ejes[0]
    ax.plot([(t - t0) for t, _ in lat], [v * 1000 if v else None for _, v in lat],
            color=SERIES[0], label="p95 de la cotizacion")
    eje(ax, "p95 de la cotizacion", "ms")
    umbral(ax, SLO_P95, f"{SLO_P95} ms")
    ax.legend(loc="upper left")

    ax = ejes[1]
    ax.step([(t - t0) for t, _ in brk], [v for _, v in brk], where="post",
            color=SERIES[1], label="estado del interruptor")
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["cerrado", "semiab.", "abierto"])
    eje(ax, "interruptor de circuito")
    ax.legend(loc="upper left")

    ax = ejes[2]
    ax.plot([(t - t0) for t, _ in resp],
            [v * 100 if v is not None else None for _, v in resp],
            color=SERIES[2], label="cotizaciones con respaldo")
    eje(ax, "proporcion resuelta con valor de respaldo", "%")
    umbral(ax, 5, "5 %")
    ax.set_xlabel("segundos desde el inicio de la ventana")
    ax.legend(loc="upper left")

    for f in meta["fases"][1:]:
        for a in ejes:
            a.axvline(f["ini"] - t0, color=TINTA_3, linewidth=1,
                      linestyle=(0, (2, 3)))
    for f in meta["fases"]:
        ejes[0].annotate(f["nombre"], xy=((f["ini"] + f["fin"]) / 2 - t0, 1.0),
                         xycoords=("data", "axes fraction"), xytext=(0, 4),
                         textcoords="offset points", ha="center", fontsize=7.5,
                         color=TINTA_2)

    fig.suptitle("HD-01.8 — " + nombre_corrida, x=0.012, ha="left",
                 fontsize=13, weight="600")
    fig.tight_layout(rect=(0, 0.02, 1, 0.955))
    guardar(fig, "fig4_serie_" + nombre_corrida + ".png",
            "Tres paneles con eje de tiempo compartido; nunca dos escalas Y "
            "en un mismo panel.")


# --- Figura 5: latencia contra tasa de llegada (bloque 4) -------------
def fig_carga(filas):
    datos = {}
    for r in filas:
        if not r["fase"].startswith("r") or not r["fase"][1:].isdigit():
            continue
        estado = "degradado" if "degradado" in r["corrida"] else "sano"
        datos.setdefault((r["brazo"], estado), {})[int(r["fase"][1:])] = (
            num(r["p95_ms"]), num(r["p99_ms"]))
    if not datos:
        return

    fig, ejes = plt.subplots(1, 2, figsize=(10.5, 4.4), sharex=True)
    claves = sorted(datos, key=lambda k: (ORDEN_BRAZO.index(k[0]), k[1]))
    for idx, (ax, i_m, slo, nombre) in enumerate([
            (ejes[0], 0, SLO_P95, "p95"), (ejes[1], 1, SLO_P99, "p99")]):
        for j, clave in enumerate(claves):
            xs = sorted(datos[clave])
            ys = [datos[clave][x][i_m] for x in xs]
            ax.plot(xs, ys, marker="o", color=SERIES[j % len(SERIES)],
                    label=f"{NOMBRE_BRAZO[clave[0]].split(' ')[0]} · {clave[1]}"
                          if idx == 0 else None,
                    markeredgecolor=SUP, markeredgewidth=1.5)
        eje(ax, nombre + " contra tasa de llegada", nombre + " (ms)")
        umbral(ax, slo, f"{slo} ms")
        ax.set_xlabel("solicitudes por segundo")
    ejes[0].legend(loc="upper left")
    fig.suptitle("Bloque 4 — latencia contra carga (EC-LAT-02)",
                 x=0.012, ha="left", fontsize=13, weight="600")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    guardar(fig, "fig5_carga.png")


# --- Figura 6: el trade-off cuantificado ------------------------------
def fig_frescura(filas):
    puntos = []
    for r in filas:
        e95, resp = num(r["edad_p95_s"]), num(r["respaldo_pct"])
        if e95 is None or resp is None or r["fase"] == "transiciones":
            continue
        puntos.append((r["brazo"], r["fase"], e95, resp))
    if not puntos:
        return

    fig, ejes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    fases = ["sana", "degradada", "recuperacion"]
    brazos = [b for b in ORDEN_BRAZO if any(p[0] == b for p in puntos)]
    ancho = 0.8 / max(len(fases), 1)

    for idx, (ax, i_v, titulo, ylab) in enumerate([
            (ejes[0], 3, "cotizaciones resueltas con respaldo", "%"),
            (ejes[1], 2, "edad p95 del dato con que se tarifica", "segundos")]):
        for j, fase in enumerate(fases):
            alturas = []
            for b in brazos:
                vs = [p[i_v] for p in puntos if p[0] == b and p[1] == fase]
                alturas.append(sum(vs) / len(vs) if vs else float("nan"))
            x = [k + (j - (len(fases) - 1) / 2) * ancho
                 for k in range(len(brazos))]
            barras = ax.bar(x, alturas, ancho * 0.86, color=SERIES[j],
                            label=fase if idx == 0 else None,
                            edgecolor=SUP, linewidth=2)
            etiquetar(ax, barras, "{:.1f}")
        eje(ax, titulo, ylab)
        ax.set_xticks(range(len(brazos)))
        ax.set_xticklabels([NOMBRE_BRAZO[b].split(" ")[0] for b in brazos])
    ejes[0].legend(loc="upper left", ncol=3, title="fase", title_fontsize=8)
    fig.suptitle("El trade-off cuantificado: frescura contra latencia",
                 x=0.012, ha="left", fontsize=13, weight="600")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    guardar(fig, "fig6_frescura.png",
            "Es el precio del brazo C, y lo que §2.8 de la wiki declara sin "
            "cuantificar.")


# --- Figura 7: saturacion del pool (HD-01.7) --------------------------
def fig_pool(corridas):
    series = []
    for nombre in corridas:
        meta = fases_de(nombre)
        if not meta or not meta.get("fases"):
            continue
        ini, fin = meta["fases"][0]["ini"], meta["fases"][-1]["fin"]
        s = rango("ha01_adapter_inflight", ini, fin)
        if s:
            series.append((meta.get("brazo", nombre), ini, s))
    if not series:
        return

    fig, ax = plt.subplots(figsize=(10, 4.4))
    for j, (brazo, t0, s) in enumerate(series):
        ax.plot([t - t0 for t, _ in s], [v for _, v in s],
                color=SERIES[j % len(SERIES)],
                label=NOMBRE_BRAZO.get(brazo, brazo))
    eje(ax, "invocaciones en vuelo contra el proveedor",
        "invocaciones concurrentes")
    umbral(ax, 40, "pool = 40")
    ax.set_xlabel("segundos desde el inicio de la ventana")
    ax.legend(loc="upper left")
    fig.suptitle("HD-01.7 — saturacion del pool del adaptador",
                 x=0.012, ha="left", fontsize=13, weight="600")
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))
    guardar(fig, "fig7_pool.png",
            "Por encima de la linea hay invocaciones encoladas esperando "
            "conexion: el aislamiento de recursos esta al limite.")


# --- enlaces a Grafana ------------------------------------------------
def enlaces_grafana(corridas):
    """Un enlace por corrida al tablero, ya acotado a su ventana.

    Sin esto habria que localizar a mano el rango de cada una de las 81
    corridas dentro de un historico de nueve horas.
    """
    lineas = ["# Enlaces al tablero de Grafana por corrida",
              "",
              "Cada enlace abre el tablero HA-01 acotado a la ventana de esa",
              "corrida. Prometheus conserva 30 dias, asi que siguen vivos",
              "despues de terminar.", ""]
    for nombre in corridas:
        meta = fases_de(nombre)
        if not meta or not meta.get("fases"):
            continue
        ini = (meta["fases"][0]["ini"] - 15) * 1000
        fin = (meta["fases"][-1]["fin"] + 15) * 1000
        lineas.append(
            f"- [{nombre}](http://localhost:3000/d/ha01/?from={ini}&to={fin})")
    destino = FIGS.parent / "enlaces_grafana.md"
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("  ../enlaces_grafana.md")


def main():
    filas = leer_csv()
    if not filas:
        print("no hay resultados_por_fase.csv; ejecuta collect_results.sh",
              file=sys.stderr)
        return 1
    corridas = sorted({r["corrida"] for r in filas})

    FIGS.mkdir(parents=True, exist_ok=True)
    print("figuras en results/analysis/figuras/:")
    fig_brazo_estado(filas)
    fig_camino(filas)
    fig_acierto(filas)
    fig_carga(filas)
    fig_frescura(filas)

    # Serie temporal: una por cada corrida del bloque 3, que son las que
    # ejercitan la transicion completa del interruptor.
    for nombre in corridas:
        if "b3_" in nombre or "_p200" in nombre or "hr050" in nombre:
            fig_serie(nombre)

    fig_pool([n for n in corridas
              if "estampida" in n or "hr050" in n or "_p200" in n])
    enlaces_grafana(corridas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
