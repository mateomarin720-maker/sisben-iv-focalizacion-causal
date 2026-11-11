"""Anexo de trazabilidad: cada cifra de la tesis con el archivo que la
produce y el comando que regenera ese archivo.

Lee las cifras de `docs/reports/` (no de los microdatos), así que corre sin
el banco de datos. Si una cifra no aparece donde se espera, falla: un
anexo con un número que no está en su fuente no sirve. Las cifras
simuladas llevan asterisco.

También escribe el contrato de datos del módulo de simulación como tabla,
generada de `src/simulacion/contrato.py`.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.utils.anexo_trazabilidad
Salidas: docs/anexos_tesis/ANEXO_TRAZABILIDAD.md y docs/anexos_tesis/CONTRATO_DATOS.md
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

R = Path("docs/reports")
OUT = Path("docs/anexos_tesis/ANEXO_TRAZABILIDAD.md")
OUT_CONTRATO = Path("docs/anexos_tesis/CONTRATO_DATOS.md")
PY = "poetry run python"


@dataclass
class Cifra:
    seccion: str
    que: str
    valor: str
    archivo: str
    donde: str
    comando: str
    simulada: bool = False


def num(x: float, dec: int = 3, pct: bool = False, signo: bool = False) -> str:
    """Número con coma decimal y punto de miles, como en la tesis."""
    v = 100 * x if pct else x
    s = f"{v:+,.{dec}f}" if signo else f"{v:,.{dec}f}"
    s = s.replace(",", "_").replace(".", ",").replace("_", ".").replace("-", "−")
    return s + (" %" if pct else "")


def ic(lo: float, hi: float, dec: int = 3, pct: bool = False) -> str:
    return f"[{num(lo, dec, pct, signo=not pct)}; {num(hi, dec, pct, signo=not pct)}]"


def linea(archivo: str, patron: str, grupo: int = 1) -> str:
    """Valor capturado por `patron` en un reporte de texto (falla si no está)."""
    texto = (R / archivo).read_text(encoding="utf-8")
    m = re.search(patron, texto, flags=re.M)
    if m is None:
        raise ValueError(f"No se encontró {patron!r} en {archivo}")
    return m.group(grupo)


def csv(archivo: str, **filtro) -> pd.Series:
    """La única fila de un reporte CSV que cumple el filtro."""
    d = pd.read_csv(R / archivo)
    for k, v in filtro.items():
        d = d[d[k] == v]
    if len(d) != 1:
        raise ValueError(f"{archivo} {filtro}: {len(d)} filas en vez de 1")
    return d.iloc[0]


def ate_dml(outcome: str) -> tuple[float, float, float]:
    """ATE con la celda exacta de `5_estimacion.py` para un resultado."""
    texto = (R / "estimacion_ate_att_atu_cate.txt").read_text(encoding="utf-8")
    bloque = texto.split(f"# Outcome: {outcome} ")[1].split("# Outcome:")[0]
    celda = bloque.split("W = CELDA EXACTA")[1]
    m = re.search(r"ATE \(toda la muestra\): n=[\d,]+ \| ([+-][\d.]+)\s+IC95%=\(([+-][\d.]+), ([+-][\d.]+)\)", celda)
    return float(m.group(1)), float(m.group(2)), float(m.group(3))


def cifras(contar_pruebas: bool = True) -> list[Cifra]:
    c: list[Cifra] = []
    hd = f"{PY} -m src.emparejamiento.emparejamiento_hotdeck_geih_sisben"

    # ---------------- Base: datos y enlace ----------------
    s = "Base: datos y enlace"
    c.append(Cifra(s, "Hogares de la GEIH 2024 en la muestra", linea("resultado_hotdeck.txt", r"Hogares GEIH fusionados: ([\d,]+)").replace(",", "."),
                   "resultado_hotdeck.txt", "«Hogares GEIH fusionados»", hd))
    c.append(Cifra(s, "Hogares donantes del Sisbén (nacional y Bogotá vigente)",
                   linea("resultado_hotdeck.txt", r"Donante Sisbén: ([\d,]+)").replace(",", "."),
                   "resultado_hotdeck.txt", "«Donante Sisbén»", hd))
    f = csv("comparacion_filtros_sdp.csv", filtro="vigencia_31dic2024")
    c.append(Cifra(s, "Hogares en celda exacta del Hot-Deck", num(f["pct_celda_exacta"] / 100, 2, pct=True),
                   "comparacion_filtros_sdp.csv", "fila `vigencia_31dic2024`, `pct_celda_exacta`",
                   f"{PY} -m src.validacion.comparar_filtros_sdp"))
    grupos = " · ".join(f"{g} {num(f[f'grupo_nacional_{g}_pct'] / 100, 1, pct=True)}" for g in "ABCD")
    c.append(Cifra(s, "Grupo asignado por Hot-Deck (ponderado)", grupos, "comparacion_filtros_sdp.csv",
                   "fila `vigencia_31dic2024`, `grupo_nacional_*_pct`", f"{PY} -m src.validacion.comparar_filtros_sdp"))
    po = "comparacion_pobreza_monetaria_oficial.txt"
    cmd_po = f"{PY} -m src.validacion.comparar_pobreza_monetaria_oficial"
    reconstruida = linea(po, r"^fgt0_reconstruida\s+([\d.]+)").replace(".", ",")
    oficial = linea(po, r"^fgt0_oficial\s+([\d.]+)").replace(".", ",")
    misma = linea(po, r"^pct_hogares_misma_clasificacion\s+([\d.]+)").replace(".", ",")
    n_ofi = f"{int(linea(po, r'^hogares[ ]+([0-9]+)')):,}".replace(",", ".")
    c.append(Cifra(s, "Pobreza monetaria (FGT0 por personas): reconstruida frente a oficial",
                   f"{reconstruida} % frente a {oficial} %", po,
                   "filas `fgt0_reconstruida` y `fgt0_oficial`, columna nacional", cmd_po))
    c.append(Cifra(s, "Hogares con la misma clasificación que la base oficial", f"{misma} % de {n_ofi} hogares", po,
                   "fila `pct_hogares_misma_clasificacion`, columna nacional", cmd_po))
    rep = pd.read_csv(R / "representatividad_sisben_por_depto.csv")
    nal = rep["sisben_hogares_registrados"].sum() / rep["geih_hogares_expandidos"].sum()
    c.append(Cifra(s, "Cobertura del Sisbén frente a los hogares de la GEIH (mín.–máx.; nacional)",
                   f"{num(rep['razon_cobertura'].min(), 1, pct=True)} – {num(rep['razon_cobertura'].max(), 0, pct=True)}; "
                   f"{num(nal, 1, pct=True)}", "representatividad_sisben_por_depto.csv",
                   "`razon_cobertura`; nacional = suma de registrados / suma de hogares",
                   f"{PY} -m src.validacion.verificar_representatividad_sisben"))
    v = pd.read_csv(R / "variabilidad_hotdeck_estimacion.csv").set_index("outcome")
    cmd_v = f"{PY} -m src.diagnostico.variabilidad_hotdeck 2"
    c.append(Cifra(s, "Parte de la varianza del contraste que viene de la imputación (100 sorteos)",
                   f"{num(v['fraccion_info_imputacion'].min(), 1, pct=True)} – {num(v['fraccion_info_imputacion'].max(), 1, pct=True)}",
                   "variabilidad_hotdeck_estimacion.csv", "`fraccion_info_imputacion`, tres resultados", cmd_v))
    g = v.loc["POBRE_GEIH"]
    c.append(Cifra(s, "Contraste placebo de `POBRE_GEIH` combinado con Rubin",
                   f"{num(g['estimacion'], 5, signo=True)} {ic(g['ic_lo'], g['ic_hi'], 4)}",
                   "variabilidad_hotdeck_estimacion.csv", "fila `POBRE_GEIH`", cmd_v))

    # ---------------- Componente 1 ----------------
    s = "Componente 1: diagnóstico con datos reales"
    for out in ("ipm_geih_score", "POBRE_GEIH", "log_ingreso_percapita", "POBRE_MONETARIO", "POBRE_MONETARIO_OFICIAL"):
        a, lo, hi = ate_dml(out)
        c.append(Cifra(s, f"ATE del DML (placebo), controles = celda exacta: `{out}`",
                       f"{num(a, 4, signo=True)} {ic(lo, hi, 4)}", "estimacion_ate_att_atu_cate.txt",
                       f"bloque `{out}`, «W = CELDA EXACTA», línea «ATE»", f"{PY} src/5_estimacion.py"))
    mono = pd.read_csv(R / "cotas_frechet_manski_monotonia.csv")
    cmd_c = f"{PY} -m src.diagnostico.cotas_frechet_manski"
    for sup, que in [("contraste", "Cota del contraste A/B frente al resto, sin el supuesto del vínculo"),
                     ("ate_sin_supuestos", "Cota del ATE sin supuestos (peor caso)"),
                     ("ate_mts_mtr_dep_positiva", "Cota del ATE con selección y respuesta monótonas")]:
        r = mono[(mono["outcome"] == "POBRE_MONETARIO") & (mono["supuesto"] == sup)].iloc[0]
        c.append(Cifra(s, f"{que}, pobreza monetaria", f"{ic(r['cota_lo'], r['cota_hi'])} (ancho {num(r['ancho'], 2)})",
                       "cotas_frechet_manski_monotonia.csv", f"`POBRE_MONETARIO`, supuesto `{sup}`", cmd_c))
    mod = pd.read_csv(R / "cotas_frechet_modelos.csv")
    mod = mod[mod["muestra"] == "todas"]  # el archivo repite cada cota con las celdas de al menos 30 hogares
    c.append(Cifra(s, "Parámetros de los modelos (ATE, ATT, ATU y CATE por subgrupo) cuya cota excluye el cero",
                   f"{int(mod['excluye_0'].sum())} de {len(mod)}", "cotas_frechet_modelos.csv",
                   "filas con `muestra` = `todas`, columna `excluye_0`",
                   f"{PY} -m src.diagnostico.cotas_frechet_modelos"))
    e = csv("errores_focalizacion_frechet.csv", ambito="nacional", pobreza="POBRE_MONETARIO", elegible="A-B")
    cmd_e = f"{PY} -m src.diagnostico.errores_focalizacion_frechet"
    c.append(Cifra(s, "Error de exclusión (A/B frente a pobreza monetaria), cota por celda agregada",
                   ic(e["exclusion_lo"], e["exclusion_hi"], 1, pct=True), "errores_focalizacion_frechet.csv",
                   "fila nacional, elegible `A-B`, `exclusion_lo` / `exclusion_hi`", cmd_e))
    c.append(Cifra(s, "Error de inclusión, cota por celda agregada", ic(e["inclusion_lo"], e["inclusion_hi"], 1, pct=True),
                   "errores_focalizacion_frechet.csv", "fila nacional, elegible `A-B`, `inclusion_lo` / `inclusion_hi`", cmd_e))
    sel = "seleccion_variables_lasso_ridge_shap.txt"
    exactitud = float(linea(sel, r"LASSO \(L1\) --- accuracy=([\d.]+)"))
    f1 = float(linea(sel, r"LASSO \(L1\) --- accuracy=[\d.]+ f1_macro=([\d.]+)"))
    c.append(Cifra(s, "Exactitud al predecir el grupo del Sisbén (LASSO; F1 macro)",
                   f"{num(exactitud, 1, pct=True)}; {num(f1, 2)}", sel,
                   "línea «LASSO (L1)»", f"{PY} -m src.diagnostico.seleccion_variables_lasso_shap"))
    dl = pd.read_csv(R / "variables_candidatas_deltas.csv")
    dl = dl[(dl["outcome"] == "POBRE_MONETARIO") & (dl["tipo"] == "logistica") & (dl["metrica"] == "exclusion")
            & (dl["referencia"] == "ficha_derivadas")].set_index("modelo")
    cmd_r = f"{PY} -m src.diagnostico.variables_candidatas_pobreza 6"
    c.append(Cifra(s, "Reducción del error de exclusión al calcular la composición del hogar (puntos)",
                   num(dl.loc["ficha", "delta"] * 100, 2), "variables_candidatas_deltas.csv",
                   "`ficha` frente a `ficha_derivadas`, métrica `exclusion`, logística", cmd_r))
    c.append(Cifra(s, "Reducción del error de exclusión con todas las variables nuevas (puntos)",
                   f"{num(-dl.loc['todo', 'delta'] * 100, 2)} {ic(-dl.loc['todo', 'ic_hi'] * 100, -dl.loc['todo', 'ic_lo'] * 100, 2)}",
                   "variables_candidatas_deltas.csv", "`todo` frente a `ficha_derivadas`", cmd_r))
    c.append(Cifra(s, "Aporte del estrato al error de exclusión (puntos)", num(dl.loc["+estrato", "delta"] * 100, 2, signo=True),
                   "variables_candidatas_deltas.csv", "`+estrato` frente a `ficha_derivadas`", cmd_r))
    po2 = pd.read_csv(R / "variables_candidatas_posterior.csv")
    cu = po2[(po2["modelo"] == "+cuenta") & (po2["metrica"] == "exclusion")].iloc[0]
    c.append(Cifra(s, "Aporte de la cuenta de ahorros al error de exclusión (puntos)", num(cu["delta"] * 100, 2, signo=True),
                   "variables_candidatas_posterior.csv", "`+cuenta`, métrica `exclusion`", cmd_r))

    # ---------------- Componente 2 ----------------
    s = "Componente 2: simulación semisintética"
    sim = pd.read_csv(R / "simulacion_semisintetica_resumen.csv")
    cmd_s = f"{PY} -m src.simulacion"

    def celda(esc: str, vin: str, out: str, est: str) -> pd.Series:
        return csv("simulacion_semisintetica_resumen.csv", escenario=esc, vinculo=vin, outcome=out, estimador=est)

    c.append(Cifra(s, "Repeticiones (Causal Forest) y celdas de resultados",
                   f"{int(sim['reps'].max())} ({int(sim.loc[sim['estimador'] == 'causal_forest', 'reps'].max())}); {len(sim)} celdas",
                   "simulacion_semisintetica_resumen.csv", "columna `reps`; filas del archivo", cmd_s, True))
    for out, que in [("log_ingreso", "log-ingreso"), ("pobre_monetario", "pobreza monetaria")]:
        r = celda("confusion_observada", "oraculo", out, "linear_dml")
        c.append(Cifra(s, f"Efecto verdadero, {que}", num(r["efecto_verdadero"], 4, signo=True) + "\\*",
                       "simulacion_semisintetica_resumen.csv", f"`efecto_verdadero`, outcome `{out}`", cmd_s, True))
    for esc, est, que in [("confusion_observada", "linear_dml", "Confusión observada, LinearDML"),
                          ("confusion_no_observada", "linear_dml", "Confusión no observada fuerte, LinearDML"),
                          ("regla_corte", "discontinuidad_rd", "Regla de corte, RD (efecto en el corte)")]:
        outs = ["log_ingreso"] if est == "discontinuidad_rd" else ["log_ingreso", "pobre_monetario"]
        for out in outs:
            vals = []
            for vin, nom in [("oraculo", "oráculo"), ("vinculo_parcial_50", "vínculo 50 %"), ("hotdeck", "Hot-Deck")]:
                r = celda(esc, vin, out, est)
                vals.append(f"{nom} {num(r['estimacion'], 3, signo=True)}\\* (cob. {num(r['cobertura'], 2)}\\*)")
            c.append(Cifra(s, f"{que}, {out}", "; ".join(vals), "simulacion_semisintetica_resumen.csv",
                           f"escenario `{esc}`, estimador `{est}`, `estimacion` y `cobertura`", cmd_s, True))
    nulo = celda("efecto_nulo", "oraculo", "log_ingreso", "linear_dml")
    c.append(Cifra(s, "Sesgo de LinearDML con efecto nulo (oráculo, log-ingreso)",
                   f"{num(nulo['sesgo'], 4, signo=True)}\\* (cobertura {num(nulo['cobertura'], 2)}\\*)",
                   "simulacion_semisintetica_resumen.csv", "escenario `efecto_nulo`, `linear_dml`, `oraculo`", cmd_s, True))
    sin_confusion = ["aleatoria", "confusion_observada", "efecto_nulo"]
    cf = sim[(sim["estimador"] == "causal_forest") & (sim["vinculo"] == "oraculo") & sim["escenario"].isin(sin_confusion)]
    c.append(Cifra(s, "Error del CATE del Causal Forest (PEHE, oráculo; asignación aleatoria, confusión observada y efecto nulo)",
                   f"{num(cf['pehe'].min(), 3)} – {num(cf['pehe'].max(), 3)}\\*", "simulacion_semisintetica_resumen.csv",
                   "`causal_forest`, `oraculo`, esos tres escenarios, columna `pehe`", cmd_s, True))
    sen = pd.read_csv(R / "sensibilidad_semisintetica_resumen.csv")
    c.append(Cifra(s, "Repeticiones de la sensibilidad", f"{int(sen['reps'].max())}", "sensibilidad_semisintetica_resumen.csv",
                   "columna `reps`", f"{PY} -m src.simulacion.sensibilidad_semisintetica", True))
    for vin in ("oraculo", "hotdeck"):
        a = csv("sensibilidad_semisintetica_resumen.csv", escenario="efecto_nulo", vinculo=vin, estimador="linear_dml")
        b = csv("sensibilidad_semisintetica_resumen.csv", escenario="efecto_nulo", vinculo=vin, estimador="linear_dml_sin_regularizar")
        c.append(Cifra(s, f"Sesgo de LinearDML con efecto nulo ({vin}): regularización del proyecto frente a casi nula",
                       f"{num(a['sesgo'], 4, signo=True)}\\* (z {num(a['z_sesgo'], 1, signo=True)}\\*) frente a "
                       f"{num(b['sesgo'], 4, signo=True)}\\* (z {num(b['z_sesgo'], 1, signo=True)}\\*)",
                       "sensibilidad_semisintetica_resumen.csv", f"`efecto_nulo`, `{vin}`, `sesgo` y `z_sesgo`",
                       f"{PY} -m src.simulacion.sensibilidad_semisintetica", True))

    # ---------------- Componente 3 ----------------
    s = "Componente 3: reglas de focalización"
    cmd_f = f"{PY} -m src.focalizacion.reglas_focalizacion"
    nombres = {"vigente_hotdeck": "Vigente (Hot-Deck)", "aleatoria": "Aleatoria", "pmt_ingreso": "Proxy de medios por ingreso",
               "pmt_brecha_cate": "Proxy + CATE con vínculo", "pmt_brecha_cate_hd": "Proxy + CATE con Hot-Deck"}
    for regla, nom in nombres.items():
        p = csv("reglas_focalizacion_resumen.csv", efecto="proporcional", presupuesto="hogares", regla=regla)
        m = csv("reglas_focalizacion_resumen.csv", efecto="monto_fijo", presupuesto="hogares", regla=regla)
        c.append(Cifra(s, f"{nom}: error de exclusión; % de la reducción ideal de FGT1 (proporcional / monto fijo)",
                       f"{num(p['error_exclusion'], 1, pct=True)}\\*; {num(p['pct_ideal'], 0)}\\* / {num(m['pct_ideal'], 0)}\\*",
                       "reglas_focalizacion_resumen.csv", f"regla `{regla}`, presupuesto `hogares`", cmd_f, True))
    rep_f = pd.read_csv(R / "reglas_focalizacion_resumen.csv")
    c.append(Cifra(s, "Repeticiones de las reglas", str(int(rep_f["reps"].max())), "reglas_focalizacion_resumen.csv",
                   "columna `reps`", cmd_f, True))
    d = csv("reglas_focalizacion_resumen.csv", efecto="monto_fijo", presupuesto="dinero", regla="pmt_ingreso")
    h = csv("reglas_focalizacion_resumen.csv", efecto="monto_fijo", presupuesto="hogares", regla="pmt_ingreso")
    c.append(Cifra(s, "Proxy de medios con el mismo dinero que la vigente: % del ideal (gasto relativo con el mismo número de hogares)",
                   f"{num(d['pct_ideal'], 0)}\\* ({num(h['gasto_rel'], 2)}\\*)", "reglas_focalizacion_resumen.csv",
                   "`pmt_ingreso`, monto fijo, presupuestos `dinero` y `hogares`", cmd_f, True))

    # ---------------- Repositorio ----------------
    s = "Repositorio"
    # Se cuenta la lista sin importar el script (importarlo corre las mutaciones).
    arbol = ast.parse(Path("tests/mutaciones.py").read_text(encoding="utf-8"))
    n_mut = next(len(n.value.elts) for n in arbol.body
                 if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "MUTACIONES")
    if contar_pruebas:
        pruebas = subprocess.run([sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
                                 capture_output=True, text=True).stdout
        n_pruebas = int(re.search(r"(\d+) tests? collected", pruebas).group(1))
        c.append(Cifra(s, "Pruebas automáticas", str(n_pruebas), "tests/", "`pytest --collect-only`",
                       f"{PY} -m pytest tests/"))
    c.append(Cifra(s, "Errores conocidos reintroducidos por la prueba de mutación", str(n_mut), "tests/mutaciones.py",
                   "lista `MUTACIONES`", "python tests/mutaciones.py"))
    return c


def markdown(c: list[Cifra]) -> str:
    partes = ["# Anexo: trazabilidad de las cifras", "",
              "Cada cifra de la tesis con el archivo de `docs/reports/` del que sale y el comando que regenera ese "
              "archivo. El anexo se genera leyendo esos archivos "
              "(`python -m src.utils.anexo_trazabilidad`); si una cifra no está en su fuente, el generador falla.", "",
              "\\* Resultado simulado (semisintético): el efecto verdadero lo fija el investigador; no es una "
              "estimación con datos reales.", ""]
    for seccion in dict.fromkeys(x.seccion for x in c):
        partes += [f"## {seccion}", "", "| Cifra | Valor | Archivo | Dónde | Comando |", "|---|---|---|---|---|"]
        for x in (x for x in c if x.seccion == seccion):
            partes.append(f"| {x.que} | {x.valor} | `{x.archivo}` | {x.donde} | `{x.comando}` |")
        partes.append("")
    return "\n".join(partes)


def contrato_markdown() -> str:
    from src.simulacion import contrato

    return "\n".join([
        "# Anexo: contrato de datos", "",
        "Columnas que exige el módulo de simulación (`src/simulacion/contrato.py`) a quien lo use con sus propios "
        "datos. Los nombres son los de las tablas estandarizadas del proyecto y no se cambian ni se traducen: el "
        "módulo valida que estén y que sus códigos estén en el dominio, y si no, falla nombrando cada columna. Las "
        "variables derivadas (celda del Hot-Deck, zona urbana, jefe mujer, P(T | celda)) las calcula el módulo.", "",
        "Los códigos se comparan como texto: un código `1.0` no es `1` y se rechaza. Esta tabla se genera del "
        "código (`python -m src.utils.anexo_trazabilidad`).", "",
        contrato.tabla_markdown(), ""])


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(markdown(cifras()), encoding="utf-8")
    OUT_CONTRATO.write_text(contrato_markdown(), encoding="utf-8")
    print(f"Guardado: {OUT}\nGuardado: {OUT_CONTRATO}")


if __name__ == "__main__":
    main()
