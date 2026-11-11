"""Modo simulado: calibración con agregados y población sintética
(`src/simulacion/calibrar.py`, `src/simulacion/generador.py`)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.simulacion import calibrar as cal
from src.simulacion import contrato, generador

N = 12_000


def _fuentes(n: int = N, seed: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hogares (códigos GEIH) y registro (códigos del Sisbén) con las
    columnas canónicas. El departamento 99 tiene solo 12 hogares: por
    debajo del umbral de protección."""
    rng = np.random.default_rng(seed)
    depto = np.r_[rng.choice(["05", "11", "76"], n - 12), ["99"] * 12]
    zona = np.where(rng.random(n) < 0.75, "1", "2")
    pisos = rng.choice(["1", "2", "4", "5"], n, p=[0.1, 0.3, 0.4, 0.2])
    mujer = rng.random(n) < 0.45
    paredes = rng.choice(["1", "1", "1", "5"], n)
    log_ing = (13 + 0.3 * (depto == "11") + 0.4 * np.isin(pisos, ["4", "5"]) - 0.4 * (zona == "2")
               - 0.15 * mujer - 0.2 * (paredes != "1") + rng.normal(0, 0.8, n))
    hogares = pd.DataFrame({
        "geo_depto": depto, "geo_zona": zona, "jefe_sexo": np.where(mujer, "2", "1"),
        "jefe_edad": rng.integers(18, 91, n).astype(str), "viv_cuartos": rng.integers(1, 8, n).astype(str),
        "viv_pisos": pisos, "viv_paredes": paredes,
        "ingreso_percapita": np.where(rng.random(n) < 0.04, 0.0, np.expm1(log_ing)),
        "dominio_pm": np.where(zona == "2", "rural", np.where(depto == "11", "13_ciudades", "otras_cabeceras")),
    })
    m = 4 * n
    reg = pd.DataFrame({
        "geo_depto": rng.choice(["05", "11", "76"], m), "jefe_edad": rng.choice(list("3456"), m, p=[.02, .2, .58, .2]),
        "viv_cuartos": rng.integers(1, 6, m).astype(str), "viv_pisos": rng.choice(list("12345"), m),
        "Grupo": rng.choice(list("ABCD"), m), "Clasificacion": "X1",
    })
    return hogares, reg


@pytest.fixture(scope="module")
def parametros():
    return cal.calibrar(*_fuentes())


def _grupos(p: dict):
    for nombre in ("depto", "zona", "dominio", "vivienda", "paredes", "mujer"):
        yield from ((nombre, k, g) for k, g in p[nombre].items())
    yield from (("ingreso", k, g) for k, g in p["ingreso"]["grupos"].items())


def test_ningun_grupo_bajo_el_umbral_de_proteccion(parametros):
    assert all(g["n"] >= cal.UMBRAL for _, _, g in _grupos(parametros))
    assert not any(k.startswith("99") for _, k, _ in _grupos(parametros))  # 12 hogares: no se guarda


def test_la_poblacion_cumple_el_contrato_y_cae_al_nivel_superior(parametros):
    hogares, p_t = generador.generar(parametros, 5_000, semilla=1)
    contrato.validar(hogares, "hogares")
    assert len(hogares) == 5_000 and p_t.between(0, 1).all()
    # el 99 no tiene grupos propios: su zona, vivienda e ingreso salen del nivel nacional
    p99 = dict(parametros, depto={"*": dict(n=12, p={"99": 1.0})})
    h99, _ = generador.generar(p99, 500, semilla=2)
    contrato.validar(h99, "hogares")


def test_las_marginales_reproducen_la_calibracion(parametros):
    hogares, _ = generador.generar(parametros, 60_000, semilla=4)
    v = cal.variables(hogares)
    esperada = pd.Series(parametros["depto"]["*"]["p"])
    np.testing.assert_allclose(v["depto"].value_counts(normalize=True)[esperada.index], esperada, atol=0.01)
    assert (v["ingreso"] <= 0).mean() == pytest.approx(parametros["ingreso"]["grupos"]["*"]["p_cero"], abs=0.01)
    # recalibrar sobre la población sintética devuelve los mismos efectos de X en el ingreso
    otra = cal.modelo_ingreso(v)["coef"]
    assert otra["mujer"] == pytest.approx(parametros["ingreso"]["coef"]["mujer"], abs=0.03)
    assert otra["precaria"] == pytest.approx(parametros["ingreso"]["coef"]["precaria"], abs=0.03)


def test_el_efecto_de_x_en_el_ingreso_es_el_de_los_datos(parametros):
    assert parametros["ingreso"]["coef"]["mujer"] == pytest.approx(-0.15, abs=0.04)
    assert parametros["ingreso"]["coef"]["precaria"] == pytest.approx(-0.2, abs=0.04)


def test_misma_semilla_misma_poblacion(parametros):
    a, _ = generador.generar(parametros, 2_000, semilla=9)
    b, _ = generador.generar(parametros, 2_000, semilla=9)
    pd.testing.assert_frame_equal(a, b)


def test_p_t_por_celda_con_la_cadena_de_respaldos(parametros):
    hogares, reg = _fuentes()
    p = cal.p_t_por_celda_exacta(hogares, reg)
    assert set(p) == set(cal.claves_por_nivel(hogares)[0][1].astype(str))
    # el depto 99 no está en el registro: toma la media de todo el registro
    celdas_99 = [k for k in p if k.startswith("99")]
    assert celdas_99 and all(p[k] == pytest.approx(reg["Grupo"].isin(["A", "B"]).mean(), abs=1e-6)
                             for k in celdas_99)


def _con_tratamiento(parametros, vinculo: str, efecto: float = 0.3, n: int = 6_000):
    """Población sintética con el grupo observado: T sorteado con P(T | celda)
    dentro de cada celda, y un efecto conocido sobre el log-ingreso."""
    from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import construir_celda

    hogares, p_t = generador.generar(parametros, n, semilla=5)
    rng = np.random.default_rng(6)
    p = construir_celda(hogares).astype(str).map(p_t).fillna(p_t.mean()).to_numpy()
    t = rng.random(n) < p
    hogares["ingreso_percapita"] = hogares["ingreso_percapita"] * np.where(t, np.exp(efecto), 1.0)
    hogares["Grupo"] = np.where(t, "A", "D")
    hogares["vinculo"] = vinculo
    return hogares, p_t


def test_datos_propios_recupera_el_efecto_con_llave(parametros):
    from src.simulacion.datos_propios import estimacion_observada

    hogares, p_t = _con_tratamiento(parametros, "llave", n=20_000)
    r = estimacion_observada(hogares, p_t).set_index("resultado")
    fila = r.loc["log-ingreso per cápita"]
    assert fila["ic_lo"] <= 0.3 <= fila["ic_hi"] and fila["ate_dml"] == pytest.approx(0.3, abs=0.1)
    assert fila["cota_frechet_lo"] <= 0.3 <= fila["cota_frechet_hi"]
    assert r["lectura"].str.startswith("efecto").all()


def test_datos_propios_con_hotdeck_es_placebo_y_exige_el_grupo(parametros):
    from src.simulacion.datos_propios import estimacion_observada

    hogares, p_t = _con_tratamiento(parametros, "hotdeck", n=2_000)
    assert estimacion_observada(hogares, p_t)["lectura"].str.startswith("placebo").all()
    with pytest.raises(contrato.ErrorContrato):
        estimacion_observada(hogares.drop(columns=["vinculo"]), p_t)
