"""Cotas de Fréchet-Manski (`src/estimacion/cotas_frechet_manski.py`): el
resultado de identificación central del proyecto con datos reales."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.estimacion.cotas_frechet_manski import ate_agregado, cotas_frechet, cotas_por_celda


@pytest.mark.parametrize("p_y", [0.0, 1.0])
@pytest.mark.parametrize("p_t", [0.1, 0.5, 0.9])
def test_sin_variacion_en_y_la_cota_es_cero(p_y, p_t):
    """Si todos (o nadie) en la celda son pobres, el efecto es 0 sin
    importar la dependencia entre T e Y."""
    c = cotas_frechet([p_y], [p_t]).iloc[0]
    assert c["cate_lo"] == pytest.approx(0, abs=1e-12) and c["cate_hi"] == pytest.approx(0, abs=1e-12)


def test_marginales_en_medio_dan_la_cota_maxima():
    c = cotas_frechet([0.5], [0.5]).iloc[0]
    assert (c["cate_lo"], c["cate_hi"]) == (-1.0, 1.0)


def test_p_t_extrema_no_define_el_contraste():
    c = cotas_frechet([0.3, 0.3], [0.0, 1.0])
    assert c[["cate_lo", "cate_hi"]].isna().all().all()


@pytest.mark.parametrize("seed", range(5))
def test_la_cota_contiene_el_efecto_de_toda_conjunta_compatible(seed):
    """Para cualquier distribución conjunta de (T, Y) con esas marginales,
    el efecto verdadero cae dentro de la cota, y los extremos se alcanzan
    (la cota es la más angosta posible)."""
    rng = np.random.default_rng(seed)
    n = 2000
    p_y, p_t = rng.uniform(0.01, 0.99, n), rng.uniform(0.01, 0.99, n)
    lo11, hi11 = np.maximum(0, p_y + p_t - 1), np.minimum(p_y, p_t)
    p11 = lo11 + rng.uniform(0, 1, n) * (hi11 - lo11)  # P(Y=1, T=1) factible
    cate = p11 / p_t - (p_y - p11) / (1 - p_t)
    c = cotas_frechet(p_y, p_t)
    assert (c["cate_lo"] <= cate + 1e-12).all() and (cate <= c["cate_hi"] + 1e-12).all()
    assert (c["cate_lo"] >= -1 - 1e-12).all() and (c["cate_hi"] <= 1 + 1e-12).all()
    assert ((c["cate_hi"] - c["cate_lo"]) <= 2 + 1e-12).all()
    np.testing.assert_allclose(c["cate_lo"], lo11 / p_t - (p_y - lo11) / (1 - p_t))
    np.testing.assert_allclose(c["cate_hi"], hi11 / p_t - (p_y - hi11) / (1 - p_t))


def test_ate_agregado_pondera_por_peso_de_la_celda():
    df = pd.DataFrame({"peso_fex": [3.0, 1.0], "cate_lo": [-0.4, 0.0], "cate_hi": [0.2, 0.6]})
    lo, hi = ate_agregado(df)
    assert lo == pytest.approx(-0.3) and hi == pytest.approx(0.3)


def test_cotas_por_celda_usa_cada_fuente_por_separado():
    """P(Y|celda) sale de GEIH ponderada por `fex`; P(T|celda) sale del
    Sisbén sin ponderar. Sin Hot-Deck de por medio."""
    geih = pd.DataFrame({"geo_depto": "05", "jefe_edad": [40, 40, 40], "viv_cuartos": 3, "viv_pisos": "4",
                         "fex": [1.0, 1.0, 2.0], "POBRE_GEIH": [1, 0, 0]})
    sisben = pd.DataFrame({"geo_depto": "05", "jefe_edad": ["5"] * 4, "viv_cuartos": 3, "viv_pisos": "1",
                           "Grupo": ["A", "B", "C", "D"], "Clasificacion": "x"})
    df = cotas_por_celda(geih, sisben, "POBRE_GEIH")
    assert len(df) == 1
    fila = df.iloc[0]
    assert fila["celda"] == "05|ciclo5|3omascuartos|acabado"
    assert fila["p_y"] == pytest.approx(0.25) and fila["p_t"] == pytest.approx(0.5)
    esperado = cotas_frechet([0.25], [0.5]).iloc[0]
    assert fila["cate_lo"] == pytest.approx(esperado["cate_lo"]) and fila["cate_hi"] == pytest.approx(esperado["cate_hi"])
