"""Carga de GEIH, contraste con la base oficial de pobreza monetaria y
chequeo de d-separación del DAG."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # geih_loader importa `ingesta.*`, como 1_integracion.py
from ingesta import geih_loader  # noqa: E402

from src.validacion import comparar_pobreza_monetaria_oficial as cpo  # noqa: E402

# --------------------------------------------------------------------------
# Carga de GEIH: 12 meses, variantes de nombre y respaldo en .DTA
# --------------------------------------------------------------------------

ARCHIVOS_MODULO = {  # nombre de archivo de cada módulo, como lo trae el DANE
    "hogar_vivienda": "Datos del hogar y la vivienda", "caracteristicas_generales": "Características generales",
    "fuerza_trabajo": "Fuerza de trabajo", "no_ocupados": "No ocupados", "ocupados": "Ocupados",
    "otras_formas_trabajo": "Otras formas de trabajo", "otros_ingresos": "Otros ingresos e impuestos",
    "migracion": "Migración",
}


def _crear_meses(base: Path) -> None:
    """Los 12 meses con las variantes reales: marzo trae "No ocupado"
    (singular); agosto solo el CSV de un módulo y los 8 en .DTA; abril
    con una carpeta CSV vacía antes de la buena."""
    for m in range(1, 13):
        mes = f"{m:02d}"
        csv = base / "2024" / mes / "CSV"
        csv.mkdir(parents=True)
        if mes == "04":
            (base / "2024" / mes / "CSV_vacia" / "CSV").mkdir(parents=True)
        for salida, nombre in ARCHIVOS_MODULO.items():
            if mes == "03" and salida == "no_ocupados":
                nombre = "No ocupado"
            if mes == "08":
                dta = base / "2024" / mes / "DTA"
                dta.mkdir(exist_ok=True)
                (dta / f"{nombre}.DTA").write_bytes(b"")
                if salida != "hogar_vivienda":
                    continue
            (csv / f"{nombre}.CSV").write_text("x\n1\n", encoding="latin1")


def test_cada_modulo_encuentra_su_archivo_y_no_el_de_otro(tmp_path):
    """"Ocupados" no debe tomar "No ocupados", y "No ocupado" debe
    encontrar el singular de marzo y el plural del resto del año."""
    _crear_meses(tmp_path)
    for mes in ("02", "03"):
        carpeta = tmp_path / "2024" / mes
        assert geih_loader._buscar_archivo_modulo(carpeta, "Ocupados", "CSV").name == "Ocupados.CSV"
        assert geih_loader._buscar_archivo_modulo(carpeta, "No ocupado", "CSV").name.startswith("No ocupado")


def test_ingesta_procesa_los_8_modulos_de_los_12_meses(tmp_path, monkeypatch):
    _crear_meses(tmp_path / "raw")
    llamadas = []

    def falso_csv(input_path, output_path, fuente_id, encoding):
        llamadas.append(("csv", Path(output_path).parent.name, Path(output_path).stem, encoding))
        return {"status": "success"}

    def falso_dta(input_path, output_path, fuente_id):
        llamadas.append(("dta", Path(output_path).parent.name, Path(output_path).stem, None))
        return {"status": "success"}

    monkeypatch.setattr(geih_loader, "RAW_BASE", tmp_path / "raw")
    monkeypatch.setattr(geih_loader, "OUT_BASE", tmp_path / "out")
    monkeypatch.setattr(geih_loader, "parse_csv_a_parquet", falso_csv)
    monkeypatch.setattr(geih_loader, "parse_stata_a_parquet", falso_dta)

    resumen = geih_loader.ingest_geih("2024")
    assert resumen == {f"{m:02d}": 8 for m in range(1, 13)}
    agosto = [c for c in llamadas if c[1] == "08"]
    assert sorted(c[0] for c in agosto) == ["csv"] + ["dta"] * 7
    assert {c[2] for c in llamadas if c[1] == "03"} == set(ARCHIVOS_MODULO)
    assert all(c[3] == "latin1" for c in llamadas if c[0] == "csv")  # GEIH crudo viene en Latin-1


# --------------------------------------------------------------------------
# Contraste con la base oficial de pobreza monetaria
# --------------------------------------------------------------------------

def test_contraste_oficial_cruza_con_llaves_de_formatos_distintos(tmp_path):
    """La base oficial trae `mes` "1" y la reconstrucción "01"; con las
    llaves normalizadas se cruzan todos los hogares, uno a uno."""
    oficial = pd.DataFrame({
        "directorio": ["7", "8", "9"], "secuencia_p": ["1", "1", "1"], "mes": ["1", "1", "2"],
        "clase": ["1", "1", "2"], "dominio": ["MEDELLIN", "RESTO URBANO", "RURAL"],
        "nper": [3, 1, 2], "npersug": [3, 1, 2], "ingtotug": [900, 100, 600], "ingtotarr": [1000, 100, 600],
        "ingpcug": [333.3, 100, 300], "lp": [500, 400, 300], "li": [200, 200, 150], "pobre": [1, 1, 0],
        "indigente": [0, 1, 0], "fex_c": [10.0, 20.0, 30.0],
    })
    ruta = tmp_path / "Hogares.csv"
    oficial.to_csv(ruta, index=False, encoding="latin1")
    recon = pd.DataFrame({
        "DIRECTORIO": ["7.0", "8.0", "9.0"], "SECUENCIA_P": ["01", "01", "1"], "mes": ["01", "01", "02"],
        "ingreso_pc_ug": [333.3, 150.0, 320.0], "personas_ug": [3, 1, 2], "POBRE_MONETARIA": [1, 1, 0],
        "POBRE_EXTREMA": [0, 1, 0], "dominio_pm": ["13_ciudades", "otras_cabeceras", "rural"],
    })
    recon_ruta = tmp_path / "recon.parquet"
    recon.to_parquet(recon_ruta)

    o = cpo.cargar_oficial(ruta)
    assert o["area_pm"].tolist() == ["ciudad", "resto_urbano", "rural"]
    tabla, res = cpo.comparar(o, cpo.cargar_reconstruccion(recon_ruta))
    assert res["hogares_comunes"] == 3 and res["oficial_sin_reconstruccion"] == 0
    nacional = tabla.set_index("universo").loc["nacional_24_deptos"]
    assert nacional["pct_hogares_misma_clasificacion"] == pytest.approx(100.0)


# --------------------------------------------------------------------------
# DAG: el grupo imputado es independiente del resultado dada la celda
# --------------------------------------------------------------------------

def test_d_separacion_del_diseno_con_hot_deck():
    spec = importlib.util.spec_from_file_location("dag_4", ROOT / "src" / "4_dag_identificacion.py")
    dag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dag)
    literal = dag.analizar_dseparacion(dag.grafo_diseno_principal(), ("elegibilidad_real",))
    refinado = dag.analizar_dseparacion(dag.grafo_diseno_principal_refinado(),
                                        ("elegibilidad_receptor", "elegibilidad_donante"))
    assert literal == {"d_separado_dado_X": False, "d_separado_dado_X_mas_elegibilidad_real": True}
    assert refinado["d_separado_dado_X"] is True
