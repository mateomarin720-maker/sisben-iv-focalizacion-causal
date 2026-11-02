"""Simulación semisintética: ¿qué estimador recupera un efecto conocido
sobre hogares reales, y cuánto se pierde al integrar las fuentes por
Hot-Deck?

A diferencia de `simulacion_identificacion.py` (mundo 100 % sintético),
aquí las covariables y el resultado sin tratamiento son los de los
hogares reales de GEIH 2024 (`muestra_estimacion_monetaria_2024.parquet`).
Solo se simulan el tratamiento y el efecto, así que el efecto verdadero
se conoce hogar por hogar.

Arquitectura:

    DATOS REALES        celda del Hot-Deck, X = {zona, sexo del jefe,
                        paredes}, Y0 = log(1 + ingreso per cápita UG)
    GENERADOR           U = parte del ingreso que la celda y X no explican
                        (no observable); T verdadero ~ Bernoulli(score),
                        score = logit P_Sisbén(T | celda) + X·b + gamma·U;
                        tau(X) conocido; Y = Y0 + tau(X)·T
    ESCENARIOS          asignación aleatoria / confusión observada /
                        confusión no observada (leve, gamma=0,25, y
                        fuerte, gamma=1) / solapamiento débil
    INTEGRACIÓN         oráculo (T verdadero) / vínculo parcial (la mitad
                        de los hogares recibe T de un donante) / Hot-Deck
                        (todos lo reciben de un donante de la misma celda)
    ESTIMADORES         diferencia de medias, regresión con efectos fijos
                        de celda, LinearDML y CausalForestDML (los mismos
                        de `5_estimacion.py`, con W = celda exacta)
    EVALUACIÓN          sesgo, RMSE, cobertura del IC95 %, ancho del IC,
                        error del CATE (PEHE) y degradación por integración

En cada repetición la población real se parte en dos muestras sin
llave común, como GEIH y Sisbén: la "encuesta" (X, Y) y el "registro"
(X, T). El T verdadero de la encuesta solo se usa para medir; los
estimadores reciben únicamente el T observado según la integración.

P(T | celda) sale del Sisbén real (misma celda que el Hot-Deck), así que
la asignación observada tiene la forma real del sistema. El efecto
verdadero es sobre log-ingreso (`TAU`): +0,10 de base, mayor en zona
rural y con paredes precarias, menor con jefa mujer.

Para usarla con otra fuente (por ejemplo, registros administrativos
integrados de una entidad), basta una tabla con las columnas de
`COLUMNAS`: celda de integración, departamento, X y el resultado base.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.simulacion_semisintetica [reps] [n] [reps_bosque]
Salidas:
    docs/reports/simulacion_semisintetica.csv (cada repetición)
    docs/reports/simulacion_semisintetica_resumen.csv
"""
from __future__ import annotations

import importlib.util
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
SISBEN = Path("data/2_models/sisben_estandarizado_2024_con_bogota.parquet")
OUT = Path("docs/reports/simulacion_semisintetica.csv")
OUT_RESUMEN = Path("docs/reports/simulacion_semisintetica_resumen.csv")
SEED = 2026

# Columnas canónicas: cualquier fuente que las tenga sirve de base.
COLUMNAS = dict(celda="_hotdeck_celda", depto="geo_depto", zona="geo_zona", sexo="jefe_sexo",
                paredes="viv_paredes", ingreso="ingreso_percapita")

ESCENARIOS = {
    "aleatoria": dict(celda=0.0, x=0.0, gamma=0.0, escala=1.0),
    "confusion_observada": dict(celda=1.0, x=1.0, gamma=0.0, escala=1.0),
    "confusion_no_observada_leve": dict(celda=1.0, x=1.0, gamma=0.25, escala=1.0),
    "confusion_no_observada": dict(celda=1.0, x=1.0, gamma=1.0, escala=1.0),
    "solapamiento_debil": dict(celda=1.0, x=1.0, gamma=0.0, escala=4.0),
}
VINCULOS = {"oraculo": 0.0, "vinculo_parcial_50": 0.5, "hotdeck": 1.0}  # fracción con T de un donante
B_X = dict(rural=0.3, mujer=0.2, paredes_precaria=0.5)  # X en la asignación (fuera de la celda)
TAU = dict(base=0.10, rural=0.05, mujer=-0.03, paredes_precaria=0.04)  # efecto verdadero sobre log-ingreso


