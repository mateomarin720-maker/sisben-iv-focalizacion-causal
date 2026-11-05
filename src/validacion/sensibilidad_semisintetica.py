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

Solo log-ingreso y estimadores rápidos (regresión con efectos fijos,
LinearDML en sus dos versiones, RD). Repeticiones hasta que el error
estándar Monte Carlo del sesgo queda bajo 0,003 en cada celda (0,008 en
la RD, ver `UMBRAL_MCSE`).

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.sensibilidad_semisintetica [n_jobs]
Salidas:
    docs/reports/sensibilidad_semisintetica.csv (cada repetición)
    docs/reports/sensibilidad_semisintetica_resumen.csv
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline

from src.simulacion import contrato
from src.simulacion.asignacion import asignar
from src.simulacion.base import celdas_por_nivel, diseno_x, preparar_base
from src.simulacion.escenarios import ESCENARIOS as ESCENARIOS_BASE
from src.simulacion.escenarios import H_RD, N_ENCUESTA, TAU, VINCULOS
from src.simulacion.estimadores import (discontinuidad, discontinuidad_difusa, estimacion5, pesos_rd,
                                        regresion_efectos_fijos)
from src.simulacion.evaluacion import HOGARES, REGISTRO, p_t_por_celda
from src.simulacion.vinculo import sortear_donante

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT = Path("docs/reports/sensibilidad_semisintetica.csv")
OUT_RESUMEN = Path("docs/reports/sensibilidad_semisintetica_resumen.csv")
OUT_FIRMA = Path("docs/reports/sensibilidad_semisintetica_config.json")
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


def _modelos_poco_regularizados():
    """Los mismos codificadores de `5_estimacion.py`, casi sin
    regularización: Ridge alpha=1e-6 y logística C=1e6."""
    est5 = estimacion5()
    w_cat, w_num = est5.W_CELDA
    columnas = est5.X_COLS + w_cat + w_num
    categoricas = est5.X_CATEGORICAS + w_cat
    modelo_y = make_pipeline(est5._codificador(columnas, categoricas, w_num), Ridge(alpha=1e-6))
    modelo_t = make_pipeline(est5._codificador(columnas, categoricas, w_num),
                             LogisticRegression(C=1e6, max_iter=5000))
    return modelo_y, modelo_t


def linear_dml(d: pd.DataFrame, y: np.ndarray, t: np.ndarray, regularizado: bool) -> tuple[float, float, float]:
    from econml.dml import LinearDML

    est5 = estimacion5()
    modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA) if regularizado else _modelos_poco_regularizados()
    m = LinearDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, random_state=SEED)
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


def main(n_jobs: int = 3, n: int = N_ENCUESTA) -> pd.DataFrame:
    from joblib import Parallel, delayed, parallel_config

    p_t = p_t_por_celda(pd.read_parquet(REGISTRO, columns=contrato.columnas("registro")))
    b = preparar_base(pd.read_parquet(HOGARES, columns=contrato.columnas("hogares")), p_t)

    r = pd.read_csv(OUT) if (OUT.exists() and OUT_FIRMA.exists()
                             and json.loads(OUT_FIRMA.read_text()).get("firma") == _firma(n)) else pd.DataFrame()
    if r.empty:
        OUT_FIRMA.write_text(json.dumps(dict(firma=_firma(n))))
    while True:
        hechas = 0 if r.empty else r["rep"].nunique()
        pend = 0 if r.empty else len(sin_converger(resumir(r)))
        if hechas >= MAX_REPS or (hechas >= MIN_REPS and pend == 0):
            break
        t0 = time.time()
        with parallel_config(backend="loky", inner_max_num_threads=1):
            partes = Parallel(n_jobs=n_jobs)(delayed(una_repeticion)(b, rep, n) for rep in range(hechas, hechas + LOTE))
        r = pd.concat([r, pd.DataFrame([f for p in partes for f in p])], ignore_index=True)
        r.to_csv(OUT, index=False)
        logger.info("Lote reps %d-%d en %.0f s | celdas sin converger: %d", hechas, hechas + LOTE - 1, time.time() - t0,
                    len(sin_converger(resumir(r))))

    res = resumir(r)
    res.to_csv(OUT_RESUMEN, index=False)
    pd.set_option("display.width", 220)
    print(f"\n=== Sensibilidad semisintética: {r['rep'].nunique()} repeticiones, {n:,} hogares reales ===")
    for esc, g in res.groupby("escenario", sort=False):
        print(f"\n--- {esc}")
        print(g.drop(columns="escenario").round(4).to_string(index=False))
    pend = sin_converger(res)
    print(f"\nConvergencia (MCSE del sesgo ≤ {UMBRAL_MCSE_DEFECTO}; RD ≤ {UMBRAL_MCSE['discontinuidad_rd']}): "
          f"{'alcanzada' if pend.empty else f'NO en {len(pend)} celdas'}")
    print(f"Guardado: {OUT}\nGuardado: {OUT_RESUMEN}")
    return res


if __name__ == "__main__":
    main(*[int(a) for a in sys.argv[1:]])
