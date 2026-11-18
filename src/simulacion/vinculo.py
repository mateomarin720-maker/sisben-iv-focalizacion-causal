"""Integración de la encuesta con el registro, con la misma cadena de
respaldos del pipeline (`claves_por_nivel` en
`src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py`): celda exacta →
sin menores → sin personas → sin pisos → depto + edad → depto → todo el
registro. Las celdas de cada nivel las calcula `base.preparar_base`.

Dos formas de imputar el tratamiento a un hogar de la encuesta:
  - Hot-Deck (`sortear_donante`, `hotdeck_celda`): el T de un donante
    sorteado en su celda.
  - Imputación fraccional (`probabilidad_celda`): la proporción de T = 1
    entre los donantes de su celda, que es lo que da la FHDI con pesos
    calibrados (`docs/metodologia/METODOLOGIA_FHDI.md`, regla R4).
"""
from __future__ import annotations

import numpy as np


def _sortear_en_celda(celda_receptor: np.ndarray, celda_donante: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Posición de un donante al azar de la misma celda; -1 si no hay."""
    orden = np.argsort(celda_donante, kind="stable")
    cd = celda_donante[orden]
    inicio = np.searchsorted(cd, celda_receptor, side="left")
    n = np.searchsorted(cd, celda_receptor, side="right") - inicio
    pos = np.full(len(celda_receptor), -1, dtype=int)
    con = n > 0
    pos[con] = orden[inicio[con] + (rng.random(con.sum()) * n[con]).astype(int)]
    return pos


def sortear_donante(celdas_receptor: np.ndarray, celdas_donante: np.ndarray, rng: np.random.Generator,
                    devolver_nivel: bool = False):
    """Posición (en el registro) de un donante sorteado al azar.

    `celdas_*` traen una columna por nivel de la cadena de respaldos, de la
    celda más fina a la más gruesa (`base.celdas_por_nivel`); un vector es
    un solo nivel. Cada nivel solo se usa para los receptores sin donante
    en el anterior y, si ninguno tiene donantes, se sortea en todo el
    registro. Con `devolver_nivel=True` devuelve también el índice del
    nivel usado por receptor (el número de niveles = todo el registro).

    Si todos los receptores tienen donante en su celda, el sorteo es el
    mismo que sin respaldos (no se consumen más números aleatorios)."""
    r, d = np.asarray(celdas_receptor), np.asarray(celdas_donante)
    if r.ndim == 1:
        r, d = r[:, None], d[:, None]
    pos = np.full(len(r), -1, dtype=int)
    nivel = np.full(len(r), r.shape[1], dtype=int)
    for k in range(r.shape[1]):
        falta = np.flatnonzero(pos < 0)
        if not len(falta):
            break
        p = _sortear_en_celda(r[falta, k], d[:, k], rng)
        pos[falta] = p
        nivel[falta[p >= 0]] = k
    falta = pos < 0
    pos[falta] = rng.integers(0, len(d), falta.sum())
    return (pos, nivel) if devolver_nivel else pos


def hotdeck_celda(celdas_receptor: np.ndarray, celdas_donante: np.ndarray, t_donante: np.ndarray,
                  rng: np.random.Generator) -> np.ndarray:
    """T de un donante de la misma celda (o de la de respaldo)."""
    return np.asarray(t_donante)[sortear_donante(celdas_receptor, celdas_donante, rng)]


def probabilidad_celda(celdas_receptor: np.ndarray, celdas_donante: np.ndarray, t_donante: np.ndarray) -> np.ndarray:
    """Proporción de T = 1 entre los donantes de la celda de cada receptor,
    en el primer nivel de la cadena con donantes (todo el registro si
    ninguno tiene). Es la imputación fraccional (FEFI) del tratamiento."""
    r, d = np.asarray(celdas_receptor), np.asarray(celdas_donante)
    if r.ndim == 1:
        r, d = r[:, None], d[:, None]
    t = np.asarray(t_donante, dtype=float)
    p = np.full(len(r), np.nan)
    for k in range(r.shape[1]):
        falta = np.isnan(p)
        if not falta.any():
            break
        tam = int(max(d[:, k].max(), r[:, k].max())) + 1
        n = np.bincount(d[:, k], minlength=tam)
        suma = np.bincount(d[:, k], t, minlength=tam)
        rk = r[falta, k]
        con = n[rk] > 0
        idx = np.flatnonzero(falta)[con]
        p[idx] = suma[rk[con]] / n[rk[con]]
    p[np.isnan(p)] = t.mean()
    return p
