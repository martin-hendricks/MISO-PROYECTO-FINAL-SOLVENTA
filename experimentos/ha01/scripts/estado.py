"""Genera ESTADO_EXPERIMENTO.md: el estado de ejecucion del experimento HA-01.

Se regenera al cerrar cada corrida y se sube al repositorio junto con su
evidencia, de modo que el equipo puede seguir la campana desde GitHub.

Solo lee archivos locales (results/plan.txt, la carpeta de cada corrida y los
archivos de estado de la campana); no consulta a Prometheus.

Uso:  python scripts/estado.py
"""
import datetime as dt
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
RAW = RAIZ / "results" / "raw"
DESTINO = RAIZ / "ESTADO_EXPERIMENTO.md"

BRAZO = {"direct": "A", "cache_blocking": "B", "cache_opportunistic": "C",
         "cache_singleflight": "C'"}
MIN_CORRIDA = 7.3            # minutos por corrida de fases (medido)
MIN_ESCALONES = 10.3         # minutos por corrida de escalones (bloque 4)
SOSPECHA_LAG_MS = 50         # umbral del detector de interferencia
# Presupuesto (120) + tarifa (60) + 50 ms de margen: en C y C' el respaldo no
# puede tardar más, salvo que el bucle de eventos estuviera bloqueado.
TECHO_RESPALDO_MS = 230


def leer(p, defecto=""):
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return defecto


def grupo(etq):
    if "b1_r2_lento" in etq or "b1_r3_lento" in etq:
        return "Réplicas de la celda cercana al umbral (B, proveedor lento)"
    if "_b1_" in etq:
        return "Bloque 1 — estrategia contra estado del proveedor (1 repetición)"
    if "_b2_" in etq:
        return "Bloque 2 — sensibilidad a la tasa de acierto, proveedor lento"
    if "estampida_ttl2" in etq:
        return "HD-01.7 — estampida sobre pocas claves (C contra C')"
    if "_b3_" in etq:
        return "Bloque 3 — interruptor, recuperación y estampida"
    if "_b4_" in etq:
        return "Bloque 4 — latencia contra tasa de llegada"
    return "Otras"


def plan():
    lineas = leer(RAIZ / "results" / "plan.txt").splitlines()
    vistos, salida = set(), []
    for ln in lineas:
        partes = ln.split("|")
        if len(partes) < 4 or partes[1] in vistos:
            continue
        vistos.add(partes[1])
        args = partes[3].split()
        salida.append({"etq": partes[1], "fn": partes[2],
                       "brazo": args[0] if args else "?",
                       "proveedor": args[2] if len(args) > 2 else "?",
                       "rate": args[3] if len(args) > 3 else "100"})
    # Corridas presentes en disco pero fuera del plan (p. ej. pilotos): se
    # listan igual, para que nada medido quede invisible.
    for d in sorted(p for p in RAW.glob("*") if p.is_dir()):
        if d.name not in vistos:
            fj = leer(d / "fases.json")
            meta = json.loads(fj) if fj else {}
            salida.append({"etq": d.name, "fn": "corrida",
                           "brazo": meta.get("brazo", "?"),
                           "proveedor": meta.get("estado", "?"),
                           "rate": str(meta.get("rate", "?"))})
    return salida


def acierto_objetivo(etq, d):
    m = re.search(r"TARGET_HIT_RATE=([0-9.]+)", leer(d / "env.txt"))
    if m:
        return m.group(1)
    m = re.search(r"hr([0-9.]+)$", etq)
    if m:
        return m.group(1)
    return "1.0 (20 claves)" if "ttl2" in etq else "0.96"


