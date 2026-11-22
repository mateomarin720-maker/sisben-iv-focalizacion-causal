"""Varianza por jackknife de grupos eliminados, para razones ponderadas.

Cada cantidad de la FHDI es una razón R = Σ w·a / Σ w·b sobre los hogares
de la GEIH, con a y b ya promediados sobre los donantes fraccionales (por
ejemplo, la tasa de exclusión: a = y·(1 − q_AB), b = y). Los hogares se
reparten al azar en G grupos; la réplica g quita el grupo g y escala el
resto por G/(G − 1):

    v = (G − 1)/G · Σ_g (R_g − R̄)²

Lo que mide: la variación muestral de la GEIH. No incluye ruido de la
imputación, que la calibración de los pesos elimina para toda cantidad que
dependa del grupo imputado.

La variación del lado de los donantes la mide aparte `bootstrap_donantes`.
Hasta el 2026-11-22 se suponía despreciable por los 3,1 millones de
donantes, pero el Sisbén nacional es una muestra con `fex` de cola larga
(tamaño efectivo de Kish ≈151.000, menor que los 290.968 hogares de la
GEIH): en la proporción de grupos pesa más que la de la GEIH. Bogotá es el
registro completo y no aporta varianza de muestreo (`fijos`). El error
total suma las dos varianzas.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

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


def bootstrap_donantes(receptor: pd.DataFrame, donante: pd.DataFrame, estadistico: Callable[[np.ndarray], np.ndarray],
                       b: int = 500, seed: int = 2026, fijos: np.ndarray | None = None) -> np.ndarray:
    """Error estándar del lado del Sisbén de `estadistico(π)` (π: n × 4, las
    probabilidades FEFI de cada receptor), por bootstrap bayesiano de los
    donantes: cada réplica multiplica el `fex` por pesos Exp(1) y recalcula π
    en toda la cadena de respaldos. Los donantes `fijos` (registro completo)
    conservan su peso."""
    from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import peso_donante
    from src.emparejamiento.fhdi import reglas
    g = reglas._codigo_grupo(donante)
    w = peso_donante(donante)
    _, celda, celdas_donante, total = reglas.asignar_nivel(receptor, donante)
    fijos = np.zeros(len(w), bool) if fijos is None else np.asarray(fijos, bool)
    rng = np.random.default_rng(seed)
    replicas = [estadistico(reglas.tabla_probabilidades(g, w * np.where(fijos, 1.0, rng.exponential(size=len(w))),
                                                        celdas_donante, total)[celda]) for _ in range(b)]
    return np.asarray(replicas, float).std(axis=0, ddof=1)
