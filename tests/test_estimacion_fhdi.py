"""Modos `fhdi` e `intra_celda` de `src/5_estimacion.py` (fase 4 de
`docs/metodologia/METODOLOGIA_FHDI.md`): con el tratamiento fraccional el
efecto no es identificable; dentro de la celda, LinearDML coincide con la
regresión con efectos fijos aunque la celda confunda."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tests.test_estimacion_dml import _datos, est5


def test_t_funcion_del_grupo_no_deja_variacion_dentro():
    rng = np.random.default_rng(0)
    grupo = rng.integers(0, 50, 5_000)
    p = rng.uniform(0.1, 0.9, 50)
    assert est5._fraccion_dentro(p[grupo], grupo) < 1e-20
    assert est5._fraccion_dentro((rng.random(5_000) < p[grupo]).astype(float), grupo) > 0.5


def test_modo_fhdi_marca_no_identificable_con_las_dos_w(capsys):
    d = _datos(1)
    d["T_fhdi"] = d["p_empirica"]
    d["T"] = d["T"].astype(int)
    for c in est5.W_PROXY[0] + est5.W_PROXY[1]:  # W_PROXY más fino que la celda, como en los datos reales
        d[c] = d["hotdeck_celda_cat"] * 10 + np.arange(len(d)) % 3 if c == "jefe_edad" else d["hotdeck_celda_cat"]
    fr = est5._fhdi(d)
    assert fr["dentro_celda"] < 1e-10 and fr["dentro_proxy"] < 1e-10
    assert capsys.readouterr().out.count("NO IDENTIFICABLE") == 2


def test_con_fhdi_exige_el_mismo_orden_de_hogares(tmp_path):
    llaves = pd.DataFrame({"llave_directorio": ["01", "2", "3.0"], "llave_secuencia_p": "1", "llave_hogar": "1",
                           "mes": ["1", "1", "2"]})
    f = llaves.assign(llave_directorio=["1", "2.0", "3"], fhdi_p_AB=[0.2, 0.5, 0.7])
    f.to_parquet(tmp_path / "fhdi.parquet")
    assert est5._con_fhdi(llaves, tmp_path / "fhdi.parquet")["T_fhdi"].tolist() == [0.2, 0.5, 0.7]
    with pytest.raises(ValueError, match="mismo orden"):
        est5._con_fhdi(llaves.iloc[::-1].reset_index(drop=True), tmp_path / "fhdi.parquet")


@pytest.mark.parametrize("efecto", [0.0, 0.4])
def test_intra_celda_recupera_el_efecto_con_confusion_entre_celdas(efecto, capsys):
    """Y depende de P(T | celda): sin quitar la celda, la diferencia de
    medias se sesga; dentro de la celda, la regresión y el LinearDML dan
    el efecto."""
    d = _datos(2, n=12_000, efecto=efecto)
    sesgada = d.loc[d["T"] == 1, "Y"].mean() - d.loc[d["T"] == 0, "Y"].mean()
    r = est5._intra_celda(d, "Y")
    assert abs(sesgada - efecto) > 0.1
    assert r["regresion"] == pytest.approx(efecto, abs=0.04)
    assert r["linear_dml_intra"] == pytest.approx(r["regresion"], abs=0.02)
    assert "LinearDML dentro de la celda" in capsys.readouterr().out