def estado_corrida(etq, en_curso, fallidas):
    d = RAW / etq
    if etq == en_curso:
        return "⏳ en curso", None
    if "__intento1_fallido" in etq:
        return "↻ intento fallido (se reintentó)", None
    if not d.is_dir() or not (d / "sanidad.txt").exists():
        return ("❌ fallida" if etq in fallidas else "· pendiente"), None
    san = leer(d / "sanidad.txt")
    valida = "todas las verificaciones pasaron" in san and "ERROR" not in san
    filas = []
    try:
        filas = json.loads(leer(d / "fases_resultado.json") or "[]")
    except json.JSONDecodeError:
        pass
    if not valida:
        return "❌ inválida", filas
    medidas = [f for f in filas if f.get("fase") != "transiciones"]
    brazo = (medidas[0].get("brazo") if medidas else "") or ""
    avisos = []

    # Interferencia: el bucle de eventos de la API estuvo retrasado.
    if any((f.get("parones_250ms") or 0) >= 1
           or (f.get("lag_p99_ms") or 0) > SOSPECHA_LAG_MS for f in medidas):
        avisos.append("interferencia")

    # Acierto fuera de tolerancia en alguna fase. Las verificaciones lo
    # comprueban de forma acumulada y sobre la corrida entera; esto lo mira
    # FASE A FASE, que es como se detecta que el pool caliente venció a mitad
    # de corrida (el escalón de 200 sol/s del bloque 4).
    # Se exceptúan las celdas con TTL muy corto (la de estampida, TTL 2 s):
    # allí el acierto NO es la variable controlada, cae por diseño y la corrida
    # se ejecuta con la verificación de acierto desactivada.
    try:
        ttl = json.loads(leer(d / "api_info.json") or "{}").get("cache", {}).get("ttl_s")
    except json.JSONDecodeError:
        ttl = None
    acierto_es_variable = brazo != "direct" and (ttl is None or ttl >= 60)

    if acierto_es_variable:
        try:
            objetivo = float(acierto_objetivo(etq, d).split()[0])
        except (ValueError, IndexError):
            objetivo = None
        if objetivo is not None and any(
                f.get("acierto") is not None
                and abs(f["acierto"] - objetivo) > 0.02 for f in medidas):
            avisos.append("acierto fuera de tolerancia")

    # El respaldo no puede tardar más que presupuesto + tarifa en los brazos
    # que abandonan la espera. En B sí puede: espera al proveedor hasta el
    # timeout duro, así que la regla no aplica.
    if brazo in ("cache_opportunistic", "cache_singleflight"):
        if any((f.get("p95_fallback_ms") or 0) > TECHO_RESPALDO_MS
               or (f.get("p95_default_ms") or 0) > TECHO_RESPALDO_MS
               for f in medidas):
            avisos.append("respaldo por encima del presupuesto")

    if avisos:
        return "⚠️ válida, revisar (" + ", ".join(avisos) + ")", filas
    return "✅ válida", filas


def fase_clave(filas):
    """La fase que decide: la degradada; en escalones, el de 200 sol/s."""
    for nombre in ("degradada", "r200"):
        for f in filas or []:
            if f.get("fase") == nombre:
                return f
    return None


def fmt(v, suf="", dec=1):
    if v is None or v == "":
        return "—"
    try:
        return f"{float(v):,.{dec}f}{suf}".replace(",", " ").replace(".", ",")
    except (TypeError, ValueError):
        return str(v)


