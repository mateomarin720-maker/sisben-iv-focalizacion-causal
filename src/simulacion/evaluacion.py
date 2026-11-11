"""Evaluación semisintética: una repetición, resumen con error estándar
Monte Carlo (MCSE) y bucle de convergencia por lotes.

En cada repetición la población se parte en dos muestras sin llave común,
como GEIH y Sisbén: la "encuesta" (X, Y) y el "registro" (X, T,
puntaje). El T verdadero de la encuesta solo se usa para medir; los
estimadores reciben únicamente el T observado según la integración.

Las repeticiones corren en lotes, en paralelo, hasta que el MCSE de cada
celda (escenario × integración × outcome × estimador) queda bajo el
umbral o hasta `MAX_REPS`. Cada lote se guarda al terminar: si la corrida
se interrumpe, se reanuda desde el último lote con la misma configuración.
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
from src.simulacion.base import celdas_por_nivel, diseno_x, preparar_base
from src.simulacion.escenarios import (B_X, ESCENARIOS, H_RD, LOTE, MAX_REPS, MAX_REPS_BOSQUE, MIN_REPS,
                                       MIN_REPS_BOSQUE, N_ENCUESTA, OUTCOMES, SEED, TAU, UMBRAL_COBERTURA,
                                       UMBRAL_SESGO, VINCULOS, VINCULOS_BOSQUE)
from src.simulacion.estimadores import (diferencia_medias, discontinuidad, dml, pesos_rd,
                                        regresion_efectos_fijos)
from src.simulacion.vinculo import sortear_donante

logger = logging.getLogger(__name__)

HOGARES = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
REGISTRO = Path("data/2_models/sisben_estandarizado_2024_con_bogota.parquet")
OUT = Path("docs/reports/simulacion_semisintetica.csv")
OUT_RESUMEN = Path("docs/reports/simulacion_semisintetica_resumen.csv")
OUT_CONVERGENCIA = Path("docs/reports/simulacion_semisintetica_convergencia.csv")
OUT_FIRMA = Path("docs/reports/simulacion_semisintetica_config.json")
CELDA = ["escenario", "vinculo", "outcome", "estimador"]


def _outcomes(d: pd.DataFrame, y0: np.ndarray, tau: np.ndarray, t: np.ndarray) -> dict:
    """Y observado y efecto verdadero por hogar para cada outcome."""
    y = y0 + tau * t
    lp = d["log_lp"].to_numpy()
    return {"log_ingreso": (y, tau),
            "pobre_monetario": ((y < lp).astype(float), (y0 + tau < lp).astype(float) - (y0 < lp).astype(float))}


def una_repeticion(b: pd.DataFrame, rep: int, n: int = N_ENCUESTA, con_bosque: bool = False) -> list[dict]:
    filas = []
    for i_esc, (nombre_esc, esc) in enumerate(ESCENARIOS.items()):
        rng = np.random.default_rng([SEED, rep, i_esc])
        t_real, puntaje, corte = asignar(b, esc, rng)
        idx = rng.permutation(len(b))
        enc, reg = idx[:n], idx[n:]  # encuesta (X, Y) y registro (X, T, puntaje), sin llave común
        d = b.iloc[enc].reset_index(drop=True)
        celda = d["hotdeck_celda_cat"].to_numpy()
        tau = esc.get("factor_tau", 1.0) * d["tau"].to_numpy()
        niveles = celdas_por_nivel(b)
        donante, nivel = sortear_donante(niveles[enc], niveles[reg], rng, devolver_nivel=True)
        donante = reg[donante]
        pct_respaldo = float((nivel > 0).mean() * 100)  # donante fuera de la celda exacta
        ys = _outcomes(d, d["y0"].to_numpy(), tau, t_real[enc])
        Z = diseno_x(d)
        h = H_RD * float(np.std(puntaje))
        w_rd = pesos_rd(puntaje[enc], corte, h) if esc.get("corte") else None

        for nombre_v, frac in VINCULOS.items():
            usa_donante = rng.random(n) < frac
            t_obs = np.where(usa_donante, t_real[donante], t_real[enc])
            p_obs = np.where(usa_donante, puntaje[donante], puntaje[enc])
            for outcome, (y, efecto_hogar) in ys.items():
                verdad = float(efecto_hogar.mean())
                comun = dict(rep=rep, escenario=nombre_esc, vinculo=nombre_v, outcome=outcome,
                             pct_tratados=float(t_obs.mean() * 100),
                             concordancia_t=float((t_obs == t_real[enc]).mean() * 100),
                             pct_respaldo=pct_respaldo)
                res = {"diferencia_medias": (*diferencia_medias(y, t_obs), None),
                       "regresion_efectos_fijos": (*regresion_efectos_fijos(y, t_obs, Z, celda), None)}
                a, lo, hi, _ = dml(d, y, t_obs, bosque=False)
                res["linear_dml"] = (a, lo, hi, None)
                if con_bosque and outcome == "log_ingreso" and nombre_v in VINCULOS_BOSQUE:
                    a, lo, hi, cate = dml(d, y, t_obs, bosque=True)
                    res["causal_forest"] = (a, lo, hi, float(np.sqrt(np.mean((np.ravel(cate) - efecto_hogar) ** 2))))
                verdades = {k: verdad for k in res}
                if w_rd is not None:
                    res["discontinuidad_rd"] = (*discontinuidad(y, p_obs, corte, h), None)
                    verdades["discontinuidad_rd"] = float(np.average(efecto_hogar, weights=w_rd))  # efecto en el corte
                for nombre_e, (a, lo, hi, pehe) in res.items():
                    filas.append(dict(comun, estimador=nombre_e, efecto_verdadero=verdades[nombre_e],
                                      estimacion=a, ic_lo=lo, ic_hi=hi, pehe=pehe))
    return filas


def resumir(r: pd.DataFrame) -> pd.DataFrame:
    """Métricas por celda con su error estándar Monte Carlo (Morris et al.,
    2019, tabla 6)."""
    r = r.assign(error=r["estimacion"] - r["efecto_verdadero"],
                 cubre=((r["ic_lo"] <= r["efecto_verdadero"]) & (r["efecto_verdadero"] <= r["ic_hi"])).astype(float),
                 ancho=r["ic_hi"] - r["ic_lo"])
    g = r.groupby(CELDA, sort=False)
    out = g.agg(reps=("rep", "size"), efecto_verdadero=("efecto_verdadero", "mean"),
                estimacion=("estimacion", "mean"), sesgo=("error", "mean"), sd_error=("error", "std"),
                rmse=("error", lambda e: float(np.sqrt(np.mean(e**2)))),
                cobertura=("cubre", "mean"), ancho_ic=("ancho", "mean"), pehe=("pehe", "mean"),
                concordancia_t=("concordancia_t", "mean")).reset_index()
    R = out["reps"]
    out["mcse_sesgo"] = out["sd_error"].fillna(0) / np.sqrt(R)
    out["mcse_cobertura"] = np.sqrt(out["cobertura"] * (1 - out["cobertura"]) / R)
    var_e2 = g["error"].agg(lambda e: float(np.var(e**2, ddof=1)) if len(e) > 1 else 0.0).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        out["mcse_rmse"] = np.sqrt(var_e2 / (4 * R * out["rmse"] ** 2)).fillna(0)
    oraculo = out[out["vinculo"] == "oraculo"].set_index(["escenario", "outcome", "estimador"])["rmse"]
    out["rmse_oraculo"] = out.set_index(["escenario", "outcome", "estimador"]).index.map(oraculo)
    out["degradacion_rmse"] = out["rmse"] - out["rmse_oraculo"]
    return out.drop(columns="sd_error")


def pendientes(res: pd.DataFrame, bosque: bool) -> pd.DataFrame:
    """Celdas que todavía no cumplen el umbral de MCSE."""
    sel = res["estimador"].eq("causal_forest") == bosque
    r = res[sel]
    falla = (r["mcse_sesgo"] > r["outcome"].map(UMBRAL_SESGO)) | (r["mcse_cobertura"] > UMBRAL_COBERTURA)
    return r[falla]


def _firma(n: int, **origen) -> str:
    """Huella de la configuración. Versión 3: el Hot-Deck simulado usa la
    cadena de respaldos del pipeline (antes, sin donantes en la celda se
    sorteaba en todo el registro); las repeticiones de la versión 2 no se
    mezclan con las nuevas. `origen` distingue los modos simulado y de
    datos propios (vacío en la corrida de la tesis)."""
    cfg = dict(ESCENARIOS=ESCENARIOS, VINCULOS=VINCULOS, OUTCOMES=OUTCOMES, B_X=B_X, TAU=TAU, H_RD=H_RD,
               LINEAS=contrato.LINEAS, SEED=SEED, n=n, version=3, **origen)
    return hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]


def rutas(salida: Path | None = None) -> dict[str, Path]:
    """Dónde se guardan las salidas: las de la tesis (`docs/`) o, en los
    modos simulado y de datos propios, una carpeta propia."""
    if salida is None:
        return dict(out=OUT, resumen=OUT_RESUMEN, convergencia=OUT_CONVERGENCIA, firma=OUT_FIRMA,
                    figura=reportes.FIGURA, tablas=reportes.OUT_TABLAS)
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    return dict(out=salida / "evaluacion.csv", resumen=salida / "evaluacion_resumen.csv",
                convergencia=salida / "evaluacion_convergencia.csv", firma=salida / "evaluacion_config.json",
                figura=salida / "evaluacion_convergencia.png", tablas=salida / "evaluacion_tablas.md")


def _previas(n: int, r: dict[str, Path], firma: str) -> pd.DataFrame | None:
    """Repeticiones ya guardadas con la misma configuración (para reanudar)."""
    if r["out"].exists() and r["firma"].exists() and json.loads(r["firma"].read_text()).get("firma") == firma:
        return reportes.sin_marca(pd.read_csv(r["out"]))
    return None


def p_t_por_celda(registro: pd.DataFrame) -> pd.Series:
    """P(T = A o B | celda) en el registro, con la celda del pipeline."""
    from src.diagnostico.cotas_frechet_manski import _p_t_por_celda

    contrato.validar(registro, "registro")
    return _p_t_por_celda(registro)["p_t"]


def cargar_base(hogares: Path = HOGARES, registro: Path = REGISTRO) -> pd.DataFrame:
    """Tabla de trabajo desde dos archivos Parquet con las columnas canónicas."""
    p_t = p_t_por_celda(pd.read_parquet(registro, columns=contrato.columnas("registro")))
    return preparar_base(pd.read_parquet(hogares, columns=contrato.columnas("hogares")), p_t)


def main(n_jobs: int = 3, n: int = N_ENCUESTA, hogares: Path = HOGARES, registro: Path = REGISTRO,
         base: pd.DataFrame | None = None, salida: Path | None = None, origen: dict | None = None,
         max_reps: int = MAX_REPS) -> pd.DataFrame:
    """Evaluación hasta la convergencia. Sin `base` ni `salida`, es la
    corrida de la tesis (hogares de la GEIH, salidas en `docs/`). Los modos
    del framework pasan su propia `base`, una carpeta de `salida` y su
    `origen` (para no mezclar repeticiones de poblaciones distintas)."""
    from joblib import Parallel, delayed, parallel_config

    if base is None:
        logger.info("Cargando %s y P(T | celda) de %s", hogares, registro)
        b = cargar_base(hogares, registro)
    else:
        b = base
    n = min(n, len(b) // 2)  # la otra mitad es el registro del que salen los donantes
    logger.info("Base: %s hogares, %s celdas | tau medio %.4f", f"{len(b):,}", b["celda"].nunique(),
                b["tau"].mean())
    rr = rutas(salida)
    firma = _firma(n, **(origen or {}))

    r = _previas(n, rr, firma)
    if r is not None:
        logger.info("Reanudando: %d repeticiones ya guardadas", r["rep"].nunique())
    else:
        r = pd.DataFrame()
        rr["firma"].write_text(json.dumps(dict(firma=firma, n=n)))
    traza = [] if r.empty or not rr["convergencia"].exists() else [pd.read_csv(rr["convergencia"])]

    while True:
        hechas = 0 if r.empty else r["rep"].nunique()
        reps_bosque = 0 if r.empty else r.loc[r["estimador"] == "causal_forest", "rep"].nunique()
        res = resumir(r) if not r.empty else None
        falta = hechas < MIN_REPS or len(pendientes(res, bosque=False)) > 0
        falta_bosque = reps_bosque < MIN_REPS_BOSQUE or (res is not None and len(pendientes(res, bosque=True)) > 0)
        falta_bosque = falta_bosque and reps_bosque < MAX_REPS_BOSQUE
        if (not falta and not falta_bosque) or hechas >= max_reps:
            break
        lote = list(range(hechas, hechas + LOTE))
        con_bosque = falta_bosque
        t0 = time.time()
        with parallel_config(backend="loky", inner_max_num_threads=1):
            partes = Parallel(n_jobs=n_jobs)(delayed(una_repeticion)(b, rep, n, con_bosque) for rep in lote)
        nuevas = pd.DataFrame([f for p in partes for f in p])
        r = pd.concat([r, nuevas], ignore_index=True)
        reportes.marcar_simulado(r).to_csv(rr["out"], index=False)
        res = resumir(r)
        traza.append(res.assign(reps_total=r["rep"].nunique()))
        reportes.marcar_simulado(pd.concat(traza, ignore_index=True)).to_csv(rr["convergencia"], index=False)
        p, pb = pendientes(res, False), pendientes(res, True)
        logger.info("Lote reps %d-%d%s en %.0f s | celdas sin converger: %d (+ %d de Causal Forest) | "
                    "MCSE sesgo máx %.4f, cobertura máx %.3f",
                    lote[0], lote[-1], " con Causal Forest" if con_bosque else "", time.time() - t0, len(p), len(pb),
                    res["mcse_sesgo"].max(), res["mcse_cobertura"].max())

    res = resumir(r)
    reportes.marcar_simulado(res).to_csv(rr["resumen"], index=False)
    reportes.graficar_convergencia(pd.read_csv(rr["convergencia"]), rr["figura"])
    reportes.tablas_markdown(res, rr["tablas"])
    conv = len(pendientes(res, False)) == 0 and len(pendientes(res, True)) == 0

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print(f"\n{reportes.NOTA_SIMULADO}")
    print(f"\n=== Simulación semisintética*: {r['rep'].nunique()} repeticiones "
          f"(Causal Forest en {r.loc[r['estimador'] == 'causal_forest', 'rep'].nunique()}), "
          f"encuesta de {n:,} hogares{' reales' if base is None else ''} ===")
    print(f"Convergencia (MCSE sesgo ≤ {UMBRAL_SESGO}, cobertura ≤ {UMBRAL_COBERTURA}): "
          f"{'alcanzada en todas las celdas' if conv else 'NO alcanzada en todas (ver pendientes abajo)'}")
    cols = ["vinculo", "estimador", "reps", "efecto_verdadero", "estimacion", "sesgo", "mcse_sesgo", "rmse",
            "cobertura", "mcse_cobertura", "ancho_ic", "pehe", "concordancia_t", "degradacion_rmse"]
    for (esc, out), g in res.groupby(["escenario", "outcome"], sort=False):
        print(f"\n--- Escenario: {esc} | outcome: {out}")
        print(g[cols].round(4).to_string(index=False))
    if not conv:
        print("\nCeldas sin converger:")
        print(pd.concat([pendientes(res, False), pendientes(res, True)])[CELDA + ["reps", "mcse_sesgo",
                                                                                 "mcse_cobertura"]].to_string(index=False))
    print("\n" + "\n".join(f"Guardado: {rr[k]}" for k in ("out", "resumen", "convergencia", "figura", "tablas")))
    return res
