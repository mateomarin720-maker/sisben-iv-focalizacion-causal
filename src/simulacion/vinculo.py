"""Integración de la encuesta con el registro: Hot-Deck simulado por celda.

Pendiente (paso 4 del diseño, prioridad 3 de la guía): la cadena de
respaldos del pipeline (celda → sin pisos → depto + edad → depto). Hoy,
una celda sin donantes sortea en todo el registro.
"""
from __future__ import annotations

import numpy as np


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
