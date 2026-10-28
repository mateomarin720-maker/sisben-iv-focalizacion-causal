"""¿El registro del Sisbén representa a la misma población que GEIH?

No automáticamente: el Sisbén solo cubre hogares que se inscribieron, y
la tasa de inscripción no tiene por qué ser uniforme entre departamentos
(ver instrucción de auditoría de Fase 3: "la distribución del registro
Sisbén no representa automáticamente a todos los hogares de GEIH, porque
no todos los hogares de la encuesta necesariamente están inscritos").

Este script compara, por departamento:
  - la población total de GEIH (hogares expandidos por `FEX_C18`)
  - los hogares efectivamente registrados en el Sisbén (con `Clasificacion`
    observada, el pool donante real del Hot-Deck)
y calcula la razón de cobertura. Si esa razón fuera pareja entre
departamentos, el supuesto de "muestra representativa aunque parcial"
sería más defendible. Si varía mucho, es evidencia directa de que el
Sisbén sobre-representa ciertos departamentos (y sub-representa otros) en
relación con su peso poblacional real — relevante para interpretar tanto
el Hot-Deck como las cotas de Fréchet-Manski
(`docs/resultados/RESULTADOS_FRECHET_MANSKI.md`).

Uso:
    poetry run python -m src.validacion.verificar_representatividad_sisben
Salida: docs/reports/representatividad_sisben_por_depto.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_PATH = Path("data/2_models/muestra_estimacion_2024.parquet")
SISBEN_PATH = Path("data/2_models/sisben_estandarizado_2024_con_bogota.parquet")
REPORT = Path("docs/reports/representatividad_sisben_por_depto.csv")


def calcular_cobertura() -> pd.DataFrame:
    geih = pd.read_parquet(GEIH_PATH, columns=["geo_depto", "fex"])
    geih["fex"] = pd.to_numeric(geih["fex"], errors="coerce").fillna(0)
    geih_pop = geih.groupby("geo_depto")["fex"].sum().rename("geih_hogares_expandidos")

    sisben = pd.read_parquet(SISBEN_PATH, columns=["geo_depto", "Clasificacion"])
    sisben = sisben[sisben["Clasificacion"].notna()]
    sisben_n = sisben.groupby("geo_depto").size().rename("sisben_hogares_registrados")

    df = pd.concat([geih_pop, sisben_n], axis=1).dropna()
    df["razon_cobertura"] = df["sisben_hogares_registrados"] / df["geih_hogares_expandidos"]
    return df.sort_values("razon_cobertura").reset_index()


def main() -> None:
    df = calcular_cobertura()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(REPORT, index=False)

    razon_nal = df["sisben_hogares_registrados"].sum() / df["geih_hogares_expandidos"].sum()
    print("\n=== Representatividad del Sisbén frente a GEIH, por departamento ===")
    print(df.round(4).to_string(index=False))
    print(f"\nRazón de cobertura nacional: {razon_nal:.3f}")
    print(f"Razón mínima: {df['razon_cobertura'].min():.3f} (depto {df.iloc[0]['geo_depto']})")
    print(f"Razón máxima: {df['razon_cobertura'].max():.3f} (depto {df.iloc[-1]['geo_depto']})")
    print(f"Factor de variación (máx/mín): {df['razon_cobertura'].max() / df['razon_cobertura'].min():.1f}x")
    print(f"\nGuardado: {REPORT}")


if __name__ == "__main__":
    main()
