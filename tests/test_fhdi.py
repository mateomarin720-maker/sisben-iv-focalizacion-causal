"""Imputación fraccional (FHDI) sobre la celda del Hot-Deck
(`src/emparejamiento/fhdi/`). Datos sintéticos: no necesita el banco."""
import numpy as np
import pandas as pd
import pytest

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import construir_celda, hotdeck
from src.emparejamiento.fhdi import reglas, validacion
from src.emparejamiento.fhdi.varianza import asignar_grupos, razon_jackknife


def _hogares(n, rng, sisben):
    """Hogares de tres departamentos y dos tramos de edad; en el Sisbén la
    edad va en ciclo de vida y los pisos en su escala."""
    d = pd.DataFrame({
        "geo_depto": rng.choice(["05", "08", "11"], n),
        "jefe_edad": rng.choice(["4", "5"] if sisben else [25, 40], n),
        "viv_cuartos": rng.choice([1, 2], n),
        "viv_pisos": rng.choice(["5", "3"] if sisben else ["1", "2"], n),
        "hog_num_personas": rng.choice([2, 4], n),
        "hog_num_menores": rng.choice([0, 1], n),
    })
    return d


@pytest.fixture(scope="module")
def datos():
    rng = np.random.default_rng(0)
    don = _hogares(6000, rng, sisben=True)
    # El grupo depende de la celda: P(A/B) distinta por departamento y pisos.
    p_ab = 0.3 + 0.2 * (don["geo_depto"] == "08") + 0.3 * (don["viv_pisos"] == "5")
    ab = rng.random(len(don)) < p_ab
    don["Grupo"] = np.where(ab, rng.choice(["A", "B"], len(don)), rng.choice(["C", "D"], len(don)))
    don["Nivel"] = don["Clasificacion"] = don["Grupo"] + "1"
    rec = _hogares(1500, rng, sisben=False)
    rec["fex"] = rng.uniform(50, 150, len(rec))
    rec["y"] = (rng.random(len(rec)) < 0.3).astype(float)
    return rec, don


def test_pesos_suman_uno_y_donantes_de_la_misma_celda(datos):
    rec, don = datos
    exp = reglas.donantes_fraccionales(rec, don, m=10)
    assert np.allclose(exp.groupby("receptor")["peso"].sum(), 1)
    exactos = exp[exp["nivel"] == "celda_exacta"]
    celda_r = construir_celda(rec).to_numpy()[exactos["receptor"]]
    celda_d = construir_celda(don, edad_en_codigos=True).to_numpy()[exactos["donante"]]
    assert (celda_r == celda_d).all()
    # Sin reemplazo: ningún donante se repite dentro de un hogar.
    assert not exp.duplicated(["receptor", "donante"]).any()


def test_calibracion_reproduce_pi_de_la_celda(datos):
    """Con pesos calibrados, la distribución por grupo de cada hogar es la
    de su celda: la FHDI con M = 10 da lo mismo que FEFI."""
    rec, don = datos
    exp = reglas.donantes_fraccionales(rec, don, m=10)
    q = reglas.probabilidad_por_receptor(exp, len(rec))
    pi, _ = reglas.probabilidades(rec, don)
    # Sorteo estratificado: todos los hogares quedan calibrados exactamente
    # (con un sorteo simple de 10 donantes y 4 grupos, solo el 63 % aquí).
    assert exp.groupby("receptor")["calibrado"].first().all()
    assert np.allclose(q, pi)
    assert (exp.groupby("receptor").size() <= 10).all()


def test_cupos_por_grupo():
    assert reglas.cupos_por_grupo(np.array([900, 80, 15, 5]), 10).tolist() == [6, 2, 1, 1]  # resto 6: 5,4 0,48 → 5+1, 0+1
    assert reglas.cupos_por_grupo(np.array([50, 50, 0, 0]), 10).tolist() == [5, 5, 0, 0]
    assert reglas.cupos_por_grupo(np.array([2, 1, 0, 0]), 10).tolist() == [2, 1, 0, 0]  # menos donantes que M


