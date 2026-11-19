"""Imputación fraccional en la simulación (preguntas 5 a 7 de
`sensibilidad_semisintetica.py`; `docs/metodologia/METODOLOGIA_FHDI.md`):
probabilidad de la celda con la cadena de respaldos, no identificable sin
vínculo, la recta de atenuación con sorteo frente a imputación fraccional
y LinearDML dentro de la celda."""
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


def _celdas_pequenas(seed: int, n: int = 8_000, k: int = 1_000, L: float = 0.25):
    """Efecto nulo, confusión por celda y ≈8 hogares por celda; T con la
    imputación fraccional en los no vinculados (el caso de la pregunta 6)."""
    rng = np.random.default_rng(seed)
    celda = rng.integers(0, k, n)
    a = rng.normal(0, 1, k)
    d = pd.DataFrame({"geo_zona_urbana": rng.integers(0, 2, n), "jefe_mujer": rng.integers(0, 2, n),
                      "viv_paredes": rng.choice([1, 1, 1, 5], n).astype(float), "hotdeck_celda_cat": celda})
    t = (rng.random(n) < 1 / (1 + np.exp(-a[celda]))).astype(float)
    y = 0.5 * a[celda] + rng.normal(0, 0.3, n)
    p = probabilidad_celda(celda[:, None], celda[:, None], t)
    return d, y, se.t_observado(t, t, p, rng.random(n) < L, "fhdi")


def test_linear_dml_dentro_de_la_celda_quita_el_sesgo_de_celdas_pequenas():
    """Pregunta 7: con FHDI y celdas pequeñas, LinearDML vigente se sesga
    (estima la celda en el ajuste cruzado) y dentro de la celda no (la
    quita exactamente, como la regresión con efectos fijos)."""
    vigente, intra = [], []
    for s in range(4):
        d, y, t = _celdas_pequenas(s)
        vigente.append(se.linear_dml(d, y, t, regularizado=True)[0])
        intra.append(se.linear_dml_intra_celda(d, y, t)[0])
    assert np.mean(vigente) > 0.08
    assert abs(np.mean(intra)) < 0.02


def test_linear_dml_dentro_de_la_celda_con_celdas_grandes_coincide_con_la_regresion():
    """Con vínculo parcial (L = 0,5): FHDI recupera τ y Hot-Deck da L·τ,
    igual que la regresión con efectos fijos."""
    b = _base(n=8_000, seed=3)
    rng = np.random.default_rng(103)
    t = asignar(b, ESCENARIOS["confusion_observada"], rng)[0].astype(float)
    y = b["y0"].to_numpy() + b["tau"].to_numpy() * t
    Z, celda = diseno_x(b), b["hotdeck_celda_cat"].to_numpy()
    td, p, v = hotdeck_celda(celda, celda, t, rng), probabilidad_celda(celda, celda, t), rng.random(len(b)) < 0.5
    tau = b["tau"].mean()
    tf = se.t_observado(t, td, p, v, "fhdi")
    a, lo, hi = se.linear_dml_intra_celda(b, y, tf)
    assert abs(a - regresion_efectos_fijos(y, tf, Z, celda)[0]) < 0.005 and lo < tau < hi
    assert abs(se.linear_dml_intra_celda(b, y, se.t_observado(t, td, p, v, "hotdeck"))[0] - 0.5 * tau) < 0.02


def test_repeticion_intra_celda_sobre_base_sintetica():
    from src.simulacion.base import preparar_base
    from tests.test_simulacion_equivalencia import hogares_sinteticos

    hogares, p_t = hogares_sinteticos(n=3_000)
    b = preparar_base(hogares, p_t)
    filas = pd.DataFrame(se.una_repeticion_intra_celda(b, rep=0, n=1_200))
    assert len(filas) == len(se.ESCENARIOS_VINCULO) * len(se.FRACCIONES_VINCULO) * len(se.IMPUTACIONES) * 3
    cero = filas[(filas["imputacion"] == "fhdi") & (filas["fraccion_vinculada"] == 0)]
    assert cero["estimacion"].isna().all()
    assert filas.drop(cero.index)["estimacion"].notna().all()
