"""De la tabla canónica de hogares a la tabla de trabajo de la simulación.

Todo lo derivado se calcula aquí a partir de las columnas canónicas, nunca
se recibe hecho: la celda del Hot-Deck con la misma regla del pipeline
(`construir_celda`), zona urbana y jefe mujer 0/1, Y0 = log(1 + ingreso
per cápita), la línea de pobreza del dominio, el logit de P_Sisbén(T |
celda), el componente no observado U y el efecto verdadero tau(X).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import construir_celda
from src.simulacion import contrato
from src.simulacion.escenarios import TAU


def preparar_base(hogares: pd.DataFrame, p_t_celda: pd.Series) -> pd.DataFrame:
    """Tabla de trabajo: celda, X, Y0, línea de pobreza y logit de
    P_Sisbén(T | celda). `hogares` debe cumplir el contrato del rol
    `hogares`; `p_t_celda` va indexada por la celda del Hot-Deck."""
    contrato.validar(hogares, "hogares")
    b = pd.DataFrame({
        "celda": construir_celda(hogares).astype(str),
        "depto": hogares["geo_depto"].astype(str),
        "geo_zona_urbana": (hogares["geo_zona"].astype(str) == "1").astype(int),
        "jefe_mujer": (hogares["jefe_sexo"].astype(str) == "2").astype(int),
        "viv_paredes": pd.to_numeric(hogares["viv_paredes"], errors="coerce"),
        "y0": np.log1p(pd.to_numeric(hogares["ingreso_percapita"], errors="coerce").clip(lower=0)),
        "log_lp": np.log1p(hogares["dominio_pm"].map(contrato.LINEAS)),
    }).dropna().reset_index(drop=True)
    p = b["celda"].map(p_t_celda)
    p = p.fillna(p_t_celda.mean()).clip(0.01, 0.99)
    b["logit_p_celda"] = np.log(p / (1 - p))
    # int64: los códigos de categoría vienen en int8/int16 y se desbordan
    # en aritmética con el tamaño de la muestra (regresion_efectos_fijos).
    b["hotdeck_celda_cat"] = b["celda"].astype("category").cat.codes.astype("int64")
    b["u"] = componente_no_observado(b)
    b["tau"] = efecto_verdadero(b)
    return b


def diseno_x(b: pd.DataFrame) -> np.ndarray:
    """X de los estimadores: zona urbana, jefe mujer e indicadoras de paredes."""
    paredes = pd.get_dummies(b["viv_paredes"].astype(int), prefix="p", drop_first=True, dtype=float)
    return np.column_stack([b["geo_zona_urbana"], b["jefe_mujer"], paredes.to_numpy()]).astype(float)


def dentro_de_celda(v: np.ndarray, celda: np.ndarray) -> np.ndarray:
    """Resta la media de la celda (transformación de efectos fijos)."""
    v = np.asarray(v, float)
    k = int(celda.max()) + 1
    cuenta = np.maximum(np.bincount(celda, minlength=k), 1)
    if v.ndim == 1:
        return v - (np.bincount(celda, v, minlength=k) / cuenta)[celda]
    return np.column_stack([c - (np.bincount(celda, c, minlength=k) / cuenta)[celda] for c in v.T])


def componente_no_observado(b: pd.DataFrame) -> np.ndarray:
    """U = necesidad que la celda y X no capturan: el residuo del ingreso
    real (con signo cambiado: mayor U = más pobre de lo que predice la
    celda), estandarizado. Es real, no inventado, y ni el Hot-Deck ni los
    estimadores lo ven."""
    y = b["y0"].to_numpy(float)
    celda = b["hotdeck_celda_cat"].to_numpy()
    yd, Zd = dentro_de_celda(y, celda), dentro_de_celda(diseno_x(b), celda)
    beta = np.linalg.lstsq(Zd, yd, rcond=None)[0]
    r = yd - Zd @ beta
    return -(r - r.mean()) / r.std()


def efecto_verdadero(b: pd.DataFrame) -> np.ndarray:
    precaria = (b["viv_paredes"] != 1).astype(float)
    return (TAU["base"] + TAU["rural"] * (1 - b["geo_zona_urbana"]) + TAU["mujer"] * b["jefe_mujer"]
            + TAU["paredes_precaria"] * precaria).to_numpy(float)
