"""Sensibilidad de la evaluación semisintética
(`src/simulacion/sensibilidad_semisintetica.py`)."""
from __future__ import annotations

import numpy as np
import pytest

from src.simulacion.estimadores import discontinuidad, discontinuidad_difusa
from src.simulacion import sensibilidad_semisintetica as se


def _rd_difusa(seed: int, n: int = 60_000, efecto: float = 0.1, p0: float = 0.2, p1: float = 0.8):
    rng = np.random.default_rng(seed)
    u = rng.normal(0, 1, n)
    puntaje = u + rng.normal(0, 0.5, n)
    elegible = puntaje >= 0
    t = (rng.random(n) < np.where(elegible, p1, p0)).astype(int)
    y = -0.8 * u + efecto * t + rng.normal(0, 0.3, n)  # confusión fuerte por U
    return y, t, puntaje


def test_rd_difusa_es_insesgada_y_su_intervalo_cubre_al_95():
    """Sobre 100 semillas, no una: con una sola, un IC al 95 % deja fuera
    el valor verdadero 1 de cada 20 veces por diseño (le pasó a la semilla
    0). Medido en 200 semillas: media 0,1004, cobertura 0,96."""
    r = np.array([discontinuidad_difusa(*_rd_difusa(s, n=40_000), 0.0, 0.5) for s in range(100)])
    est, cubre = r[:, 0], (r[:, 1] <= 0.1) & (0.1 <= r[:, 2])
    assert abs(est.mean() - 0.1) < 3 * est.std(ddof=1) / np.sqrt(len(est))
    assert 0.90 <= cubre.mean() <= 0.99


def test_la_rd_nitida_sobre_la_participacion_difusa_se_atenua():
    """Ignorar que la participación es difusa (dividir solo por el salto en
    Y) subestima el efecto en el salto de participación (0,6)."""
    y, t, puntaje = _rd_difusa(0)
    nitida, _, _ = discontinuidad(y, puntaje, 0.0, 0.5)
    difusa, _, _ = discontinuidad_difusa(y, t, puntaje, 0.0, 0.5)
    assert nitida == pytest.approx(0.6 * difusa, abs=0.03)


def test_escenarios_de_sensibilidad():
    factores = {k: v.get("factor_tau", 1.0) for k, v in se.ESCENARIOS.items()}
    assert factores["efecto_nulo"] == 0.0
    assert {factores[f"confusion_observada_x{f}"] for f in (0.5, 1.0, 2.0)} == {0.5, 1.0, 2.0}
    assert se.ESCENARIOS["regla_corte_difusa"]["difusa"] and se.ESCENARIOS["regla_corte_difusa"]["corte"]
    assert se.PARTICIPACION[0] < se.PARTICIPACION[1]


def test_la_version_sin_regularizar_cambia_solo_la_regularizacion():
    modelo_y, modelo_t = se._modelos_poco_regularizados()
    assert modelo_y[-1].alpha == pytest.approx(1e-6)
    assert modelo_t[-1].C == pytest.approx(1e6)
