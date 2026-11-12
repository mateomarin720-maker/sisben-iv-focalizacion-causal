"""¿El registro del Sisbén representa a la misma población que GEIH?

No automáticamente: el Sisbén solo cubre hogares que se inscribieron, y
la tasa de inscripción no tiene por qué ser uniforme entre departamentos
(ver instrucción de auditoría de Fase 3: "la distribución del registro
Sisbén no representa automáticamente a todos los hogares de GEIH, porque
no todos los hogares de la encuesta necesariamente están inscritos").

Este script compara, por departamento:
  - los hogares de la GEIH en un mes promedio (expandidos por `FEX_C18`)
  - los hogares efectivamente registrados en el Sisbén (con `Clasificacion`
    observada, el pool donante real del Hot-Deck)
y calcula la razón de cobertura sobre el mismo marco. En los 9
departamentos de la Orinoquía, la Amazonía y San Andrés la GEIH solo
encuesta la cabecera de la capital (todos sus hogares son urbanos); ahí
el Sisbén se cuenta también solo en la cabecera de la capital (municipio
terminado en 001, zona 1). Hasta el 2026-11-11 se dividía el
departamento entero entre la capital y la razón pasaba del 100 %
(Putumayo 154 %). Si esa razón fuera pareja entre
departamentos, el supuesto de "muestra representativa aunque parcial"
sería más defendible. Si varía mucho, es evidencia directa de que el
Sisbén sobre-representa ciertos departamentos (y sub-representa otros) en
relación con su peso poblacional real — relevante para interpretar tanto
el Hot-Deck como las cotas de Fréchet-Manski
(`docs/resultados/2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md`).

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


def solo_capital(geih: pd.DataFrame) -> set[str]:
    """Departamentos donde la GEIH solo encuesta la cabecera de la capital:
    todos sus hogares son urbanos (`geo_zona` 1)."""
    if "geo_zona" not in geih:
        return set()
    urbano = geih["geo_zona"].astype(str).eq("1").groupby(geih["geo_depto"]).all()
    return set(urbano[urbano].index)


def calcular_cobertura(geih: pd.DataFrame | None = None, sisben: pd.DataFrame | None = None) -> pd.DataFrame:
    """Hogares de la GEIH (expandidos) y registrados en el Sisbén, por
    departamento y sobre el mismo marco. La GEIH anual junta 12 muestras
    mensuales y cada una se expande a toda la población: la suma de `fex`
    del año son 12 veces los hogares. Se divide por el número de meses de
    la muestra (hogares de un mes promedio). Hasta el 2026-11-10 no se
    dividía y las coberturas salían 12 veces menores.

    Donde la GEIH solo cubre la cabecera de la capital, el Sisbén se
    restringe a esa cabecera (`marco` = "cabecera de la capital")."""
    if geih is None:
        geih = pd.read_parquet(GEIH_PATH, columns=["geo_depto", "geo_zona", "fex", "mes"])
    if sisben is None:
        sisben = pd.read_parquet(SISBEN_PATH, columns=["geo_depto", "cod_mpio", "geo_zona", "Clasificacion"])
    geih = geih.assign(fex=pd.to_numeric(geih["fex"], errors="coerce").fillna(0))
    meses = geih["mes"].nunique()
    geih_pop = (geih.groupby("geo_depto")["fex"].sum() / meses).rename("geih_hogares_expandidos")

    capital = solo_capital(geih)
    sisben = sisben[sisben["Clasificacion"].notna()]
    if capital:
        en_capital = (sisben["cod_mpio"].astype(str).str[-3:].eq("001")
                      & sisben["geo_zona"].astype(str).eq("1"))
        sisben = sisben[~sisben["geo_depto"].isin(capital) | en_capital]
    sisben_n = sisben.groupby("geo_depto").size().rename("sisben_hogares_registrados")

    df = pd.concat([geih_pop, sisben_n], axis=1).dropna()
    df["razon_cobertura"] = df["sisben_hogares_registrados"] / df["geih_hogares_expandidos"]
    df["marco"] = ["cabecera de la capital" if d in capital else "departamento" for d in df.index]
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
    dep = df[df["marco"] == "departamento"]
    print(f"Solo departamentos completos ({len(dep)}): {dep['razon_cobertura'].min():.3f} a "
          f"{dep['razon_cobertura'].max():.3f}, factor {dep['razon_cobertura'].max() / dep['razon_cobertura'].min():.1f}x")
    print(f"\nGuardado: {REPORT}")


if __name__ == "__main__":
    main()
