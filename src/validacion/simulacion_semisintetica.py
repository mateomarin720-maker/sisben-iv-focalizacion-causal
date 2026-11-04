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
                        paredes}, Y0 = log(1 + ingreso per cápita UG),
                        línea de pobreza del dominio
    GENERADOR           U = parte del ingreso que la celda y X no explican
                        (no observable); score = logit P_Sisbén(T | celda)
                        + X·b + gamma·U; T verdadero ~ Bernoulli(score) o,
                        en `regla_corte`, T = 1(puntaje >= corte) con un
                        puntaje medido con ruido; tau(X) conocido;
                        Y = Y0 + tau(X)·T
    OUTCOMES            log-ingreso (continuo) y pobreza monetaria
                        (1 si el ingreso queda bajo la línea del dominio)
    ESCENARIOS          aleatoria / confusión observada / efecto nulo /
                        confusión no observada (gamma 0,25, 0,5 y 1) /
                        solapamiento débil / regla de corte
    INTEGRACIÓN         oráculo (T verdadero) / vínculo parcial (la mitad
                        de los hogares recibe T y puntaje de un donante) /
                        Hot-Deck (todos los reciben de un donante de la
                        misma celda)
    ESTIMADORES         diferencia de medias, regresión con efectos fijos
                        de celda, LinearDML, CausalForestDML (los de
                        `5_estimacion.py`, con W = celda exacta) y, en la
                        regla de corte, discontinuidad de regresión (RD)
    EVALUACIÓN          sesgo, RMSE, cobertura del IC95 %, ancho del IC,
                        error del CATE (PEHE), degradación por integración
                        y error estándar Monte Carlo (MCSE) de cada una

En cada repetición la población real se parte en dos muestras sin llave
común, como GEIH y Sisbén: la "encuesta" (X, Y) y el "registro" (X, T,
puntaje). El T verdadero de la encuesta solo se usa para medir; los
estimadores reciben únicamente el T observado según la integración.

**Convergencia.** Las repeticiones corren en lotes, en paralelo, hasta
que el MCSE de cada celda (escenario × integración × outcome ×
estimador) queda bajo el umbral (`UMBRAL_*`, criterio de Morris, White y
Crowther, 2019, Statistics in Medicine 38:2074) o hasta `MAX_REPS`. Cada
lote se guarda al terminar: si la corrida se interrumpe, se reanuda desde
el último lote con la misma configuración.

Para usarla con otra fuente (por ejemplo, registros administrativos
integrados de una entidad), basta una tabla con las columnas de
`COLUMNAS`: celda de integración, departamento, X, ingreso y dominio.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.simulacion_semisintetica [n_jobs]
Salidas:
    docs/reports/simulacion_semisintetica.csv (cada repetición)
    docs/reports/simulacion_semisintetica_resumen.csv (con MCSE)
    docs/reports/simulacion_semisintetica_convergencia.csv (traza por lote)
    docs/reports/simulacion_semisintetica_tablas.md (tablas del documento)
    docs/resultados/simulacion_semisintetica_convergencia.png
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
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
OUT_CONVERGENCIA = Path("docs/reports/simulacion_semisintetica_convergencia.csv")
OUT_FIRMA = Path("docs/reports/simulacion_semisintetica_config.json")
SEED = 2026
N_ENCUESTA = 30_000

# Columnas canónicas: cualquier fuente que las tenga sirve de base.
COLUMNAS = dict(celda="_hotdeck_celda", depto="geo_depto", zona="geo_zona", sexo="jefe_sexo",
                paredes="viv_paredes", ingreso="ingreso_percapita", dominio="dominio_pm")
LINEAS = {"13_ciudades": 566_228.0, "otras_cabeceras": 434_323.0, "rural": 291_998.0}  # DANE 2024

