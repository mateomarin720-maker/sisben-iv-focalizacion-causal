"""Cotas de Fréchet-Manski (`src/diagnostico/cotas_frechet_manski.py`): el
resultado de identificación central del proyecto con datos reales."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.diagnostico.cotas_frechet_manski import ate_agregado, cotas_con_supuestos, cotas_frechet, cotas_por_celda


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


# --------------------------------------------------------------------------
# Supuestos de monotonía (Manski y Pepper, 2000)
# --------------------------------------------------------------------------

def _poblaciones(n: int, seed: int, mts: bool, mtr: bool, dep: bool):
    """Poblaciones binarias al azar (P(T), P(Y(0)=1|T), P(Y(1)=1|T)) que
    cumplen los supuestos pedidos. Devuelve las marginales observables,
    P11 verdadero y el ATE verdadero."""
    rng = np.random.default_rng(seed)
    p_t = rng.uniform(0.05, 0.95, n)
    a1, a0 = rng.uniform(0, 1, n), rng.uniform(0, 1, n)  # P(Y(0)=1 | T=1), P(Y(0)=1 | T=0)
    b1, b0 = rng.uniform(0, 1, n), rng.uniform(0, 1, n)  # P(Y(1)=1 | T=1), P(Y(1)=1 | T=0)
    if mtr:  # Y(1) <= Y(0): el programa no aumenta la pobreza
        b1, b0 = b1 * a1, b0 * a0
    ok = np.ones(n, bool)
    if mts:  # los A/B son al menos tan pobres en ambos resultados potenciales
        ok &= (a1 >= a0) & (b1 >= b0)
    if dep:  # observado: los A/B son al menos tan pobres dentro de la celda
        ok &= b1 >= a0
    p_t, a1, a0, b1, b0 = (v[ok] for v in (p_t, a1, a0, b1, b0))
    p_y = p_t * b1 + (1 - p_t) * a0
    ate = p_t * (b1 - a1) + (1 - p_t) * (b0 - a0)
    return p_y, p_t, p_t * b1, ate


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("nombre, mts, mtr, dep", [
    ("ate_sin_supuestos", False, False, False),
    ("ate_mts", True, False, False),
    ("ate_mtr", False, True, False),
    ("ate_mts_mtr", True, True, False),
    ("ate_mts_mtr_dep_positiva", True, True, True),
])
def test_la_cota_contiene_el_ate_de_toda_poblacion_que_cumple_el_supuesto(seed, nombre, mts, mtr, dep):
    p_y, p_t, _, ate = _poblaciones(20_000, seed, mts, mtr, dep)
    assert len(ate) > 500
    c = cotas_con_supuestos(p_y, p_t)
    assert (c[f"{nombre}_lo"] <= ate + 1e-12).all()
    assert (ate <= c[f"{nombre}_hi"] + 1e-12).all()


def test_el_contraste_con_dependencia_positiva_no_es_negativo():
    p_y, p_t, p11, _ = _poblaciones(20_000, 0, False, False, True)
    c = cotas_con_supuestos(p_y, p_t)
    contraste = p11 / p_t - (p_y - p11) / (1 - p_t)
    assert (c["contraste_dep_positiva_lo"] >= -1e-12).all()
    assert (c["contraste_dep_positiva_lo"] <= contraste + 1e-12).all()
    assert (contraste <= c["contraste_dep_positiva_hi"] + 1e-12).all()


def test_cada_supuesto_angosta_o_deja_igual_la_cota():
    rng = np.random.default_rng(3)
    c = cotas_con_supuestos(rng.uniform(0.01, 0.99, 5000), rng.uniform(0.01, 0.99, 5000))
    anidadas = [("ate_sin_supuestos", "ate_mts"), ("ate_sin_supuestos", "ate_mtr"), ("ate_mts", "ate_mts_mtr"),
                ("ate_mtr", "ate_mts_mtr"), ("ate_mts_mtr", "ate_mts_mtr_dep_positiva"),
                ("contraste", "contraste_dep_positiva")]
    for amplia, estrecha in anidadas:
        assert (c[f"{estrecha}_lo"] >= c[f"{amplia}_lo"] - 1e-12).all()
        assert (c[f"{estrecha}_hi"] <= c[f"{amplia}_hi"] + 1e-12).all()
    assert (c["ate_mtr_hi"] == 0).all()


def test_el_contraste_coincide_con_las_cotas_de_frechet():
    rng = np.random.default_rng(4)
    p_y, p_t = rng.uniform(0.01, 0.99, 2000), rng.uniform(0.01, 0.99, 2000)
    c, f = cotas_con_supuestos(p_y, p_t), cotas_frechet(p_y, p_t)
    np.testing.assert_allclose(c["contraste_lo"], f["cate_lo"])
    np.testing.assert_allclose(c["contraste_hi"], f["cate_hi"])
