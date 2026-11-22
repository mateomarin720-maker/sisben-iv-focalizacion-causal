"""Celda del Hot-Deck: pisos homologados (2026-11-02) y tramos de personas
y menores (2026-11-14), con su cadena de respaldos."""
import pandas as pd
import pytest

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import (
    CELDA_COLUMNAS, claves_por_nivel, construir_celda, hotdeck, nivel_pisos, tramo_menores, tramo_personas,
)

CELDA = "05|ciclo5|2cuartos|tierra|3omaspersonas|1menor"


def _geih(**kw):
    base = dict(geo_depto=["05"], jefe_edad=[40], viv_cuartos=[2], viv_pisos=["1"], hog_num_personas=["3"],
                hog_num_menores=[1], fex=[1.0])
    base.update(kw)
    return pd.DataFrame(base)


def _sisben(**kw):
    base = dict(geo_depto=["05"], jefe_edad=["5"], viv_cuartos=[2], viv_pisos=["5"], hog_num_personas=[3],
                hog_num_menores=["1"], Grupo=["A"], Nivel=["A1"], Clasificacion=["A1"], fex=[1.0])
    base.update(kw)
    return pd.DataFrame(base)


def test_pisos_se_homologan_en_sentido_contrario():
    # Tierra es 1 en GEIH y 5 en el Sisbén; acabado es 4-7 en GEIH y 1-2 en el Sisbén.
    assert nivel_pisos(pd.DataFrame({"viv_pisos": ["1", "4", "2"]}), sisben=False).tolist() == \
        ["tierra", "acabado", "cemento_madera"]
    assert nivel_pisos(pd.DataFrame({"viv_pisos": [5, 1.0, "3"]}), sisben=True).tolist() == \
        ["tierra", "acabado", "cemento_madera"]


def test_tramos_de_personas_y_menores():
    """Personas: 1-2, 3 o más; menores: 0, 1, 2 o más. Los conteos
    llegan como texto o número según la fuente; faltante o 0 personas: NA."""
    d = pd.DataFrame({"hog_num_personas": ["1", 2, "3", 4.0, "5", "12", None, "0"],
                      "hog_num_menores": [0, "0", 1, "1", 2, "7", None, "x"]})
    assert tramo_personas(d).tolist() == ["1a2personas", "1a2personas", "3omaspersonas", "3omaspersonas",
                                          "3omaspersonas", "3omaspersonas", "NA", "NA"]
    assert tramo_menores(d).tolist() == ["0menores", "0menores", "1menor", "1menor", "2omasmenores",
                                         "2omasmenores", "NA", "NA"]


def test_celda_igual_entre_fuentes():
    assert construir_celda(_geih()).iloc[0] == construir_celda(_sisben(), edad_en_codigos=True).iloc[0] == CELDA
    assert construir_celda(_geih(), incluir_menores=False).iloc[0] == "05|ciclo5|2cuartos|tierra|3omaspersonas"
    assert construir_celda(_geih(), incluir_personas=False).iloc[0] == "05|ciclo5|2cuartos|tierra"
    assert construir_celda(_geih(), incluir_pisos=False).iloc[0] == "05|ciclo5|2cuartos"
    assert construir_celda(_geih(), incluir_vivienda=False).iloc[0] == "05|ciclo5"
    assert set(CELDA_COLUMNAS) <= set(_geih().columns) and set(CELDA_COLUMNAS) <= set(_sisben().columns)


def test_cadena_de_respaldos_suelta_primero_lo_que_menos_aporta():
    assert [n for n, _ in claves_por_nivel(_geih())] == \
        ["celda_exacta", "sin_menores", "sin_personas", "sin_pisos", "solo_depto_edad", "solo_depto"]
    assert [n for n, _ in claves_por_nivel(_geih(), incluir_menores=False)] == \
        ["celda_exacta", "sin_personas", "sin_pisos", "solo_depto_edad", "solo_depto"]
    assert [n for n, _ in claves_por_nivel(_geih(), incluir_personas=False)] == \
        ["celda_exacta", "sin_pisos", "solo_depto_edad", "solo_depto"]
    assert [n for n, _ in claves_por_nivel(_geih(), incluir_vivienda=False)] == ["celda_exacta", "solo_depto"]
    claves = dict(claves_por_nivel(_geih()))
    assert claves["sin_personas"].iloc[0] == "05|ciclo5|2cuartos|tierra" and claves["solo_depto"].iloc[0] == "05"


def test_hotdeck_respalda_por_niveles():
    rec = pd.concat([_geih(), _geih(hog_num_menores=[3]), _geih(hog_num_personas=["1"]), _geih(viv_pisos=["4"])],
                    ignore_index=True)
    out = hotdeck(rec, _sisben())
    assert out["_hotdeck_nivel"].tolist() == ["celda_exacta", "sin_menores", "sin_personas", "sin_pisos"]
    assert out["_hotdeck_celda"].iloc[0] == CELDA
    assert out["viv_pisos_nivel"].tolist() == ["tierra", "tierra", "tierra", "acabado"]
    assert out["Grupo_hotdeck"].tolist() == ["A"] * 4


def test_hotdeck_exige_las_columnas_de_la_celda():
    """Sin la columna, todo caería al respaldo sin dar error."""
    for columna in ("viv_pisos", "hog_num_personas", "hog_num_menores"):
        with pytest.raises(ValueError, match=columna):
            hotdeck(_geih(), _sisben().drop(columns=columna))
    out = hotdeck(_geih(), _sisben().drop(columns="hog_num_menores"), incluir_menores=False)
    assert out["_hotdeck_celda"].iloc[0] == "05|ciclo5|2cuartos|tierra|3omaspersonas"


def test_hotdeck_celda_anterior():
    out = hotdeck(_geih(viv_pisos=["4"], hog_num_personas=["1"]), _sisben(), incluir_personas=False)
    assert out["_hotdeck_nivel"].iloc[0] == "sin_pisos"
    out = hotdeck(_geih(viv_pisos=["4"]), _sisben(), incluir_pisos=False)
    assert out["_hotdeck_nivel"].iloc[0] == "celda_exacta"
    assert out["_hotdeck_celda"].iloc[0] == "05|ciclo5|2cuartos"


def test_hotdeck_sortea_los_donantes_por_su_factor_de_expansion():
    """El Sisbén nacional es una muestra expandible: un donante con fex 9
    representa 9 hogares. Sin ponderar (el error hasta el 2026-11-21) los
    dos donantes saldrían la mitad de las veces cada uno."""
    import numpy as np
    don = pd.concat([_sisben(), _sisben(Grupo=["D"], Nivel=["D1"], Clasificacion=["D1"], fex=[1.0])],
                    ignore_index=True)
    don.loc[0, "fex"] = 9.0
    rec = pd.concat([_geih()] * 4000, ignore_index=True)
    out = hotdeck(rec, don)
    assert (out["_hotdeck_nivel"] == "celda_exacta").all()
    assert np.mean(out["Grupo_hotdeck"] == "A") == pytest.approx(0.9, abs=0.02)


def test_hotdeck_exige_el_factor_de_expansion_del_donante():
    with pytest.raises(ValueError, match="fex"):
        hotdeck(_geih(), _sisben().drop(columns="fex"))
    with pytest.raises(ValueError, match="fex"):
        hotdeck(_geih(), _sisben(fex=[0.0]))
