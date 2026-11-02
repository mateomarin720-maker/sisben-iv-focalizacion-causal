"""Pruebas sobre las transformaciones críticas de
`src/3b_preprocesamiento_monetario.py` (outcome de pobreza monetaria).

Usan un mes real (enero 2024) ya procesado en `data/1_processed/geih/`,
igual que `tests/test_preprocesamiento.py`. `_ingreso_mes` se prueba
contra datos reales; `_clasificar_pobreza` se prueba con un DataFrame
sintético pequeño, porque es lógica pura (no necesita I/O) y así se
pueden probar casos de borde exactos (ingreso justo en la línea, ingreso
0, zona rural vs. urbana).

Uso:
    poetry run pytest tests/
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("preprocesamiento_monetario", ROOT / "src" / "3b_preprocesamiento_monetario.py")
pm = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pm)

LLAVE = ["llave_directorio", "llave_secuencia_p", "llave_hogar"]
pytestmark = pytest.mark.skipif(
    not (pm.GEIH_DIR / "01" / "ocupados.parquet").exists(),
    reason="Falta data/1_processed/geih/2024/01/ — restaurar el banco de datos desde Azure",
)


@pytest.fixture(scope="module")
def ingreso_enero():
    df = pm._ingreso_mes("01")
    assert df is not None
    return df


def test_una_fila_por_hogar(ingreso_enero):
    assert ingreso_enero.duplicated(subset=LLAVE).sum() == 0


def test_ingreso_no_negativo(ingreso_enero):
    assert (ingreso_enero["ingreso_hogar_mensual"] >= 0).all()


def test_ingreso_sin_faltantes(ingreso_enero):
    assert ingreso_enero["ingreso_hogar_mensual"].isna().sum() == 0


def test_clasificar_pobreza_casos_de_borde():
    """DataFrame sintético: un hogar justo en la línea urbana, uno muy por
    debajo (extremo), uno muy por encima (no pobre), y uno rural con el
    mismo ingreso que uno urbano — deben clasificar distinto porque la
    línea rural es más baja."""
    df = pd.DataFrame({
        "ingreso_hogar_mensual": [510_161 * 2, 50_000 * 2, 5_000_000 * 2, 400_000 * 2],
        "hog_num_personas": ["2", "2", "2", "2"],
        "geo_zona": ["1", "1", "1", "2"],
    })
    out = pm._clasificar_pobreza(df)

    assert out.loc[0, "POBRE_MONETARIO"] == 0, "ingreso == línea no es pobre (desigualdad estricta <)"
    assert out.loc[1, "POBRE_EXTREMO_MONETARIO"] == 1, "muy por debajo de la línea extrema debe ser pobre extremo"
    assert out.loc[2, "POBRE_MONETARIO"] == 0
    assert out.loc[2, "brecha_pobreza_monetaria"] == 0, "la brecha de un hogar no pobre debe ser 0, no negativa"
    # Mismo ingreso per cápita (400.000) en zona urbana (línea 510.161, pobre)
    # vs. rural (línea 291.998, no pobre) — la clasificación debe diferir.
    df_urbano = pd.DataFrame({"ingreso_hogar_mensual": [800_000], "hog_num_personas": ["2"], "geo_zona": ["1"]})
    df_rural = pd.DataFrame({"ingreso_hogar_mensual": [800_000], "hog_num_personas": ["2"], "geo_zona": ["2"]})
    assert pm._clasificar_pobreza(df_urbano).loc[0, "POBRE_MONETARIO"] == 1
    assert pm._clasificar_pobreza(df_rural).loc[0, "POBRE_MONETARIO"] == 0


def test_brecha_entre_0_y_1_para_pobres():
    df = pd.DataFrame({
        "ingreso_hogar_mensual": [0, 510_161 * 2 - 2],
        "hog_num_personas": ["2", "2"],
        "geo_zona": ["1", "1"],
    })
    out = pm._clasificar_pobreza(df)
    assert out["brecha_pobreza_monetaria"].between(0, 1).all()
    assert out.loc[0, "brecha_pobreza_monetaria"] == 1.0, "ingreso 0 implica brecha máxima (100%)"


def test_ingreso_percapita_nan_sin_personas():
    df = pd.DataFrame({"ingreso_hogar_mensual": [500_000], "hog_num_personas": ["0"], "geo_zona": ["1"]})
    out = pm._clasificar_pobreza(df)
    assert out["ingreso_percapita"].isna().all()
