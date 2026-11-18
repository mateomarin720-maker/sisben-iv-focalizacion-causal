"""Varianza por jackknife de grupos eliminados, para razones ponderadas.

Cada cantidad de la FHDI es una razón R = Σ w·a / Σ w·b sobre los hogares
de la GEIH, con a y b ya promediados sobre los donantes fraccionales (por
ejemplo, la tasa de exclusión: a = y·(1 − q_AB), b = y). Los hogares se
reparten al azar en G grupos; la réplica g quita el grupo g y escala el
resto por G/(G − 1):

    v = (G − 1)/G · Σ_g (R_g − R̄)²

Lo que mide: la variación muestral de la GEIH. No incluye la del lado de
los donantes porque el Sisbén es un registro de 3,1 millones de hogares
(casi un censo de la población registrada), ni ruido de la imputación,
que la calibración de los pesos elimina para toda cantidad que dependa
del grupo imputado.
"""
from __future__ import annotations

import numpy as np

GRUPOS_JACKKNIFE = 100


def asignar_grupos(n: int, g: int = GRUPOS_JACKKNIFE, seed: int = 2024) -> np.ndarray:
    return np.random.default_rng(seed).permutation(np.arange(n) % g)


def razon_jackknife(w: np.ndarray, a: np.ndarray, b: np.ndarray, grupos: np.ndarray) -> tuple[float, float]:
    """(R, error estándar) de R = Σ w·a / Σ w·b."""
    ok = ~(np.isnan(a) | np.isnan(b))
    w, a, b, grupos = w[ok], a[ok], b[ok], grupos[ok]
    g = grupos.max() + 1
    num, den = (w * a).sum(), (w * b).sum()
    num_g = np.bincount(grupos, w * a, minlength=g)
    den_g = np.bincount(grupos, w * b, minlength=g)
    replicas = (num - num_g) / (den - den_g)
    return float(num / den), float(np.sqrt((g - 1) / g * ((replicas - replicas.mean()) ** 2).sum()))
