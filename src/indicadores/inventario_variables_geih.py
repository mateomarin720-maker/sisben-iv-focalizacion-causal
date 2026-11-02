"""Inventario de variables GEIH 2024 disponibles para construir privaciones
tipo IPM (Fase 1 de la comparación de proxies, ver
`docs/metodologia/comparacion_proxies/00_auditoria_variables.md`).

Cruza tres cosas, para cada columna de cada módulo de GEIH:
  1. Si la columna existe en los parquet procesados
     (`data/1_processed/geih/2024/<mes>/<modulo>.parquet`) y en cuántos de
     los 12 meses aparece.
  2. Si el código está en el diccionario oficial
     (`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`) y con qué etiqueta.
  3. Qué tan completa viene: % de valores no vacíos sobre todas las filas
     del módulo (12 meses apilados). Ojo: un % bajo no es necesariamente un
     problema — muchas preguntas tienen flujo (p. ej. `P7250` solo se le
     pregunta a desocupados). El universo correcto de cada pregunta se
     revisa en `homologacion_ipm.py`, no aquí.

Además marca si la columna ya la usa algún script del proyecto
(armonización, preprocesamiento o emparejamiento), buscando el código
literal en el fuente — para no duplicar variables ya construidas.

No construye ninguna privación ni toca resultados existentes.

Uso:
    poetry run python -m src.indicadores.inventario_variables_geih
Salida: docs/reports/inventario_variables_geih.csv
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
DICCIONARIO = Path("docs/insumos/DICCIONARIO_GEIH_2024.xlsx")
OUT = Path("docs/reports/inventario_variables_geih.csv")
MESES = [f"{m:02d}" for m in range(1, 13)]

# Scripts cuyo uso de códigos GEIH cuenta como "variable ya construida".
SCRIPTS_PROYECTO = [
    Path("src/armonizacion/armonizar_geih_hogar_2024.py"),
    Path("src/3_preprocesamiento.py"),
    Path("src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py"),
]

# Archivo parquet -> nombre del módulo en el diccionario oficial.
MODULOS = {
    "caracteristicas_generales": "Caracteristicas generales, seguridad social en salud y educacion",
    "hogar_vivienda": "Datos del hogar y la vivienda",
    "fuerza_trabajo": "Fuerza de trabajo",
    "ocupados": "Ocupados",
    "no_ocupados": "No ocupados",
    "otras_formas_trabajo": "Otras formas de trabajo",
    "otros_ingresos": "Otros ingresos e impuestos",
    "migracion": "Migracion",
}


def _codigos_usados() -> dict[str, list[str]]:
    """Código GEIH -> scripts del proyecto que lo mencionan entre comillas."""
    usados: dict[str, list[str]] = {}
    for script in SCRIPTS_PROYECTO:
        if not script.exists():
            continue
        texto = script.read_text(encoding="utf-8")
        for codigo in set(re.findall(r"[\"']([A-Z][A-Z0-9_]{1,15})[\"']", texto)):
            usados.setdefault(codigo, []).append(script.name)
    return usados


def _completitud_modulo(modulo: str) -> pd.DataFrame:
    """Filas y valores no vacíos por columna, sumando los 12 meses."""
    filas, no_vacios, meses = 0, {}, {}
    for mes in MESES:
        path = GEIH_DIR / mes / f"{modulo}.parquet"
        if not path.exists():
            logger.warning("GEIH %s/%s: no encontrado — se omite", mes, modulo)
            continue
        df = pq.read_table(path).to_pandas()
        filas += len(df)
        for c in df.columns:
            s = df[c]
            n = int((s.notna() & (s.astype("string").str.strip() != "")).sum())
            no_vacios[c] = no_vacios.get(c, 0) + n
            meses[c] = meses.get(c, 0) + 1
    return pd.DataFrame({
        "modulo_archivo": modulo,
        "variable": list(no_vacios),
        "meses_presente": [meses[c] for c in no_vacios],
        "filas_modulo": filas,
        "pct_no_vacio": [round(100 * no_vacios[c] / filas, 2) if filas else None for c in no_vacios],
    })


def construir_inventario() -> pd.DataFrame:
    dic = pd.read_excel(DICCIONARIO)[["Nombre", "Etiqueta", "Tipo", "Módulo"]]
    dic = dic.rename(columns={"Nombre": "variable", "Etiqueta": "etiqueta_diccionario",
                              "Tipo": "tipo_diccionario", "Módulo": "modulo_diccionario"})

    inv = pd.concat([_completitud_modulo(m) for m in MODULOS], ignore_index=True)
    inv["modulo_diccionario"] = inv["modulo_archivo"].map(MODULOS)
    inv = inv.merge(dic, on=["variable", "modulo_diccionario"], how="left")
    # Algunas columnas se repiten entre módulos (llaves, CLASE, DPTO...): si no
    # calzan en su propio módulo, se busca la etiqueta en cualquier módulo.
    sin_etiqueta = inv["etiqueta_diccionario"].isna()
    etiqueta_global = dic.drop_duplicates("variable").set_index("variable")["etiqueta_diccionario"]
    inv.loc[sin_etiqueta, "etiqueta_diccionario"] = inv.loc[sin_etiqueta, "variable"].map(etiqueta_global)
    inv["en_diccionario"] = inv["etiqueta_diccionario"].notna()

    usados = _codigos_usados()
    inv["usado_en_proyecto"] = inv["variable"].map(lambda v: ", ".join(usados.get(v, [])))
    return inv[["modulo_archivo", "variable", "etiqueta_diccionario", "tipo_diccionario", "en_diccionario",
                "meses_presente", "filas_modulo", "pct_no_vacio", "usado_en_proyecto"]]


def main() -> None:
    inv = construir_inventario()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    inv.to_csv(OUT, index=False, encoding="utf-8")

    print("\n=== Inventario de variables GEIH 2024 ===")
    resumen = inv.groupby("modulo_archivo").agg(
        variables=("variable", "size"),
        en_diccionario=("en_diccionario", "sum"),
        en_12_meses=("meses_presente", lambda s: int((s == 12).sum())),
        usadas_proyecto=("usado_en_proyecto", lambda s: int((s != "").sum())),
    )
    print(resumen.to_string())
    no_dic = inv.loc[~inv["en_diccionario"], "variable"].unique()
    print(f"\nColumnas sin entrada en el diccionario oficial: {len(no_dic)} "
          f"(p. ej. {', '.join(sorted(no_dic)[:10])})")
    print(f"\nGuardado: {OUT}")


if __name__ == "__main__":
    main()
