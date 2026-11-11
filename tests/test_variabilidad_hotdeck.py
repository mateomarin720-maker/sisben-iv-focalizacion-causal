"""Variabilidad de la imputación del Hot-Deck (`src/diagnostico/variabilidad_hotdeck.py`)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.diagnostico import variabilidad_hotdeck as v


def test_concordancia_por_hogar_es_el_estimador_insesgado():
    """Hogar 1: siempre A (concordancia 1). Hogar 2: A,A,B,B: pares
    coincidentes (2·1 + 2·1) / (4·3) = 1/3."""
    sorteos = np.array([[0, 0, 0, 0], [0, 0, 1, 1]], dtype=np.int8)
    np.testing.assert_allclose(v.concordancia_por_hogar(sorteos, 4), [1.0, 1 / 3])


def test_concordancia_converge_a_la_teorica_de_la_celda():
    """Con sorteos de una celda con proporciones π, la concordancia
    empírica estima Σ π²."""
    rng = np.random.default_rng(0)
    pi = np.array([0.1, 0.3, 0.4, 0.2])
    sorteos = rng.choice(4, size=(3000, 50), p=pi).astype(np.int8)
    assert v.concordancia_por_hogar(sorteos, 4).mean() == pytest.approx((pi**2).sum(), abs=0.005)


def test_concordancia_teorica_por_celda():
    celda_d = pd.Series(["x", "x", "x", "x", "y", "y"])
    grupo_d = pd.Series(["A", "A", "B", "C", "D", "D"])
    teo = v.concordancia_teorica(pd.Series(["x", "y", "z"]), celda_d, grupo_d, ["A", "B", "C", "D"])
    assert teo.iloc[0] == pytest.approx(0.5**2 + 0.25**2 + 0.25**2)
    assert teo.iloc[1] == pytest.approx(1.0)
    assert np.isnan(teo.iloc[2])  # celda sin donantes


def test_por_celda_mide_cv_y_error_relativo():
    """Celda c1 con dos hogares de peso 1 y 3; en el sorteo 1 solo el
    primero es A/B (proporción 0,25) y en el 2 los dos (1,0)."""
    t = np.array([[1, 1], [0, 1]], dtype=float)
    res = v.por_celda(np.array(["c1", "c1"]), np.array([1.0, 3.0]), t, pd.Series({"c1": 0.5})).iloc[0]
    assert res["prop_ab_media"] == pytest.approx(0.625)
    assert res["prop_ab_sd"] == pytest.approx(np.std([0.25, 1.0], ddof=1))
    assert res["cv"] == pytest.approx(np.std([0.25, 1.0], ddof=1) / 0.625)
    assert res["error_relativo_medio"] == pytest.approx((0.25 + 0.5) / 2 / 0.5)


def test_contraste_placebo_es_mco_con_efectos_fijos():
    rng = np.random.default_rng(1)
    n, k = 2000, 15
    celda = rng.integers(0, k, n)
    t = rng.integers(0, 2, n).astype(float)
    y = 0.3 * t + np.linspace(-1, 1, k)[celda] + rng.normal(0, 0.5, n)
    b, se = v.contraste_placebo(y, t, celda)
    X = np.column_stack([t, np.eye(k)[celda]])
    assert b == pytest.approx(np.linalg.lstsq(X, y, rcond=None)[0][0])
    assert 0 < se < 0.05


def test_reglas_de_rubin():
    est, err = np.array([0.1, 0.2, 0.3]), np.array([0.1, 0.1, 0.1])
    r = v.reglas_de_rubin(est, err)
    assert r["estimacion"] == pytest.approx(0.2)
    assert r["var_dentro"] == pytest.approx(0.01)
    assert r["var_entre"] == pytest.approx(0.01)
    assert r["var_total"] == pytest.approx(0.01 + (1 + 1 / 3) * 0.01)
    assert r["fraccion_info_imputacion"] == pytest.approx((4 / 3 * 0.01) / (0.01 + 4 / 3 * 0.01))


def test_la_semilla_del_pipeline_va_primero():
    assert v.SEMILLAS[0] == 42 and len(set(v.SEMILLAS)) == v.N_SORTEOS
