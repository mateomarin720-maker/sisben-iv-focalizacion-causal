"""Definiciones compartidas entre fuentes: una sola versión de cada regla.

Antes del 2026-11-04 estas reglas estaban copiadas en varios módulos (la
normalización de llaves en seis; los tramos de ciclo de vida en el
Hot-Deck y en el Sisbén de Bogotá). Una copia que cambia sin las demás no
da error: produce cruces vacíos o celdas que no coinciden entre fuentes.
Las pruebas están en `tests/test_variables_canonicas.py`.

- `normalizar_llave`: identificadores de hogar a texto de entero. Las
  llaves llegan con formatos distintos según el módulo y el mes ("01",
  "1", "1.0", " 1 ", 1); sin normalizar, los cruces fallan sin error (le
  pasó a `mes` en la base oficial de pobreza el 2026-11-02).
- `JEFE`: columna y valor que marcan al jefe de hogar en cada fuente.
- Ciclo de vida: el Sisbén nacional trae `PER002` como código de ciclo
  de vida (3=12-17, 4=18-28, 5=29-59, 6=60+, corroborado indirectamente,
  no contra la ficha de ANDA); GEIH y el Sisbén de Bogotá traen la edad
  en años y se llevan al mismo código con `edad_a_ciclo`.
- Menores de edad (`hog_num_menores`, en la celda del Hot-Deck desde el
  2026-11-14): en GEIH y en el Sisbén de Bogotá, personas con menos de
  `EDAD_MENOR` años; en el Sisbén nacional, `PER002` en `CICLOS_MENOR`
  (1, 2 y 3: hasta 17 años; el 4 ya es 18-28). `es_menor` aplica la regla.
"""
from __future__ import annotations

import pandas as pd

# Fuente -> (columna, valor) que marca al jefe de hogar.
JEFE = {
    "geih": ("P6050", "1"),
    "sisben": ("PER003", "1"),
    "sdp": ("tip_parentesco", "1"),
}

# Edad en años -> código de ciclo de vida de PER002. Intervalos cerrados a
# la derecha: (−1, 17] -> "3", (17, 28] -> "4", (28, 59] -> "5", (59, 200] -> "6".
CORTES_CICLO = [-1, 17, 28, 59, 200]
CODIGOS_CICLO = ["3", "4", "5", "6"]

# Menor de edad: menos de 18 años, o código de ciclo de vida 1, 2 o 3 (los
# ciclos 1 y 2 van antes del 3 = 12-17; comprobado con `PER016`, "estudia":
# el ciclo 1 casi no aplica, el 2 estudia el 96 %, el 3 el 87 %, el 4 el 23 %).
EDAD_MENOR = 18
CICLOS_MENOR = ["1", "2", "3"]


def normalizar_llave(serie: pd.Series) -> pd.Series:
    """Texto de entero: '7893865.0', ' 01 ', 1 -> '7893865', '1', '1'.
    Lo no numérico queda como faltante."""
    texto = serie.astype("string").str.strip() if serie.dtype == object or str(serie.dtype) == "string" else serie
    return pd.to_numeric(texto, errors="coerce").astype("Int64").astype("string")


def es_jefe(df: pd.DataFrame, fuente: str) -> pd.Series:
    """Máscara del jefe de hogar según la regla de la fuente."""
    columna, valor = JEFE[fuente]
    return normalizar_llave(df[columna]) == valor


def edad_a_ciclo(edad: pd.Series) -> pd.Series:
    """Edad en años -> código de ciclo de vida ("3".."6"), como `PER002`.
    Fuera de rango o no numérica queda como faltante."""
    anios = pd.to_numeric(edad, errors="coerce")
    return pd.cut(anios, bins=CORTES_CICLO, labels=CODIGOS_CICLO).astype("object")


def es_menor(edad: pd.Series, en_codigos: bool = False) -> pd.Series:
    """Máscara de menores de edad. `en_codigos=True` lee códigos de ciclo
    de vida (`PER002`); si no, años cumplidos. Faltantes: False."""
    if en_codigos:
        return normalizar_llave(edad).isin(CICLOS_MENOR).fillna(False).astype(bool)
    return (pd.to_numeric(edad, errors="coerce") < EDAD_MENOR).fillna(False).astype(bool)
