"""Script de preprocesamiento y construcción de variables.

Construye el OUTCOME real que pide la Figura 2 del documento de pipeline
("Resultado Y: IPM, bienestar del hogar, GEIH") — un índice de privaciones
multidimensionales calculado SOBRE GEIH (no sobre la encuesta IPM, que no
comparte llave de hogar con GEIH/Sisbén). Se usa un subconjunto REDUCIDO de
privaciones: solo las que se pueden construir con códigos cuyo significado
está razonablemente verificado (ver sección "Qué se incluyó y qué no").

⚠️ No es el IPM oficial de 15 indicadores — es un proxy con 4, a nivel del
jefe de hogar (no de todos los miembros, por simplicidad). Se documenta así
explícitamente para no presentarlo como el IPM real.

## Qué se incluyó y por qué

| Indicador | Código GEIH | Verificación |
|---|---|---|
| `analfabetismo` | `P6160` (jefe) | Código compartido con IPM (ver `docs/insumos/DICCIONARIO_DATOS.md`); 1=Sí sabe/2=No, proporción 8.5% analfabetismo calza con cifras nacionales. |
| `sin_aseguramiento_salud` | `P6090` (jefe) | Código compartido con IPM; 1=Sí afiliado/2=No, proporción 4.3% sin afiliación calza con cobertura de salud ~95-96% en Colombia. |
| `hacinamiento` | `P5020` (cuartos para dormir) + conteo de personas por hogar | Umbral >3 personas/cuarto — **umbral aproximado, no verificado contra la metodología oficial DANE del IPM**. |
| `sin_cotizacion_pension_jefe` | `P6920` (cotiza a pensión, módulo `ocupados`) | 1=cotiza/2=no cotiza/3=pensionado. Tasa de no cotización entre ocupados: 56.3% en enero 2024 — calza con la tasa de informalidad laboral nacional reportada por DANE (~55-58% en 2024), lo que da bastante confianza en la interpretación del código aunque no esté en un diccionario oficial en el repo. |

⚠️ **`sin_cotizacion_pension_jefe` mezcla causas muy distintas y por eso da
un 75% de privación — más alto de lo esperable para un solo indicador del
IPM.** Un jefe puede no cotizar por ser informal (lo que sí es privación en
el sentido del IPM), pero también por estar desempleado, ser ama de casa, o
ser un adulto mayor que ya no trabaja — casos donde "no cotiza" no
necesariamente implica pobreza. El indicador queda así porque no hay en el
repo una forma confiable de separar "informal" de "inactivo por elección"
con los datos disponibles; se deja como está, documentado, en vez de
inventar una regla de separación sin respaldo. **Tratar `ipm_geih_score`
con cautela mientras este indicador no se refine** — ver
"Próximos pasos" en `docs/seguimiento/CHANGELOG_PENDIENTES.md`.

## Qué se excluyó y por qué

`viv_paredes` (`P4020`) y `viv_pisos` (`P4030S1`) — las categorías NO están
verificadas (ver `docs/insumos/DICCIONARIO_HOTDECK.md` §8): la distribución
real de `P4020` no calza con lo que se esperaría de la codificación DANE
estándar recordada de memoria, así que incluirlas como privación habría
significado adivinar la dirección (qué categoría es "material inadecuado")
sin poder confirmarlo — se prefirió dejarlas fuera del outcome antes que
fabricar un indicador con la dirección equivocada. Sí se usan como
confusores/controles (X) en la estimación, donde no hace falta saber la
dirección de la categoría para que aporten como control.

Tratamiento: `Grupo_hotdeck` / `Clasificacion_hotdeck`
(`data/2_models/geih_sisben_fusionado_2024.parquet`, ya con vivienda sumada
a la celda del Hot-Deck).

Uso:
    poetry run python src/3_preprocesamiento.py
Salida: data/2_models/muestra_estimacion_2024.parquet
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
FUSIONADO = Path("data/2_models/geih_sisben_fusionado_2024.parquet")
OUT = Path("data/2_models/muestra_estimacion_2024.parquet")
REPORT_DIR = Path("docs/reports")
MESES = [f"{m:02d}" for m in range(1, 13)]
UMBRAL_HACINAMIENTO = 3  # personas por cuarto para dormir — ver nota de verificación arriba
K_POBRE = 2  # umbral adoptado (privaciones de 4). Ver sensibilidad K=1..4 en `_validar`.
PRIVACIONES = ["analfabetismo", "sin_aseguramiento_salud", "hacinamiento", "sin_cotizacion_pension_jefe"]
IPM_OFICIAL_TASA_POBREZA = 0.130  # IPM Hogares Nacional 2024 (data/catalogo.yaml) — referencia de plausibilidad, no un objetivo a igualar


def _norm_llave(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce").astype("Int64").astype("string")


def _outcome_mes(mes: str) -> pd.DataFrame | None:
    path_hv = GEIH_DIR / mes / "hogar_vivienda.parquet"
    path_cg = GEIH_DIR / mes / "caracteristicas_generales.parquet"
    path_oc = GEIH_DIR / mes / "ocupados.parquet"
    if not (path_hv.exists() and path_cg.exists()):
        logger.warning("GEIH %s: faltan módulos base — se omite", mes)
        return None

    k3 = ["DIRECTORIO", "SECUENCIA_P", "HOGAR"]
    hv = pd.read_parquet(path_hv, columns=[*k3, "P5020"]).replace("", pd.NA)
    for c in k3:
        hv[c] = _norm_llave(hv[c])

    cg = pd.read_parquet(path_cg, columns=[*k3, "ORDEN", "P6050", "P6160", "P6090"]).replace("", pd.NA)
    for c in [*k3, "ORDEN"]:
        cg[c] = _norm_llave(cg[c])

    n_pers = cg.groupby(k3).size().rename("hog_num_personas").reset_index()
    jefes = cg[_norm_llave(cg["P6050"]).astype("string") == "1"][[*k3, "ORDEN", "P6160", "P6090"]].copy()

    if path_oc.exists():
        oc = pd.read_parquet(path_oc, columns=[*k3, "ORDEN", "P6920"]).replace("", pd.NA)
        for c in [*k3, "ORDEN"]:
            oc[c] = _norm_llave(oc[c])
        jefes = jefes.merge(oc[[*k3, "ORDEN", "P6920"]], on=[*k3, "ORDEN"], how="left")
    else:
        jefes["P6920"] = pd.NA

    df = jefes.merge(hv, on=k3, how="left").merge(n_pers, on=k3, how="left")

    df["analfabetismo"] = (df["P6160"] == "2").astype("Int8")
    df["sin_aseguramiento_salud"] = (df["P6090"] == "2").astype("Int8")

    cuartos_dormir = pd.to_numeric(df["P5020"], errors="coerce")
    personas_cuarto = df["hog_num_personas"] / cuartos_dormir.replace(0, pd.NA)
    df["hacinamiento"] = (personas_cuarto > UMBRAL_HACINAMIENTO).astype("Int8")

    # Privado si NO está ocupado y cotizando a pensión (combina informalidad +
    # desempleo/inactividad del jefe en un solo indicador de trabajo).
    df["sin_cotizacion_pension_jefe"] = (df["P6920"] != "1").astype("Int8")

    df["ipm_geih_score"] = df[PRIVACIONES].sum(axis=1, min_count=1)
    df["POBRE_GEIH"] = (df["ipm_geih_score"] >= K_POBRE).astype("Int8")
    # Variantes de umbral para análisis de sensibilidad (ver _validar) — el
    # mismo score, distinto corte. K_POBRE=2 es el umbral adoptado.
    for k in (1, 2, 3, 4):
        df[f"POBRE_GEIH_K{k}"] = (df["ipm_geih_score"] >= k).astype("Int8")

    cols_salida = ["llave_directorio", "llave_secuencia_p", "llave_hogar", *PRIVACIONES,
                   "ipm_geih_score", "POBRE_GEIH", *[f"POBRE_GEIH_K{k}" for k in (1, 2, 3, 4)]]
    out = df.rename(columns={
        "DIRECTORIO": "llave_directorio", "SECUENCIA_P": "llave_secuencia_p", "HOGAR": "llave_hogar",
    })[cols_salida]
    out["mes"] = mes
    return out


def _validar(df: pd.DataFrame) -> None:
    """Validaciones obligatorias sobre la tabla final. Falla con
    AssertionError si algo estructural está mal (no se queda callado)."""
    llave = ["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"]
    n_dup = df.duplicated(subset=llave).sum()
    assert n_dup == 0, f"{n_dup} filas duplicadas por llave de hogar+mes — revisar el cruce"
    # GEIH es panel ROTATIVO, no sigue al mismo hogar entre meses: la
    # unicidad es por hogar DENTRO de cada mes, no un hogar único en el año.

    for c in PRIVACIONES:
        n_na = df[c].isna().sum()
        assert n_na == 0, f"{c}: {n_na} valores faltantes sin tratar explícitamente"

    n_na_score = df["ipm_geih_score"].isna().sum()
    assert n_na_score == 0, f"ipm_geih_score: {n_na_score} valores faltantes"

    print("\n=== Validaciones ===")
    print(f"Filas: {len(df):,} | duplicados por llave hogar+mes: {n_dup} | privaciones sin faltantes: OK")

    print("\nCobertura por privación (% con valor 1, sobre el total — 0% de faltantes en las 4):")
    for c in PRIVACIONES:
        print(f"  {c}: {df[c].mean()*100:.1f}%")

    print(f"\nDistribución del score (0-{len(PRIVACIONES)}):")
    print((df["ipm_geih_score"].value_counts(normalize=True).sort_index() * 100).round(1).astype(str) + " %")

    print("\nSensibilidad al umbral K (tasa de pobreza según dónde se corte el score):")
    for k in (1, 2, 3, 4):
        tasa = df[f"POBRE_GEIH_K{k}"].mean() * 100
        marca = " <- adoptado (K_POBRE)" if k == K_POBRE else ""
        print(f"  K>={k}: {tasa:.1f}%{marca}")
    print(
        f"  Referencia externa: IPM oficial (Hogares Nacional 2024, 15 privaciones) = "
        f"{IPM_OFICIAL_TASA_POBREZA*100:.1f}% — K={K_POBRE} es el más cercano en orden de "
        f"magnitud entre los 4 cortes probados; no se ajustó el umbral para igualarlo, es una "
        f"verificación de plausibilidad ex post, no una calibración."
    )


def main() -> None:
    if not FUSIONADO.exists():
        raise SystemExit(f"Falta {FUSIONADO}: corra src.emparejamiento.emparejamiento_hotdeck_geih_sisben")

    tablas = [t for mes in MESES if (t := _outcome_mes(mes)) is not None]
    outcome = pd.concat(tablas, ignore_index=True)
    logger.info("Outcome IPM-GEIH (reducido) construido: %s hogares", f"{len(outcome):,}")

    fus = pd.read_parquet(FUSIONADO)
    for c in ("llave_directorio", "llave_secuencia_p", "llave_hogar"):
        fus[c] = fus[c].astype("string")
    df = fus.merge(outcome, on=["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"], how="left")

    n_sin = df["ipm_geih_score"].isna().sum()
    assert n_sin == 0, f"{n_sin} hogares del Hot-Deck sin outcome tras el cruce — revisar llaves"
    logger.info("Hogares sin outcome tras el cruce: %s de %s (0.0%%)", n_sin, len(df))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)

    print("\n=== Outcome real: IPM-GEIH (reducido, 4 privaciones de 4) ===")
    print(f"Hogares: {len(df):,}")
    print(f"Score medio: {df['ipm_geih_score'].mean():.2f} (0-4)")

    _validar(df)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "reporte_sensibilidad_ipm_geih.csv").write_text(
        df["ipm_geih_score"].value_counts(normalize=True).sort_index().mul(100).round(2).to_csv(
            header=["pct_hogares"], index_label="score"
        ),
        encoding="utf-8",
    )
    print(f"\nGuardado: {OUT}")
    print(f"Guardado: {REPORT_DIR / 'reporte_sensibilidad_ipm_geih.csv'}")


if __name__ == "__main__":
    main()
