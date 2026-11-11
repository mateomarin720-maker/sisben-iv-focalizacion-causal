"""Variables candidatas para ampliar la medición de pobreza
(`src/diagnostico/variables_candidatas_pobreza.py`), con datos sintéticos."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.diagnostico import variables_candidatas_pobreza as vc

CANDIDATAS = [c for g in vc.GRUPOS.values() for c in g]


def _personas() -> pd.DataFrame:
    """Hogar 1: jefa con dos menores, sin cónyuge. Hogar 2: jefe con cónyuge."""
    filas = [
        dict(HOGAR="1", ORDEN="1", P6050="1", P6040="40", P6071=None, P6080="5", P2057="1", P2061="2", P6070="6", P3042="3",
             P3373="1", P3374="1", P3382="2", P3384="2", P3094="2", P3095="1", P3092=None, OCI="1", P6430="4",
             es_victima="1", es_desplazado="1"),
        dict(HOGAR="1", ORDEN="2", P6050="3", P6040="10", P6071=None, P6080="5", P2057="2", P2061="2", P6070=None, P3042="3",
             P3373="1", P3374="1", P3382="2", P3384="2", P3094=None, P3095=None, P3092=None, OCI=None, P6430=None,
             es_victima=None, es_desplazado=None),
        dict(HOGAR="1", ORDEN="3", P6050="3", P6040="5", P6071=None, P6080="5", P2057="2", P2061="2", P6070=None, P3042="2",
             P3373="1", P3374="1", P3382="1", P3384="2", P3094=None, P3095=None, P3092=None, OCI=None, P6430=None,
             es_victima=None, es_desplazado=None),
        dict(HOGAR="2", ORDEN="1", P6050="1", P6040="65", P6071="1", P6080="6", P2057="2", P2061="1", P6070="3", P3042="10",
             P3373="3", P3374="3", P3382="4", P3384="3", P3094="2", P3095="2", P3092="1", OCI=None, P6430=None,
             es_victima=None, es_desplazado=None),
        dict(HOGAR="2", ORDEN="2", P6050="2", P6040="30", P6071="1", P6080="6", P2057="2", P2061="1", P6070="3", P3042="5",
             P3373="1", P3374="1", P3382="2", P3384="2", P3094="2", P3095="2", P3092="2", OCI="1", P6430="1",
             es_victima=None, es_desplazado=None),
    ]
    p = pd.DataFrame(filas).assign(DIRECTORIO="7", SECUENCIA_P="1")
    for c in vc.DIFICULTADES:
        p[c] = "4"
    return p


def _hogar(h: pd.DataFrame, n: str) -> pd.Series:
    return h[h["HOGAR"] == n].iloc[0]


def test_composicion_del_hogar():
    h = vc.agregar_personas(_personas())
    uno, dos = _hogar(h, "1"), _hogar(h, "2")
    assert (uno["n_menores"], uno["n_mayores"]) == (2, 0) and uno["razon_dependencia"] == 2
    assert uno["monoparental"] == 1 and dos["monoparental"] == 0
    assert uno["tasa_ocupados"] == 1 and dos["tasa_ocupados"] == 0.5
    assert uno["adulto_educ_superior"] == 0 and dos["adulto_educ_superior"] == 1  # universitaria, adulto


def test_educacion_superior_de_un_menor_no_cuenta():
    p = _personas()
    p.loc[p["ORDEN"] == "2", "P3042"] = "10"
    assert _hogar(vc.agregar_personas(p), "1")["adulto_educ_superior"] == 0


def test_candidatas_del_jefe_y_de_algun_miembro():
    h = vc.agregar_personas(_personas())
    uno, dos = _hogar(h, "1"), _hogar(h, "2")
    assert uno["jefe_afro"] == 1 and uno["jefe_campesino"] == 1 and uno["hog_animales"] == 1
    assert uno["hog_victima"] == 1 and uno["hog_desplazado"] == 1 and dos["hog_victima"] == 0
    assert dos["hog_nacido_exterior"] == 1 and dos["jefe_extranjero"] == 1
    assert dos["hog_migrante_12m"] == 1 and dos["hog_migrante_5a"] == 1 and uno["hog_migrante_5a"] == 0
    assert dos["hog_trae_agua"] == 1 and dos["jefe_comunidad_campesina"] == 1
    assert dos["jefe_ocupacion"] == "no_ocupado" and uno["jefe_ocupacion"] == "4"


def test_discapacidad_solo_con_no_puede_o_mucha_dificultad():
    """En `P1906`: 1 no puede, 2 mucha, 3 alguna, 4 ninguna (verificado con el
    gradiente por edad)."""
    p = _personas()
    p.loc[p["ORDEN"] == "2", "P1906S3"] = "3"  # alguna: no cuenta
    p.loc[(p["HOGAR"] == "2") & (p["ORDEN"] == "2"), "P1906S4"] = "2"  # mucha, del cónyuge
    h = vc.agregar_personas(p)
    assert _hogar(h, "1")["hog_discapacidad"] == 0
    assert _hogar(h, "2")["hog_discapacidad"] == 1 and _hogar(h, "2")["jefe_discapacidad"] == 0
    p.loc[(p["HOGAR"] == "2") & (p["ORDEN"] == "1"), "P1906S1"] = "1"
    assert _hogar(vc.agregar_personas(p), "2")["jefe_discapacidad"] == 1


def test_productos_financieros_sin_confundir_columnas():
    v = pd.DataFrame({c: ["1"] for c in vc.K3})
    for c in list(vc.HOGAR_VIVIENDA) + list(vc.FINANCIEROS) + vc.FIN_CORRIENTE_CDT:
        v[c] = [pd.NA]
    v["P5222S2"], v["P5222S3"] = "1", "1"
    h = vc.variables_vivienda(v).iloc[0]
    assert h["fin_ahorros"] == 1 and h["fin_corriente_cdt"] == 1
    assert h["fin_ninguno"] == 0 and h["fin_tarjeta"] == 0


def test_auc_ponderada():
    y = np.array([0.0, 0, 1, 1])
    w = np.ones(4)
    assert vc.auc_ponderada(y, np.array([0.1, 0.2, 0.8, 0.9]), w) == 1
    assert vc.auc_ponderada(y, np.array([0.9, 0.8, 0.2, 0.1]), w) == 0
    assert vc.auc_ponderada(y, np.full(4, 0.5), w) == 0.5  # empates
    # Un peso de 2 equivale a repetir la fila.
    y2, p2 = np.array([0.0, 1, 1, 0, 1]), np.array([0.3, 0.2, 0.9, 0.5, 0.4])
    w2 = np.array([1.0, 2, 1, 3, 1])
    assert vc.auc_ponderada(y2, p2, w2) == pytest.approx(vc.auc_ponderada(np.repeat(y2, w2.astype(int)),
                                                                          np.repeat(p2, w2.astype(int)), np.ones(8)))


def test_errores_de_focalizacion_con_presupuesto():
    y = np.array([1.0, 1, 0, 0, 1, 0])
    p = np.array([0.9, 0.2, 0.8, 0.1, 0.7, 0.3])
    w = np.ones(6)
    elegidos = vc.seleccionados(p, w, 0.5)
    assert elegidos.tolist() == [True, False, True, False, True, False]
    exclusion, inclusion = vc.errores_focalizacion(y, elegidos, w)
    assert exclusion == pytest.approx(1 / 3)  # un pobre de tres no elegido
    assert inclusion == pytest.approx(1 / 3)  # un no pobre entre los tres elegidos
    # Con menos pobres que elegidos las dos tasas difieren: no se pueden intercambiar.
    exclusion, inclusion = vc.errores_focalizacion(np.array([1.0, 1, 0, 0, 0, 0]), np.array([True, False, True, True, False, False]), w)
    assert exclusion == pytest.approx(1 / 2) and inclusion == pytest.approx(2 / 3)
    # El presupuesto cuenta peso, no hogares.
    assert vc.seleccionados(p, np.array([3.0, 1, 1, 1, 1, 1]), 0.5).sum() == 2  # 3 + 1 = 4 de 8


def test_holm():
    p = pd.Series([0.01, 0.04, 0.03], index=list("abc"))
    assert vc.holm(p).round(6).to_dict() == {"a": 0.03, "b": 0.06, "c": 0.06}


FILA = dict(wald_holm=0.001, d_exclusion=-0.01, d_exclusion_hi=-0.005, d_auc_lo=0.001, d_exclusion_temporal=-0.01,
            d_exclusion_depto=-0.01, d_exclusion_urbano=-0.01, d_exclusion_rural=-0.01, d_exclusion_sin_grupo=-0.002)


def test_decidir_recomienda_solo_con_mejora_clara_y_estable():
    assert vc.decidir(FILA) == "recomendar"


@pytest.mark.parametrize("cambio", [dict(d_exclusion=-0.003), dict(d_exclusion_temporal=0.001), dict(d_exclusion_depto=0.001),
                                    dict(d_exclusion_urbano=0.001), dict(d_exclusion_rural=0.001),
                                    dict(d_exclusion_sin_grupo=0.001)])
def test_decidir_sin_mejora_grande_o_estable_baja_a_considerar(cambio):
    assert vc.decidir({**FILA, **cambio}) == "considerar"


def test_decidir_sin_significancia_o_sin_mejora_no_recomienda():
    assert vc.decidir({**FILA, "wald_holm": 0.2}) == "no_recomendar"
    assert vc.decidir({**FILA, "d_exclusion": -0.001, "d_exclusion_hi": 0.002, "d_auc_lo": -0.001}) == "no_recomendar"
    # La mejora puntual sin IC que excluya el cero tampoco basta para recomendar.
    assert vc.decidir({**FILA, "d_exclusion_hi": 0.001}) == "considerar"


def _tabla(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = pd.DataFrame(index=range(n))
    for c in vc.FICHA_CAT:
        t[c] = rng.choice(["1", "2", "3"], n)
    t["estrato"] = rng.choice(["0", "1", "2"], n)
    for c in vc.FICHA_NUM + vc.DERIVADAS:
        t[c] = rng.integers(0, 6, n).astype(float)
    t["hacinamiento"] = rng.integers(0, 2, n).astype(float)
    for c in CANDIDATAS:
        if c != "estrato":
            t[c] = rng.integers(0, 2, n).astype(float)
    return t


def test_categoricas_nunca_como_numero_y_binarias_quedan_0_1():
    X, mapa = vc.matriz(_tabla())
    for v in vc.CATEGORICAS:
        assert v not in X.columns, f"{v} entró como número"
        assert sum(m == v for m in mapa.values()) >= 2, f"{v} sin indicadoras"
    assert {"estrato_0", "estrato_1", "estrato_2"} <= set(X.columns)
    assert set(X["fin_ahorros"].unique()) <= {0, 1} and set(X["hacinamiento"].unique()) <= {0, 1}
    assert abs(X["viv_cuartos"].mean()) < 1e-5  # las demás, estandarizadas


def test_ninguna_entrada_mide_el_ingreso_ni_usa_las_privaciones_del_sisben():
    variables = set(vc.FICHA_CAT + vc.FICHA_NUM + vc.DERIVADAS + CANDIDATAS)
    prohibidas = {f"I{i}" for i in range(1, 16)} | {"H_5", "P5100", "P5110", "P5130", "P5140", "P6120", "ingreso_percapita",
                                                    "brecha_pobreza_monetaria", "personas_ug", *vc.OUTCOMES}
    assert not variables & prohibidas
    assert not set(vc.HOGAR_VIVIENDA) & prohibidas


def test_referencia_sin_candidatas_y_cada_modelo_agrega_su_grupo():
    specs = vc.especificaciones(vc.PRINCIPAL)
    base = set(specs["ficha_derivadas"])
    assert not base & set(CANDIDATAS)
    assert set(vc.DERIVADAS) <= base and set(specs["canonico"]) < set(specs["ficha"]) < base
    for g, cols in vc.GRUPOS.items():
        assert set(specs[f"+{g}"]) == base | set(cols)
        assert set(specs[f"todo-{g}"]) == (base | set(CANDIDATAS)) - set(cols)


def test_el_ipm_no_se_predice_con_sus_componentes():
    specs = vc.especificaciones("POBRE_GEIH")
    for modelo in specs.values():
        assert not set(modelo) & vc.MECANICAS_IPM
    assert vc.especificaciones(vc.PRINCIPAL)["ficha_derivadas"].count("hacinamiento") == 1


def test_una_vivienda_queda_en_un_solo_pliegue():
    viviendas = np.array(["a", "b", "a", "c", "b", "d", "a"] * 20)
    pliegues = vc.particion_por_grupo(viviendas, 3)
    for v in np.unique(viviendas):
        assert len(set(pliegues[viviendas == v])) == 1
    assert set(pliegues) <= {0, 1, 2}


def test_comparar_mide_la_diferencia_pareada():
    rng = np.random.default_rng(0)
    n = 4000
    y = rng.integers(0, 2, n).astype(float)
    pobre = 0.3 * y + rng.random(n)
    pred = {"ref": pobre, "mejor": 2 * y + rng.random(n), "igual": pobre.copy()}
    _, d = vc.comparar(pred, y, np.ones(n), rng.random(n) < 0.5, np.arange(n), 0.5, [("mejor", "ref"), ("igual", "ref")])
    auc = d[d["metrica"] == "auc"].set_index("modelo")
    assert auc.loc["mejor", "ic_lo"] > 0.1
    assert auc.loc["igual", ["delta", "ic_lo", "ic_hi"]].abs().max() == 0  # mismos pesos en ambos modelos
    assert d[(d["metrica"] == "exclusion") & (d["modelo"] == "mejor")].iloc[0]["ic_hi"] < 0


def test_logit_agrupado_coincide_con_statsmodels():
    sm = pytest.importorskip("statsmodels.api")
    rng = np.random.default_rng(1)
    n, G = 6000, 25
    g = rng.integers(0, G, n)
    Z = np.column_stack([rng.normal(size=n), rng.integers(0, 2, n)]).astype(float)
    y = (rng.random(n) < 1 / (1 + np.exp(-(0.3 + 0.8 * Z[:, 0] - 0.5 * Z[:, 1] + rng.normal(0, 0.3, G)[g])))).astype(float)
    w = rng.uniform(0.5, 2, n)
    beta, V, grupos = vc.logit_agrupado(Z, y, w, g, C=1e8)
    r = sm.GLM(y, sm.add_constant(Z), family=sm.families.Binomial(), var_weights=w / w.mean()).fit(
        cov_type="cluster", cov_kwds={"groups": g, "use_correction": False})
    assert grupos == G
    np.testing.assert_allclose(beta, r.params, atol=1e-3)
    np.testing.assert_allclose(np.sqrt(np.diag(V)) / np.sqrt(G / (G - 1)), r.bse, rtol=1e-3)


def test_significancia_detecta_el_candidato_con_senal():
    """Solo `fin_ahorros` predice, en contra de la pobreza. Se detecta, el cambio
    de probabilidad tiene su signo y los demás grupos no pasan Holm."""
    rng = np.random.default_rng(2)
    n = 20_000
    t = _tabla(n, seed=2)
    y = (rng.random(n) < 1 / (1 + np.exp(-(0.2 - 1.2 * t["fin_ahorros"].to_numpy())))).astype(float)
    X, mapa = vc.matriz(t)
    columnas = np.arange(X.shape[1])
    deptos = rng.integers(0, 30, n)
    tabla, grupos = vc.significancia(X, y, np.ones(n), deptos, mapa, columnas)
    fila = tabla.set_index("variable").loc["fin_ahorros"]
    assert fila["p_holm"] < 0.05 and -0.3 < fila["cambio_prob"] < -0.2
    assert fila["tasa_con"] < fila["tasa_sin"]
    grupos = grupos.set_index("grupo")
    assert grupos.loc["inclusion_financiera", "wald_holm"] < 0.05
    assert grupos.drop(index="inclusion_financiera")["wald_holm"].min() > 0.05
    # La categórica se mide contra su referencia: una fila menos que categorías.
    assert tabla["variable"].str.startswith("estrato_").sum() == 2


def test_cuenta_segun_transferencia_compara_dentro_de_cada_poblacion():
    """Los que reciben ayuda tienen menos cuenta, dentro de pobres y no pobres,
    aunque en el total la composición pese: el cambio ajustado conserva el signo."""
    rng = np.random.default_rng(3)
    n = 20_000
    pobre = rng.random(n) < 0.3
    ayuda = rng.random(n) < np.where(pobre, 0.3, 0.1)
    cuenta = rng.random(n) < np.where(pobre, 0.4, 0.8) - 0.15 * ayuda
    t = pd.DataFrame({"ayuda_gobierno": ayuda, "fin_ahorros": cuenta.astype(float), vc.PRINCIPAL: pobre.astype(float),
                      "geo_depto": rng.integers(0, 30, n).astype(str), "pobre": pobre.astype(float)})
    tabla = vc.cuenta_segun_transferencia(t, t[["pobre"]], {}, np.ones(n), np.array([0])).set_index("poblacion")
    assert tabla.loc["pobres", "pct_con_ayuda"] == pytest.approx(30, abs=2)
    for poblacion in ("pobres", "no_pobres"):
        assert tabla.loc[poblacion, "cuenta_sin_ayuda"] - tabla.loc[poblacion, "cuenta_con_ayuda"] == pytest.approx(15, abs=4)
    assert tabla["cambio_ajustado_pp"].iloc[0] == pytest.approx(-15, abs=4)
    assert tabla["p_ajustado"].iloc[0] < 0.05


def test_poblacion_por_atributo_cuenta_hogares_y_personas():
    X = pd.DataFrame({"fin_ahorros": [1.0, 1, 0, 0]})
    h = np.array([10.0, 20, 30, 40])
    n = h * np.array([2.0, 3, 4, 5])
    pobre = np.array([True, False, True, False])
    f = vc.poblacion_por_atributo(pd.DataFrame(), X, h, n, pobre, ["fin_ahorros"], {"fin_ahorros": "fin_ahorros"}).iloc[0]
    assert (f["hogares_con"], f["personas_con"], f["hogares_pobres_con"], f["personas_pobres_con"]) == (30, 80, 10, 20)
    assert (f["hogares_sin"], f["personas_sin"], f["hogares_pobres_sin"], f["personas_pobres_sin"]) == (70, 320, 30, 120)
    assert f["pct_pobreza_con"] == pytest.approx(100 / 3)


def test_flujo_entre_modelos_separa_a_quienes_entran_y_salen():
    pobre = np.array([True, True, True, False])
    ref = np.array([True, True, False, True])
    mod = np.array([True, False, True, False])
    h, n = np.array([1.0, 2, 5, 9]), np.array([3.0, 8, 25, 40])
    f = vc.flujo_entre_modelos(pobre, ref, mod, h, n)
    assert (f["hogares_pobres_entran"], f["hogares_pobres_salen"], f["hogares_pobres_neto"]) == (5, 2, 3)
    assert (f["personas_pobres_entran"], f["personas_pobres_salen"], f["personas_pobres_neto"]) == (25, 8, 17)
