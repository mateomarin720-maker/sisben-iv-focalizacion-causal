"""Estimadores de la evaluación. Reciben solo el T observado según la
integración, nunca el verdadero. Cada uno devuelve (estimación, límite
inferior, límite superior) del IC 95 %."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

from src.simulacion.base import dentro_de_celda
from src.simulacion.escenarios import SEED

_EST5 = None


def estimacion5():
    """Los estimadores de `5_estimacion.py` (el nombre empieza por dígito,
    no se importa con `import`). Se carga una vez."""
    global _EST5
    if _EST5 is None:
        ruta = Path(__file__).resolve().parents[1] / "5_estimacion.py"
        spec = importlib.util.spec_from_file_location("estimacion_5", ruta)
        _EST5 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_EST5)
    return _EST5


def diferencia_medias(y: np.ndarray, t: np.ndarray) -> tuple[float, float, float]:
    y1, y0 = y[t == 1], y[t == 0]
    est = y1.mean() - y0.mean()
    se = np.sqrt(y1.var(ddof=1) / len(y1) + y0.var(ddof=1) / len(y0))
    return est, est - 1.96 * se, est + 1.96 * se


def regresion_efectos_fijos(y: np.ndarray, t: np.ndarray, Z: np.ndarray, celda: np.ndarray) -> tuple[float, float, float]:
    """MCO de Y sobre T y X con efectos fijos de celda (transformación
    dentro de la celda), error estándar robusto HC1."""
    D = dentro_de_celda(np.column_stack([t, Z]), celda)
    yd = dentro_de_celda(y, celda)
    D = D[:, D.std(axis=0) > 0]
    XtX_inv = np.linalg.pinv(D.T @ D)
    beta = XtX_inv @ D.T @ yd
    e = yd - D @ beta
    gl = len(y) - D.shape[1] - (int(celda.max()) + 1)
    V = XtX_inv @ (D.T * e**2) @ D @ XtX_inv * len(y) / max(gl, 1)
    se = np.sqrt(V[0, 0])
    return beta[0], beta[0] - 1.96 * se, beta[0] + 1.96 * se


def pesos_rd(puntaje: np.ndarray, corte: float, h: float) -> np.ndarray:
    return np.clip(1 - np.abs(puntaje - corte) / h, 0, None)  # kernel triangular


def discontinuidad(y: np.ndarray, puntaje: np.ndarray, corte: float, h: float) -> tuple[float, float, float]:
    """RD nítida local lineal en el corte, kernel triangular, ancho h; el
    efecto es el salto de Y en el corte. Error estándar robusto."""
    w = pesos_rd(puntaje, corte, h)
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


def discontinuidad_difusa(y: np.ndarray, t: np.ndarray, puntaje: np.ndarray, corte: float,
                          h: float) -> tuple[float, float, float]:
    """RD difusa local lineal: mínimos cuadrados en dos etapas con kernel
    triangular; la participación T se instrumenta con 1(puntaje ≥ corte).
    El efecto es el salto en Y dividido por el salto en la participación.
    Error estándar robusto."""
    w = pesos_rd(puntaje, corte, h)
    m = w > 0
    dd, yy, tt, w = puntaje[m] - corte, y[m], t[m].astype(float), w[m]
    z = (dd >= 0).astype(float)
    X = np.column_stack([np.ones_like(dd), tt, dd, z * dd])
    Z = np.column_stack([np.ones_like(dd), z, dd, z * dd])
    ZwX_inv = np.linalg.pinv((Z * w[:, None]).T @ X)
    beta = ZwX_inv @ (Z * w[:, None]).T @ yy
    e = yy - X @ beta
    Zwe = Z * (w * e)[:, None]
    V = ZwX_inv @ (Zwe.T @ Zwe) @ ZwX_inv.T
    se = np.sqrt(V[1, 1])
    return beta[1], beta[1] - 1.96 * se, beta[1] + 1.96 * se


def dml(d: pd.DataFrame, y: np.ndarray, t: np.ndarray, bosque: bool):
    """LinearDML o CausalForestDML con los modelos auxiliares de
    `5_estimacion.py` y W = celda exacta. Devuelve (ate, lo, hi, cate)."""
    from econml.dml import CausalForestDML, LinearDML

    est5 = estimacion5()
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
