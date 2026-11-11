"""Proposiciones del enlace por celdas (docs/anexos_tesis/PROPOSICIONES.md),
comprobadas con poblaciones sintéticas pequeñas."""
import numpy as np

from src.diagnostico import proposiciones as pr


def test_proposicion_1_el_imputado_da_cero_sea_cual_sea_el_efecto():
    t = pr.proposicion_1(reps=60)
    assert (t["media_imputado"].abs() < 4 * t["error_mc"]).all()
    # con confusión dentro de la celda, el T verdadero se aleja del efecto; el imputado sigue en cero
    assert t.loc[t["confusion"] > 0, "contraste_t_verdadero"].iloc[0] > 0.3


def test_proposicion_2_atenuacion_proporcional_al_enlace():
    t = pr.proposicion_2(reps=15)
    assert ((t["factor_simulado"] - t["factor_esperado"]).abs() < 4 * t["error_mc"] + 0.02).all()
    celda = t[t["resto"] == "imputado en la celda"]
    assert np.allclose(celda["factor_esperado"], celda["enlazados"])


def test_enlace_falso_coincide_con_la_imputacion_si_todas_las_celdas_son_iguales():
    pob = pr.poblacion(n=5000, semilla=4)
    pob.p[:] = pob.t.mean()
    for enlazados in (0.0, 0.3, 1.0):
        assert np.isclose(pr.atenuacion_enlace_falso(pob, enlazados), enlazados)


def test_proposicion_3_la_mitad_de_la_varianza_viene_de_la_imputacion():
    t = pr.proposicion_3(sorteos=60, poblaciones=4)
    assert t["razon_entre_dentro"].between(0.75, 1.3).all()
    assert t["fraccion_media"].between(0.43, 0.57).all()


def test_ancho_de_la_cota_es_uno_mas_dos_delta():
    rng = np.random.default_rng(0)
    p_y, p_t = rng.uniform(0.01, 0.99, 500), rng.uniform(0.01, 0.99, 500)
    a = pr.ancho_cota(p_y, p_t)
    assert np.allclose(a["ancho"], a["uno_mas_dos_delta"])
    assert (a["ancho"] >= 1).all() and (a["ancho"] <= 2).all()


def test_ancho_publicado_de_pobreza_monetaria():
    pub = pr.ancho_cota_publicada()
    assert pub is not None and pub["celdas"] == 921
    assert round(pub["ancho"], 2) == 1.40 and round(pub["delta_medio"], 2) == 0.20
