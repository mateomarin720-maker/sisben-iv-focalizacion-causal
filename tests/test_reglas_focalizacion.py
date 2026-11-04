"""Reglas de focalización (P3/OE3, `src/validacion/reglas_focalizacion.py`)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.validacion import reglas_focalizacion as rf

LP = 500_000.0


def _hogares(ingresos, tau=0.1, peso=1.0) -> pd.DataFrame:
    ingresos = np.asarray(ingresos, float)
    return pd.DataFrame({"y0": np.log1p(ingresos), "lp": LP, "tau": tau, "peso": peso})


def test_brecha_y_despues():
    assert rf.brecha(np.array([0.0, 0.5, 1.0, 2.0])).tolist() == [1.0, 0.5, 0.0, 0.0]
    y0 = np.log1p(np.array([0.0, 250_000.0]))
    prop = rf.despues(y0, np.array([0.1, 0.1]), np.array([LP, LP]), "proporcional")
    fijo = rf.despues(y0, np.array([0.1, 0.1]), np.array([LP, LP]), "monto_fijo")
    assert prop[0] == pytest.approx((np.e ** 0.1 - 1) / LP)  # sin ingreso, el efecto proporcional casi no da nada
    assert prop[1] == pytest.approx(np.expm1(np.log1p(250_000) + 0.1) / LP)
    assert fijo.tolist() == pytest.approx([0.1, 0.6])  # la transferencia fija suma 0,1 líneas a todos


def test_reduccion_esperada_sin_incertidumbre_es_la_reduccion_verdadera():
    d = _hogares([100_000, 450_000, 900_000])
    for tipo in rf.TIPOS_EFECTO:
        verdad = rf.brecha(rf.ingreso_relativo(d["y0"], LP)) - rf.brecha(rf.despues(d["y0"], 0.1, LP, tipo))
        esperada = rf.reduccion_esperada(d["y0"].to_numpy(), np.zeros(5), np.full(3, 0.1), np.full(3, LP), tipo)
        np.testing.assert_allclose(esperada, verdad)


def test_reduccion_esperada_promedia_sobre_los_residuos():
    media, residuos = np.log1p(np.array([400_000.0])), np.array([-0.5, 0.0, 0.5])
    esperada = rf.reduccion_esperada(media, residuos, np.array([0.1]), np.array([LP]), "monto_fijo")
    y = media + residuos
    a_mano = np.mean(rf.brecha(rf.ingreso_relativo(y, LP)) - rf.brecha(rf.ingreso_relativo(y, LP) + 0.1))
    assert esperada[0] == pytest.approx(a_mano)


def test_elegir_trata_a_los_k_de_mayor_puntaje():
    t = rf.elegir(np.array([0.1, 0.9, 0.5, 0.7]), 2, np.random.default_rng(0))
    assert t.tolist() == [0, 1, 0, 1]
    empates = [rf.elegir(np.zeros(4), 1, np.random.default_rng(s)).argmax() for s in range(30)]
    assert len(set(empates)) > 1  # los empates se rompen al azar, no por posición


def test_metricas_de_focalizacion_sobre_personas():
    """Dos pobres (ingreso 100 y 300 mil) y dos no pobres; se trata a un
    pobre y a un no pobre. Pesos distintos para comprobar la ponderación."""
    d = _hogares([100_000, 300_000, 800_000, 900_000], tau=0.1)
    d["peso"] = [1.0, 3.0, 1.0, 1.0]
    m = rf.metricas(d, np.array([1, 0, 1, 0]), "monto_fijo")
    assert m["error_inclusion"] == pytest.approx(1 / 2)  # tratados: 1 pobre (peso 1) y 1 no pobre (peso 1)
    assert m["error_exclusion"] == pytest.approx(3 / 4)  # pobres: peso 4, sin tratar el de peso 3
    assert m["fgt0_post"] == pytest.approx(4 / 6)
    assert m["fgt1_post"] == pytest.approx((1 * 0.7 + 3 * 0.4) / 6)


def test_la_regla_ideal_reduce_la_brecha_al_menos_como_cualquier_otra():
    rng = np.random.default_rng(1)
    d = _hogares(rng.lognormal(13, 0.8, 2000), tau=rng.uniform(0.05, 0.2, 2000))
    for tipo in rf.TIPOS_EFECTO:
        x0 = rf.ingreso_relativo(d["y0"].to_numpy(), LP)
        ideal = rf.brecha(x0) - rf.brecha(rf.despues(d["y0"].to_numpy(), d["tau"].to_numpy(), LP, tipo))
        k = 600
        fgt1_ideal = rf.metricas(d, rf.elegir(ideal, k, rng), tipo)["fgt1_post"]
        for _ in range(20):
            otra = rf.metricas(d, rf.elegir(rng.random(len(d)), k, rng), tipo)["fgt1_post"]
            assert fgt1_ideal <= otra + 1e-12
        por_ingreso = rf.metricas(d, rf.elegir(-x0, k, rng), tipo)["fgt1_post"]
        assert fgt1_ideal <= por_ingreso + 1e-12


def test_el_proxy_de_medios_no_usa_el_ingreso():
    assert not {"y0", "ingreso_percapita", "POBRE_MONETARIO"} & set(rf.PMT_CATEGORICAS + rf.PMT_NUMERICAS)