ESCENARIOS = {
    "aleatoria": dict(celda=0.0, x=0.0, gamma=0.0, escala=1.0),
    "confusion_observada": dict(celda=1.0, x=1.0, gamma=0.0, escala=1.0),
    "efecto_nulo": dict(celda=1.0, x=1.0, gamma=0.0, escala=1.0, factor_tau=0.0),
    "confusion_no_observada_leve": dict(celda=1.0, x=1.0, gamma=0.25, escala=1.0),
    "confusion_no_observada_media": dict(celda=1.0, x=1.0, gamma=0.5, escala=1.0),
    "confusion_no_observada": dict(celda=1.0, x=1.0, gamma=1.0, escala=1.0),
    "solapamiento_debil": dict(celda=1.0, x=1.0, gamma=0.0, escala=4.0),
    # Regla del Sisbén: T por un puntaje con corte, con confusión no observada fuerte.
    "regla_corte": dict(celda=1.0, x=1.0, gamma=1.0, escala=1.0, corte=True, ruido_puntaje=0.5),
}
VINCULOS = {"oraculo": 0.0, "vinculo_parcial_50": 0.5, "hotdeck": 1.0}  # fracción con T de un donante
VINCULOS_BOSQUE = ("oraculo", "hotdeck")
OUTCOMES = ("log_ingreso", "pobre_monetario")
B_X = dict(rural=0.3, mujer=0.2, paredes_precaria=0.5)  # X en la asignación (fuera de la celda)
TAU = dict(base=0.10, rural=0.05, mujer=-0.03, paredes_precaria=0.04)  # efecto verdadero sobre log-ingreso
H_RD = 0.5  # ancho de banda de la RD, en desviaciones estándar del puntaje

# Convergencia: MCSE máximo admitido en cada celda.
UMBRAL_SESGO = {"log_ingreso": 0.003, "pobre_monetario": 0.0015}
UMBRAL_COBERTURA = 0.025
MIN_REPS, MAX_REPS, LOTE = 100, 600, 24
MIN_REPS_BOSQUE, MAX_REPS_BOSQUE = 50, 200


