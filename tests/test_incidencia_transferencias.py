"""Incidencia de las ayudas declaradas en la GEIH (`incidencia_transferencias.py`)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.estimacion import incidencia_transferencias as it


def _personas() -> pd.DataFrame:
    filas = [
        dict(HOGAR="1", ORDEN="1", P6050="1", P750S2="1", P750S2A1="960000", P1661S1=None, P1661S2=None, P1661S3="1", FEX_C18="120"),
        dict(HOGAR="1", ORDEN="2", P6050="10", P750S2="1", P750S2A1="1200000", P1661S1="1", P1661S2=None, P1661S3=None, FEX_C18="120"),
        dict(HOGAR="2", ORDEN="1", P6050="1", P750S2="1", P750S2A1="98", P1661S1=None, P1661S2="1", P1661S3=None, FEX_C18="240"),
        dict(HOGAR="3", ORDEN="1", P6050="1", P750S2=None, P750S2A1=None, P1661S1=None, P1661S2=None, P1661S3=None, FEX_C18="240"),
    ]
    return pd.DataFrame(filas).assign(DIRECTORIO="7", SECUENCIA_P="1", mes="03")


def test_el_monto_no_cuenta_no_sabe_ni_empleados_domesticos():
    h = it.por_hogar(_personas()).set_index("HOGAR")
    assert h.loc["1", "ayuda_mes"] == 80_000  # sin el empleado doméstico
    assert h.loc["2", "ayuda_mes"] == 0 and bool(h.loc["2", "alguna_ayuda"]) and bool(h.loc["2", "jovenes_en_accion"])
    assert not h.loc["3", "alguna_ayuda"]
    assert bool(h.loc["1", "colombia_mayor"]) and not h.loc["3", "colombia_mayor"]


def test_beneficiarios_directos_en_un_mes_promedio():
    b = it.beneficiarios_directos(_personas())
    assert b["colombia_mayor"] == 10 and b["jovenes_en_accion"] == 20 and b["alguna_ayuda"] == 40


def test_ingreso_sin_ayuda_nunca_negativo():
    np.testing.assert_allclose(it.ingreso_sin_ayuda([300.0, 50.0], [300.0, 400.0], [3.0, 2.0]), [200.0, 0.0])


def _tabla():
    return pd.DataFrame({
        "h": [10.0, 20, 30, 40], "n": [40.0, 60, 90, 80], "pobre_sin_ayuda": [True, True, False, False],
        "alguna_ayuda": [True, False, True, False], "familias_en_accion": [True, False, False, False],
        "jovenes_en_accion": [False] * 4, "colombia_mayor": [False, False, True, False],
    })


def test_tabla_de_programas_en_hogares_y_personas():
    directos = dict(alguna_ayuda=5.0, familias_en_accion=1.0, jovenes_en_accion=0.0, colombia_mayor=2.0)
    f = it.tabla_programas(_tabla().assign(jovenes_en_accion=[False, True, False, False]), directos).set_index("programa").loc["alguna_ayuda"]
    assert (f["hogares_receptores"], f["personas_en_receptores"]) == (40, 130)
    assert (f["hogares_pobres_receptores"], f["personas_pobres_receptores"]) == (10, 40)
    assert (f["hogares_pobres_sin_programa"], f["personas_pobres_sin_programa"]) == (20, 60)
    assert (f["hogares_no_pobres_receptores"], f["personas_no_pobres_receptores"]) == (30, 90)
    assert f["pct_receptores_pobres"] == 25 and f["pct_pobres_cubiertos"] == pytest.approx(100 / 3)


def test_pobreza_con_y_sin_ayuda():
    y_con, y_sin, linea = np.array([120.0, 80, 200]), np.array([90.0, 60, 200]), np.full(3, 100.0)
    h, n = np.array([1.0, 2, 3]), np.array([4.0, 8, 9])
    f = it.tabla_pobreza(y_con, y_sin, linea, h, n, "pobreza")
    assert (f["hogares_con_ayuda"], f["hogares_sin_ayuda"], f["hogares_sobre_linea_por_ayuda"]) == (2, 3, 1)
    assert (f["personas_con_ayuda"], f["personas_sin_ayuda"], f["personas_sobre_linea_por_ayuda"]) == (8, 12, 4)
    assert f["brecha_sin_ayuda"] == pytest.approx(100 * (1 * 0.1 + 2 * 0.4) / 6)


def test_quintiles_reparten_el_peso():
    h = np.ones(10)
    q = it.quintiles(np.arange(10.0)[::-1], h)
    assert q.tolist() == [4, 4, 3, 3, 2, 2, 1, 1, 0, 0]
