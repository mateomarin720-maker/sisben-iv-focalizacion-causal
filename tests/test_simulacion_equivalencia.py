"""Equivalencia del módulo `src/simulacion/` con la versión anterior
(`src/validacion/simulacion_semisintetica.py`, ya borrada, que produjo las 432
repeticiones de `SIMULACION_SEMISINTETICA.md`).

`tests/referencia/simulacion_una_repeticion.csv` se generó con la versión
anterior, antes de mover el código, sobre la tabla sintética de
`hogares_sinteticos` (columnas canónicas). El módulo nuevo debe dar las
mismas filas: si una refactorización cambia un resultado, esta prueba lo
detecta antes que la corrida completa.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REFERENCIA = Path(__file__).parent / "referencia" / "simulacion_una_repeticion.csv"
REPS, N_HOGARES, N_ENCUESTA = (0, 1, 2), 6000, 2000


def hogares_sinteticos(n: int = N_HOGARES, seed: int = 7) -> tuple[pd.DataFrame, pd.Series]:
    """Tabla de hogares con las columnas canónicas (códigos como texto,
    igual que `data/2_models/`) y P(T | celda) inventada para sus celdas."""
    from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import construir_celda

    rng = np.random.default_rng(seed)
    depto = rng.choice(["05", "11", "76"], n)
    zona = np.where(rng.random(n) < 0.8, "1", "2")
    pisos = rng.choice(["1", "2", "4"], n, p=[0.1, 0.3, 0.6])
    log_ing = 13 + 0.3 * (depto == "11") + 0.4 * (pisos == "4") - 0.3 * (zona == "2") + rng.normal(0, 0.8, n)
    hogares = pd.DataFrame({
        "geo_depto": depto,
        "geo_zona": zona,
        "jefe_sexo": rng.choice(["1", "2"], n),
        "jefe_edad": rng.integers(18, 91, n).astype(str),
        "viv_cuartos": rng.integers(1, 5, n).astype(str),
        "viv_pisos": pisos,
        "viv_paredes": rng.choice(["1", "1", "1", "5"], n),
        "ingreso_percapita": np.where(rng.random(n) < 0.03, 0.0, np.exp(log_ing)),
        "dominio_pm": np.where(zona == "2", "rural", np.where(np.isin(depto, ["05", "11"]), "13_ciudades",
                                                              "otras_cabeceras")),
    })
    celdas = np.sort(construir_celda(hogares).unique())
    p_t = pd.Series(np.random.default_rng(seed + 1).uniform(0.15, 0.85, len(celdas)), index=celdas)
    return hogares, p_t


def test_una_repeticion_igual_a_la_version_anterior():
    """3 repeticiones (la 0 con Causal Forest) dan las mismas filas que la
    versión anterior. Con los datos reales se comprobó lo mismo el
    2026-11-04: tabla de trabajo de 290.968 hogares y las 150 filas de la
    repetición 0, idénticas."""
    from src.simulacion import evaluacion
    from src.simulacion.base import preparar_base

    hogares, p_t = hogares_sinteticos()
    b = preparar_base(hogares, p_t)
    filas = [f for rep in REPS for f in evaluacion.una_repeticion(b, rep, N_ENCUESTA, con_bosque=(rep == 0))]
    nueva = pd.DataFrame(filas)
    nueva = pd.read_csv(pd.io.common.StringIO(nueva.to_csv(index=False, float_format="%.12g")))
    pd.testing.assert_frame_equal(nueva, pd.read_csv(REFERENCIA), rtol=1e-6, atol=1e-9)


def test_columnas_extra_o_en_otro_orden_no_cambian_la_base():
    from src.simulacion.base import preparar_base

    hogares, p_t = hogares_sinteticos(n=800)
    otra = hogares[hogares.columns[::-1]].assign(columna_ajena=1)
    pd.testing.assert_frame_equal(preparar_base(otra, p_t), preparar_base(hogares, p_t))
