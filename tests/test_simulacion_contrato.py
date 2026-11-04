"""Contrato de columnas canónicas del módulo de simulación
(`src/simulacion/contrato.py`): exige y valida, no traduce."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.simulacion import contrato
from src.simulacion.contrato import ErrorContrato
from tests.test_simulacion_equivalencia import hogares_sinteticos


def _registro(n: int = 50) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "geo_depto": rng.choice(["05", "11"], n), "jefe_edad": rng.choice(list("3456"), n),
        "viv_cuartos": rng.integers(1, 5, n).astype(str), "viv_pisos": rng.choice(list("123456"), n),
        "Grupo": rng.choice(list("ABCD"), n), "Clasificacion": rng.choice(["A1", "B2", "C3"], n),
    })


def test_tablas_validas_pasan_sin_cambios():
    hogares, _ = hogares_sinteticos(n=300)
    assert contrato.validar(hogares, "hogares") is hogares
    reg = _registro()
    assert contrato.validar(reg, "registro") is reg


@pytest.mark.parametrize("columna", contrato.columnas("hogares"))
def test_falta_una_columna_y_el_error_la_nombra(columna):
    hogares, _ = hogares_sinteticos(n=300)
    with pytest.raises(ErrorContrato, match=columna):
        contrato.validar(hogares.drop(columns=columna), "hogares")


def test_no_acepta_nombres_distintos_aunque_el_contenido_sea_el_mismo():
    """La regla del tutor: no hay alias ni mapeo de nombres."""
    hogares, _ = hogares_sinteticos(n=300)
    with pytest.raises(ErrorContrato, match="jefe_sexo"):
        contrato.validar(hogares.rename(columns={"jefe_sexo": "sexo_jefe"}), "hogares")
    assert not hasattr(contrato, "COLUMNAS")


@pytest.mark.parametrize("columna,valor", [
    ("geo_zona", "3"), ("jefe_sexo", "0"), ("viv_pisos", "9"), ("viv_paredes", "0"),
    ("dominio_pm", "urbano"), ("geo_depto", "5"), ("jefe_edad", "-1"), ("viv_cuartos", "0"),
    ("ingreso_percapita", -1.0), ("geo_zona", "1.0"),  # "1.0": el error de agosto (.DTA)
])
def test_codigo_fuera_de_dominio(columna, valor):
    hogares, _ = hogares_sinteticos(n=300)
    hogares[columna] = hogares[columna].astype(object)
    hogares.loc[5, columna] = valor
    with pytest.raises(ErrorContrato, match=columna):
        contrato.validar(hogares, "hogares")


def test_faltantes_se_rechazan():
    hogares, _ = hogares_sinteticos(n=300)
    hogares.loc[0, "viv_pisos"] = None
    with pytest.raises(ErrorContrato, match="viv_pisos"):
        contrato.validar(hogares, "hogares")


def test_pisos_del_sisben_en_la_tabla_de_hogares_se_detecta_si_sale_del_dominio_geih():
    """El registro admite el código 6 (otro) en pisos; los hogares GEIH van
    de 1 a 7. Un 0 o un 8 no existen en ninguna de las dos fuentes."""
    reg = _registro()
    reg.loc[0, "viv_pisos"] = "7"  # existe en GEIH, no en el Sisbén
    with pytest.raises(ErrorContrato, match="viv_pisos"):
        contrato.validar(reg, "registro")


def test_registro_solo_revisa_hogares_clasificados():
    reg = _registro()
    reg.loc[0, ["jefe_edad", "Grupo", "Clasificacion"]] = [None, None, None]
    contrato.validar(reg, "registro")
    reg.loc[1, "jefe_edad"] = "25"  # años en vez de código de ciclo de vida
    with pytest.raises(ErrorContrato, match="jefe_edad"):
        contrato.validar(reg, "registro")


def test_opcionales_se_validan_solo_si_estan():
    hogares, _ = hogares_sinteticos(n=300)
    contrato.validar(hogares.assign(Grupo="A", vinculo="llave", fex=10.0), "hogares")
    with pytest.raises(ErrorContrato, match="vinculo"):
        contrato.validar(hogares.assign(vinculo="exacto"), "hogares")


def test_columnas_duplicadas():
    hogares, _ = hogares_sinteticos(n=300)
    dup = pd.concat([hogares, hogares[["geo_zona"]]], axis=1)
    with pytest.raises(ErrorContrato, match="duplicadas"):
        contrato.validar(dup, "hogares")


def test_preparar_base_valida_el_contrato():
    from src.simulacion.base import preparar_base

    hogares, p_t = hogares_sinteticos(n=300)
    with pytest.raises(ErrorContrato):
        preparar_base(hogares.drop(columns="dominio_pm"), p_t)