def _cargar_estimacion():
    """Los estimadores de `5_estimacion.py` (el nombre empieza por dígito,
    no se importa con `import`)."""
    ruta = Path(__file__).resolve().parents[1] / "5_estimacion.py"
    spec = importlib.util.spec_from_file_location("estimacion_5", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_EST5 = None


def _est5():
    global _EST5
    if _EST5 is None:
        _EST5 = _cargar_estimacion()
    return _EST5


# --------------------------------------------------------------------------
# Datos reales y generador
# --------------------------------------------------------------------------

def preparar_base(df: pd.DataFrame, p_t_celda: pd.Series) -> pd.DataFrame:
    """Tabla canónica: celda, X, Y0, línea de pobreza y logit de
    P_Sisbén(T | celda)."""
    c = COLUMNAS
    b = pd.DataFrame({
        "celda": df[c["celda"]].astype(str),
        "depto": df[c["depto"]].astype(str),
        "geo_zona_urbana": (df[c["zona"]].astype(str) == "1").astype(int),
        "jefe_mujer": (df[c["sexo"]].astype(str) == "2").astype(int),
        "viv_paredes": pd.to_numeric(df[c["paredes"]], errors="coerce"),
        "y0": np.log1p(pd.to_numeric(df[c["ingreso"]], errors="coerce").clip(lower=0)),
        "log_lp": np.log1p(df[c["dominio"]].map(LINEAS)),
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
    celda = b["hotdeck_celda_cat"].to_numpy()
    yd, Zd = _dentro_de_celda(y, celda), _dentro_de_celda(_diseno_x(b), celda)
    beta = np.linalg.lstsq(Zd, yd, rcond=None)[0]
    r = yd - Zd @ beta
    return -(r - r.mean()) / r.std()


def efecto_verdadero(b: pd.DataFrame) -> np.ndarray:
    precaria = (b["viv_paredes"] != 1).astype(float)
    return (TAU["base"] + TAU["rural"] * (1 - b["geo_zona_urbana"]) + TAU["mujer"] * b["jefe_mujer"]
            + TAU["paredes_precaria"] * precaria).to_numpy(float)


def _sigm(z):
    return 1 / (1 + np.exp(-z))


def asignar(b: pd.DataFrame, escenario: dict, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, float]:
    """T verdadero, puntaje y corte. La tasa de tratados es la del Sisbén
    real (media de P(T | celda)) en todos los escenarios: el intercepto se
    calibra en los de Bernoulli y el corte es un cuantil en la regla."""
    pbar = float(_sigm(b["logit_p_celda"]).mean())
    precaria = (b["viv_paredes"] != 1).astype(float)
    x = (B_X["rural"] * (1 - b["geo_zona_urbana"]) + B_X["mujer"] * b["jefe_mujer"]
         + B_X["paredes_precaria"] * precaria)
    s = (escenario["celda"] * b["logit_p_celda"] + escenario["x"] * x
         + escenario["gamma"] * b["u"]).to_numpy(float)
    s = escenario["escala"] * (s - s.mean())
    if escenario.get("corte"):
        puntaje = s + rng.normal(0, escenario["ruido_puntaje"], len(s))
        corte = float(np.quantile(puntaje, 1 - pbar))
        return (puntaje >= corte).astype(int), puntaje, corte
    lo, hi = -20.0, 20.0
    for _ in range(60):  # bisección: media de la propensión = pbar
        c = (lo + hi) / 2
        lo, hi = (c, hi) if _sigm(c + s).mean() < pbar else (lo, c)
    return (rng.random(len(b)) < _sigm(c + s)).astype(int), s, np.nan


def sortear_donante(celda_receptor: np.ndarray, celda_donante: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Posición (en el registro) de un donante sorteado al azar en la misma
    celda, como el pipeline. Si la celda no tiene donantes, se sortea en
    todo el registro."""
    orden = np.argsort(celda_donante, kind="stable")
    cd = celda_donante[orden]
    inicio = np.searchsorted(cd, celda_receptor, side="left")
    n = np.searchsorted(cd, celda_receptor, side="right") - inicio
    pos = np.empty(len(celda_receptor), dtype=int)
    con = n > 0
    pos[con] = orden[inicio[con] + (rng.random(con.sum()) * n[con]).astype(int)]
    pos[~con] = rng.integers(0, len(celda_donante), (~con).sum())
    return pos


def hotdeck_celda(celda_receptor: np.ndarray, celda_donante: np.ndarray, t_donante: np.ndarray,
                  rng: np.random.Generator) -> np.ndarray:
    """T de un donante de la misma celda."""
    return np.asarray(t_donante)[sortear_donante(celda_receptor, celda_donante, rng)]


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


def _pesos_rd(puntaje: np.ndarray, corte: float, h: float) -> np.ndarray:
    return np.clip(1 - np.abs(puntaje - corte) / h, 0, None)  # kernel triangular


def discontinuidad(y: np.ndarray, puntaje: np.ndarray, corte: float, h: float) -> tuple[float, float, float]:
    """RD nítida local lineal en el corte, kernel triangular, ancho h; el
    efecto es el salto de Y en el corte. Error estándar robusto."""
    w = _pesos_rd(puntaje, corte, h)
    m = w > 0
    d, yy, w = puntaje[m] - corte, y[m], w[m]
    t = (d >= 0).astype(float)
    X = np.column_stack([np.ones_like(d), t, d, t * d])
    Xw = X * w[:, None]
    A = np.linalg.pinv(X.T @ Xw)
    beta = A @ Xw.T @ yy
    e = yy - X @ beta
    V = A @ (Xw.T * e**2) @ Xw @ A
    se = np.sqrt(V[1, 1])
    return beta[1], beta[1] - 1.96 * se, beta[1] + 1.96 * se


def dml(d: pd.DataFrame, y: np.ndarray, t: np.ndarray, bosque: bool):
    """LinearDML o CausalForestDML con los modelos auxiliares de
    `5_estimacion.py` y W = celda exacta. Devuelve (ate, lo, hi, cate)."""
    from econml.dml import CausalForestDML, LinearDML

    est5 = _est5()
    X = d[est5.X_COLS].to_numpy(float)
    W = d[est5.W_CELDA[0]].to_numpy(float)
    modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA)
    if bosque:
        m = CausalForestDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, n_estimators=200,
                            min_samples_leaf=50, random_state=SEED, n_jobs=1)
    else:
        m = LinearDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, random_state=SEED)
    m.fit(y, t, X=X, W=W)
    lo, hi = m.ate_interval(X, alpha=0.05)
    return float(m.ate(X)), float(lo), float(hi), m.effect(X)


# --------------------------------------------------------------------------
# Una repetición
# --------------------------------------------------------------------------

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
        donante = reg[sortear_donante(celda, b["hotdeck_celda_cat"].to_numpy()[reg], rng)]
        ys = _outcomes(d, d["y0"].to_numpy(), tau, t_real[enc])
        Z = _diseno_x(d)
        h = H_RD * float(np.std(puntaje))
        w_rd = _pesos_rd(puntaje[enc], corte, h) if esc.get("corte") else None

        for nombre_v, frac in VINCULOS.items():
            usa_donante = rng.random(n) < frac
            t_obs = np.where(usa_donante, t_real[donante], t_real[enc])
            p_obs = np.where(usa_donante, puntaje[donante], puntaje[enc])
            for outcome, (y, efecto_hogar) in ys.items():
                verdad = float(efecto_hogar.mean())
                comun = dict(rep=rep, escenario=nombre_esc, vinculo=nombre_v, outcome=outcome,
                             pct_tratados=float(t_obs.mean() * 100),
                             concordancia_t=float((t_obs == t_real[enc]).mean() * 100))
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


# --------------------------------------------------------------------------
# Resumen, MCSE y convergencia
# --------------------------------------------------------------------------

CELDA = ["escenario", "vinculo", "outcome", "estimador"]


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


def _firma(n: int) -> str:
    cfg = dict(ESCENARIOS=ESCENARIOS, VINCULOS=VINCULOS, OUTCOMES=OUTCOMES, B_X=B_X, TAU=TAU, H_RD=H_RD,
               LINEAS=LINEAS, SEED=SEED, n=n, version=2)
    return hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]


def _previas(n: int) -> pd.DataFrame | None:
    """Repeticiones ya guardadas con la misma configuración (para reanudar)."""
    if OUT.exists() and OUT_FIRMA.exists() and json.loads(OUT_FIRMA.read_text()).get("firma") == _firma(n):
        return pd.read_csv(OUT)
    return None


FIGURA = Path("docs/resultados/simulacion_semisintetica_convergencia.png")
PANELES = [  # (escenario, outcome, estimador)
    ("confusion_observada", "log_ingreso", "linear_dml"),
    ("confusion_observada", "pobre_monetario", "linear_dml"),
    ("confusion_no_observada", "log_ingreso", "linear_dml"),
    ("regla_corte", "log_ingreso", "discontinuidad_rd"),
]
COLORES = {"oraculo": "#2a78d6", "vinculo_parcial_50": "#eb6834", "hotdeck": "#1baf7a"}  # paleta de referencia, 3 primeros
ETIQUETAS = {"oraculo": "Oráculo", "vinculo_parcial_50": "Vínculo 50 %", "hotdeck": "Hot-Deck"}
TITULOS = {"confusion_observada": "Confusión observada", "confusion_no_observada": "Confusión no observada fuerte",
           "regla_corte": "Regla de corte", "linear_dml": "LinearDML", "discontinuidad_rd": "RD en el corte",
           "log_ingreso": "log-ingreso", "pobre_monetario": "pobreza monetaria"}


def graficar_convergencia(traza: pd.DataFrame, ruta: Path = FIGURA) -> None:
    """Estimación media ± 1,96·MCSE según se acumulan repeticiones, por
    integración, en cuatro celdas clave. La línea punteada es el efecto
    verdadero."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    texto, texto2, superficie, rejilla = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
    fig, ejes = plt.subplots(2, 2, figsize=(11, 7.5), facecolor=superficie)
    for ax, (esc, out, est) in zip(ejes.ravel(), PANELES):
        ax.set_facecolor(superficie)
        g = traza[(traza["escenario"] == esc) & (traza["outcome"] == out) & (traza["estimador"] == est)]
        verdad = g["efecto_verdadero"].mean()
        ax.axhline(verdad, color=texto2, lw=1, ls=(0, (4, 3)), zorder=1)
        ax.annotate("efecto verdadero", (0.4, verdad), xycoords=("axes fraction", "data"), xytext=(0, 4),
                    textcoords="offset points", color=texto2, fontsize=8)
        for v, color in COLORES.items():
            s = g[g["vinculo"] == v].sort_values("reps_total")
            if s.empty:
                continue
            x, m, e = s["reps_total"], s["estimacion"], 1.96 * s["mcse_sesgo"]
            ax.fill_between(x, m - e, m + e, color=color, alpha=0.18, lw=0, zorder=2)
            ax.plot(x, m, color=color, lw=2, zorder=3, label=ETIQUETAS[v])
            ax.annotate(ETIQUETAS[v], (x.iloc[-1], m.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color=texto)
        ax.set_title(f"{TITULOS[esc]} · {TITULOS[out]} · {TITULOS[est]}", fontsize=9.5, color=texto, loc="left")
        ax.grid(axis="y", color=rejilla, lw=0.8)
        ax.tick_params(colors=texto2, labelsize=8)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(rejilla)
        ax.set_xlabel("repeticiones acumuladas", fontsize=8, color=texto2)
        ax.set_ylabel("estimación media", fontsize=8, color=texto2)
        ax.margins(x=0.12)
    manijas, nombres = ejes.ravel()[0].get_legend_handles_labels()
    fig.suptitle("Convergencia de la simulación semisintética (banda: ± 1,96 · MCSE)", y=0.985, fontsize=11,
                 color=texto)
    fig.legend(manijas, nombres, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=3, frameon=False,
               fontsize=9, labelcolor=texto)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=150, facecolor=superficie)
    plt.close(fig)


OUT_TABLAS = Path("docs/reports/simulacion_semisintetica_tablas.md")
ORDEN_EST = ["diferencia_medias", "regresion_efectos_fijos", "linear_dml", "causal_forest", "discontinuidad_rd"]
NOMBRES_EST = {"diferencia_medias": "Dif. de medias", "regresion_efectos_fijos": "Regresión EF celda",
               "linear_dml": "LinearDML", "causal_forest": "Causal Forest", "discontinuidad_rd": "RD en el corte"}


def tablas_markdown(res: pd.DataFrame, ruta: Path = OUT_TABLAS) -> str:
    """Tablas del documento de resultados, generadas del resumen: media de
    la estimación (cobertura del IC 95 % entre paréntesis) por escenario,
    integración y estimador, una tabla por outcome."""
    num = lambda v, fmt: format(v, fmt).replace(".", ",")  # noqa: E731
    partes = []
    for out in OUTCOMES:
        x = res[res["outcome"] == out]
        ests = [e for e in ORDEN_EST if e in set(x["estimador"])]
        partes.append(f"### {TITULOS.get(out, out)}\n")
        partes.append("| Escenario | Efecto verdadero | Integración | " + " | ".join(NOMBRES_EST[e] for e in ests) + " |")
        partes.append("|" + "---|" * (len(ests) + 3))
        for esc in ESCENARIOS:
            for v in VINCULOS:
                g = x[(x["escenario"] == esc) & (x["vinculo"] == v)].set_index("estimador")
                if g.empty:
                    continue
                verdad = g.loc[[e for e in g.index if e != "discontinuidad_rd"], "efecto_verdadero"].mean()
                celdas = []
                for e in ests:
                    if e in g.index:
                        c = g.loc[e]
                        celdas.append(f"{num(c['estimacion'], '+.3f')} ({num(c['cobertura'], '.2f')})")
                    else:
                        celdas.append("—")
                cab = esc.replace("_", " ") if v == "oraculo" else ""
                partes.append(f"| {cab} | {num(verdad, '+.3f')} | {ETIQUETAS[v]} | " + " | ".join(celdas) + " |")
        partes.append("")
    rd = res[res["estimador"] == "discontinuidad_rd"]
    if not rd.empty:
        partes.append("Efecto verdadero en el corte (objetivo de la RD): " + ", ".join(
            f"{TITULOS.get(o, o)} {num(g['efecto_verdadero'].mean(), '+.3f')}" for o, g in rd.groupby("outcome", sort=False)))
    texto = "\n".join(partes) + "\n"
    ruta.write_text(texto, encoding="utf-8")
    return texto


def main(n_jobs: int = 3, n: int = N_ENCUESTA) -> pd.DataFrame:
    from joblib import Parallel, delayed, parallel_config

    from src.estimacion.cotas_frechet_manski import _p_t_por_celda

    logger.info("Cargando %s y P(T | celda) del Sisbén real", BASE)
    sisben = pd.read_parquet(SISBEN, columns=["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos", "Grupo",
                                               "Clasificacion"])
    p_t = _p_t_por_celda(sisben)["p_t"]
    del sisben
    b = preparar_base(pd.read_parquet(BASE, columns=list(COLUMNAS.values())), p_t)
    logger.info("Base: %s hogares reales, %s celdas | tau medio %.4f", f"{len(b):,}", b["celda"].nunique(),
                b["tau"].mean())

    r = _previas(n)
    if r is not None:
        logger.info("Reanudando: %d repeticiones ya guardadas", r["rep"].nunique())
    else:
        r = pd.DataFrame()
        OUT_FIRMA.write_text(json.dumps(dict(firma=_firma(n), n=n)))
    traza = [] if r.empty or not OUT_CONVERGENCIA.exists() else [pd.read_csv(OUT_CONVERGENCIA)]

    while True:
        hechas = 0 if r.empty else r["rep"].nunique()
        reps_bosque = 0 if r.empty else r.loc[r["estimador"] == "causal_forest", "rep"].nunique()
        res = resumir(r) if not r.empty else None
        falta = hechas < MIN_REPS or len(pendientes(res, bosque=False)) > 0
        falta_bosque = reps_bosque < MIN_REPS_BOSQUE or (res is not None and len(pendientes(res, bosque=True)) > 0)
        falta_bosque = falta_bosque and reps_bosque < MAX_REPS_BOSQUE
        if (not falta and not falta_bosque) or hechas >= MAX_REPS:
            break
        lote = list(range(hechas, hechas + LOTE))
        con_bosque = falta_bosque
        t0 = time.time()
        with parallel_config(backend="loky", inner_max_num_threads=1):
            partes = Parallel(n_jobs=n_jobs)(delayed(una_repeticion)(b, rep, n, con_bosque) for rep in lote)
        nuevas = pd.DataFrame([f for p in partes for f in p])
        r = pd.concat([r, nuevas], ignore_index=True)
        r.to_csv(OUT, index=False)
        res = resumir(r)
        traza.append(res.assign(reps_total=r["rep"].nunique()))
        pd.concat(traza, ignore_index=True).to_csv(OUT_CONVERGENCIA, index=False)
        p, pb = pendientes(res, False), pendientes(res, True)
        logger.info("Lote reps %d-%d%s en %.0f s | celdas sin converger: %d (+ %d de Causal Forest) | "
                    "MCSE sesgo máx %.4f, cobertura máx %.3f",
                    lote[0], lote[-1], " con Causal Forest" if con_bosque else "", time.time() - t0, len(p), len(pb),
                    res["mcse_sesgo"].max(), res["mcse_cobertura"].max())

    res = resumir(r)
    res.to_csv(OUT_RESUMEN, index=False)
    graficar_convergencia(pd.read_csv(OUT_CONVERGENCIA))
    conv =len(pendientes(res, False)) == 0 and len(pendientes(res, True)) == 0

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print(f"\n=== Simulación semisintética: {r['rep'].nunique()} repeticiones "
          f"(Causal Forest en {r.loc[r['estimador'] == 'causal_forest', 'rep'].nunique()}), "
          f"encuesta de {n:,} hogares reales ===")
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
    print(f"\nGuardado: {OUT}\nGuardado: {OUT_RESUMEN}\nGuardado: {OUT_CONVERGENCIA}\nGuardado: {FIGURA}\nGuardado: {OUT_TABLAS}")
    return res


if __name__ == "__main__":
    main(*[int(a) for a in sys.argv[1:]])
