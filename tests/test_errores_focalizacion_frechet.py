"""Errores de focalización con cotas de Fréchet (`src/diagnostico/errores_focalizacion_frechet.py`)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.diagnostico import errores_focalizacion_frechet as ef


def _poblacion(rng, n_celdas=30):
    """Hogares con pobreza y elegibilidad conjuntas (que ninguna fuente observa junta)."""
    filas = []
    for c in range(n_celdas):
        n = int(rng.integers(20, 200))
        pobre = (rng.random(n) < rng.random()).astype(float)
        rho = rng.uniform(-1, 1)  # dependencia arbitraria dentro de la celda
        z = rho * (pobre - pobre.mean()) + rng.normal(0, 0.5, n)
        elegible = (z > np.quantile(z, rng.uniform(0, 1))).astype(float)
        filas.append(pd.DataFrame({"celda": c, "pobre": pobre, "elegible": elegible, "w": rng.uniform(1, 50, n)}))
    return pd.concat(filas, ignore_index=True)


def _marginales(d):
    g = d.assign(wp=d.w * d.pobre, we=d.w * d.elegible).groupby("celda")[["w", "wp", "we"]].sum()
    return pd.DataFrame({"peso": g.w, "p": g.wp / g.w, "e": g.we / g.w})


@pytest.mark.parametrize("semilla", range(5))
def test_las_tasas_verdaderas_caen_en_la_cota(semilla):
    d = _poblacion(np.random.default_rng(semilla))
    r = ef.tasas(_marginales(d))
    excl = np.sum(d.w * d.pobre * (1 - d.elegible)) / np.sum(d.w * d.pobre)
    incl = np.sum(d.w * d.elegible * (1 - d.pobre)) / np.sum(d.w * d.elegible)
    assert r["exclusion_lo"] - 1e-12 <= excl <= r["exclusion_hi"] + 1e-12
    assert r["inclusion_lo"] - 1e-12 <= incl <= r["inclusion_hi"] + 1e-12


def test_las_cotas_se_alcanzan():
    # elegibles = los más pobres primero (mínima exclusión) o los no pobres primero (máxima)
    c = ef.cotas_celda(np.array([0.3, 0.6]), np.array([0.5, 0.2]))
    np.testing.assert_allclose(c["excl_lo"], [0.0, 0.4])
    np.testing.assert_allclose(c["excl_hi"], [0.3, 0.6])
    np.testing.assert_allclose(c["incl_lo"], [0.2, 0.0])
    np.testing.assert_allclose(c["incl_hi"], [0.5, 0.2])
    np.testing.assert_allclose(c["excl_ind"], [0.15, 0.48])
    # identidades de las marginales: P(P=1,E=0) − P(P=0,E=1) = p − e en cualquier acople
    np.testing.assert_allclose(c["excl_lo"] - c["incl_lo"], [-0.2, 0.4])
    np.testing.assert_allclose(c["excl_hi"] - c["incl_hi"], [-0.2, 0.4])


def test_definiciones_iguales_a_las_reglas_simuladas():
    """Con e igual a 0 o 1 en cada celda (sin acople que elegir), las tasas
    son las de `reglas_focalizacion.metricas`."""
    celdas = pd.DataFrame({"peso": [2.0, 1.0, 1.0], "p": [0.5, 1.0, 0.0], "e": [1.0, 0.0, 1.0]})
    r = ef.tasas(celdas)
    assert r["exclusion_lo"] == r["exclusion_hi"] == pytest.approx(1.0 / 2.0)  # 1 pobre excluido de 2
    assert r["inclusion_lo"] == r["inclusion_hi"] == pytest.approx(2.0 / 3.0)  # 2 no pobres de 3 elegibles


def test_e_con_la_cadena_de_respaldos():
    geih = pd.DataFrame({"geo_depto": ["05", "05", "99"], "jefe_edad": ["40", "40", "40"],
                         "viv_cuartos": ["3", "1", "3"], "viv_pisos": ["4", "4", "4"]})
    sis = pd.DataFrame({"geo_depto": ["05", "05", "08"], "jefe_edad": ["5", "5", "5"], "viv_cuartos": ["3", "3", "3"],
                        "viv_pisos": ["1", "1", "1"], "Grupo": ["A", "D", "B"]})
    e, nivel = ef.elegibles_por_hogar(geih, sis, ["A", "B"])
    assert e[0] == 0.5 and nivel[0] == 0           # celda exacta
    assert e[1] == 0.5 and nivel[1] > 0            # otro tramo de cuartos: respaldo en depto + edad
    assert e[2] == pytest.approx(2 / 3)            # depto sin registro: todo el Sisbén
