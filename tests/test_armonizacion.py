"""Armonización de GEIH y del Sisbén al esquema canónico.

El mapeo de vivienda de GEIH estuvo equivocado hasta el 2026-10-28
(`viv_paredes` leía pisos, `viv_pisos` leía energía eléctrica,
`viv_cuartos` leía cuartos para dormir) sin dar error: los códigos
"sonaban" bien. Estas pruebas fijan cada código contra la etiqueta del
diccionario oficial y prueban la armonización con datos sintéticos."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.armonizacion import armonizar_geih_hogar_2024 as geih
from src.armonizacion import armonizar_sisben_bogota_sdp as sdp
from src.armonizacion import armonizar_sisben_hogar_2024 as sisben

ROOT = Path(__file__).resolve().parents[1]
DIC_GEIH = ROOT / "docs" / "insumos" / "DICCIONARIO_GEIH_2024.xlsx"
DIC_SISBEN = ROOT / "docs" / "insumos" / "DICCIONARIO_SISBEN_2024.xlsx"

# Variable canónica -> palabra que debe aparecer en la etiqueta oficial del código que se le asigna.
ETIQUETA_GEIH = {
    "viv_paredes": "paredes", "viv_pisos": "pisos", "viv_cuartos": "cuartos en total",
    "viv_cuartos_dormir": "duermen", "viv_alcantarillado": "alcantarillado", "viv_acueducto": "acueducto",
    "hog_num_personas": "total de personas", "geo_zona": "clase", "geo_depto": "departamento",
    "jefe_sexo": "sexo", "jefe_edad": "años cumplidos",
}
ETIQUETA_SISBEN = {
    "viv_paredes": "paredes", "viv_pisos": "pisos", "viv_cuartos": "cuartos",
    "viv_alcantarillado": "alcantarillado", "viv_acueducto": "acueducto",
    "hog_num_personas": "total de personas", "geo_zona": "zona", "jefe_sexo": "sexo", "jefe_edad": "edad",
}


def _etiquetas(ruta: Path, col_codigo: str, col_etiqueta: str, hojas=None) -> dict[str, str]:
    d = pd.read_excel(ruta, sheet_name=hojas)
    d = pd.concat(d.values()) if isinstance(d, dict) else d
    return dict(zip(d[col_codigo].astype(str).str.upper(), d[col_etiqueta].astype(str).str.lower()))


# --------------------------------------------------------------------------
# Códigos contra el diccionario oficial
# --------------------------------------------------------------------------

def test_codigos_geih_coinciden_con_el_diccionario():
    etiquetas = _etiquetas(DIC_GEIH, "Nombre", "Etiqueta")
    mapa = {**geih.MAPA_HOGAR_VIVIENDA, **geih.MAPA_JEFE}
    for codigo, canonica in mapa.items():
        if canonica not in ETIQUETA_GEIH:
            continue
        assert codigo in etiquetas, f"{codigo} no está en el diccionario de GEIH"
        assert ETIQUETA_GEIH[canonica] in etiquetas[codigo], (
            f"{canonica} lee {codigo} ('{etiquetas[codigo]}'), que no es '{ETIQUETA_GEIH[canonica]}'")
    assert set(ETIQUETA_GEIH) <= set(mapa.values()), "falta mapear una variable canónica"


def test_variables_candidatas_leen_la_pregunta_correcta():
    """`variables_candidatas_pobreza.py`: cada código contra la pregunta del
    diccionario, incluida la lista de categorías cuando la trae."""
    d = pd.read_excel(DIC_GEIH)
    pregunta = {n: f"{e} {q}".lower() for n, e, q in zip(d["Nombre"], d["Etiqueta"], d["Pregunta"])}
    esperado = {
        "P5222S1": "cuenta corriente", "P5222S2": "cuenta de ahorros", "P5222S3": "cdt",
        "P5222S4": "compra de vivienda", "P5222S5": "compra de vehículo", "P5222S6": "libre inversión",
        "P5222S7": "tarjeta de crédito", "P5222S8": "8 otro", "P5222S9": "9 ninguno",
        "P4030S1A1": "estrato", "P4000": "tipo de vivienda", "P4030S1": "energía eléctrica", "P4030S2": "gas natural",
        "P4030S4": "recolección de basuras", "P70": "cuántos hogares", "P5020": "servicio sanitario",
        "P5030": "uso exclusivo", "P5040": "basura", "P5050": "agua para consumo", "P5070": "preparan los alimentos",
        "P5080": "combustible", "P5090": "vivienda ocupada", "P6070": "actualmente", "P6071": "cónyuge",
        "P3042": "mayor nivel educativo", "P6430": "en este trabajo", "OCI": "ocupada",
        "P6080": "1 indígena", "P2057": "campesino", "P2061": "comunidad en que vive",
        "P1906S1": "oír", "P1906S3": "ver", "P1906S4": "caminar", "P1906S7": "comer",
        "P3373": "dónde nació", "P3374": "nacionalidad", "P3382": "hace 5 años", "P3384": "hace 12 meses",
        "P3092": "traer agua", "P3094": "huerta", "P3095": "criar animales",
        "P750S2": "entidades del gobierno", "P1661S1": "familias en acción", "P1661S2": "jóvenes en acción",
        "P1661S3": "colombia mayor",
    }
    for codigo, palabra in esperado.items():
        assert palabra in pregunta[codigo], f"{codigo}: '{palabra}' no está en '{pregunta[codigo][:120]}'"


def test_el_jefe_de_geih_es_p6050():
    etiquetas = _etiquetas(DIC_GEIH, "Nombre", "Etiqueta")
    assert (geih.FILTRO_JEFE_COL, geih.FILTRO_JEFE_VAL) == ("P6050", "1")
    assert "parentesco" in etiquetas["P6050"]


def test_codigos_sisben_coinciden_con_el_diccionario():
    etiquetas = _etiquetas(DIC_SISBEN, "Nombre", "Etiqueta")
    mapa = {**sisben.MAPA_HOGAR, **sisben.MAPA_VIVIENDA, **sisben.MAPA_JEFE}
    for codigo, canonica in mapa.items():
        if canonica not in ETIQUETA_SISBEN:
            continue
        assert ETIQUETA_SISBEN[canonica] in etiquetas[codigo], (
            f"{canonica} lee {codigo} ('{etiquetas[codigo]}'), que no es '{ETIQUETA_SISBEN[canonica]}'")
    assert (sisben.FILTRO_JEFE_COL, sisben.FILTRO_JEFE_VAL) == ("PER003", "1")
    assert "parentesco" in etiquetas["PER003"]


# --------------------------------------------------------------------------
# GEIH con datos sintéticos
# --------------------------------------------------------------------------

def test_geih_lee_cada_variable_de_su_columna_y_cruza_el_jefe(tmp_path, monkeypatch):
    """Cada columna de vivienda trae un valor distinto, así que leer la
    columna equivocada (el error anterior) cambia el resultado. Las llaves
    llegan con formatos distintos en los dos módulos."""
    mes = tmp_path / "01"
    mes.mkdir()
    pd.DataFrame({
        "DIRECTORIO": ["7.0", "8.0"], "SECUENCIA_P": ["1", "1"], "HOGAR": ["1", "1"], "DPTO": ["05", "11"],
        "CLASE": ["1", "2"], "P4010": ["2", "9"], "P4020": ["3", "1"], "P4030S1": ["1", "2"],
        "P5000": ["4", "2"], "P5010": ["2", "1"], "P4030S3": ["1", "2"], "P4030S5": ["1", "1"],
        "P6008": ["3", "1"], "FEX_C18": ["100.5", "80"],
    }).to_parquet(mes / "hogar_vivienda.parquet")
    pd.DataFrame({
        "DIRECTORIO": ["7", "7", "7", "8"], "SECUENCIA_P": ["01", "01", "01", "1"], "HOGAR": ["1", "1", "1", "1"],
        "P6050": ["3", "1", "2", "1"], "P3271": ["1", "2", "1", "1"], "P6040": ["10", "45", "44", "70"],
    }).to_parquet(mes / "caracteristicas_generales.parquet")
    monkeypatch.setattr(geih, "GEIH_DIR", tmp_path)

    out = geih._cargar_mes("01").set_index("llave_directorio")
    assert out.loc["7", ["viv_paredes", "viv_pisos", "viv_cuartos", "viv_cuartos_dormir"]].tolist() == ["2", "3", "4", "2"]
    assert out.loc["8", ["viv_paredes", "viv_pisos", "viv_cuartos"]].tolist() == ["9", "1", "2"]
    assert out.loc["7", "jefe_edad"] == "45" and out.loc["7", "jefe_sexo"] == "2"
    assert out.loc["8", "jefe_edad"] == "70"
    assert len(out) == 2


# --------------------------------------------------------------------------
# Sisbén nacional con datos sintéticos
# --------------------------------------------------------------------------

def test_sisben_nacional_toma_al_jefe_y_conserva_el_codigo_de_edad(tmp_path, monkeypatch):
    llave = {"cod_mpio": ["05001", "11001"], "ZONA": ["1", "1"], "llave": ["a", "b"], "CORTE": ["SIV", "SIV"]}
    pd.DataFrame({**llave, "HOGAR": ["1", "1"], "HOG027": ["2", "1"], "FEX": ["1", "1"]}).to_parquet(tmp_path / "hogares.parquet")
    pd.DataFrame({**llave, "VIV002": ["1", "3"], "VIV003": ["2", "5"], "VIV005": ["1", "2"], "VIV008": ["1", "1"],
                  "VIV009": ["3", "1"]}).to_parquet(tmp_path / "viviendas.parquet")
    pd.DataFrame({
        "cod_mpio": ["05001", "05001", "11001", "11001"], "ZONA": "1", "llave": ["a", "a", "b", "b"], "CORTE": "SIV",
        "HOGAR": "1", "PER003": ["2", "1", "1", "1"], "PER001": ["1", "2", "1", "2"], "PER002": ["3", "5", "6", "4"],
        "Grupo": ["A", "A", "C", "C"], "Nivel": "1", "Clasificacion": ["A1", "A1", "C2", "C2"],
    }).to_parquet(tmp_path / "personas.parquet")
    monkeypatch.setattr(sisben, "SISBEN_DIR", tmp_path)

    out = sisben.armonizar_sisben_hogar().set_index("llave")
    assert len(out) == 2
    assert out.loc["a", ["jefe_sexo", "jefe_edad"]].tolist() == ["2", "5"]  # el jefe, con PER002 como código
    assert out.loc["b", "jefe_edad"] == "6"  # dos jefes marcados: se conserva el primero
    assert out.loc["a", ["viv_paredes", "viv_pisos", "viv_cuartos"]].tolist() == ["1", "2", "3"]
    assert out.loc["a", "geo_depto"] == "05" and out.loc["b", "geo_depto"] == "11"


# --------------------------------------------------------------------------
# Sisbén de Bogotá (SDP) con datos sintéticos
# --------------------------------------------------------------------------

def _csv_sdp(ruta: Path) -> Path:
    filas = [  # ficha, hogar, persona, parentesco, sexo, nacimiento, fin de encuesta
        ("1", "1", "1", "1", "2", "1990-06-01", "2022-05-10"),  # vigente (encuesta vieja)
        ("1", "1", "2", "3", "1", "2015-01-01", "2022-05-10"),
        ("2", "1", "1", "1", "4", "2008-01-01", "2024-06-30"),  # vigente y del año; sexo 4 inválido
        ("3", "1", "1", "1", "1", "1950-01-01", "2025-03-01"),  # posterior al corte
    ]
    cols = ["ide_ficha_origen", "ide_hogar", "ide_persona", "tip_parentesco", "sexo_persona", "fec_nacimiento",
            "fec_fin_encuesta"]
    d = pd.DataFrame(filas, columns=cols)
    for c in set(sdp.COLS) - set(cols):
        d[c] = "1"
    d["num_cuartos_vivienda"] = "3"
    d["Clasificacion"] = "B4"
    archivo = ruta / "sdp.csv"
    d[sdp.COLS].to_csv(archivo, sep=";", index=False, encoding="utf-8-sig")
    return archivo


def test_sdp_filtra_por_vigencia_no_por_anio_exacto(tmp_path):
    archivo = _csv_sdp(tmp_path)
    vig = sdp.armonizar_sisben_bogota(str(archivo), modo="vigencia")
    exacto = sdp.armonizar_sisben_bogota(str(archivo), modo="anio_exacto")
    assert sorted(vig["llave_directorio"]) == ["1", "2"]  # la encuesta de 2022 sigue vigente
    assert exacto["llave_directorio"].tolist() == ["2"]
    with pytest.raises(ValueError):
        sdp.armonizar_sisben_bogota(str(archivo), modo="otro")


def test_sdp_toma_al_jefe_y_lleva_la_edad_al_codigo_de_ciclo(tmp_path):
    vig = sdp.armonizar_sisben_bogota(str(_csv_sdp(tmp_path)), modo="vigencia").set_index("llave_directorio")
    assert vig.loc["1", "jefe_edad"] == "5"  # 34 años al 31-dic-2024
    assert vig.loc["2", "jefe_edad"] == "3"  # 16 años
    assert vig.loc["1", "hog_num_personas"] == 2
    assert vig.loc["1", "jefe_sexo"] == "2" and pd.isna(vig.loc["2", "jefe_sexo"])
    assert vig.loc["1", "Nivel"] == "4"


# --------------------------------------------------------------------------
# Selección de variables (OE1): sin circularidad
# --------------------------------------------------------------------------

def test_seleccion_de_variables_nunca_usa_las_privaciones_del_sisben():
    """`I1`-`I15` y `H_5` son privaciones que el propio Sisbén calcula para
    clasificar: usarlas para predecir el grupo es circular."""
    from src.estimacion import seleccion_variables_lasso_shap as sel

    prohibidas = {f"I{i}" for i in range(1, 16)} | {"H_5"}
    assert not prohibidas & set(sel.TODAS)
    rng = np.random.default_rng(0)
    n = 200
    df = pd.DataFrame({
        "hog_num_personas": rng.integers(1, 6, n), "viv_cuartos": rng.integers(1, 5, n), "jefe_edad": rng.integers(3, 7, n),
        **{c: rng.choice(["1", "2"], n) for c in sel.CATEGORICAS}, "geo_depto": rng.choice(["05", "11"], n),
        "Grupo": rng.choice(list("ABCD"), n), **{c: rng.integers(0, 2, n) for c in prohibidas},
    })
    X, y, mapa = sel._preparar(df)
    assert not prohibidas & set(mapa.values())
    assert not any(c.split("_")[0] in prohibidas or c.startswith("H_5") for c in X.columns)
    assert len(X) == n and set(y) <= set("ABCD")