def _cargar_estimacion():
    """Los estimadores de `5_estimacion.py` (el nombre empieza por dígito,
    no se importa con `import`)."""
    ruta = Path(__file__).resolve().parents[1] / "5_estimacion.py"
    spec = importlib.util.spec_from_file_location("estimacion_5", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# Datos reales y generador
# --------------------------------------------------------------------------

def preparar_base(df: pd.DataFrame, p_t_celda: pd.Series) -> pd.DataFrame:
    """Tabla canónica: celda, X, Y0 y logit de P_Sisbén(T | celda)."""
    c = COLUMNAS
    b = pd.DataFrame({
        "celda": df[c["celda"]].astype(str),
        "depto": df[c["depto"]].astype(str),
        "geo_zona_urbana": (df[c["zona"]].astype(str) == "1").astype(int),
        "jefe_mujer": (df[c["sexo"]].astype(str) == "2").astype(int),
        "viv_paredes": pd.to_numeric(df[c["paredes"]], errors="coerce"),
        "y0": np.log1p(pd.to_numeric(df[c["ingreso"]], errors="coerce").clip(lower=0)),
    }).dropna().reset_index(drop=True)
    p = b["celda"].map(p_t_celda)
    p = p.fillna(p_t_celda.mean()).clip(0.01, 0.99)
    b["logit_p_celda"] = np.log(p / (1 - p))
    b["hotdeck_celda_cat"] = b["celda"].astype("category").cat.codes
    b["u"] = componente_no_observado(b)
    b["tau"] = efecto_verdadero(b)
    return b


def componente_no_observado(b: pd.DataFrame) -> np.ndarray:
    """U = necesidad que la celda y X no capturan: el residuo del ingreso
    real (con signo cambiado: mayor U = más pobre de lo que predice la
    celda), estandarizado. Es real, no inventado, y ni el Hot-Deck ni los
    estimadores lo ven."""
    y = b["y0"].to_numpy(float)
    Z = _diseno_x(b)
    yd, Zd = _dentro_de_celda(y, b["hotdeck_celda_cat"].to_numpy()), _dentro_de_celda(Z, b["hotdeck_celda_cat"].to_numpy())
    beta = np.linalg.lstsq(Zd, yd, rcond=None)[0]
    r = yd - Zd @ beta
    return -(r - r.mean()) / r.std()


def efecto_verdadero(b: pd.DataFrame) -> np.ndarray:
    precaria = (b["viv_paredes"] != 1).astype(float)
    return (TAU["base"] + TAU["rural"] * (1 - b["geo_zona_urbana"]) + TAU["mujer"] * b["jefe_mujer"]
            + TAU["paredes_precaria"] * precaria).to_numpy(float)


def asignar(b: pd.DataFrame, escenario: dict, rng: np.random.Generator) -> np.ndarray:
    """T verdadero. El intercepto se calibra para que en todos los
    escenarios la tasa de tratados sea la del Sisbén real (media de
    P(T | celda) sobre los hogares de la base)."""
    sigm = lambda z: 1 / (1 + np.exp(-z))  # noqa: E731
    pbar = float(sigm(b["logit_p_celda"]).mean())
    precaria = (b["viv_paredes"] != 1).astype(float)
    x = (B_X["rural"] * (1 - b["geo_zona_urbana"]) + B_X["mujer"] * b["jefe_mujer"]
         + B_X["paredes_precaria"] * precaria)
    s = (escenario["celda"] * b["logit_p_celda"] + escenario["x"] * x
         + escenario["gamma"] * b["u"]).to_numpy(float)
    s = escenario["escala"] * (s - s.mean())
    lo, hi = -20.0, 20.0
    for _ in range(60):  # bisección: media de la propensión = pbar
        c = (lo + hi) / 2
        lo, hi = (c, hi) if sigm(c + s).mean() < pbar else (lo, c)
    return (rng.random(len(b)) < sigm(c + s)).astype(int)


def hotdeck_celda(celda_receptor: np.ndarray, celda_donante: np.ndarray, t_donante: np.ndarray,
                  rng: np.random.Generator) -> np.ndarray:
    """T de un donante sorteado al azar en la misma celda (como el
    pipeline). Si la celda no tiene donantes, se sortea en todo el
    registro."""
    orden = np.argsort(celda_donante, kind="stable")
    cd, td = celda_donante[orden], t_donante[orden]
    inicio = np.searchsorted(cd, celda_receptor, side="left")
    fin = np.searchsorted(cd, celda_receptor, side="right")
    n = fin - inicio
    t = np.empty(len(celda_receptor), dtype=int)
    con = n > 0
    t[con] = td[inicio[con] + (rng.random(con.sum()) * n[con]).astype(int)]
    t[~con] = rng.choice(t_donante, (~con).sum())
    return t


# --------------------------------------------------------------------------
# Estimadores (reciben solo el T observado)
# --------------------------------------------------------------------------

def _diseno_x(b: pd.DataFrame) -> np.ndarray:
    paredes = pd.get_dummies(b["viv_paredes"].astype(int), prefix="p", drop_first=True, dtype=float)
    return np.column_stack([b["geo_zona_urbana"], b["jefe_mujer"], paredes.to_numpy()]).astype(float)


def _dentro_de_celda(v: np.ndarray, celda: np.ndarray) -> np.ndarray:
    v = np.asarray(v, float)
    k = celda.max() + 1
    cuenta = np.maximum(np.bincount(celda, minlength=k), 1)
    if v.ndim == 1:
        return v - (np.bincount(celda, v, minlength=k) / cuenta)[celda]
    return np.column_stack([c - (np.bincount(celda, c, minlength=k) / cuenta)[celda] for c in v.T])


def diferencia_medias(y: np.ndarray, t: np.ndarray) -> tuple[float, float, float]:
    y1, y0 = y[t == 1], y[t == 0]
    est = y1.mean() - y0.mean()
    se = np.sqrt(y1.var(ddof=1) / len(y1) + y0.var(ddof=1) / len(y0))
    return est, est - 1.96 * se, est + 1.96 * se


def regresion_efectos_fijos(y: np.ndarray, t: np.ndarray, Z: np.ndarray, celda: np.ndarray) -> tuple[float, float, float]:
    """MCO de Y sobre T y X con efectos fijos de celda (transformación
    dentro de la celda), error estándar robusto HC1."""
    D = _dentro_de_celda(np.column_stack([t, Z]), celda)
    yd = _dentro_de_celda(y, celda)
    D = D[:, D.std(axis=0) > 0]
    XtX_inv = np.linalg.pinv(D.T @ D)
    beta = XtX_inv @ D.T @ yd
    e = yd - D @ beta
    gl = len(y) - D.shape[1] - (celda.max() + 1)
    V = XtX_inv @ (D.T * e**2) @ D @ XtX_inv * len(y) / max(gl, 1)
    se = np.sqrt(V[0, 0])
    return beta[0], beta[0] - 1.96 * se, beta[0] + 1.96 * se


def dml(est5, d: pd.DataFrame, y: np.ndarray, t: np.ndarray, bosque: bool):
    """LinearDML o CausalForestDML con los modelos auxiliares de
    `5_estimacion.py` y W = celda exacta. Devuelve (ate, lo, hi, cate)."""
    from econml.dml import CausalForestDML, LinearDML

    X = d[est5.X_COLS].to_numpy(float)
    W = d[est5.W_CELDA[0]].to_numpy(float)
    modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA)
    if bosque:
        m = CausalForestDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, n_estimators=200,
                            min_samples_leaf=50, random_state=SEED)
    else:
        m = LinearDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, random_state=SEED)
    m.fit(y, t, X=X, W=W)
    lo, hi = m.ate_interval(X, alpha=0.05)
    return float(m.ate(X)), float(lo), float(hi), m.effect(X)