def main():
    ahora = dt.datetime.now()
    corridas = plan()
    en_curso = leer(RAIZ / "results" / "corrida_en_curso.txt").split("|")[0].strip()
    fallidas = leer(RAIZ / "results" / "corridas_fallidas.txt")
    campana = [ln for ln in leer(RAIZ / "results" / "campana_estado.txt").splitlines() if ln.strip()]

    filas_md, cuenta, grupos = [], {}, {}
    pendientes_min = 0.0
    for i, c in enumerate(corridas, 1):
        est, filas = estado_corrida(c["etq"], en_curso, fallidas)
        clave = est.split(" ", 1)[1] if " " in est else est
        cuenta[clave] = cuenta.get(clave, 0) + 1
        if est.startswith(("·", "⏳")):
            pendientes_min += MIN_ESCALONES if c["fn"] == "corrida_escalones" else MIN_CORRIDA
        f = fase_clave(filas)
        d = RAW / c["etq"]
        fin = ""
        if (d / "sanidad.txt").exists():
            fin = dt.datetime.fromtimestamp((d / "sanidad.txt").stat().st_mtime).strftime("%d/%m %H:%M")
        tasa = c["rate"] if c["fn"] == "corrida" else "20→200"
        grupos.setdefault(grupo(c["etq"]), []).append(
            f"| {i} | `{c['etq']}` | {BRAZO.get(c['brazo'], c['brazo'])} | {c['proveedor']} "
            f"| {acierto_objetivo(c['etq'], d)} | {tasa} | {est} "
            f"| {fmt(f and f.get('p95_ms'))} | {fmt(f and f.get('p99_ms'))} "
            f"| {fmt(f and f.get('sobre_475_pct'), ' %', 2)} | {fmt(f and f.get('respaldo_pct'), ' %', 2)} "
            f"| {fmt(f and f.get('lag_p99_ms'))} | {fin} |")

    total = len(corridas)
    hechas = sum(v for k, v in cuenta.items() if k.startswith(("válida", "inválida", "fallida")))
    validas = sum(v for k, v in cuenta.items() if k.startswith("válida"))
    fin_est = (ahora + dt.timedelta(minutes=pendientes_min)).strftime("%H:%M") if pendientes_min else "—"

    md = [
        "# Estado de ejecución — Experimento HA-01",
        "",
        f"_Actualizado automáticamente: {ahora.strftime('%Y-%m-%d %H:%M:%S')}. "
        "Se regenera al cerrar cada corrida y se sube al repositorio con su evidencia._",
        "",
        "## Resumen",
        "",
        "| | |",
        "| --- | --- |",
        f"| Campaña | {(campana[-1] if campana else 'sin campaña en curso').replace('|', '·')} |",
        f"| Progreso | **{hechas} de {total}** corridas ejecutadas · {validas} válidas |",
        f"| En curso | {('`' + en_curso + '`') if en_curso else '—'} |",
        f"| Pendientes | {cuenta.get('pendiente', 0)} · fin estimado hacia las {fin_est} |",
        f"| Válidas / sospechosas / inválidas / fallidas | "
        f"{cuenta.get('válida', 0)} / {cuenta.get('válida, sospechosa', 0)} / "
        f"{cuenta.get('inválida', 0)} / {cuenta.get('fallida', 0)} |",
        "",
        "**Umbral del servicio:** p95 ≤ 225 ms y p99 ≤ 475 ms (250/500 extremo a extremo "
        "menos 25 ms de borde, Anexo G). `> 475 ms` es la fracción EXACTA de cotizaciones "
        "sobre el umbral del p99, por conteo de buckets: el ASR permite como máximo el 1 %.",
        "",
        "Las métricas de cada fila corresponden a la **fase degradada** (proveedor en el "
        "estado indicado); en el bloque 4, al escalón de 200 sol/s.",
        "",
    ]
    for nombre, lineas in grupos.items():
        md += [f"## {nombre}", "",
               "| # | Corrida | Brazo | Proveedor | Acierto | sol/s | Estado | p95 ms | p99 ms "
               "| > 475 ms | Con respaldo | Lag bucle p99 ms | Fin |",
               "| ---: | --- | :---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"]
        md += lineas + [""]
    md += [
        "## Leyenda",
        "",
        "- **✅ válida** — pasó las nueve verificaciones de sanidad (tráfico en cada fase, "
        "acierto en tolerancia, sin iteraciones descartadas, sin fugas, sin evicción, error < 1 %).",
        "- **⚠️ válida, revisar** — pasó las verificaciones, pero algo pide una segunda "
        "lectura antes de citarla en el informe:",
        f"  - *interferencia*: el bucle de eventos de la API estuvo retrasado "
        f"(p99 > {SOSPECHA_LAG_MS} ms o algún parón > 250 ms), así que su cola de latencia "
        "puede estar contaminada.",
        "  - *acierto fuera de tolerancia*: alguna fase se desvió más de 2 puntos del "
        "objetivo. Las verificaciones lo miran de forma acumulada; esto lo mira fase a fase.",
        f"  - *respaldo por encima del presupuesto*: en C o C' el respaldo superó "
        f"{TECHO_RESPALDO_MS} ms, que es presupuesto + tarifa + margen. En B no aplica, "
        "porque allí el respaldo espera al proveedor hasta el timeout duro.",
        "- **❌ inválida / fallida** — no pasó las verificaciones o no terminó; queda en "
        "`results/corridas_fallidas.txt` para repetirla.",
        "- **—** en el lag: corrida anterior a la sonda del detector.",
        "",
        "## Dónde está la evidencia",
        "",
        "- `results/raw/<corrida>/` — evidencia cruda (métricas finales, configuración efectiva "
        "`api_info.json`, verificaciones `sanidad.txt`, resumen de k6), resultados por fase "
        "(`fases_resultado.json`) y **series temporales segundo a segundo** (`series.csv`), "
        "que no dependen de Prometheus.",
        "- `results/analysis/` — CSV consolidado y figuras del informe.",
        "- Desviaciones respecto del diseño publicado: `README.md`, sección *Desviaciones*.",
        "",
    ]
    DESTINO.write_text("\n".join(md), encoding="utf-8")
    print(f"estado: {hechas}/{total} ejecutadas, {validas} válidas -> {DESTINO.name}")


if __name__ == "__main__":
    main()
