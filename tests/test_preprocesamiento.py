"""Pruebas sobre las transformaciones críticas de `src/3_preprocesamiento.py`
(construcción del outcome IPM-GEIH reducido).

Usan un mes real (enero 2024) ya procesado en `data/1_processed/geih/`,
no datos sintéticos — lo que valida es que la transformación real se
comporta como debe, no una aproximación idealizada. Requieren que
`data/1_processed/geih/2024/01/` exista (restaurar desde Azure si falta:
`poetry run python -m src.utils.restaurar_banco_datos_azure`).

`3_preprocesamiento.py` empieza con un dígito (convención del proyecto
para las etapas numeradas del pipeline) y no se puede `import`ar
directamente — se carga con `importlib` por ruta de archivo.

Uso:
    poetry run pytest tests/
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("preprocesamiento", ROOT / "src" / "3_preprocesamiento.py")
preprocesamiento = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(preprocesamiento)

LLAVE = ["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"]
pytestmark = pytest.mark.skipif(
    not (preprocesamiento.GEIH_DIR / "01" / "hogar_vivienda.parquet").exists(),
    reason="Falta data/1_processed/geih/2024/01/ — restaurar el banco de datos desde Azure",
)


@pytest.fixture(scope="module")
def df_enero():
    df = preprocesamiento._outcome_mes("01")
    assert df is not None
    return df


def test_una_fila_por_hogar(df_enero):
    assert df_enero.duplicated(subset=LLAVE).sum() == 0


def test_privaciones_sin_faltantes_y_binarias(df_enero):
    for c in preprocesamiento.PRIVACIONES:
        assert df_enero[c].isna().sum() == 0, f"{c} tiene faltantes sin tratar"
        assert set(df_enero[c].unique()) <= {0, 1}, f"{c} no es binaria"


def test_score_es_la_suma_de_privaciones(df_enero):
    suma = df_enero[preprocesamiento.PRIVACIONES].sum(axis=1)
    assert (df_enero["ipm_geih_score"] == suma).all()
    assert df_enero["ipm_geih_score"].between(0, len(preprocesamiento.PRIVACIONES)).all()


def test_umbrales_k_son_monotonos(df_enero):
    """Un umbral más exigente (K más alto) nunca puede clasificar como
    pobre a más hogares que uno menos exigente — si esto falla, el score
    o los cortes están mal construidos."""
    for k in (1, 2, 3):
        col_a, col_b = f"POBRE_GEIH_K{k}", f"POBRE_GEIH_K{k + 1}"
        assert (df_enero[col_a] >= df_enero[col_b]).all(), f"{col_a} debe dominar a {col_b}"


def test_pobre_geih_coincide_con_el_umbral_adoptado(df_enero):
    columna_k_adoptada = f"POBRE_GEIH_K{preprocesamiento.K_POBRE}"
    assert (df_enero["POBRE_GEIH"] == df_enero[columna_k_adoptada]).all()


def test_sin_cotizacion_pension_no_genera_faltantes(df_enero):
    """Un jefe que no aparece en el módulo `ocupados` (no ocupado) debe
    quedar privado (1) en este indicador, no NaN — ver docstring del
    script sobre por qué se combina informalidad con desempleo/inactividad."""
    assert df_enero["sin_cotizacion_pension_jefe"].isin([0, 1]).all()
