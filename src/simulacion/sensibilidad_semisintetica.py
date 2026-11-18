"""Sensibilidad de la evaluación semisintética (complemento de
`src/simulacion/`, mismo generador y mismos hogares reales).

Tres preguntas que dejó abierta la corrida principal:

1. **Tamaño del efecto.** ¿La pérdida por integración (Hot-Deck ≈ 0,
   vínculo del 50 % ≈ la mitad) es proporcional al efecto, o depende de su
   tamaño? Se multiplica tau(X) por 0,5, 1 y 2.
2. **Regla de corte difusa.** En la principal, todo elegible participa
   (RD nítida). Aquí participa el 80 % de los elegibles y el 20 % de los no
   elegibles, y el efecto en el corte se estima con RD difusa (salto en Y /
   salto en la participación, por mínimos cuadrados en dos etapas local).
3. **El sesgo pequeño de LinearDML** (−0,004 a −0,008 en la principal,
   también con efecto nulo). Hipótesis: la regularización de los modelos
   auxiliares (Ridge alpha=1 y logística C=10 sobre 993 indicadoras de
   celda) encoge los efectos de celda y deja confusión entre celdas. Se
   compara con LinearDML casi sin regularizar (alpha=1e-6, C=1e6).
4. **Tamaño de la encuesta simulada** (2026-11-15). Con la celda de 3.721
   valores, 30.000 hogares dejan ≈8 por celda y LinearDML se sesga
   (−0,036 con efecto nulo). ¿Cuánto se debe al tamaño? Regresión con
   efectos fijos y LinearDML en sus dos versiones, con efecto nulo y con
   confusión observada, oráculo y Hot-Deck, en encuestas de 30.000,
   60.000 y 120.000 hogares (`TAMANOS`).
5. **Imputación fraccional y vínculo parcial** (2026-11-18). Con vínculo
   parcial, ¿la recta L·τ de la Proposición 2 es del sorteo del Hot-Deck o
   de cualquier imputación por celda? A una fracción L de los hogares se
   le da su T verdadero y al resto se le imputa: (a) el T de un donante
   sorteado en su celda (Hot-Deck) o (b) la proporción de T = 1 entre los
   donantes de su celda (FHDI con pesos calibrados = FEFI). L de 0 a 1 en
   pasos de 0,25, los mismos hogares vinculados en las dos imputaciones.
   Con (b) y L = 0 no queda variación dentro de la celda: no
   identificable (vacío, no 0). Metodología:
   `docs/metodologia/METODOLOGIA_FHDI.md`.
6. **Por qué LinearDML se sesga con imputación fraccional** (diagnóstico
   de la pregunta 5). Con FHDI y L = 0,25, LinearDML da −0,161 con
   efecto nulo (−0,036 con Hot-Deck). Hipótesis: la parte imputada solo
   varía entre celdas y la regularización de los modelos auxiliares no
   quita los efectos de celda con ≈8 hogares por celda. Se repite con
   LinearDML casi sin regularizar y con encuestas de 30.000, 60.000 y
   120.000 hogares. Repeticiones fijas (`REPS_DIAGNOSTICO`): basta
   distinguir sesgos de −0,16 y −0,03.

Solo log-ingreso y estimadores rápidos (regresión con efectos fijos,
LinearDML en sus dos versiones, RD). Repeticiones hasta que el error
estándar Monte Carlo del sesgo queda bajo 0,003 en cada celda (0,008 en
la RD, ver `UMBRAL_MCSE`).

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.simulacion.sensibilidad_semisintetica [n_jobs]
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.simulacion.sensibilidad_semisintetica tamano [n_jobs]
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.simulacion.sensibilidad_semisintetica vinculo [n_jobs]
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.simulacion.sensibilidad_semisintetica vinculo_diagnostico [n_jobs]
Salidas:
    docs/reports/sensibilidad_semisintetica.csv (cada repetición)
    docs/reports/sensibilidad_semisintetica_resumen.csv
    docs/reports/sensibilidad_tamano_muestra{.csv,_resumen.csv} (pregunta 4)
    docs/reports/sensibilidad_vinculo_fhdi{.csv,_resumen.csv} (pregunta 5)
    docs/reports/sensibilidad_vinculo_fhdi_diagnostico{.csv,_resumen.csv} (pregunta 6)
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

from src.simulacion import contrato
from src.simulacion.asignacion import asignar
from src.simulacion.base import celdas_por_nivel, diseno_x, firma_con_datos, preparar_base
from src.simulacion.escenarios import ESCENARIOS as ESCENARIOS_BASE
from src.simulacion.escenarios import H_RD, N_ENCUESTA, TAU, VINCULOS
from src.simulacion.estimadores import (discontinuidad, discontinuidad_difusa, estimacion5, identificable,
                                        pesos_rd, regresion_efectos_fijos)
from src.simulacion.evaluacion import HOGARES, REGISTRO, p_t_por_celda
from src.simulacion.reportes import NOTA_SIMULADO, marcar_simulado, sin_marca
from src.simulacion.vinculo import probabilidad_celda, sortear_donante

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT = Path("docs/reports/sensibilidad_semisintetica.csv")
OUT_RESUMEN = Path("docs/reports/sensibilidad_semisintetica_resumen.csv")
OUT_FIRMA = Path("docs/reports/sensibilidad_semisintetica_config.json")
OUT_TAMANO = Path("docs/reports/sensibilidad_tamano_muestra.csv")
OUT_TAMANO_RESUMEN = Path("docs/reports/sensibilidad_tamano_muestra_resumen.csv")
OUT_TAMANO_FIRMA = Path("docs/reports/sensibilidad_tamano_muestra_config.json")
TAMANOS = (30_000, 60_000, 120_000)  # hogares de la encuesta simulada (pregunta 4)
ESCENARIOS_TAMANO = ("efecto_nulo", "confusion_observada_x1.0")
VINCULOS_TAMANO = ("oraculo", "hotdeck")
OUT_VINCULO = Path("docs/reports/sensibilidad_vinculo_fhdi.csv")
OUT_VINCULO_RESUMEN = Path("docs/reports/sensibilidad_vinculo_fhdi_resumen.csv")
OUT_VINCULO_FIRMA = Path("docs/reports/sensibilidad_vinculo_fhdi_config.json")
FRACCIONES_VINCULO = (0.0, 0.25, 0.5, 0.75, 1.0)  # L: fracción de hogares con su T verdadero (pregunta 5)
ESCENARIOS_VINCULO = ("efecto_nulo", "confusion_observada_x1.0")
IMPUTACIONES = ("hotdeck", "fhdi")
OUT_DIAG = Path("docs/reports/sensibilidad_vinculo_fhdi_diagnostico.csv")
OUT_DIAG_RESUMEN = Path("docs/reports/sensibilidad_vinculo_fhdi_diagnostico_resumen.csv")
OUT_DIAG_FIRMA = Path("docs/reports/sensibilidad_vinculo_fhdi_diagnostico_config.json")
FRACCIONES_DIAGNOSTICO = (0.25, 0.5, 0.75)
REPS_DIAGNOSTICO = 96  # MCSE ≈ 0,005: basta para distinguir −0,16 de −0,03
SEED = 2028
# MCSE máximo del sesgo. La RD usa solo los hogares cerca del corte y la
# difusa divide por el salto en la participación: con 0,003 necesitarían
# más de 1.000 repeticiones; 0,008 (≈9 % del efecto) basta para saber si
# recupera el efecto en el corte.
UMBRAL_MCSE = {"discontinuidad_rd": 0.008}
UMBRAL_MCSE_DEFECTO = 0.003
MIN_REPS, MAX_REPS, LOTE = 60, 400, 12
PARTICIPACION = (0.2, 0.8)  # P(participa | no elegible), P(participa | elegible)

_obs = ESCENARIOS_BASE["confusion_observada"]
_corte = ESCENARIOS_BASE["regla_corte"]
ESCENARIOS = {
    "efecto_nulo": dict(_obs, factor_tau=0.0),
    **{f"confusion_observada_x{f}": dict(_obs, factor_tau=f) for f in (0.5, 1.0, 2.0)},
    **{f"regla_corte_x{f}": dict(_corte, factor_tau=f) for f in (0.5, 1.0, 2.0)},
    "regla_corte_difusa": dict(_corte, difusa=True),
}


def linear_dml(d: pd.DataFrame, y: np.ndarray, t: np.ndarray, regularizado: bool) -> tuple[float, float, float]:
    from econml.dml import LinearDML

    est5 = estimacion5()
    # `regularizado`: la del proyecto (alpha 1, C 10); si no, casi nula.
    extra = {} if regularizado else est5.CASI_SIN_REGULARIZAR
    modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA, **extra)
    # Con la imputación fraccional T no es 0/1 (probabilidad de la celda en
    # los no vinculados): tratamiento continuo y, para T, el mismo modelo
    # de regresión que para Y.
    discreto = bool(np.isin(t, (0, 1)).all())
    if not discreto:
        from sklearn.base import clone
        modelo_t = clone(modelo_y)
    m = LinearDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=discreto, random_state=SEED)
    X = d[est5.X_COLS].to_numpy(float)
    m.fit(y, t, X=X, W=d[est5.W_CELDA[0]].to_numpy(float))
    lo, hi = m.ate_interval(X, alpha=0.05)
    return float(m.ate(X)), float(lo), float(hi)


def una_repeticion(b: pd.DataFrame, rep: int, n: int = N_ENCUESTA) -> list[dict]:
    filas = []
    for i_esc, (nombre, esc) in enumerate(ESCENARIOS.items()):
        rng = np.random.default_rng([SEED, rep, i_esc])
        elegible, puntaje, corte = asignar(b, esc, rng)
        t_real = ((rng.random(len(b)) < np.where(elegible == 1, PARTICIPACION[1], PARTICIPACION[0])).astype(int)
                  if esc.get("difusa") else elegible)
        idx = rng.permutation(len(b))
        enc, reg = idx[:n], idx[n:]
        d = b.iloc[enc].reset_index(drop=True)
        celda = d["hotdeck_celda_cat"].to_numpy()
        tau = esc.get("factor_tau", 1.0) * d["tau"].to_numpy()
        y = d["y0"].to_numpy() + tau * t_real[enc]
        niveles = celdas_por_nivel(b)
        donante = reg[sortear_donante(niveles[enc], niveles[reg], rng)]
        Z = diseno_x(d)
        h = H_RD * float(np.std(puntaje))
        w_rd = pesos_rd(puntaje[enc], corte, h) if esc.get("corte") else None
        for vinculo, frac in VINCULOS.items():
            usa = rng.random(n) < frac
            t_obs = np.where(usa, t_real[donante], t_real[enc])
            p_obs = np.where(usa, puntaje[donante], puntaje[enc])
            res = {"regresion_efectos_fijos": regresion_efectos_fijos(y, t_obs, Z, celda)}
            if esc.get("corte") is None or esc.get("factor_tau", 1.0) == 1.0 or esc.get("difusa"):
                res["linear_dml"] = linear_dml(d, y, t_obs, regularizado=True)
                res["linear_dml_sin_regularizar"] = linear_dml(d, y, t_obs, regularizado=False)
            verdades = {k: float(tau.mean()) for k in res}
            if w_rd is not None:
                res["discontinuidad_rd"] = (discontinuidad_difusa(y, t_obs, p_obs, corte, h) if esc.get("difusa")
                                            else discontinuidad(y, p_obs, corte, h))
                verdades["discontinuidad_rd"] = float(np.average(tau, weights=w_rd))
            for est, (a, lo, hi) in res.items():
                filas.append(dict(rep=rep, escenario=nombre, vinculo=vinculo, estimador=est,
                                  efecto_verdadero=verdades[est], estimacion=a, ic_lo=lo, ic_hi=hi))
    return filas


def una_repeticion_tamano(b: pd.DataFrame, rep: int, tamanos: tuple[int, ...] = TAMANOS) -> list[dict]:
    """Pregunta 4: los mismos estimadores de la celda con encuestas de
    distinto tamaño. Cada tamaño sortea su propia encuesta; el registro es
    el resto de los hogares, como en la corrida principal."""
    filas = []
    niveles = celdas_por_nivel(b)
    n_celdas = b["hotdeck_celda_cat"].nunique()
    for n in tamanos:
        for i_esc, nombre in enumerate(ESCENARIOS_TAMANO):
            esc = ESCENARIOS[nombre]
            rng = np.random.default_rng([SEED, rep, i_esc, n])
            t_real, _, _ = asignar(b, esc, rng)
            idx = rng.permutation(len(b))
            enc, reg = idx[:n], idx[n:]
            d = b.iloc[enc].reset_index(drop=True)
            celda = d["hotdeck_celda_cat"].to_numpy()
            tau = esc.get("factor_tau", 1.0) * d["tau"].to_numpy()
            y = d["y0"].to_numpy() + tau * t_real[enc]
            donante = reg[sortear_donante(niveles[enc], niveles[reg], rng)]
            Z = diseno_x(d)
            for vinculo in VINCULOS_TAMANO:
                t_obs = t_real[donante] if VINCULOS[vinculo] == 1.0 else t_real[enc]
                res = {"regresion_efectos_fijos": regresion_efectos_fijos(y, t_obs, Z, celda),
                       "linear_dml": linear_dml(d, y, t_obs, regularizado=True),
                       "linear_dml_sin_regularizar": linear_dml(d, y, t_obs, regularizado=False)}
                for est, (a, lo, hi) in res.items():
                    filas.append(dict(rep=rep, escenario=f"{nombre}_n{n}", vinculo=vinculo, estimador=est,
                                      efecto_verdadero=float(tau.mean()), estimacion=a, ic_lo=lo, ic_hi=hi,
                                      hogares=n, hogares_por_celda=n / n_celdas))
    return filas


def t_observado(t_hogar: np.ndarray, t_donante: np.ndarray, p_celda: np.ndarray, vinculado: np.ndarray,
                imputacion: str) -> np.ndarray:
    """T que ve el estimador: el verdadero en los hogares vinculados y, en
    el resto, el del donante sorteado (Hot-Deck) o la proporción de T = 1
    de la celda (FHDI)."""
    imputado = {"hotdeck": t_donante, "fhdi": p_celda}[imputacion]
    return np.where(vinculado, t_hogar, imputado).astype(float)


def una_repeticion_vinculo(b: pd.DataFrame, rep: int, n: int = N_ENCUESTA) -> list[dict]:
    """Pregunta 5: recta de atenuación con las dos imputaciones."""
    filas = []
    niveles = celdas_por_nivel(b)
    for i_esc, nombre in enumerate(ESCENARIOS_VINCULO):
        esc = ESCENARIOS[nombre]
        rng = np.random.default_rng([SEED, rep, i_esc, 5])
        t_real, _, _ = asignar(b, esc, rng)
        idx = rng.permutation(len(b))
        enc, reg = idx[:n], idx[n:]
        d = b.iloc[enc].reset_index(drop=True)
        celda = d["hotdeck_celda_cat"].to_numpy()
        tau = esc.get("factor_tau", 1.0) * d["tau"].to_numpy()
        y = d["y0"].to_numpy() + tau * t_real[enc]
        donante = reg[sortear_donante(niveles[enc], niveles[reg], rng)]
        p = probabilidad_celda(niveles[enc], niveles[reg], t_real[reg])
        Z = diseno_x(d)
        u = rng.random(n)  # los mismos hogares vinculados en las dos imputaciones
        for L in FRACCIONES_VINCULO:
            vinculado = u < L
            for imputacion in IMPUTACIONES:
                t_obs = t_observado(t_real[enc], t_real[donante], p, vinculado, imputacion)
                ok = identificable(t_obs, celda)
                if ok:
                    res = {"regresion_efectos_fijos": regresion_efectos_fijos(y, t_obs, Z, celda),
                           "linear_dml": linear_dml(d, y, t_obs, regularizado=True)}
                else:
                    res = {e: (np.nan, np.nan, np.nan) for e in ("regresion_efectos_fijos", "linear_dml")}
                for est, (a, lo, hi) in res.items():
                    filas.append(dict(rep=rep, escenario=nombre, vinculo=f"{imputacion}_L{L:.2f}", estimador=est,
                                      efecto_verdadero=float(tau.mean()), estimacion=a, ic_lo=lo, ic_hi=hi,
                                      imputacion=imputacion, fraccion_vinculada=L, identificable=ok))
    return filas


def una_repeticion_vinculo_diagnostico(b: pd.DataFrame, rep: int, tamanos: tuple[int, ...] = TAMANOS,
                                       fracciones: tuple[float, ...] = FRACCIONES_DIAGNOSTICO) -> list[dict]:
    """Pregunta 6: la pregunta 5 con LinearDML en sus dos versiones y
    encuestas de distinto tamaño."""
    filas = []
    niveles = celdas_por_nivel(b)
    n_celdas = b["hotdeck_celda_cat"].nunique()
    for n in tamanos:
        for i_esc, nombre in enumerate(ESCENARIOS_VINCULO):
            esc = ESCENARIOS[nombre]
            rng = np.random.default_rng([SEED, rep, i_esc, n, 6])
            t_real, _, _ = asignar(b, esc, rng)
            idx = rng.permutation(len(b))
            enc, reg = idx[:n], idx[n:]
            d = b.iloc[enc].reset_index(drop=True)
            celda = d["hotdeck_celda_cat"].to_numpy()
            tau = esc.get("factor_tau", 1.0) * d["tau"].to_numpy()
            y = d["y0"].to_numpy() + tau * t_real[enc]
            donante = reg[sortear_donante(niveles[enc], niveles[reg], rng)]
            p = probabilidad_celda(niveles[enc], niveles[reg], t_real[reg])
            Z = diseno_x(d)
            u = rng.random(n)
            for L in fracciones:
                for imputacion in IMPUTACIONES:
                    t_obs = t_observado(t_real[enc], t_real[donante], p, u < L, imputacion)
                    res = {"regresion_efectos_fijos": regresion_efectos_fijos(y, t_obs, Z, celda),
                           "linear_dml": linear_dml(d, y, t_obs, regularizado=True),
                           "linear_dml_sin_regularizar": linear_dml(d, y, t_obs, regularizado=False)}
                    for est, (a, lo, hi) in res.items():
                        filas.append(dict(rep=rep, escenario=f"{nombre}_n{n}", vinculo=f"{imputacion}_L{L:.2f}",
                                          estimador=est, efecto_verdadero=float(tau.mean()), estimacion=a,
                                          ic_lo=lo, ic_hi=hi, imputacion=imputacion, fraccion_vinculada=L,
                                          hogares=n, hogares_por_celda=n / n_celdas))
    return filas


def resumir(r: pd.DataFrame) -> pd.DataFrame:
    r = r.assign(error=r["estimacion"] - r["efecto_verdadero"],
                 cubre=((r["ic_lo"] <= r["efecto_verdadero"]) & (r["efecto_verdadero"] <= r["ic_hi"])).astype(float))
    g = r.groupby(["escenario", "vinculo", "estimador"], sort=False)
    out = g.agg(reps=("rep", "size"), efecto_verdadero=("efecto_verdadero", "mean"),
                estimacion=("estimacion", "mean"), sesgo=("error", "mean"), sd=("error", "std"),
                cobertura=("cubre", "mean")).reset_index()
    out["mcse_sesgo"] = out["sd"] / np.sqrt(out["reps"])
    out["z_sesgo"] = out["sesgo"] / out["mcse_sesgo"]
    out["fraccion_recuperada"] = out["estimacion"] / out["efecto_verdadero"].where(out["efecto_verdadero"] != 0)
    out["umbral"] = out["estimador"].map(UMBRAL_MCSE).fillna(UMBRAL_MCSE_DEFECTO)
    return out.drop(columns="sd")


def sin_converger(res: pd.DataFrame) -> pd.DataFrame:
    return res[res["mcse_sesgo"] > res["umbral"]]


def _firma(n: int) -> str:
    # Versión 2: el Hot-Deck simulado usa la cadena de respaldos del pipeline.
    cfg = dict(ESCENARIOS=ESCENARIOS, PARTICIPACION=PARTICIPACION, SEED=SEED, n=n, TAU=TAU, version=2)
    return hashlib.sha1(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _base() -> pd.DataFrame:
    p_t = p_t_por_celda(pd.read_parquet(REGISTRO, columns=contrato.columnas("registro")))
    return preparar_base(pd.read_parquet(HOGARES, columns=contrato.columnas("hogares")), p_t)


def _correr(b: pd.DataFrame, una, out: Path, out_firma: Path, firma: str, n_jobs: int,
            min_reps: int | None = None, max_reps: int | None = None) -> pd.DataFrame:
    """Lotes en paralelo hasta la convergencia (o hasta `max_reps`); reanuda
    lo guardado si la firma (configuración y datos) coincide."""
    min_reps = MIN_REPS if min_reps is None else min_reps
    max_reps = MAX_REPS if max_reps is None else max_reps
    from joblib import Parallel, delayed, parallel_config

    r = sin_marca(pd.read_csv(out)) if (out.exists() and out_firma.exists()
                             and json.loads(out_firma.read_text()).get("firma") == firma) else pd.DataFrame()
    if r.empty:
        out_firma.write_text(json.dumps(dict(firma=firma)))
    else:
        logger.info("Reanudando: %d repeticiones ya guardadas", r["rep"].nunique())
    while True:
        hechas = 0 if r.empty else r["rep"].nunique()
        pend = 0 if r.empty else len(sin_converger(resumir(r)))
        if hechas >= max_reps or (hechas >= min_reps and pend == 0):
            break
        t0 = time.time()
        with parallel_config(backend="loky", inner_max_num_threads=1):
            partes = Parallel(n_jobs=n_jobs)(delayed(una)(b, rep) for rep in range(hechas, hechas + LOTE))
        r = pd.concat([r, pd.DataFrame([f for p in partes for f in p])], ignore_index=True)
        marcar_simulado(r).to_csv(out, index=False)
        logger.info("Lote reps %d-%d en %.0f s | celdas sin converger: %d", hechas, hechas + LOTE - 1, time.time() - t0,
                    len(sin_converger(resumir(r))))
    return r


def main(n_jobs: int = 3, n: int = N_ENCUESTA) -> pd.DataFrame:
    b = _base()
    firma = firma_con_datos(_firma(n), b)  # reanuda solo con los mismos datos
    r = _correr(b, partial(una_repeticion, n=n), OUT, OUT_FIRMA, firma, n_jobs)

    res = resumir(r)
    marcar_simulado(res).to_csv(OUT_RESUMEN, index=False)
    pd.set_option("display.width", 220)
    print(f"\n{NOTA_SIMULADO}")
    print(f"\n=== Sensibilidad semisintética*: {r['rep'].nunique()} repeticiones, {n:,} hogares reales ===")
    for esc, g in res.groupby("escenario", sort=False):
        print(f"\n--- {esc}")
        print(g.drop(columns="escenario").round(4).to_string(index=False))
    pend = sin_converger(res)
    print(f"\nConvergencia (MCSE del sesgo ≤ {UMBRAL_MCSE_DEFECTO}; RD ≤ {UMBRAL_MCSE['discontinuidad_rd']}): "
          f"{'alcanzada' if pend.empty else f'NO en {len(pend)} celdas'}")
    print(f"Guardado: {OUT}\nGuardado: {OUT_RESUMEN}")
    return res


def main_tamano(n_jobs: int = 3) -> pd.DataFrame:
    """Pregunta 4: sesgo de los estimadores de la celda según el tamaño de
    la encuesta simulada."""
    b = _base()
    cfg = dict(ESCENARIOS={k: ESCENARIOS[k] for k in ESCENARIOS_TAMANO}, VINCULOS=VINCULOS_TAMANO, TAMANOS=TAMANOS,
               SEED=SEED, TAU=TAU, version=1)
    firma = firma_con_datos(hashlib.sha1(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12], b)
    r = _correr(b, partial(una_repeticion_tamano, tamanos=TAMANOS), OUT_TAMANO, OUT_TAMANO_FIRMA, firma, n_jobs)

    res = resumir(r)
    res = res.merge(r.groupby("escenario")[["hogares", "hogares_por_celda"]].first().reset_index(), on="escenario")
    marcar_simulado(res).to_csv(OUT_TAMANO_RESUMEN, index=False)
    pd.set_option("display.width", 220)
    print(f"\n{NOTA_SIMULADO}")
    print(f"\n=== Tamaño de la encuesta simulada*: {r['rep'].nunique()} repeticiones, "
          f"{b['hotdeck_celda_cat'].nunique():,} celdas ===")
    for esc, g in res.groupby("escenario", sort=False):
        print(f"\n--- {esc} ({int(g['hogares'].iloc[0]):,} hogares, {g['hogares_por_celda'].iloc[0]:.1f} por celda)")
        print(g.drop(columns=["escenario", "hogares", "hogares_por_celda"]).round(4).to_string(index=False))
    pend = sin_converger(res)
    print(f"\nConvergencia (MCSE del sesgo ≤ {UMBRAL_MCSE_DEFECTO}): "
          f"{'alcanzada' if pend.empty else f'NO en {len(pend)} celdas'}")
    print(f"Guardado: {OUT_TAMANO}\nGuardado: {OUT_TAMANO_RESUMEN}")
    return res


def main_vinculo(n_jobs: int = 3) -> pd.DataFrame:
    """Pregunta 5: recta de atenuación con Hot-Deck y con imputación
    fraccional en los hogares sin vínculo."""
    b = _base()
    cfg = dict(ESCENARIOS={k: ESCENARIOS[k] for k in ESCENARIOS_VINCULO}, FRACCIONES=FRACCIONES_VINCULO,
               IMPUTACIONES=IMPUTACIONES, SEED=SEED, TAU=TAU, n=N_ENCUESTA, version=1)
    firma = firma_con_datos(hashlib.sha1(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12], b)
    r = _correr(b, una_repeticion_vinculo, OUT_VINCULO, OUT_VINCULO_FIRMA, firma, n_jobs)

    res = resumir(r)
    extra = r.groupby(["escenario", "vinculo", "estimador"]).agg(
        imputacion=("imputacion", "first"), fraccion_vinculada=("fraccion_vinculada", "first"),
        pct_identificable=("identificable", lambda v: float(np.mean(v) * 100))).reset_index()
    res = res.merge(extra, on=["escenario", "vinculo", "estimador"])
    res["L_por_tau"] = res["fraccion_vinculada"] * res["efecto_verdadero"]
    marcar_simulado(res).to_csv(OUT_VINCULO_RESUMEN, index=False)
    pd.set_option("display.width", 220)
    print(f"\n{NOTA_SIMULADO}")
    print(f"\n=== Vínculo parcial con Hot-Deck o imputación fraccional*: {r['rep'].nunique()} repeticiones, "
          f"{N_ENCUESTA:,} hogares por encuesta ===")
    cols = ["imputacion", "fraccion_vinculada", "estimador", "reps", "pct_identificable", "efecto_verdadero",
            "L_por_tau", "estimacion", "sesgo", "mcse_sesgo", "cobertura", "fraccion_recuperada"]
    for esc, g in res.groupby("escenario", sort=False):
        print(f"\n--- {esc}")
        print(g.sort_values(["estimador", "imputacion", "fraccion_vinculada"])[cols].round(4).to_string(index=False))
    pend = sin_converger(res)
    print(f"\nConvergencia (MCSE del sesgo ≤ {UMBRAL_MCSE_DEFECTO}): "
          f"{'alcanzada' if pend.empty else f'NO en {len(pend)} celdas'}")
    print(f"Guardado: {OUT_VINCULO}\nGuardado: {OUT_VINCULO_RESUMEN}")
    return res


def main_vinculo_diagnostico(n_jobs: int = 3) -> pd.DataFrame:
    """Pregunta 6: ¿el sesgo de LinearDML con imputación fraccional es de
    la regularización, del tamaño de las celdas o de los dos?"""
    b = _base()
    cfg = dict(ESCENARIOS={k: ESCENARIOS[k] for k in ESCENARIOS_VINCULO}, FRACCIONES=FRACCIONES_DIAGNOSTICO,
               IMPUTACIONES=IMPUTACIONES, TAMANOS=TAMANOS, SEED=SEED, TAU=TAU, version=1)
    firma = firma_con_datos(hashlib.sha1(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12], b)
    r = _correr(b, una_repeticion_vinculo_diagnostico, OUT_DIAG, OUT_DIAG_FIRMA, firma, n_jobs,
                min_reps=REPS_DIAGNOSTICO, max_reps=REPS_DIAGNOSTICO)

    res = resumir(r)
    extra = r.groupby(["escenario", "vinculo", "estimador"]).agg(
        imputacion=("imputacion", "first"), fraccion_vinculada=("fraccion_vinculada", "first"),
        hogares=("hogares", "first"), hogares_por_celda=("hogares_por_celda", "first")).reset_index()
    res = res.merge(extra, on=["escenario", "vinculo", "estimador"])
    marcar_simulado(res).to_csv(OUT_DIAG_RESUMEN, index=False)
    pd.set_option("display.width", 220)
    print(f"\n{NOTA_SIMULADO}")
    print(f"\n=== Diagnóstico de LinearDML con imputación fraccional*: {r['rep'].nunique()} repeticiones ===")
    tabla = res.pivot_table(index=["escenario", "imputacion", "fraccion_vinculada"], columns="estimador",
                            values="sesgo").round(4)
    print("\nSesgo (estimación − efecto verdadero):")
    print(tabla.to_string())
    print(f"\nMCSE del sesgo: máximo {res['mcse_sesgo'].max():.4f}")
    print(f"Guardado: {OUT_DIAG}\nGuardado: {OUT_DIAG_RESUMEN}")
    return res


if __name__ == "__main__":
    if sys.argv[1:2] == ["tamano"]:
        main_tamano(*[int(a) for a in sys.argv[2:]])
    elif sys.argv[1:2] == ["vinculo"]:
        main_vinculo(*[int(a) for a in sys.argv[2:]])
    elif sys.argv[1:2] == ["vinculo_diagnostico"]:
        main_vinculo_diagnostico(*[int(a) for a in sys.argv[2:]])
    else:
        main(*[int(a) for a in sys.argv[1:]])
