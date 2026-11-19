"""Reglas de focalización ampliadas (`src/focalizacion/reglas_ampliadas.py`,
fase 3 de `docs/metodologia/METODOLOGIA_FHDI.md`): mismos sorteos que la
corrida vigente, vigente con el enlace fraccional en valor esperado y CATE
con FHDI sin vínculo no identificable."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.focalizacion import reglas_ampliadas as ra
from src.focalizacion import reglas_focalizacion as rf
from tests.test_simulacion_equivalencia import hogares_sinteticos


def _base(n: int = 3_000) -> pd.DataFrame:
    hogares, p_t = hogares_sinteticos(n=n)
    rng = np.random.default_rng(11)
    hogares = hogares.assign(
        Grupo_hotdeck=rng.choice(list("ABCD"), n), fex=rng.uniform(50, 150, n), personas_ug=rng.integers(1, 6, n),
        viv_acueducto=rng.choice(["1", "2"], n), viv_alcantarillado=rng.choice(["1", "2"], n),
        **{c: rng.integers(0, 2, n) for c in rf.PMT_NUMERICAS if c not in hogares})
    b = rf.preparar(hogares, p_t)
    b["p_ab_fhdi"] = rng.uniform(0.2, 0.8, n)
    return b


@pytest.fixture(scope="module")
def filas():
    b = _base()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(rf, "N_EVAL", 900)
        mp.setattr(rf, "N_ENTRENA", 900)
        vigente = pd.DataFrame(rf.una_repeticion(b, rep=0))
        nueva = pd.DataFrame(ra.una_repeticion(b, rep=0))
    return vigente, nueva


def test_reproduce_los_sorteos_de_la_corrida_vigente(filas):
    """`vigente_hotdeck`, `pmt_ingreso` e `ideal` dan lo mismo que en
    `reglas_focalizacion` (mismas muestras, mundo y desempates), con los
    dos presupuestos."""
    vigente, nueva = filas
    clave = rf.CLAVES
    v = vigente[vigente["regla"].isin(ra.CONTROL)].set_index(clave)[rf.METRICAS]
    a = nueva[nueva["regla"].isin(ra.CONTROL)].set_index(clave)[rf.METRICAS]
    assert len(a) == len(v) == 9
    np.testing.assert_allclose(a.loc[v.index].to_numpy(float), v.to_numpy(float), atol=1e-12)


def test_reglas_nuevas_y_no_identificable(filas):
    _, nueva = filas
    assert set(nueva["regla"]) == {*ra.CONTROL, *ra.NUEVAS}
    nada = nueva[nueva["regla"] == "pmt_brecha_cate_fhdi"]
    assert len(nada) == 3 and (~nada["identificable"]).all() and nada["error_inclusion"].isna().all()
    resto = nueva[nueva["identificable"]]
    assert resto[rf.METRICAS].notna().all().all()
    k = nueva.loc[nueva["regla"] == "vigente_hotdeck", "k"].iloc[0]
    assert (nueva.loc[nueva["regla"].isin(ra.NUEVAS_ORDINALES) & (nueva["presupuesto"] == "hogares"), "k"] == k).all()


def test_metricas_fraccionales_con_p_entero_son_las_de_la_regla():
    rng = np.random.default_rng(3)
    d = pd.DataFrame({"y0": np.log1p(rng.uniform(0, 1e6, 400)), "lp": 5e5, "tau": 0.1, "peso": rng.uniform(1, 3, 400)})
    t = (rng.random(400) < 0.4).astype(int)
    for tipo in rf.TIPOS_EFECTO:
        a, b = ra.metricas_fraccionales(d, t, tipo), rf.metricas(d, t, tipo)
        assert a == pytest.approx(b)


def test_metricas_fraccionales_son_el_promedio_de_los_sorteos():
    """Exclusión, FGT0 y FGT1 son el valor esperado exacto sobre sorteos
    independientes; la inclusión, el cociente de esperados (≈ esperado del
    cociente con muchos hogares)."""
    rng = np.random.default_rng(5)
    n = 2_000
    d = pd.DataFrame({"y0": np.log1p(rng.uniform(0, 1e6, n)), "lp": 5e5, "tau": 0.2, "peso": rng.uniform(1, 3, n)})
    p = rng.uniform(0.1, 0.9, n)
    sorteos = pd.DataFrame([rf.metricas(d, (rng.random(n) < p).astype(int), "monto_fijo") for _ in range(400)]).mean()
    esperado = ra.metricas_fraccionales(d, p, "monto_fijo")
    for c in esperado:
        assert esperado[c] == pytest.approx(sorteos[c], abs=3e-3)
