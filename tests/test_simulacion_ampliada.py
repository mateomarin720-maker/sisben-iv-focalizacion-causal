"""Simulación ampliada (`src/simulacion/ampliada.py`, fase 2b de
`docs/metodologia/METODOLOGIA_FHDI.md`): mismos sorteos que la corrida
vigente, régimen FHDI sin vínculo no identificable y estimadores dentro
de la celda."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.simulacion import ampliada, evaluacion
from src.simulacion.base import preparar_base
from tests.test_simulacion_equivalencia import hogares_sinteticos


@pytest.fixture(scope="module")
def filas():
    hogares, p_t = hogares_sinteticos(n=3_000)
    b = preparar_base(hogares, p_t)
    vigente = pd.DataFrame(evaluacion.una_repeticion(b, rep=0, n=1_200))
    nueva = pd.DataFrame(ampliada.una_repeticion(b, rep=0, n=1_200, con_bosque=True))
    return vigente, nueva


def test_reproduce_los_sorteos_de_la_corrida_vigente(filas):
    """La regresión con efectos fijos de la ampliada es la de la vigente,
    repetición por repetición: misma encuesta, donante y hogares con
    donante (los sorteos del régimen FHDI van después)."""
    vigente, nueva = filas
    clave = ["escenario", "vinculo", "outcome"]
    v = vigente[vigente["estimador"] == "regresion_efectos_fijos"].set_index(clave)["estimacion"]
    a = nueva[(nueva["estimador"] == "regresion_efectos_fijos")
              & nueva["vinculo"].isin(evaluacion.VINCULOS)].set_index(clave)["estimacion"]
    assert len(a) == len(v)
    np.testing.assert_allclose(a.loc[v.index], v, atol=1e-12)


def test_fhdi_sin_vinculo_no_identificable(filas):
    _, nueva = filas
    cero = nueva[nueva["vinculo"] == "fhdi"]
    assert len(cero) and (~cero["identificable"]).all() and cero["estimacion"].isna().all()
    resto = nueva[nueva["vinculo"] != "fhdi"]
    assert resto["identificable"].all() and resto["estimacion"].notna().all()


def test_estimadores_por_integracion(filas):
    _, nueva = filas
    est = nueva.groupby("vinculo")["estimador"].apply(set)
    assert "linear_dml" in est["fhdi_parcial_50"] and "linear_dml" not in est["hotdeck"]
    bosque = nueva[nueva["estimador"] == "causal_forest_intra_celda"]
    assert set(bosque["vinculo"]) == {"oraculo", "hotdeck", "fhdi_parcial_50"}
    assert set(bosque["outcome"]) == {"log_ingreso"} and (bosque["pehe"] >= 0).all()
