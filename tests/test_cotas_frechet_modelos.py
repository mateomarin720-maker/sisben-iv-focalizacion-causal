"""Cotas de Fréchet por parámetro (`src/diagnostico/cotas_frechet_modelos.py`)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.diagnostico import cotas_frechet_modelos as cm
from src.diagnostico.cotas_frechet_manski import cotas_frechet


def _poblacion(rng, n_celdas=40, binaria=False):
    """Hogares GEIH con pesos y un T verdadero (que la GEIH no observa)."""
    filas = []
    for c in range(n_celdas):
        n = int(rng.integers(5, 60))
        y = (rng.random(n) < rng.random()).astype(float) if binaria else rng.gamma(2, 1 + c % 3, n)
        u = rng.normal(size=n) + rng.normal() * (y - y.mean())  # dependencia arbitraria entre T e Y
        t = (u > np.quantile(u, rng.uniform(0.1, 0.9))).astype(int)
        filas.append(pd.DataFrame({"celda": f"c{c}", "y": y, "t": t, "fex": rng.uniform(1, 100, n)}))
    d = pd.concat(filas, ignore_index=True)
    p_t = (d["t"] * d["fex"]).groupby(d["celda"]).sum() / d.groupby("celda")["fex"].sum()
    return d, p_t


def _contraste_verdadero(d):
    def m(g, t):
        h = g[g["t"] == t]
        return np.average(h["y"], weights=h["fex"])
    return d.groupby("celda")[["y", "t", "fex"]].apply(lambda g: m(g, 1) - m(g, 0))


def test_con_y_binaria_coincide_con_frechet():
    rng = np.random.default_rng(0)
    d, p_t = _poblacion(rng, binaria=True)
    g = cm.cotas_contraste(d, p_t, "y")
    p_y = (d["y"] * d["fex"]).groupby(d["celda"]).sum() / d.groupby("celda")["fex"].sum()
    f = cotas_frechet(p_y[g.index], g["p_t"])
    np.testing.assert_allclose(g["cota_lo"], f["cate_lo"], atol=1e-12)
    np.testing.assert_allclose(g["cota_hi"], f["cate_hi"], atol=1e-12)


@pytest.mark.parametrize("semilla", range(5))
def test_el_contraste_verdadero_cae_en_la_cota(semilla):
    rng = np.random.default_rng(semilla)
    d, p_t = _poblacion(rng)
    g = cm.cotas_contraste(d, p_t, "y")
    v = _contraste_verdadero(d)[g.index]
    assert (g["cota_lo"] <= v + 1e-9).all() and (v <= g["cota_hi"] + 1e-9).all()
    # el acople extremo se alcanza: T = cola alta de Y da el máximo
    d2 = d.sort_values(["celda", "y"]).copy()
    d2["t"] = (d2.groupby("celda")["y"].rank(method="first", ascending=False) <= 1).astype(int)
    w1 = (d2["t"] * d2["fex"]).groupby(d2["celda"]).sum() / d2.groupby("celda")["fex"].sum()
    g2 = cm.cotas_contraste(d2, w1, "y")
    np.testing.assert_allclose(g2["cota_hi"], _contraste_verdadero(d2)[g2.index], atol=1e-9)


def test_agregacion_por_parametro():
    g = pd.DataFrame({"peso": [1.0, 3.0], "p_t": [0.5, 0.25], "cota_lo": [-1.0, 0.0], "cota_hi": [1.0, 2.0]})
    assert cm.agregar(g, "ATE") == pytest.approx((-0.25, 1.75))
    assert cm.agregar(g, "ATT") == pytest.approx((-0.4, 1.6))      # pesos 0,5 y 0,75
    assert cm.agregar(g, "ATU") == pytest.approx((-0.5 / 2.75, 5 / 2.75))  # pesos 0,5 y 2,25


def test_subgrupos_con_el_mismo_codigo_en_las_dos_fuentes():
    geih = pd.DataFrame({"geo_zona": ["1", "2"], "jefe_sexo": ["1", "2"], "viv_paredes": ["1", "5"]})
    sis = pd.DataFrame({"geo_zona": ["1", "2"], "jefe_sexo": ["1", "2"], "viv_paredes": ["1", "2"]})
    assert cm.subgrupos(geih, "geih").values.tolist() == [["urbana", "hombre", "ladrillo"], ["rural", "mujer", "precaria"]]
    # paredes: el código 2 es ladrillo en GEIH y tapia o bahareque en el Sisbén
    assert cm.subgrupos(sis, "sisben")["paredes"].tolist() == ["ladrillo", "tapia_bahareque"]
