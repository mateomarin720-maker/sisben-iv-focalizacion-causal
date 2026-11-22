"""Validación interna: ¿qué tan exacto es el enlace por celda?

En la GEIH no se conoce el grupo del Sisbén de ningún hogar, pero en el
Sisbén sí. Se esconde el grupo de una parte de los hogares del Sisbén
(20 %), se imputa con el resto como donantes y se compara con el grupo
verdadero. Mide lo bien que la celda predice el grupo; no mide si la GEIH
y el Sisbén registran igual las variables de la celda (eso lo cubre la
homologación).

Métodos:
  sorteo   el Hot-Deck: un donante al azar de la celda
  moda     el grupo más frecuente de la celda (techo del acierto por hogar)
  fhdi     M donantes con pesos calibrados
  fefi     π de la celda (todos los donantes)

Medidas:
  acierto_ab, acierto_grupo  proporción de hogares con el grupo correcto. En
      los métodos fraccionales es el acierto esperado, Σ_j w_j·1[g_j = g].
  brier_ab   error cuadrático de la probabilidad de A/B (en el sorteo y la
      moda la probabilidad es 0 o 1)
  calibracion_ab  diferencia absoluta media entre la probabilidad
      asignada y la proporción observada de A/B, en diez tramos de
      probabilidad (ponderada por hogares)
  error_depto_ab  diferencia absoluta media, en puntos, entre la
      proporción de A/B imputada y la verdadera por departamento

Todas las medidas se ponderan por el `fex` de los hogares de prueba, y
los donantes por el suyo (desde el 2026-11-21): el Sisbén nacional de
ANDA es una muestra expandible.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.emparejamiento.fhdi import reglas

FRACCION_PRUEBA = 0.2


def _medidas(nombre: str, q: np.ndarray, verdad: np.ndarray, depto: np.ndarray, w: np.ndarray) -> dict:
    """q: probabilidad por grupo asignada a cada hogar (n × 4); w: su `fex`."""
    p_ab = q[:, list(reglas.ELEGIBLE)].sum(axis=1)
    t = np.isin(verdad, reglas.ELEGIBLE).astype(float)
    tramo = np.minimum((p_ab * 10).astype(int), 9)
    d = pd.DataFrame({"tramo": tramo, "d": depto, "w": w, "wp": w * p_ab, "wt": w * t})
    cal = d.groupby("tramo")[["w", "wp", "wt"]].sum()
    por_depto = d.groupby("d")[["w", "wp", "wt"]].sum()
    return dict(metodo=nombre,
                acierto_ab=float(np.average(t * p_ab + (1 - t) * (1 - p_ab), weights=w)),
                acierto_grupo=float(np.average(q[np.arange(len(q)), verdad], weights=w)),
                brier_ab=float(np.average((p_ab - t) ** 2, weights=w)),
                calibracion_ab=float(np.average(((cal["wp"] - cal["wt"]) / cal["w"]).abs(), weights=cal["w"])),
                error_depto_ab=float(((por_depto["wp"] - por_depto["wt"]) / por_depto["w"]).abs().mean() * 100))


def validar(sisben: pd.DataFrame, m: int = reglas.M_DONANTES, seed: int = 7) -> pd.DataFrame:
    """sisben: hogares con CELDA_COLUMNAS y Grupo (A-D)."""
    rng = np.random.default_rng(seed)
    prueba = rng.random(len(sisben)) < FRACCION_PRUEBA
    rec = sisben[prueba].reset_index(drop=True)
    don = sisben[~prueba].reset_index(drop=True)
    verdad = reglas._codigo_grupo(rec)
    depto = rec["geo_depto"].astype(str).str.zfill(2).to_numpy()
    w = reglas.peso_donante(rec)
    n = len(rec)

    pi, nivel = reglas.probabilidades(rec, don, receptor_en_codigos=True)
    exp = reglas.donantes_fraccionales(rec, don, m=m, seed=seed, receptor_en_codigos=True)
    q_fhdi = reglas.probabilidad_por_receptor(exp, n)
    # Sorteo: un donante de la celda con probabilidad π (equivale al Hot-Deck).
    u = rng.random(n)[:, None]
    sorteo = (u > np.cumsum(pi, axis=1)).sum(axis=1).clip(0, 3)
    moda = pi.argmax(axis=1)
    uno = np.eye(len(reglas.GRUPOS))

    filas = [_medidas("sorteo (Hot-Deck)", uno[sorteo], verdad, depto, w),
             _medidas("moda de la celda", uno[moda], verdad, depto, w),
             _medidas(f"fhdi (M = {m})", q_fhdi, verdad, depto, w),
             _medidas("fefi", pi, verdad, depto, w)]
    w_don = reglas.peso_donante(don)
    sin_celda = np.bincount(reglas._codigo_grupo(don), weights=w_don, minlength=4) / w_don.sum()
    filas.append(_medidas("sin celda (todo el registro)", np.tile(sin_celda, (n, 1)), verdad, depto, w))
    out = pd.DataFrame(filas)
    out["hogares_prueba"] = n
    out["celda_exacta_pct"] = float(np.average(nivel == "celda_exacta", weights=w) * 100)
    out["fhdi_calibrado_pct"] = float(exp.groupby("receptor")["calibrado"].first().mean() * 100)
    return out
