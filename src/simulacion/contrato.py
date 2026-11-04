"""Contrato de datos del módulo de simulación: qué columnas exige cada
tabla y con qué códigos.

Regla del tutor (2026-11-03): los nombres estandarizados de GEIH y Sisbén
no se cambian ni se hacen configurables. Este módulo **exige** las
columnas canónicas y valida que estén; no renombra, no completa y no
adivina. Quien tenga otros nombres los convierte en su propia
armonización, como hace este proyecto en `src/armonizacion/`.

Los dominios salen del diccionario oficial de la GEIH 2024, de la ficha
del Sisbén IV y de las homologaciones ya verificadas
(`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`). Los códigos se
comparan como texto, igual que en `data/2_models/`: un código "1.0" no
es "1" (el error de agosto de 2024, CLAUDE.md) y se rechaza.

Diseño: `docs/metodologia/DISENO_MODULO_SIMULACION.md`, sección 3.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

LINEAS = {"13_ciudades": 566_228.0, "otras_cabeceras": 434_323.0, "rural": 291_998.0}  # DANE 2024, pesos


class ErrorContrato(ValueError):
    """La tabla no cumple el contrato de columnas canónicas."""


@dataclass(frozen=True)
class Columna:
    descripcion: str
    validar: Callable[[pd.Series], pd.Series]  # True en los valores válidos (sin faltantes)


def _codigos(*validos: str) -> Callable[[pd.Series], pd.Series]:
    return lambda s: s.astype("string").isin(validos)


def _entero(minimo: int, maximo: int | None = None) -> Callable[[pd.Series], pd.Series]:
    def f(s: pd.Series) -> pd.Series:
        texto = s.astype("string")
        num = pd.to_numeric(texto.where(texto.str.fullmatch(r"\d+")), errors="coerce")
        ok = num >= minimo
        return (ok & (num <= maximo)) if maximo is not None else ok
    return f


def _real(minimo: float, estricto: bool = False) -> Callable[[pd.Series], pd.Series]:
    def f(s: pd.Series) -> pd.Series:
        num = pd.to_numeric(s, errors="coerce")
        return num > minimo if estricto else num >= minimo
    return f


HOGARES = {
    "geo_depto": Columna("código DANE de 2 dígitos", lambda s: s.astype("string").str.fullmatch(r"\d{2}")),
    "geo_zona": Columna("1 urbano, 2 rural (CLASE)", _codigos("1", "2")),
    "jefe_sexo": Columna("1 hombre, 2 mujer (P3271)", _codigos("1", "2")),
    "jefe_edad": Columna("edad del jefe en años", _entero(0, 120)),
    "viv_cuartos": Columna("cuartos en total (P5000)", _entero(1)),
    "viv_pisos": Columna("material de pisos, códigos GEIH de P4020 (1-7)", _codigos(*"1234567")),
    "viv_paredes": Columna("material de paredes, códigos GEIH de P4010 (1-9)", _codigos(*"123456789")),
    "ingreso_percapita": Columna("ingreso per cápita de la unidad de gasto, pesos", _real(0)),
    "dominio_pm": Columna("dominio de la línea de pobreza", _codigos(*LINEAS)),
}
HOGARES_OPCIONALES = {
    "fex": Columna("factor de expansión", _real(0, estricto=True)),
    "Grupo": Columna("grupo del Sisbén observado (A-D)", _codigos(*"ABCD")),
    "vinculo": Columna("cómo se obtuvo Grupo: llave o hotdeck", _codigos("llave", "hotdeck")),
}
REGISTRO = {
    "geo_depto": HOGARES["geo_depto"],
    "jefe_edad": Columna("código de ciclo de vida de PER002 (3-6)", _codigos(*"3456")),
    "viv_cuartos": Columna("cuartos en total (VIV009)", _entero(1)),
    "viv_pisos": Columna("material de pisos, códigos del Sisbén (1-6; orden inverso al de la GEIH)",
                         _codigos(*"123456")),
    "Grupo": Columna("grupo del Sisbén (A-D)", _codigos(*"ABCD")),
    "Clasificacion": Columna("subgrupo del Sisbén; nulo en hogares sin clasificar", lambda s: s.notna()),
}
ROLES = {"hogares": (HOGARES, HOGARES_OPCIONALES), "registro": (REGISTRO, {})}


def columnas(rol: str) -> list[str]:
    """Columnas obligatorias del rol, en el orden del contrato."""
    return list(ROLES[rol][0])


def validar(tabla: pd.DataFrame, rol: str) -> pd.DataFrame:
    """Revisa que `tabla` cumpla el contrato del rol (`hogares` o
    `registro`) y la devuelve sin cambios. Falla con `ErrorContrato`
    nombrando cada columna faltante o con códigos fuera de dominio.

    En el registro solo se revisan los hogares clasificados
    (`Clasificacion` no nula): los demás no entran a P(T | celda)."""
    if rol not in ROLES:
        raise ValueError(f"Rol desconocido: {rol!r}; use uno de {sorted(ROLES)}")
    obligatorias, opcionales = ROLES[rol]
    problemas = []
    duplicadas = tabla.columns[tabla.columns.duplicated()].unique().tolist()
    if duplicadas:
        problemas.append(f"columnas duplicadas: {duplicadas}")
    faltan = [c for c in obligatorias if c not in tabla.columns]
    if faltan:
        problemas.append("faltan columnas obligatorias: " + ", ".join(f"{c} ({obligatorias[c].descripcion})"
                                                                      for c in faltan))
    if problemas:
        raise ErrorContrato(f"Tabla '{rol}' no cumple el contrato: " + "; ".join(problemas))

    filas = tabla
    if rol == "registro":
        filas = tabla[tabla["Clasificacion"].notna()]
    for nombre, col in {**obligatorias, **{k: v for k, v in opcionales.items() if k in tabla.columns}}.items():
        ok = col.validar(filas[nombre]).fillna(False).astype(bool)
        if not ok.all():
            malos = filas.loc[~ok, nombre]
            ejemplos = malos.astype("string").fillna("<faltante>").value_counts().head(5).to_dict()
            problemas.append(f"{nombre}: {len(malos):,} valores fuera de dominio ({col.descripcion}); "
                             f"ejemplos {ejemplos}")
    if problemas:
        raise ErrorContrato(f"Tabla '{rol}' no cumple el contrato: " + "; ".join(problemas))
    return tabla
