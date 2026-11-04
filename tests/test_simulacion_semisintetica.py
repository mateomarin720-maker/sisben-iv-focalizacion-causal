"""Pruebas del generador y los estimadores simples de la simulación
semisintética (`src/simulacion/`), con datos sintéticos (no requieren la base real)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.simulacion.asignacion import asignar
from src.simulacion.base import diseno_x, efecto_verdadero
from src.simulacion.escenarios import ESCENARIOS
from src.simulacion.estimadores import diferencia_medias, discontinuidad, regresion_efectos_fijos
from src.simulacion.evaluacion import resumir
from src.simulacion.vinculo import hotdeck_celda, sortear_donante


def _base(n: int = 4000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    celda = rng.integers(0, 20, n)
    b = pd.DataFrame({
        "geo_zona_urbana": rng.integers(0, 2, n), "jefe_mujer": rng.integers(0, 2, n),
        "viv_paredes": rng.choice([1, 1, 1, 5], n).astype(float), "hotdeck_celda_cat": celda,
        "logit_p_celda": np.linspace(-1, 1, 20)[celda], "u": rng.normal(0, 1, n),
    })
    b["y0"] = 0.3 * celda / 20 + rng.normal(0, 0.1, n)
    b["tau"] = efecto_verdadero(b)
    return b


def test_efecto_verdadero_por_tipo_de_hogar():
    b = pd.DataFrame({"geo_zona_urbana": [1, 0, 1], "jefe_mujer": [0, 0, 1], "viv_paredes": [1.0, 1.0, 5.0]})
    np.testing.assert_allclose(efecto_verdadero(b), [0.10, 0.15, 0.11])


def test_asignar_conserva_la_tasa_de_tratados_en_todos_los_escenarios():
    b = _base()
    pbar = (1 / (1 + np.exp(-b["logit_p_celda"]))).mean()
    for esc in ESCENARIOS.values():
        t = asignar(b, esc, np.random.default_rng(1))[0]
        assert abs(t.mean() - pbar) < 0.03


def test_hotdeck_solo_sortea_donantes_de_la_misma_celda():
    rng = np.random.default_rng(0)
    celda_don = np.repeat([0, 1, 2], 50)
    t_don = (celda_don == 1).astype(int)  # solo la celda 1 está tratada
    t = hotdeck_celda(np.array([0, 1, 2, 1]), celda_don, t_don, rng)
    assert t.tolist() == [0, 1, 0, 1]


def test_regresion_recupera_el_efecto_con_t_verdadero_y_se_anula_con_hotdeck():
    b = _base(n=20_000)
    rng = np.random.default_rng(3)
    t = asignar(b, ESCENARIOS["confusion_observada"], rng)[0]
    y = b["y0"].to_numpy() + b["tau"].to_numpy() * t
    Z = diseno_x(b)
    celda = b["hotdeck_celda_cat"].to_numpy()
    est, lo, hi = regresion_efectos_fijos(y, t, Z, celda)
    assert lo <= b["tau"].mean() <= hi
    t_hd = hotdeck_celda(celda, celda, t, rng)  # donante de la misma celda, sin relación con Y
    est_hd, _, _ = regresion_efectos_fijos(y, t_hd, Z, celda)
    assert abs(est_hd) < 0.01


def test_resumir_mide_sesgo_y_cobertura():
    r = pd.DataFrame({"rep": [0, 1], "escenario": "a", "vinculo": "oraculo", "estimador": "e",
                      "outcome": "log_ingreso", "efecto_verdadero": [0.1, 0.1], "estimacion": [0.12, 0.08], "ic_lo": [0.05, 0.02],
                      "ic_hi": [0.15, 0.09], "pehe": None, "concordancia_t": 100.0})
    out = resumir(r).iloc[0]
    assert abs(out["sesgo"]) < 1e-12
    assert abs(out["cobertura"] - 0.5) < 1e-12
    assert abs(out["rmse"] - 0.02) < 1e-12
    assert abs(out["mcse_cobertura"] - 0.5 / np.sqrt(2)) < 1e-12
    assert abs(out["mcse_sesgo"] - np.std([0.02, -0.02], ddof=1) / np.sqrt(2)) < 1e-12


def test_regla_corte_asigna_por_puntaje_con_la_tasa_del_sisben():
    b = _base()
    t, puntaje, corte = asignar(b, ESCENARIOS["regla_corte"], np.random.default_rng(0))
    assert ((puntaje >= corte) == (t == 1)).all()
    pbar = (1 / (1 + np.exp(-b["logit_p_celda"]))).mean()
    assert abs(t.mean() - pbar) < 0.01


def test_discontinuidad_recupera_el_salto_aunque_haya_confusion():
    rng = np.random.default_rng(1)
    n = 40_000
    u = rng.normal(0, 1, n)
    puntaje = u + rng.normal(0, 0.5, n)
    t = (puntaje >= 0).astype(float)
    y = -0.8 * u + 0.1 * t + rng.normal(0, 0.3, n)  # confusión fuerte por U
    est, lo, hi = discontinuidad(y, puntaje, 0.0, 0.5)
    assert lo <= 0.1 <= hi
    assert diferencia_medias(y, t.astype(int))[0] < -0.5


def test_sortear_donante_devuelve_posiciones_de_la_misma_celda():
    celda_don = np.array([2, 0, 1, 2, 0])
    pos = sortear_donante(np.array([0, 1, 2] * 20), celda_don, np.random.default_rng(0))
    assert (celda_don[pos] == np.array([0, 1, 2] * 20)).all()


def test_efectos_fijos_con_codigos_de_celda_pequenos():
    """`cat.codes` da int8 con menos de 128 celdas (int16 con las 993
    reales): restarlo del tamaño de la muestra se desbordaba (error del
    2026-11-04, con 2.000 hogares y 81 celdas; con las celdas reales
    pasaba por encima de 32.767 hogares)."""
    rng = np.random.default_rng(3)
    n = 2000
    celda = rng.integers(0, 81, n).astype(np.int8)
    t = rng.integers(0, 2, n)
    y = 0.2 * t + rng.normal(0, 1, n)
    est, lo, hi = regresion_efectos_fijos(y, t, np.ones((n, 1)), celda)
    assert lo < 0.2 < hi


def test_preparar_base_deja_la_celda_en_int64():
    from src.simulacion.base import preparar_base
    from tests.test_simulacion_equivalencia import hogares_sinteticos

    hogares, p_t = hogares_sinteticos(n=500)
    assert preparar_base(hogares, p_t)["hotdeck_celda_cat"].dtype == np.int64
