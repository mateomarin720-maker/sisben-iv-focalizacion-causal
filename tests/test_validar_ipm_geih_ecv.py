"""Validación del IPM-GEIH contra la ECV (`src/validacion/validar_ipm_geih_ecv.py`)
y reglas compartidas del proxy (`src/indicadores/ipm_proxy.py`). Datos
sintéticos: no requiere la ECV ni la base del IPM."""
from __future__ import annotations

import pandas as pd
import pytest

from src.indicadores.ipm_proxy import PRIVACIONES, privaciones
from src.validacion.validar_ipm_geih_ecv import codigo, concordancia, proxy_hogares


def _hogar(**cambios) -> dict:
    base = dict(P6160="1", P6090="1", P3042="5", P6920="1", P6008=4, P5010=2, P4030S3="1", P4030S5="1",
                inasistencia_escolar_menores=False)
    return {**base, **cambios}


def test_privaciones_un_hogar_sin_y_otro_con_todas():
    df = pd.DataFrame([_hogar(),
                       _hogar(P6160="2", P6090="2", P3042="3", P6920="2", P6008=7, P5010=2, P4030S3="2",
                              P4030S5="2", inasistencia_escolar_menores=True)])
    r = privaciones(df)
    assert r.loc[0, "ipm_geih_score"] == 0 and r.loc[0, "POBRE_GEIH"] == 0
    assert r.loc[1, "ipm_geih_score"] == len(PRIVACIONES) and r.loc[1, "POBRE_GEIH"] == 1


def test_nivel_99_no_cuenta_como_bajo_logro():
    r = privaciones(pd.DataFrame([_hogar(P3042="99"), _hogar(P3042="1")]))
    assert r["bajo_logro_educativo_jefe"].tolist() == [0, 1]


def test_jefe_no_ocupado_cuenta_sin_cotizacion_como_en_la_geih():
    """En la GEIH el jefe que no está ocupado no aparece en el módulo de
    ocupados y queda privado. En la ECV P6920 viene vacío: debe dar lo mismo."""
    hog = ["DIRECTORIO", "SECUENCIA_P"]
    personas = pd.DataFrame({"DIRECTORIO": [1, 2], "SECUENCIA_P": [1, 1], "es_jefe": [True, True],
                             "P6040": [40, 40], "asiste": codigo(pd.Series([None, None])),
                             "P6160": codigo(pd.Series([1, 1])), "P6090": codigo(pd.Series([1, 1])),
                             "P3042": codigo(pd.Series([5, 5])), "P6920": codigo(pd.Series([1, None]))})
    hogares = pd.DataFrame({"DIRECTORIO": [1, 2], "SECUENCIA_P": [1, 1], "P6008": [2, 2], "P5010": [1, 1],
                            "P4030S3": ["1", "1"], "P4030S5": ["1", "1"]})
    r = proxy_hogares(personas, hogares, hog).set_index("DIRECTORIO")
    assert r.loc[1, "sin_cotizacion_pension_jefe"] == 0
    assert r.loc[2, "sin_cotizacion_pension_jefe"] == 1


def test_concordancia_ponderada():
    proxy = pd.Series([1, 1, 0, 0])
    oficial = pd.Series([1, 0, 1, 0])
    w = pd.Series([1.0, 1.0, 1.0, 1.0])
    c = concordancia(proxy, oficial, w)
    assert c["concordancia"] == pytest.approx(0.5)
    assert c["sensibilidad"] == pytest.approx(0.5) and c["especificidad"] == pytest.approx(0.5)
    assert c["kappa"] == pytest.approx(0.0)
    c = concordancia(proxy, oficial, pd.Series([3.0, 1.0, 1.0, 3.0]))
    assert c["concordancia"] == pytest.approx(0.75)
    assert c["sensibilidad"] == pytest.approx(0.75)
