"""Simulación principal ampliada (fase 2b de `docs/metodologia/METODOLOGIA_FHDI.md`):
los estimadores que quitan la celda exactamente y el régimen de
imputación fraccional (FHDI), sin cambiar la corrida vigente.

Usa las mismas semillas y los mismos sorteos que `evaluacion.py`: en cada
repetición la encuesta, el registro, el donante y los hogares con donante
son los mismos que en la corrida de la Tabla 6. Solo se estima lo nuevo y,
como control, la regresión con efectos fijos, que debe reproducir la de la
corrida vigente repetición por repetición:

- **LinearDML y Causal Forest dentro de la celda** (preguntas 7 y 8 de
  `sensibilidad_semisintetica.py`) en las tres integraciones vigentes
  (oráculo, vínculo del 50 % y Hot-Deck). El Causal Forest, como en la
  corrida vigente, solo en log-ingreso, oráculo y Hot-Deck, y en el
  régimen FHDI con vínculo del 50 %.
- **Régimen FHDI:** `fhdi_parcial_50` (la mitad de los hogares con su T
  verdadero y el resto con la proporción de T = 1 de su celda) y `fhdi`
  (todos con la proporción de su celda: no identificable, se reporta
  vacío). En `fhdi_parcial_50` también el LinearDML vigente (con
  tratamiento continuo), para comparar.

Los vigentes en las integraciones vigentes (diferencia de medias,
LinearDML, Causal Forest y RD) no se vuelven a estimar: salen de
`docs/reports/simulacion_semisintetica_resumen.csv`, con las mismas
repeticiones, y `tabla_comparativa` los pone al lado.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.simulacion ampliada [n_jobs]
Salidas (simuladas*):
    docs/reports/simulacion_ampliada{.csv,_resumen.csv,_config.json}
    docs/reports/simulacion_ampliada_tablas.md
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.simulacion import contrato, reportes
from src.simulacion.asignacion import asignar
from src.simulacion.base import celdas_por_nivel, diseno_x, firma_con_datos
from src.simulacion.escenarios import (B_X, ESCENARIOS, LOTE, MAX_REPS, MAX_REPS_BOSQUE, MIN_REPS, MIN_REPS_BOSQUE,
                                       N_ENCUESTA, OUTCOMES, SEED, TAU, UMBRAL_COBERTURA, UMBRAL_SESGO, VINCULOS,
                                       VINCULOS_BOSQUE)
from src.simulacion.estimadores import identificable, regresion_efectos_fijos
from src.simulacion.evaluacion import CELDA, OUT_RESUMEN, _outcomes, cargar_base, resumir
from src.simulacion.sensibilidad_semisintetica import (causal_forest_intra_celda, linear_dml, linear_dml_intra_celda,
                                                       t_observado)
from src.simulacion.vinculo import probabilidad_celda, sortear_donante

logger = logging.getLogger(__name__)

OUT = Path("docs/reports/simulacion_ampliada.csv")
OUT_RESUMEN_AMPLIADA = Path("docs/reports/simulacion_ampliada_resumen.csv")
OUT_FIRMA = Path("docs/reports/simulacion_ampliada_config.json")
OUT_TABLAS = Path("docs/reports/simulacion_ampliada_tablas.md")
# Fracción de hogares con su T verdadero en el régimen FHDI.
VINCULOS_FHDI = {"fhdi_parcial_50": 0.5, "fhdi": 0.0}
BOSQUES = ("causal_forest", "causal_forest_intra_celda")


def una_repeticion(b: pd.DataFrame, rep: int, n: int = N_ENCUESTA, con_bosque: bool = False) -> list[dict]:
    """Los sorteos de `evaluacion.una_repeticion` en el mismo orden (los
    del régimen FHDI van después, para no mover los vigentes)."""
    filas = []
    for i_esc, (nombre_esc, esc) in enumerate(ESCENARIOS.items()):
        rng = np.random.default_rng([SEED, rep, i_esc])
        t_real, _, _ = asignar(b, esc, rng)
        idx = rng.permutation(len(b))
        enc, reg = idx[:n], idx[n:]
        d = b.iloc[enc].reset_index(drop=True)
        celda = d["hotdeck_celda_cat"].to_numpy()
        tau = esc.get("factor_tau", 1.0) * d["tau"].to_numpy()
        niveles = celdas_por_nivel(b)
        donante, _ = sortear_donante(niveles[enc], niveles[reg], rng, devolver_nivel=True)
        donante = reg[donante]
        ys = _outcomes(d, d["y0"].to_numpy(), tau, t_real[enc])
        Z = diseno_x(d)

        t_vinculos = {}
        for nombre_v, frac in VINCULOS.items():
            usa_donante = rng.random(n) < frac
            t_vinculos[nombre_v] = np.where(usa_donante, t_real[donante], t_real[enc])
        p = probabilidad_celda(niveles[enc], niveles[reg], t_real[reg])
        for nombre_v, L in VINCULOS_FHDI.items():
            t_vinculos[nombre_v] = t_observado(t_real[enc], t_real[donante], p, rng.random(n) < L, "fhdi")

        for nombre_v, t_obs in t_vinculos.items():
            ok = identificable(t_obs, celda)
            fhdi = nombre_v in VINCULOS_FHDI
            for outcome, (y, efecto_hogar) in ys.items():
                res = {}
                if ok:
                    res["regresion_efectos_fijos"] = (*regresion_efectos_fijos(y, t_obs, Z, celda), None)
                    res["linear_dml_intra_celda"] = (*linear_dml_intra_celda(d, y, t_obs), None)
                    if fhdi:
                        res["linear_dml"] = (*linear_dml(d, y, t_obs, regularizado=True), None)
                    bosque_aqui = nombre_v in VINCULOS_BOSQUE or nombre_v == "fhdi_parcial_50"
                    if con_bosque and outcome == "log_ingreso" and bosque_aqui:
                        a, lo, hi, cate = causal_forest_intra_celda(d, y, t_obs)
                        res["causal_forest_intra_celda"] = (a, lo, hi, float(np.sqrt(np.mean((cate - efecto_hogar) ** 2))))
                else:
                    res = {e: (np.nan, np.nan, np.nan, None) for e in
                           ("regresion_efectos_fijos", "linear_dml_intra_celda", "linear_dml")}
                for nombre_e, (a, lo, hi, pehe) in res.items():
                    filas.append(dict(rep=rep, escenario=nombre_esc, vinculo=nombre_v, outcome=outcome,
                                      estimador=nombre_e, efecto_verdadero=float(efecto_hogar.mean()), estimacion=a,
                                      ic_lo=lo, ic_hi=hi, pehe=pehe, identificable=ok,
                                      concordancia_t=float(np.mean(t_obs == t_real[enc]) * 100)))
    return filas


def pendientes(res: pd.DataFrame, bosque: bool) -> pd.DataFrame:
    """Celdas que todavía no cumplen el umbral de MCSE (los mismos de la
    corrida vigente); las no identificables no cuentan."""
    r = res[res["estimador"].isin(BOSQUES) == bosque].dropna(subset=["sesgo"])
    falla = (r["mcse_sesgo"] > r["outcome"].map(UMBRAL_SESGO)) | (r["mcse_cobertura"] > UMBRAL_COBERTURA)
    return r[falla]


def _firma(n: int) -> str:
    cfg = dict(ESCENARIOS=ESCENARIOS, VINCULOS=VINCULOS, VINCULOS_FHDI=VINCULOS_FHDI, OUTCOMES=OUTCOMES, B_X=B_X,
               TAU=TAU, LINEAS=contrato.LINEAS, SEED=SEED, n=n, version=1)
    return hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]


ETIQUETAS = {"oraculo": "Oráculo", "vinculo_parcial_50": "Vínculo 50 %", "hotdeck": "Hot-Deck",
             "fhdi_parcial_50": "FHDI, vínculo 50 %", "fhdi": "FHDI sin vínculo"}
COLUMNAS = [("regresion_efectos_fijos", "Regresión EF celda"), ("linear_dml", "LinearDML vigente"),
            ("linear_dml_intra_celda", "LinearDML dentro de la celda"), ("causal_forest", "Causal Forest vigente"),
            ("causal_forest_intra_celda", "Causal Forest dentro de la celda")]


def tabla_comparativa(nueva: pd.DataFrame, vigente: pd.DataFrame) -> str:
    """Media de la estimación (cobertura) por escenario, integración y
    estimador: los vigentes de la Tabla 6 al lado de los nuevos. La
    regresión sale de la corrida vigente (la ampliada la reproduce)."""
    num = lambda v, fmt: format(v, fmt).replace(".", ",") + "\\*"  # noqa: E731
    vig = vigente[vigente["estimador"].isin(["regresion_efectos_fijos", "linear_dml", "causal_forest"])]
    nueva = nueva[~((nueva["estimador"] == "regresion_efectos_fijos") & nueva["vinculo"].isin(VINCULOS))]
    x = pd.concat([vig, nueva], ignore_index=True)
    partes = []
    for out in OUTCOMES:
        cols = [(e, t) for e, t in COLUMNAS if e in set(x.loc[x["outcome"] == out, "estimador"])]
        partes.append(f"### {reportes.TITULOS.get(out, out)}\n")
        partes.append("| Escenario | Efecto verdadero | Integración | " + " | ".join(t for _, t in cols) + " |")
        partes.append("|" + "---|" * (len(cols) + 3))
        for esc in ESCENARIOS:
            for v in ETIQUETAS:
                g = x[(x["outcome"] == out) & (x["escenario"] == esc) & (x["vinculo"] == v)].set_index("estimador")
                if g.empty:
                    continue
                celdas = []
                for e, _ in cols:
                    if e in g.index and pd.notna(g.loc[e, "estimacion"]):
                        c = g.loc[e]
                        celdas.append(f"{num(c['estimacion'], '+.3f')} ({num(c['cobertura'], '.2f')})")
                    elif e in g.index:
                        celdas.append("no identificable")
                    else:
                        celdas.append("—")
                cab = esc.replace("_", " ") if v == "oraculo" else ""
                partes.append(f"| {cab} | {num(g['efecto_verdadero'].mean(), '+.3f')} | {ETIQUETAS[v]} | "
                              + " | ".join(celdas) + " |")
        partes.append("")
    return "\n".join(partes)


def control_reproduccion(r: pd.DataFrame, vigente: Path = Path("docs/reports/simulacion_semisintetica.csv")) -> float:
    """Máxima diferencia, repetición por repetición, entre la regresión con
    efectos fijos de la ampliada y la de la corrida vigente (debe ser ≈0:
    mismos sorteos)."""
    v = reportes.sin_marca(pd.read_csv(vigente))
    v = v[v["estimador"] == "regresion_efectos_fijos"]
    a = r[(r["estimador"] == "regresion_efectos_fijos") & r["vinculo"].isin(VINCULOS)]
    m = a.merge(v, on=["rep", "escenario", "vinculo", "outcome"], suffixes=("", "_vigente"))
    return float((m["estimacion"] - m["estimacion_vigente"]).abs().max()) if len(m) else float("nan")


def main(n_jobs: int = 4, n: int = N_ENCUESTA) -> pd.DataFrame:
    from joblib import Parallel, delayed, parallel_config

    b = cargar_base()
    firma = firma_con_datos(_firma(n), b)
    r = pd.DataFrame()
    if OUT.exists() and OUT_FIRMA.exists() and json.loads(OUT_FIRMA.read_text()).get("firma") == firma:
        r = reportes.sin_marca(pd.read_csv(OUT))
        logger.info("Reanudando: %d repeticiones ya guardadas", r["rep"].nunique())
    else:
        OUT_FIRMA.write_text(json.dumps(dict(firma=firma, n=n)))
    while True:
        hechas = 0 if r.empty else r["rep"].nunique()
        reps_bosque = 0 if r.empty else r.loc[r["estimador"].isin(BOSQUES), "rep"].nunique()
        res = resumir(r) if not r.empty else None
        falta = hechas < MIN_REPS or len(pendientes(res, bosque=False)) > 0
        falta_bosque = reps_bosque < MIN_REPS_BOSQUE or (res is not None and len(pendientes(res, bosque=True)) > 0)
        falta_bosque = falta_bosque and reps_bosque < MAX_REPS_BOSQUE
        if (not falta and not falta_bosque) or hechas >= MAX_REPS:
            break
        lote = list(range(hechas, hechas + LOTE))
        t0 = time.time()
        with parallel_config(backend="loky", inner_max_num_threads=1):
            partes = Parallel(n_jobs=n_jobs)(delayed(una_repeticion)(b, rep, n, falta_bosque) for rep in lote)
        r = pd.concat([r, pd.DataFrame([f for p in partes for f in p])], ignore_index=True)
        reportes.marcar_simulado(r).to_csv(OUT, index=False)
        res = resumir(r)
        logger.info("Lote reps %d-%d%s en %.0f s | celdas sin converger: %d (+ %d de Causal Forest)", lote[0],
                    lote[-1], " con Causal Forest" if falta_bosque else "", time.time() - t0,
                    len(pendientes(res, False)), len(pendientes(res, True)))

    res = resumir(r)
    reportes.marcar_simulado(res).to_csv(OUT_RESUMEN_AMPLIADA, index=False)
    vigente = reportes.sin_marca(pd.read_csv(OUT_RESUMEN))
    tablas = tabla_comparativa(res, vigente)
    OUT_TABLAS.write_text(f"{reportes.NOTA_SIMULADO}\n\n{tablas}", encoding="utf-8")
    conv = pendientes(res, False).empty and pendientes(res, True).empty

    print(f"\n{reportes.NOTA_SIMULADO}")
    print(f"\n=== Simulación ampliada*: {r['rep'].nunique()} repeticiones (Causal Forest en "
          f"{r.loc[r['estimador'].isin(BOSQUES), 'rep'].nunique()}), encuesta de {n:,} hogares reales ===")
    print(f"Convergencia: {'alcanzada en todas las celdas' if conv else 'NO alcanzada en todas'}")
    print(f"Control: la regresión con efectos fijos reproduce la corrida vigente (diferencia máxima por "
          f"repetición {control_reproduccion(r):.2e})")
    print(f"\n{tablas}")
    if not conv:
        print(pd.concat([pendientes(res, False), pendientes(res, True)])[CELDA + ["reps", "mcse_sesgo",
                                                                                 "mcse_cobertura"]].to_string(index=False))
    print(f"Guardado: {OUT}\nGuardado: {OUT_RESUMEN_AMPLIADA}\nGuardado: {OUT_TABLAS}")
    return res
