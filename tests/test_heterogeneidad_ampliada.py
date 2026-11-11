"""Heterogeneidad ampliada del efecto (`src/validacion/heterogeneidad_ampliada.py`)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.validacion import heterogeneidad_ampliada as ha


def _base(n: int = 4000, semilla: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(semilla)
    b = pd.DataFrame({
        "geo_zona_urbana": rng.integers(0, 2, n), "jefe_mujer": rng.integers(0, 2, n),
        "viv_paredes": rng.integers(1, 4, n), "bajo_logro_educativo_jefe": rng.integers(0, 2, n).astype(float),
        "sin_cotizacion_pension_jefe": rng.integers(0, 2, n).astype(float),
        "hog_num_personas": rng.integers(1, 9, n).astype(float),
        "depto": rng.choice(["05", "08", "11", "76"], n),
    })
    hogares = pd.DataFrame({"jefe_edad": rng.integers(18, 90, n).astype(str),
                            "viv_pisos": rng.choice(list("1234567"), n)})
    return ha.modificadores(b, hogares), hogares


def test_modificadores_con_los_codigos_de_la_geih():
    b, hogares = _base()
    assert b["het_piso_tierra"].tolist() == (hogares["viv_pisos"] == "1").astype(float).tolist()  # P4020: 1 = tierra
    assert b["het_jefe_mayor"].tolist() == (hogares["jefe_edad"].astype(int) >= 60).astype(float).tolist()


@pytest.mark.parametrize("nivel", ha.NIVELES)
def test_efecto_con_la_media_del_generador_y_mas_variacion(nivel):
    b, _ = _base()
    tau = ha.efecto_por_nivel(b, nivel)
    assert tau.mean() == pytest.approx(ha.TAU_MEDIA, abs=0.003)
    assert tau.std() == pytest.approx(ha.TAU_DESVIACION, abs=0.004)  # más del doble que el generador base (0,028)
    assert tau.min() >= ha.TAU_PISO


def test_el_efecto_depende_de_los_modificadores_nuevos():
    b, _ = _base()
    otra = b.copy()
    otra["het_bajo_logro"] = 1 - otra["het_bajo_logro"]
    assert not np.allclose(ha.forma(b, "ampliado"), ha.forma(otra, "ampliado"))
    # el complejo agrega diferencias entre departamentos: dentro de un mismo perfil, cambia con el depto
    perfil = b.iloc[[0, 0]].copy()
    perfil["depto"] = ["05", "76"]
    assert ha.forma(perfil, "complejo")[0] != ha.forma(perfil, "complejo")[1]
    assert ha.forma(perfil, "ampliado")[0] == ha.forma(perfil, "ampliado")[1]


def test_el_bosque_ve_todos_los_modificadores():
    b, _ = _base()
    assert set(ha.X_POR_NIVEL["ampliado"]) <= set(b.columns) | {"geo_zona_urbana", "jefe_mujer", "viv_paredes"}
    assert "het_depto" in ha.X_POR_NIVEL["complejo"]


def test_nivel_desconocido():
    b, _ = _base(50)
    with pytest.raises(ValueError):
        ha.forma(b, "basico")


@pytest.mark.parametrize("x_cols", [None, ha.X_POR_NIVEL["complejo"]])
def test_el_bosque_controla_la_celda_con_cualquier_x(x_cols):
    """La celda confunde (sube T y Y a la vez); con X de 3 o de 9 columnas,
    el ATE del bosque debe quedar cerca del verdadero. Con el codificador
    armado para 3 X, la celda quedaba fuera y el ATE salía negativo."""
    from src.validacion import reglas_focalizacion as rf
    b, _ = _base(6000, semilla=1)
    rng = np.random.default_rng(2)
    b["hotdeck_celda_cat"] = rng.integers(0, 12, len(b)).astype(float)
    p = 0.15 + 0.06 * b["hotdeck_celda_cat"].to_numpy()
    t = (rng.random(len(b)) < p).astype(int)
    y = -3 * p + 0.1 * t + rng.normal(0, 0.1, len(b))
    ate = float(rf.ajustar_bosque(b, y, t, x_cols).ate(b[x_cols or rf.estimacion5().X_COLS].to_numpy(float)))
    assert ate == pytest.approx(0.1, abs=0.03)
