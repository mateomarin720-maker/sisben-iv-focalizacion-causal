"""Imputación fraccional en la simulación (pregunta 5 de
`sensibilidad_semisintetica.py`; `docs/metodologia/METODOLOGIA_FHDI.md`):
probabilidad de la celda con la cadena de respaldos, no identificable sin
vínculo, y la recta de atenuación con sorteo frente a imputación fraccional."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.simulacion import sensibilidad_semisintetica as se
from src.simulacion.asignacion import asignar
from src.simulacion.base import diseno_x
from src.simulacion.escenarios import ESCENARIOS
from src.simulacion.estimadores import identificable, regresion_efectos_fijos
from src.simulacion.vinculo import hotdeck_celda, probabilidad_celda
from tests.test_simulacion_semisintetica import _base


def test_probabilidad_de_la_celda_con_respaldos():
    """Proporción de T = 1 de los donantes de la celda; si la celda no
    tiene donantes, la del siguiente nivel; si ninguno, la del registro."""
    receptor = np.array([[0, 10], [1, 10], [2, 11], [3, 99]])
    donante = np.array([[0, 10], [0, 10], [1, 10], [5, 11], [5, 11], [5, 11]])
    t = np.array([1, 0, 1, 1, 1, 0])
    p = probabilidad_celda(receptor, donante, t)
    assert np.allclose(p, [0.5, 1.0, 2 / 3, 4 / 6])


def test_sin_vinculo_la_imputacion_fraccional_no_es_identificable():
    rng = np.random.default_rng(0)
    celda = rng.integers(0, 50, 5000)
    p = rng.uniform(0.2, 0.8, 50)[celda]
    t = (rng.random(5000) < p).astype(float)
    assert not identificable(p, celda)          # L = 0: igual dentro de la celda
    assert identificable(t, celda)              # T verdadero o sorteado: varía
    mezcla = se.t_observado(t, t, p, rng.random(5000) < 0.25, "fhdi")
    assert identificable(mezcla, celda)


def test_t_observado():
    t, td, p = np.array([1, 0, 1, 0]), np.array([0, 1, 0, 1]), np.array([0.3, 0.3, 0.7, 0.7])
    v = np.array([True, False, True, False])
    assert se.t_observado(t, td, p, v, "hotdeck").tolist() == [1, 1, 1, 1]
    assert se.t_observado(t, td, p, v, "fhdi").tolist() == [1, 0.3, 1, 0.7]


def test_con_vinculo_parcial_el_sorteo_atenua_y_la_imputacion_fraccional_no():
    """Proposición 2 acotada: con el sorteo la regresión con efectos fijos
    cae a L·τ; con la probabilidad de la celda en los no vinculados
    recupera τ. Promedio de 20 semillas, L = 0,5."""
    sorteo, fraccional, verdad = [], [], []
    for s in range(20):
        b = _base(n=20_000, seed=s)
        rng = np.random.default_rng(100 + s)
        t = asignar(b, ESCENARIOS["confusion_observada"], rng)[0].astype(float)
        y = b["y0"].to_numpy() + b["tau"].to_numpy() * t
        Z, celda = diseno_x(b), b["hotdeck_celda_cat"].to_numpy()
        t_donante = hotdeck_celda(celda, celda, t, rng)
        p = probabilidad_celda(celda, celda, t)
        v = rng.random(len(b)) < 0.5
        sorteo.append(regresion_efectos_fijos(y, se.t_observado(t, t_donante, p, v, "hotdeck"), Z, celda)[0])
        fraccional.append(regresion_efectos_fijos(y, se.t_observado(t, t_donante, p, v, "fhdi"), Z, celda)[0])
        verdad.append(b["tau"].mean())
    tau = float(np.mean(verdad))
    assert abs(np.mean(sorteo) - 0.5 * tau) < 0.01
    assert abs(np.mean(fraccional) - tau) < 0.01


def test_repeticion_de_vinculo_sobre_base_sintetica():
    """Filas por escenario × L × imputación × estimador; con FHDI y L = 0
    se reporta vacío y no identificable, no 0."""
    from src.simulacion.base import preparar_base
    from tests.test_simulacion_equivalencia import hogares_sinteticos

    hogares, p_t = hogares_sinteticos(n=3_000)
    b = preparar_base(hogares, p_t)
    filas = pd.DataFrame(se.una_repeticion_vinculo(b, rep=0, n=1_200))
    n_esperado = len(se.ESCENARIOS_VINCULO) * len(se.FRACCIONES_VINCULO) * len(se.IMPUTACIONES) * 2
    assert len(filas) == n_esperado
    cero = filas[(filas["imputacion"] == "fhdi") & (filas["fraccion_vinculada"] == 0)]
    assert (~cero["identificable"]).all() and cero["estimacion"].isna().all()
    resto = filas.drop(cero.index)
    assert resto["identificable"].all() and resto["estimacion"].notna().all()
    # Con L = 1 las dos imputaciones ven el mismo T: misma estimación.
    uno = filas[filas["fraccion_vinculada"] == 1].pivot_table(index=["escenario", "estimador"], columns="imputacion",
                                                              values="estimacion")
    assert np.allclose(uno["hotdeck"], uno["fhdi"])


def test_repeticion_de_diagnostico_sobre_base_sintetica():
    """Pregunta 6: cada tamaño × escenario × L × imputación con los tres
    estimadores (LinearDML en sus dos versiones)."""
    from src.simulacion.base import preparar_base
    from tests.test_simulacion_equivalencia import hogares_sinteticos

    hogares, p_t = hogares_sinteticos(n=3_000)
    b = preparar_base(hogares, p_t)
    filas = pd.DataFrame(se.una_repeticion_vinculo_diagnostico(b, rep=0, tamanos=(800,), fracciones=(0.5,)))
    assert len(filas) == len(se.ESCENARIOS_VINCULO) * len(se.IMPUTACIONES) * 3
    assert set(filas["estimador"]) == {"regresion_efectos_fijos", "linear_dml", "linear_dml_sin_regularizar"}
    assert filas["estimacion"].notna().all() and set(filas["hogares"]) == {800}
