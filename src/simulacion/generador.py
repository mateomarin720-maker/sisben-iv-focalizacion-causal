"""Población sintética para el modo simulado (paso 6 del diseño).

Sortea hogares con las columnas canónicas a partir de los parámetros
agregados de `calibrar.py`, en el orden de su cadena de condicionales.
En cada paso usa el grupo más fino guardado y, si no está (tenía menos
hogares que el umbral), el del nivel superior. La tabla resultante cumple
el contrato del rol `hogares` y entra a la evaluación como si fuera una
encuesta real; P(T | celda) sale de los mismos parámetros.

Lo que no reproduce: la dependencia fina entre variables que la cadena no
modela (por ejemplo, entre cuartos e ingreso dentro de un mismo nivel de
pisos). Los resultados del modo simulado son simulados (*), igual que los
de la evaluación con hogares reales.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.simulacion.calibrar import PARAMETROS, SEP, TODOS, _nivel_pisos

EDAD_POR_CICLO = {"3": (12, 17), "4": (18, 28), "5": (29, 59), "6": (60, 95)}


def cargar_parametros(ruta: Path = PARAMETROS) -> dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _resolver(tabla: dict, candidatas: list[pd.Series]) -> pd.Series:
    """Para cada hogar, la primera clave candidata que está en `tabla`
    (de la más fina a la más gruesa)."""
    clave = pd.Series(pd.NA, index=candidatas[0].index, dtype="object")
    for c in candidatas:
        faltan = clave.isna()
        clave[faltan] = c[faltan].where(c[faltan].isin(tabla.keys()))
    if clave.isna().any():
        raise KeyError(f"Sin grupo en los parámetros para claves como {candidatas[0][clave.isna()].iloc[0]!r}")
    return clave


def _sortear(rng: np.random.Generator, tabla: dict, candidatas: list[pd.Series]) -> pd.Series:
    """Una categoría por hogar, con las proporciones de su grupo."""
    clave = _resolver(tabla, candidatas)
    out = pd.Series(index=clave.index, dtype="object")
    for k in sorted(clave.unique()):
        filas = clave.index[clave == k]
        categorias, p = zip(*tabla[k]["p"].items())
        p = np.asarray(p, float)
        out[filas] = rng.choice(np.asarray(categorias, dtype=object), size=len(filas), p=p / p.sum())
    return out


def _constante(n: int, valor: str = TODOS) -> pd.Series:
    return pd.Series(valor, index=range(n), dtype="object")


def generar(p: dict, n: int, semilla: int = 2026) -> tuple[pd.DataFrame, pd.Series]:
    """`n` hogares sintéticos con las columnas canónicas, y P(T | celda)
    indexada por la celda del Hot-Deck."""
    rng = np.random.default_rng(semilla)
    todos = _constante(n)
    depto = _sortear(rng, p["depto"], [todos])
    zona = _sortear(rng, p["zona"], [depto, todos])
    dz = depto + SEP + zona
    dominio = _sortear(rng, p["dominio"], [dz, zona])
    vivienda = _sortear(rng, p["vivienda"], [dz, depto, todos]).str.split(SEP, expand=True)
    ciclo, cuartos, pisos = vivienda[0], vivienda[1], vivienda[2]
    nivel = _nivel_pisos(pisos)
    paredes = _sortear(rng, p["paredes"], [zona + SEP + nivel, nivel, todos])
    mujer = _sortear(rng, p["mujer"], [zona + SEP + ciclo, todos]).astype(int)
    lo = ciclo.map(lambda c: EDAD_POR_CICLO[c][0]).to_numpy()
    hi = ciclo.map(lambda c: EDAD_POR_CICLO[c][1]).to_numpy()
    edad = rng.integers(lo, hi + 1)

    ing = p["ingreso"]
    grupo = _resolver(ing["grupos"], [dz + SEP + nivel, dz, depto, todos])
    g = pd.DataFrame([ing["grupos"][k] for k in grupo], index=grupo.index)
    precaria = (paredes != "1").astype(float)
    y = (g["media"] + ing["coef"]["mujer"] * mujer + ing["coef"]["precaria"] * precaria
         + g["sd"] * rng.standard_normal(n))
    ingreso = np.where(rng.random(n) < g["p_cero"], 0.0, np.expm1(y))

    hogares = pd.DataFrame({
        "geo_depto": depto.astype(str), "geo_zona": zona.astype(str), "jefe_sexo": np.where(mujer == 1, "2", "1"),
        "jefe_edad": edad.astype(str), "viv_cuartos": cuartos.astype(str), "viv_pisos": pisos.astype(str),
        "viv_paredes": paredes.astype(str), "ingreso_percapita": np.maximum(ingreso, 0.0),
        "dominio_pm": dominio.astype(str),
    })
    return hogares, pd.Series(p["p_t_celda"], dtype=float)