def test_fefi_es_la_proporcion_de_la_celda(datos):
    rec, don = datos
    pi, nivel = reglas.probabilidades(rec, don)
    celda_d = construir_celda(don, edad_en_codigos=True)
    esperado = pd.crosstab(celda_d, don["Grupo"], normalize="index").reindex(columns=list("ABCD"), fill_value=0)
    ok = nivel == "celda_exacta"
    assert np.allclose(pi[ok], esperado.loc[construir_celda(rec)[ok]].to_numpy())
    assert np.allclose(pi.sum(axis=1), 1)


def test_mismo_nivel_que_el_hotdeck(datos):
    """La FHDI usa la cadena de respaldos del Hot-Deck sin cambiarla."""
    rec, don = datos
    rec = rec.copy()
    rec.loc[:4, "geo_depto"] = "99"   # sin donantes: todo el registro
    rec.loc[5:9, "viv_cuartos"] = 9   # cae a un respaldo
    _, nivel = reglas.probabilidades(rec, don)
    assert (nivel == hotdeck(rec, don, seed=1)["_hotdeck_nivel"].to_numpy()).all()
    assert (nivel[:5] == "pool_nacional").all()


def test_contraste_placebo_es_cero_con_pesos_calibrados(datos):
    """Proposición 1: dentro de la celda, todos los hogares tienen la misma
    proporción ponderada de A/B, y el contraste es 0 aunque y dependa de la celda."""
    rec, don = datos
    exp = reglas.donantes_fraccionales(rec, don, m=10)
    y = rec["y"].to_numpy() + 0.5 * (rec["geo_depto"] == "08")
    b, _ = reglas.contraste_placebo(y.to_numpy(float), rec["fex"].to_numpy(), construir_celda(rec).to_numpy(), exp)
    assert abs(b) < 1e-10


def test_validacion_ordena_los_metodos(datos):
    """La moda acierta más que el sorteo por hogar; FHDI y FEFI tienen el
    menor error cuadrático; sin celda es el peor."""
    _, don = datos
    v = validacion.validar(don, m=10).set_index("metodo")
    assert v.loc["moda de la celda", "acierto_ab"] > v.loc["sorteo (Hot-Deck)", "acierto_ab"]
    assert v.loc["fefi", "brier_ab"] < v.loc["sorteo (Hot-Deck)", "brier_ab"]
    assert abs(v.loc["fhdi (M = 10)", "brier_ab"] - v.loc["fefi", "brier_ab"]) < 1e-12
    assert v.loc["sin celda (todo el registro)", "brier_ab"] > v.loc["fefi", "brier_ab"]


def test_jackknife_de_una_media():
    """Para una media simple, el jackknife de grupos se acerca al error
    estándar analítico."""
    rng = np.random.default_rng(3)
    a = rng.normal(size=20000)
    w = np.ones_like(a)
    r, se = razon_jackknife(w, a, np.ones_like(a), asignar_grupos(len(a)))
    assert abs(r - a.mean()) < 1e-12
    assert 0.7 < se / (a.std() / np.sqrt(len(a))) < 1.3


def test_tabla_de_enlace_por_hogar(datos):
    """El archivo que leen los demás módulos: una fila por hogar en su
    orden, probabilidades que suman 1, A/B = A + B, y FEFI de su celda."""
    from src.emparejamiento.fhdi.enlace import tabla_enlace
    rec, don = datos
    rec = rec.assign(llave_hogar=[f"h{i}" for i in range(len(rec))])
    t = tabla_enlace(rec, don)
    assert len(t) == len(rec) and (t["llave_hogar"] == rec["llave_hogar"]).all()
    p = t[[f"fhdi_p_{g}" for g in "ABCD"]].to_numpy()
    assert np.allclose(p.sum(axis=1), 1)
    assert np.allclose(t["fhdi_p_AB"], p[:, 0] + p[:, 1])
    pi, nivel = reglas.probabilidades(rec, don)
    assert np.allclose(p, pi) and (t["fhdi_nivel"].to_numpy() == nivel).all()
    exactos = t["fhdi_nivel"] == "celda_exacta"
    tam = construir_celda(don, edad_en_codigos=True).value_counts()
    assert (t.loc[exactos, "fhdi_donantes_celda"].to_numpy() == tam.loc[t.loc[exactos, "_hotdeck_celda"]].to_numpy()).all()