# --------------------------------------------------------------------------
# Corrida
# --------------------------------------------------------------------------

def una_repeticion(b: pd.DataFrame, rep: int, n: int, reps_bosque: int, est5) -> list[dict]:
    filas = []
    for i_esc, (nombre_esc, esc) in enumerate(ESCENARIOS.items()):
        rng = np.random.default_rng([SEED, rep, i_esc])
        t_real = asignar(b, esc, rng)
        y = b["y0"].to_numpy() + b["tau"].to_numpy() * t_real
        idx = rng.permutation(len(b))
        enc, reg = idx[:n], idx[n:]  # encuesta (X, Y) y registro (X, T), sin llave común
        d = b.iloc[enc].reset_index(drop=True)
        celda = d["hotdeck_celda_cat"].to_numpy()
        y_enc = y[enc]
        ate_verdadero = float(d["tau"].mean())
        t_donante = hotdeck_celda(celda, b["hotdeck_celda_cat"].to_numpy()[reg], t_real[reg], rng)
        Z = _diseno_x(d)

        for nombre_v, frac in VINCULOS.items():
            usa_donante = rng.random(n) < frac
            t_obs = np.where(usa_donante, t_donante, t_real[enc])
            comun = dict(rep=rep, escenario=nombre_esc, vinculo=nombre_v, ate_verdadero=ate_verdadero,
                         pct_tratados=float(t_obs.mean() * 100),
                         concordancia_t=float((t_obs == t_real[enc]).mean() * 100))
            res = {"diferencia_medias": diferencia_medias(y_enc, t_obs),
                   "regresion_efectos_fijos": regresion_efectos_fijos(y_enc, t_obs, Z, celda)}
            a, lo, hi, _ = dml(est5, d, y_enc, t_obs, bosque=False)
            res["linear_dml"] = (a, lo, hi)
            pehe = None
            if rep < reps_bosque:
                a, lo, hi, cate = dml(est5, d, y_enc, t_obs, bosque=True)
                res["causal_forest"] = (a, lo, hi)
                pehe = float(np.sqrt(np.mean((np.ravel(cate) - d["tau"].to_numpy()) ** 2)))
            for nombre_e, (a, lo, hi) in res.items():
                filas.append(dict(comun, estimador=nombre_e, estimacion=a, ic_lo=lo, ic_hi=hi,
                                  pehe=pehe if nombre_e == "causal_forest" else None))
    return filas


