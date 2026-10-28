"""Estandariza GEIH a un esquema canónico por hogar, para los 12 meses.

Combina el módulo hogar_vivienda (nivel hogar) con las características
del jefe de hogar extraídas de caracteristicas_generales (nivel
persona, filtrado a P6050=="1"), y renombra todo a nombres canónicos
compartidos con el estandarizador de Sisbén (ver
armonizar_sisben_hogar_2024.py), para que el Hot-Deck opere sobre columnas ya
homologadas en vez de tener que mapear nombres cada vez.

⚠️ CORREGIDO 2026-10-28 con el diccionario oficial de variables de GEIH
2024 (`docs/insumos/Diccionario_variables_GEIH_2024.xlsx`, conseguido
después de documentar el bloqueo en
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`). El mapeo de vivienda
que tenía este script ANTES de esa fecha estaba mal — no por adivinar,
sino por una correspondencia de códigos incorrecta que nadie había
verificado contra la ficha real:

  | Canónico | Antes (incorrecto) | Ahora (verificado contra el diccionario) |
  |---|---|---|
  | `viv_paredes` | `P4020` (en realidad: material de PISOS) | `P4010` — "material predominante de las paredes exteriores" |
  | `viv_pisos` | `P4030S1` (en realidad: "¿tiene energía eléctrica? Sí/No") | `P4020` — "material predominante de los pisos" |
  | `viv_cuartos` | `P5010` (en realidad: cuartos para DORMIR, no el total) | `P5000` — "cuántos cuartos en total dispone el hogar" (mismo concepto que `VIV009` del Sisbén) |

Esto afectó la celda del Hot-Deck (que usaba `viv_cuartos` ya corregido
aquí) y el cálculo de hacinamiento en `3_preprocesamiento.py` (que usaba
directamente `P5020` — tipo de servicio sanitario — como si fueran
cuartos). Toda la cadena (armonización → Hot-Deck → preprocesamiento →
estimación) se re-corrió después de esta corrección — ver
`docs/seguimiento/CHANGELOG_PENDIENTES.md` (2026-10-28).

Confirmado con el diccionario oficial:
  - `geo_depto`: `DPTO` (GEIH) y los 2 primeros dígitos de `cod_mpio`
    (Sisbén) usan el mismo código DIVIPOLA — confirmado antes y ahora.
  - `geo_zona`: `CLASE` — **1 = Urbano, 2 = Rural** (confirmado contra la
    pregunta oficial).
  - `jefe_sexo`: `P3271` — "¿cuál fue su sexo al nacer?" (confirmado,
    sigue sin la tabla de códigos 1/2 explícita en el diccionario, pero
    la pregunta en sí está confirmada).
  - `viv_paredes` (`P4010`): a=Ladrillo/bloque/prefabricado/piedra,
    b=Madera pulida, c=Adobe/tapia, d=Bahareque, e=Madera burda/tablón,
    f=Guadua, g=Caña/esterilla/vegetal, h=Zinc/tela/cartón/desechos,
    i=Sin paredes (codificadas 1-9 en ese orden, confirmado contra la
    distribución real: código 1 = 92% de los hogares, consistente con
    "ladrillo/bloque" siendo el material dominante en Colombia).
  - `viv_pisos` (`P4020`): a=Tierra/arena (privación), b=Cemento/gravilla,
    c=Madera burda, d=Baldosín/ladrillo/vinisol, e=Mármol, f=Madera
    pulida, g=Alfombra (codificadas 1-7).

Uso:
    poetry run python -m src.armonizacion.armonizar_geih_hogar_2024
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
OUT_PATH = Path("data/2_models/geih_estandarizado_2024.parquet")

MESES = [f"{m:02d}" for m in range(1, 13)]

# Columnas de hogar_vivienda -> nombre canónico (corregido 2026-10-28, ver
# docstring del módulo)
MAPA_HOGAR_VIVIENDA = {
    "DIRECTORIO": "llave_directorio",
    "SECUENCIA_P": "llave_secuencia_p",
    "HOGAR": "llave_hogar",
    "DPTO": "geo_depto",
    "CLASE": "geo_zona",
    "P4010": "viv_paredes",           # material predominante de paredes exteriores
    "P4020": "viv_pisos",             # material predominante de pisos
    "P5000": "viv_cuartos",           # cuartos en total (incl. sala-comedor) — mismo concepto que VIV009 del Sisbén
    "P5010": "viv_cuartos_dormir",    # de esos, cuántos se usan para dormir (insumo de hacinamiento)
    "P4030S3": "viv_alcantarillado",  # ¿tiene alcantarillado? 1=Sí/2=No
    "P4030S5": "viv_acueducto",       # ¿tiene acueducto? 1=Sí/2=No
    "P6008": "hog_num_personas",      # total de personas en el hogar (directo, no hay que contar filas)
    "FEX_C18": "fex",
}

# Columna de caracteristicas_generales (jefe de hogar) -> nombre canónico.
# Nota: este script solo alimenta el Hot-Deck (src/emparejamiento/) — las
# privaciones del outcome (P6160, P3042, P6170, etc.) se leen aparte en
# `3_preprocesamiento.py`, directo de los módulos crudos, no de aquí.
MAPA_JEFE = {
    "P3271": "jefe_sexo",
    "P6040": "jefe_edad",
}

FILTRO_JEFE_COL = "P6050"
FILTRO_JEFE_VAL = "1"


def _norm_llave(serie: pd.Series) -> pd.Series:
    """Normaliza identificadores a texto de entero ('7893865.0', ' 01 ', 1 -> '7893865', '1', '1'),
    para que hogar_vivienda y caracteristicas_generales crucen igual en todos los meses."""
    return pd.to_numeric(serie, errors="coerce").astype("Int64").astype("string")


def _cargar_mes(mes: str) -> pd.DataFrame | None:
    path_hv = GEIH_DIR / mes / "hogar_vivienda.parquet"
    path_cg = GEIH_DIR / mes / "caracteristicas_generales.parquet"

    if not path_hv.exists():
        logger.warning("GEIH %s: no encontrado (%s) — se omite", mes, path_hv)
        return None

    hv = pd.read_parquet(path_hv).replace("", pd.NA)
    columnas_hv = [c for c in MAPA_HOGAR_VIVIENDA if c in hv.columns]
    hv = hv[["DIRECTORIO", "SECUENCIA_P", "HOGAR", *[c for c in columnas_hv if c not in ("DIRECTORIO", "SECUENCIA_P", "HOGAR")]]]
    hv = hv.rename(columns=MAPA_HOGAR_VIVIENDA)
    for c in ("llave_directorio", "llave_secuencia_p", "llave_hogar"):
        hv[c] = _norm_llave(hv[c])

    if path_cg.exists():
        cg = pd.read_parquet(path_cg).replace("", pd.NA)
        for c in ("DIRECTORIO", "SECUENCIA_P", "HOGAR"):
            cg[c] = _norm_llave(cg[c])
        jefes = cg[_norm_llave(cg[FILTRO_JEFE_COL]).astype("string") == FILTRO_JEFE_VAL].copy()
        columnas_jefe = [c for c in MAPA_JEFE if c in jefes.columns]
        jefes = jefes[["DIRECTORIO", "SECUENCIA_P", "HOGAR", *columnas_jefe]].rename(columns=MAPA_JEFE)
        hv = hv.merge(
            jefes,
            left_on=["llave_directorio", "llave_secuencia_p", "llave_hogar"],
            right_on=["DIRECTORIO", "SECUENCIA_P", "HOGAR"],
            how="left",
        ).drop(columns=["DIRECTORIO", "SECUENCIA_P", "HOGAR"], errors="ignore")
        n_sin = int(hv["jefe_edad"].isna().sum()) if "jefe_edad" in hv.columns else len(hv)
        if n_sin > 0.02 * len(hv):
            logger.warning("GEIH %s: %s de %s hogares SIN jefe cruzado — revisar llaves", mes, f"{n_sin:,}", f"{len(hv):,}")
    else:
        logger.warning("GEIH %s: caracteristicas_generales.parquet no encontrado — sin datos de jefe", mes)

    hv["mes"] = mes
    hv["fuente"] = "geih"
    return hv


def armonizar_geih_hogar() -> pd.DataFrame:
    """Apila los 12 meses de GEIH ya estandarizados. Procesa los meses
    disponibles — no requiere tener los 12 para funcionar."""
    tablas = []
    for mes in MESES:
        df_mes = _cargar_mes(mes)
        if df_mes is not None:
            tablas.append(df_mes)
            logger.info("GEIH %s: %s hogares estandarizados", mes, f"{len(df_mes):,}")

    if not tablas:
        raise RuntimeError("No se encontró ningún mes de GEIH en data/1_processed/geih/2024/")

    resultado = pd.concat(tablas, ignore_index=True)
    return resultado


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = armonizar_geih_hogar()
    df.to_parquet(OUT_PATH, index=False)
    print(f"\n=== GEIH estandarizado ===")
    print(f"Total hogares (todos los meses apilados): {len(df):,}")
    print(df["mes"].value_counts().sort_index())
    print(f"\nGuardado: {OUT_PATH}")


if __name__ == "__main__":
    main()
