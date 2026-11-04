"""Reglas compartidas entre fuentes (`src/utils/variables_canonicas.py`):
llaves de hogar, jefe de hogar y ciclo de vida."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import _tramo_edad
from src.utils.variables_canonicas import CODIGOS_CICLO, JEFE, edad_a_ciclo, es_jefe, normalizar_llave


@pytest.mark.parametrize("entrada, esperado", [
    (["7893865.0", "7893865", 7893865, " 7893865 "], "7893865"),
    (["01", "1", "1.0", 1, 1.0], "1"),
])
def test_normalizar_llave_iguala_formatos_distintos(entrada, esperado):
    """Los mismos identificadores llegan con formatos distintos según el
    módulo y el mes; sin normalizar, el cruce falla sin dar error."""
    assert normalizar_llave(pd.Series(entrada, dtype=object)).tolist() == [esperado] * len(entrada)


def test_normalizar_llave_deja_faltante_lo_no_numerico():
    out = normalizar_llave(pd.Series(["abc", None, "", "nan"], dtype=object))
    assert out.isna().all()


def test_cruce_con_llaves_normalizadas_no_pierde_hogares():
    """El caso del 2026-11-02: `mes` "01" en la muestra y "1" en la base
    oficial."""
    a = pd.DataFrame({"mes": ["01", "02"], "x": [1, 2]})
    b = pd.DataFrame({"mes": ["1", "2"], "y": [3, 4]})
    assert len(a.merge(b, on="mes")) == 0
    a["mes"], b["mes"] = normalizar_llave(a["mes"]), normalizar_llave(b["mes"])
    assert len(a.merge(b, on="mes")) == 2


@pytest.mark.parametrize("fuente, columna", [("geih", "P6050"), ("sisben", "PER003"), ("sdp", "tip_parentesco")])
def test_es_jefe_usa_la_regla_de_cada_fuente(fuente, columna):
    assert JEFE[fuente] == (columna, "1")
    df = pd.DataFrame({columna: ["1", "01", "1.0", "2", "13", None]})
    assert es_jefe(df, fuente).fillna(False).tolist() == [True, True, True, False, False, False]


@pytest.mark.parametrize("edad, codigo", [
    (12, "3"), (17, "3"), (18, "4"), (28, "4"), (29, "5"), (59, "5"), (60, "6"), (99, "6"),
])
def test_edad_a_ciclo_respeta_los_cortes_de_per002(edad, codigo):
    """3=12-17, 4=18-28, 5=29-59, 6=60+ (código de PER002)."""
    assert edad_a_ciclo(pd.Series([edad])).iloc[0] == codigo


def test_edad_a_ciclo_deja_faltante_lo_invalido():
    out = edad_a_ciclo(pd.Series([np.nan, "abc", 250]))
    assert out.isna().all()


def test_hotdeck_y_sisben_usan_los_mismos_tramos():
    """La celda solo empata si GEIH (años) y el Sisbén (código PER002) caen
    en el mismo tramo."""
    edades = pd.Series(range(12, 100))
    geih = _tramo_edad(pd.DataFrame({"jefe_edad": edades}), edad_en_codigos=False)
    sisben = _tramo_edad(pd.DataFrame({"jefe_edad": edad_a_ciclo(edades)}), edad_en_codigos=True)
    assert (geih == sisben).all()
    assert set(sisben) == {f"ciclo{c}" for c in CODIGOS_CICLO}
