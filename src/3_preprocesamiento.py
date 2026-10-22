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
MESES = [f"{m:02d}" for m in range(1, 13)]
UMBRAL_HACINAMIENTO = 3  # personas por cuarto para dormir — ver nota de verificación arriba
K_POBRE = 2  # privaciones de 4 para marcar POBRE_GEIH (umbral arbitrario, documentado)


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

    privaciones = ["analfabetismo", "sin_aseguramiento_salud", "hacinamiento", "sin_cotizacion_pension_jefe"]
    df["ipm_geih_score"] = df[privaciones].sum(axis=1, min_count=1)
    df["POBRE_GEIH"] = (df["ipm_geih_score"] >= K_POBRE).astype("Int8")

    out = df.rename(columns={
        "DIRECTORIO": "llave_directorio", "SECUENCIA_P": "llave_secuencia_p", "HOGAR": "llave_hogar",
    })[["llave_directorio", "llave_secuencia_p", "llave_hogar", *privaciones, "ipm_geih_score", "POBRE_GEIH"]]
    out["mes"] = mes
    return out


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
    logger.info("Hogares sin outcome tras el cruce: %s de %s (%.1f%%)", n_sin, len(df), n_sin / len(df) * 100)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)

    print("\n=== Outcome real: IPM-GEIH (reducido, 4 privaciones de 4) ===")
    print(f"Hogares: {len(df):,}")
    for c in ["analfabetismo", "sin_aseguramiento_salud", "hacinamiento", "sin_cotizacion_pension_jefe"]:
        print(f"  {c}: {df[c].mean()*100:.1f}% privados")
    print(f"  Score medio: {df['ipm_geih_score'].mean():.2f} (0-4)")
    print(f"  POBRE_GEIH (score >= {K_POBRE}): {df['POBRE_GEIH'].mean()*100:.1f}%")
    print(f"\nGuardado: {OUT}")


if __name__ == "__main__":
    main()
