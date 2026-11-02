"""Pruebas de la reconstrucción de pobreza monetaria
(`src/indicadores/pobreza_monetaria_geih.py`) y de su paso a la muestra de
estimación (`src/3b_preprocesamiento_monetario.py`).

Las reglas (unidad de gasto, líneas por dominio, trabajadores sin
remuneración, arriendo imputado) se prueban con DataFrames sintéticos;
la lectura de un mes real solo si existe `data/1_processed/geih/2024/01/`.

Uso:
    poetry run pytest tests/
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.indicadores import pobreza_monetaria_geih as pm

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("preprocesamiento_monetario", ROOT / "src" / "3b_preprocesamiento_monetario.py")
b3 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b3)


def _personas(**cols) -> pd.DataFrame:
    """Un hogar urbano de 13 ciudades con los valores por defecto en 0."""
    n = len(next(iter(cols.values())))
    base = dict(
        mes=["01"] * n, DIRECTORIO=["1"] * n, SECUENCIA_P=["1"] * n, HOGAR=["1"] * n,
        ORDEN=[str(i + 1) for i in range(n)], P6050=["1"] + ["3"] * (n - 1), P6430=[pd.NA] * n,
        ocupado=[False] * n, inglabo=[np.nan] * n, p6750=[np.nan] * n, p550_mes=[np.nan] * n,
        CLASE=["1"] * n, AREA=["11"] * n, DPTO=["11"] * n, peso=[1.0] * n,
        P5090=["3"] * n, arriendo_imputado=[0.0] * n,
    )
    for c in ("lab_no_incluido", "primas_anuales", "especie_indep", "trabajo_no_ocupado",
              "no_laboral", "cesantias", "accidentes"):
        base[c] = [0.0] * n
    base.update(cols)
    p = pd.DataFrame(base)
    p["dominio"] = pm._dominio(p)
    return p


def test_dominio_y_lineas():
    p = pd.DataFrame({"CLASE": ["1", "1", "2", "1"], "AREA": ["11", "15", pd.NA, "5"]})
    assert pm._dominio(p).tolist() == ["13_ciudades", "otras_cabeceras", "rural", "13_ciudades"]


def test_servicio_domestico_fuera_de_la_unidad_de_gasto():
    p = _personas(P6050=["1", "10"], ocupado=[True, True], P6430=["1", "3"],
                  inglabo=[1_200_000.0, 1_300_000.0])
    per = pm._construir(p, pm._imputar_laboral(p))
    assert len(per) == 1 and per["personas_ug"].iloc[0] == 1
    assert per["ingreso_pc_ug"].iloc[0] == 1_200_000.0


def test_jornalero_es_remunerado_y_familiar_no():
    p = _personas(ocupado=[True, True, True], P6430=["7", "6", "8"], inglabo=[np.nan, np.nan, np.nan])
    assert pm._remunerado(p).tolist() == [True, False, False]


def test_hotdeck_solo_imputa_faltantes_remunerados():
    p = _personas(P3271=["1"] * 4, P6040=["30"] * 4, P3042=["5"] * 4, RAMA2D_R4=["47"] * 4,
                  ocupado=[True] * 4, P6430=["1", "1", "6", "1"],
                  inglabo=[900_000.0, np.nan, np.nan, 0.0])
    lab = pm._imputar_laboral(p)
    assert lab.tolist() == [900_000.0, 900_000.0, 0.0, 900_000.0]


def test_arriendo_imputado_solo_a_propietarios_y_usufructo():
    p = _personas(P6050=["1"], P5090=["1"], arriendo_imputado=[600_000.0])
    assert pm._construir(p, pm._imputar_laboral(p))["ingreso_pc_ug"].iloc[0] == 600_000.0
    p = _personas(P6050=["1"], P5090=["3"], arriendo_imputado=[600_000.0])
    assert pm._construir(p, pm._imputar_laboral(p))["ingreso_pc_ug"].iloc[0] == 0.0


def test_linea_por_dominio_y_brecha():
    ingreso = 500_000.0  # pobre en 13 ciudades (566.228), no pobre en otras cabeceras (434.323)
    for area, pobre in (("11", 1), ("15", 0)):
        p = _personas(P6050=["1"], AREA=[area], no_laboral=[ingreso])
        p["dominio"] = pm._dominio(p)
        per = pm._construir(p, pm._imputar_laboral(p))
        assert per["POBRE_MONETARIA"].iloc[0] == pobre
        assert 0 <= per["BRECHA_PM"].iloc[0] < 1


def test_gini_extremos():
    assert pm._gini(np.array([5.0, 5.0, 5.0]), np.ones(3)) == pytest.approx(0.0)
    assert pm._gini(np.array([0.0, 0.0, 0.0, 10.0]), np.ones(4)) == pytest.approx(0.75)


def test_pegar_pobreza_uno_a_uno():
    base = pd.DataFrame({"llave_directorio": ["1", "2"], "llave_secuencia_p": ["1", "1"],
                         "llave_hogar": ["1", "1"], "mes": ["01", "01"]})
    pob = pd.DataFrame({"DIRECTORIO": ["1", "2"], "SECUENCIA_P": ["1", "1"], "HOGAR": ["1", "1"],
                        "mes": ["01", "01"], "ingreso_pc_ug": [100.0, 900_000.0], "personas_ug": [2, 3],
                        "dominio_pm": ["rural", "rural"], "POBRE_MONETARIA": [1, 0], "POBRE_EXTREMA": [1, 0],
                        "BRECHA_PM": [0.9, 0.0], "BRECHA_PE": [0.9, 0.0]})
    out = b3.pegar_pobreza(base, pob)
    assert out["POBRE_MONETARIO"].tolist() == [1, 0]
    assert out["ingreso_percapita"].tolist() == [100.0, 900_000.0]


@pytest.mark.skipif(not (pm.GEIH_DIR / "01" / "ocupados.parquet").exists(),
                    reason="Falta data/1_processed/geih/2024/01/ — restaurar el banco de datos desde Azure")
def test_mes_real_una_fila_por_persona():
    p = pm._personas_mes("01")
    assert not p.duplicated(subset=["DIRECTORIO", "SECUENCIA_P", "HOGAR", "ORDEN"]).any()
    assert p["ocupado"].dtype == bool
    assert (p[["lab_no_incluido", "primas_anuales", "no_laboral"]] >= 0).all().all()
