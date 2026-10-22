"""Construye un OUTCOME PROVISIONAL (empleo/ingreso del jefe de hogar) para
poder correr modelos de prueba de ATE/ATT/CATE mientras `3_preprocesamiento.py`
(Fase 2/3, outcomes oficiales: ingreso per cápita, IPM, acceso a programas,
seguridad alimentaria) sigue sin implementar.

⚠️ Esto NO es la especificación final de outcomes del anteproyecto — es la
variable más simple que se puede derivar de los módulos crudos de GEIH ya
disponibles, solo para validar que el pipeline de estimación (DML/Causal
Forest) corre y se comporta razonablemente con las variables que ya tenemos.

Construcción, por mes:
  1. `caracteristicas_generales` filtrado a P6050=="1" (jefe) -> ORDEN del jefe.
  2. Cruce de esa llave (DIRECTORIO+SECUENCIA_P+HOGAR+ORDEN) contra `ocupados`:
     si hay match -> jefe_ocupado=1, jefe_ingreso_laboral=INGLABO.
     si no hay match -> jefe_ocupado=0, jefe_ingreso_laboral=NaN (jefe
     desocupado o inactivo; no se imputa).

Uso:
    poetry run python -m src.estimacion.preparar_outcome_prueba_empleo
Salida: data/2_models/muestra_estimacion_prueba.parquet
        (geih_sisben_fusionado_2024.parquet + jefe_ocupado + jefe_ingreso_laboral)
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
FUSIONADO = Path("data/2_models/geih_sisben_fusionado_2024.parquet")
OUT = Path("data/2_models/muestra_estimacion_prueba.parquet")
MESES = [f"{m:02d}" for m in range(1, 13)]


def _norm_llave(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce").astype("Int64").astype("string")


def _outcome_mes(mes: str) -> pd.DataFrame | None:
    path_cg = GEIH_DIR / mes / "caracteristicas_generales.parquet"
    path_oc = GEIH_DIR / mes / "ocupados.parquet"
    if not path_cg.exists():
        logger.warning("GEIH %s: falta caracteristicas_generales — se omite", mes)
        return None

    cg = pd.read_parquet(path_cg).replace("", pd.NA)
    k3 = ["DIRECTORIO", "SECUENCIA_P", "HOGAR"]
    for c in k3:
        cg[c] = _norm_llave(cg[c])
    jefes = cg[_norm_llave(cg["P6050"]).astype("string") == "1"][[*k3, "ORDEN"]].copy()
    jefes["ORDEN"] = _norm_llave(jefes["ORDEN"])

    if path_oc.exists():
        oc = pd.read_parquet(path_oc).replace("", pd.NA)
        for c in [*k3, "ORDEN"]:
            oc[c] = _norm_llave(oc[c])
        oc = oc[[*k3, "ORDEN", "INGLABO"]]
        jefes = jefes.merge(oc, on=[*k3, "ORDEN"], how="left")
        jefes["jefe_ocupado"] = jefes["INGLABO"].notna().astype("Int8")
        jefes["jefe_ingreso_laboral"] = pd.to_numeric(jefes["INGLABO"], errors="coerce")
        jefes = jefes.drop(columns=["INGLABO"])
    else:
        logger.warning("GEIH %s: falta ocupados — jefe_ocupado queda en 0 para todos", mes)
        jefes["jefe_ocupado"] = pd.array([0] * len(jefes), dtype="Int8")
        jefes["jefe_ingreso_laboral"] = pd.NA

    jefes = jefes.rename(columns={
        "DIRECTORIO": "llave_directorio", "SECUENCIA_P": "llave_secuencia_p", "HOGAR": "llave_hogar",
    }).drop(columns=["ORDEN"])
    jefes["mes"] = mes
    return jefes


def main() -> None:
    tablas = [t for mes in MESES if (t := _outcome_mes(mes)) is not None]
    outcome = pd.concat(tablas, ignore_index=True)
    logger.info("Outcome de prueba construido: %s jefes (todos los meses)", f"{len(outcome):,}")

    fus = pd.read_parquet(FUSIONADO)
    for c in ("llave_directorio", "llave_secuencia_p", "llave_hogar"):
        fus[c] = fus[c].astype("string")
    merged = fus.merge(outcome, on=["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"], how="left")

    n_sin = merged["jefe_ocupado"].isna().sum()
    logger.info("Hogares sin outcome tras el cruce: %s de %s (%.1f%%)", n_sin, len(merged), n_sin / len(merged) * 100)
    merged.to_parquet(OUT, index=False)

    print("\n=== Outcome de prueba (empleo/ingreso del jefe) ===")
    print(f"Hogares: {len(merged):,} | jefe_ocupado=1: {(merged['jefe_ocupado']==1).mean()*100:.1f}%")
    print(f"Ingreso laboral (jefes ocupados, n={merged['jefe_ingreso_laboral'].notna().sum():,}):")
    print(merged["jefe_ingreso_laboral"].describe())
    print(f"\nGuardado: {OUT}")


if __name__ == "__main__":
    main()