def resumir(r: pd.DataFrame) -> pd.DataFrame:
    r = r.assign(error=r["estimacion"] - r["ate_verdadero"],
                 cubre=(r["ic_lo"] <= r["ate_verdadero"]) & (r["ate_verdadero"] <= r["ic_hi"]),
                 ancho=r["ic_hi"] - r["ic_lo"])
    g = r.groupby(["escenario", "vinculo", "estimador"], sort=False)
    out = g.agg(reps=("rep", "size"), ate_verdadero=("ate_verdadero", "mean"), estimacion=("estimacion", "mean"),
                sesgo=("error", "mean"), rmse=("error", lambda e: float(np.sqrt(np.mean(e**2)))),
                cobertura=("cubre", "mean"), ancho_ic=("ancho", "mean"), pehe=("pehe", "mean"),
                concordancia_t=("concordancia_t", "mean")).reset_index()
    oraculo = out[out["vinculo"] == "oraculo"].set_index(["escenario", "estimador"])["rmse"]
    out["rmse_oraculo"] = out.set_index(["escenario", "estimador"]).index.map(oraculo)
    out["degradacion_rmse"] = out["rmse"] - out["rmse_oraculo"]
    return out


def main(reps: int = 50, n: int = 30_000, reps_bosque: int = 10) -> pd.DataFrame:
    from src.estimacion.cotas_frechet_manski import _p_t_por_celda

    est5 = _cargar_estimacion()
    logger.info("Cargando %s y P(T | celda) del Sisbén real", BASE)
    sisben = pd.read_parquet(SISBEN, columns=["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos", "Grupo",
                                               "Clasificacion"])
    p_t = _p_t_por_celda(sisben)["p_t"]
    b = preparar_base(pd.read_parquet(BASE, columns=list(COLUMNAS.values())), p_t)
    logger.info("Base: %s hogares reales, %s celdas | ATE verdadero poblacional %.4f",
                f"{len(b):,}", b["celda"].nunique(), b["tau"].mean())

    filas = []
    for rep in range(reps):
        t0 = time.time()
        filas += una_repeticion(b, rep, n, reps_bosque, est5)
        logger.info("Repetición %d/%d (%.0f s)", rep + 1, reps, time.time() - t0)
    r = pd.DataFrame(filas)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r.to_csv(OUT, index=False)
    res = resumir(r)
    res.to_csv(OUT_RESUMEN, index=False)

    pd.set_option("display.width", 220)
    print(f"\n=== Simulación semisintética: {reps} repeticiones, encuesta de {n:,} hogares reales "
          f"(Causal Forest en {min(reps, reps_bosque)}) ===")
    print(f"ATE verdadero (media de tau en la encuesta): {r['ate_verdadero'].mean():.4f} log-puntos")
    for esc, g in res.groupby("escenario", sort=False):
        print(f"\n--- Escenario: {esc}")
        print(g.drop(columns=["escenario"]).round(4).to_string(index=False))
    print(f"\nGuardado: {OUT}\nGuardado: {OUT_RESUMEN}")
    return res


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:]]
    main(*args)
