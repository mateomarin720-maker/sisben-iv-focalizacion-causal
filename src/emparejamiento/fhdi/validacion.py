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
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.emparejamiento.fhdi import reglas

FRACCION_PRUEBA = 0.2


def _medidas(nombre: str, q: np.ndarray, verdad: np.ndarray, depto: np.ndarray) -> dict:
    """q: probabilidad por grupo asignada a cada hogar (n × 4)."""
    p_ab = q[:, list(reglas.ELEGIBLE)].sum(axis=1)
    t = np.isin(verdad, reglas.ELEGIBLE).astype(float)
    tramo = np.minimum((p_ab * 10).astype(int), 9)
    cal = pd.DataFrame({"tramo": tramo, "p": p_ab, "t": t}).groupby("tramo").agg(n=("t", "size"), p=("p", "mean"),
                                                                                 t=("t", "mean"))
    por_depto = pd.DataFrame({"d": depto, "p": p_ab, "t": t}).groupby("d")[["p", "t"]].mean()
    return dict(metodo=nombre,
                acierto_ab=float(np.mean(t * p_ab + (1 - t) * (1 - p_ab))),
                acierto_grupo=float(np.mean(q[np.arange(len(q)), verdad])),
                brier_ab=float(np.mean((p_ab - t) ** 2)),
                calibracion_ab=float(np.average((cal["p"] - cal["t"]).abs(), weights=cal["n"])),
                error_depto_ab=float((por_depto["p"] - por_depto["t"]).abs().mean() * 100))


def validar(sisben: pd.DataFrame, m: int = reglas.M_DONANTES, seed: int = 7) -> pd.DataFrame:
    """sisben: hogares con CELDA_COLUMNAS y Grupo (A-D)."""
    rng = np.random.default_rng(seed)
    prueba = rng.random(len(sisben)) < FRACCION_PRUEBA
    rec = sisben[prueba].reset_index(drop=True)
    don = sisben[~prueba].reset_index(drop=True)
    verdad = reglas._codigo_grupo(rec)
    depto = rec["geo_depto"].astype(str).str.zfill(2).to_numpy()
    n = len(rec)

    pi, nivel = reglas.probabilidades(rec, don, receptor_en_codigos=True)
    exp = reglas.donantes_fraccionales(rec, don, m=m, seed=seed, receptor_en_codigos=True)
    q_fhdi = reglas.probabilidad_por_receptor(exp, n)
    # Sorteo: un donante de la celda con probabilidad π (equivale al Hot-Deck).
    u = rng.random(n)[:, None]
    sorteo = (u > np.cumsum(pi, axis=1)).sum(axis=1).clip(0, 3)
    moda = pi.argmax(axis=1)
    uno = np.eye(len(reglas.GRUPOS))

    filas = [_medidas("sorteo (Hot-Deck)", uno[sorteo], verdad, depto),
             _medidas("moda de la celda", uno[moda], verdad, depto),
             _medidas(f"fhdi (M = {m})", q_fhdi, verdad, depto),
             _medidas("fefi", pi, verdad, depto)]
    sin_celda = np.bincount(reglas._codigo_grupo(don), minlength=4) / len(don)
    filas.append(_medidas("sin celda (todo el registro)", np.tile(sin_celda, (n, 1)), verdad, depto))
    out = pd.DataFrame(filas)
    out["hogares_prueba"] = n
    out["celda_exacta_pct"] = float(np.mean(nivel == "celda_exacta") * 100)
    out["fhdi_calibrado_pct"] = float(exp.groupby("receptor")["calibrado"].first().mean() * 100)
    return out
