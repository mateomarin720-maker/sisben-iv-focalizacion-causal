"""Celda del Hot-Deck con nivel de pisos homologado (2026-11-02)."""
import pandas as pd
import pytest

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import construir_celda, hotdeck, nivel_pisos


def _geih(**kw):
    base = dict(geo_depto=["05"], jefe_edad=[40], viv_cuartos=[2], viv_pisos=["1"], fex=[1.0])
    base.update(kw)
    return pd.DataFrame(base)


def _sisben(**kw):
    base = dict(geo_depto=["05"], jefe_edad=["5"], viv_cuartos=[2], viv_pisos=["5"],
                Grupo=["A"], Nivel=["A1"], Clasificacion=["A1"])
    base.update(kw)
    return pd.DataFrame(base)


def test_pisos_se_homologan_en_sentido_contrario():
    # Tierra es 1 en GEIH y 5 en el Sisbén; acabado es 4-7 en GEIH y 1-2 en el Sisbén.
    assert nivel_pisos(pd.DataFrame({"viv_pisos": ["1", "4", "2"]}), sisben=False).tolist() == \
        ["tierra", "acabado", "cemento_madera"]
    assert nivel_pisos(pd.DataFrame({"viv_pisos": [5, 1.0, "3"]}), sisben=True).tolist() == \
        ["tierra", "acabado", "cemento_madera"]


def test_celda_igual_entre_fuentes():
    assert construir_celda(_geih()).iloc[0] == construir_celda(_sisben(), edad_en_codigos=True).iloc[0] \
        == "05|ciclo5|2cuartos|tierra"
    assert construir_celda(_geih(), incluir_pisos=False).iloc[0] == "05|ciclo5|2cuartos"


def test_hotdeck_respalda_sin_pisos():
    rec = pd.concat([_geih(), _geih(viv_pisos=["4"])], ignore_index=True)
    out = hotdeck(rec, _sisben())
    assert out["_hotdeck_nivel"].tolist() == ["celda_exacta", "sin_pisos"]
    assert out["viv_pisos_nivel"].tolist() == ["tierra", "acabado"]
    assert out["Grupo_hotdeck"].tolist() == ["A", "A"]


def test_hotdeck_exige_pisos_en_el_donante():
    with pytest.raises(ValueError):
        hotdeck(_geih(), _sisben().drop(columns="viv_pisos"))


def test_hotdeck_celda_anterior():
    out = hotdeck(_geih(viv_pisos=["4"]), _sisben(), incluir_pisos=False)
    assert out["_hotdeck_nivel"].iloc[0] == "celda_exacta"
    assert out["_hotdeck_celda"].iloc[0] == "05|ciclo5|2cuartos"
