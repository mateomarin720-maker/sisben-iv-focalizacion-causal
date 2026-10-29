"""Script de preprocesamiento y construcción de variables.

Construye el OUTCOME real que pide la Figura 2 del documento de pipeline
("Resultado Y: IPM, bienestar del hogar, GEIH") — un índice de privaciones
multidimensionales calculado SOBRE GEIH (no sobre la encuesta IPM, que no
comparte llave de hogar con GEIH/Sisbén).

⚠️ CORREGIDO Y AMPLIADO 2026-10-28 con el diccionario oficial de GEIH
(`docs/insumos/Diccionario_variables_GEIH_2024.xlsx`). Antes de esa fecha:
- `hacinamiento` estaba MAL calculado — usaba `P5020` (que en realidad es
  "tipo de servicio sanitario", una categórica 1-6) como si fuera "cuartos
  para dormir". El cociente personas/P5020 producía un número con la
  forma de una tasa de hacinamiento pero sin ese significado. Corregido:
  ahora usa `P5010` (el código real de "cuántos cuartos se usan para
  dormir") y `P6008` ("total de personas en el hogar", directo).
- El índice solo tenía 4 privaciones porque no había forma de verificar
  más códigos sin el diccionario oficial (ver intento documentado en
  `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` §5, histórico). Con el
  diccionario ya conseguido, se amplía a **8 privaciones**, cubriendo las
  5 dimensiones del IPM (antes solo 4 dimensiones con 1 indicador cada
  una).

⚠️ **`material_pisos_inadecuado` y `material_paredes_inadecuado` se
construyeron el 2026-10-28 y se retiraron el mismo día** — eran
`P4020`/`P4010`, los MISMOS códigos que `viv_pisos`/`viv_paredes`, usados
como covariables de heterogeneidad (`X`) en `5_estimacion.py`. Tenerlos
también como componentes del outcome creaba una tautología parcial: un
hogar con piso de tierra sumaba un punto al score por definición,
independiente del tratamiento, y el Causal Forest podía estar
"redescubriendo" ese hecho mecánico al reportar `viv_pisos`/`viv_paredes`
como las covariables más importantes — no necesariamente una señal real
de heterogeneidad. Se prefirió sacarlos del outcome y dejar la vivienda
donde sí aporta algo no circular: como covariable de heterogeneidad en
`X`. El índice queda en 8 privaciones en vez de 10.

No es el IPM oficial de 15 indicadores — es un proxy con 8, construido
sobre GEIH, a nivel del jefe de hogar para los indicadores de persona (no
de todos los miembros, salvo `inasistencia_escolar_menores` que sí revisa
a todos). Se documenta así explícitamente para no presentarlo como el IPM
real.

## Las 8 privaciones — código oficial y verificación

| Privación | Dimensión | Código GEIH | Verificación |
|---|---|---|---|
| `analfabetismo` | Educación | `P6160` (jefe), 1=Sí sabe/2=No | Confirmado contra el diccionario oficial: "¿Sabe leer y escribir? 1 Sí 2 No". |
| `bajo_logro_educativo_jefe` | Educación | `P3042` (jefe) | Confirmado: "¿Cuál es el mayor nivel educativo alcanzado...? 1.Ninguno 2.Preescolar 3.Básica primaria 4.Básica secundaria 5.Media académica ... 13.Doctorado". Privación si el jefe no alcanzó básica secundaria (código < 4). Umbral propio del proyecto, no necesariamente el corte exacto de la metodología Alkire-Foster oficial del DANE (que usa años de educación aprobados por cohorte de edad). |
| `inasistencia_escolar_menores` | Niñez | `P6170` + `P6040`, TODOS los miembros | Confirmado: P6170 "¿Actualmente asiste al preescolar/escuela/colegio/universidad? 1 Sí 2 No". Privación si ALGÚN miembro del hogar entre 6 y 16 años (inclusive) tiene P6170==2. A diferencia de las demás, se calcula sobre todos los miembros, no solo el jefe — aplicar "inasistencia escolar" al jefe (normalmente adulto) no tendría sentido conceptual. |
| `sin_aseguramiento_salud` | Salud | `P6090` (jefe), 1=Sí/2=No | Confirmado: "¿Está afiliado/cotizante/beneficiario de EPS/ARS? 1 Sí 2 No 9 No sabe". |
| `sin_cotizacion_pension_jefe` | Trabajo | `P6920` (jefe, módulo `ocupados`), 1=Sí/2=No/3=Ya pensionado | Confirmado: "¿Está cotizando a un fondo de pensiones? 1 Sí 2 No 3 Ya es pensionado". Sigue mezclando informalidad con desempleo/inactividad del jefe — ver nota abajo. |
| `hacinamiento` | Vivienda | `P5010` (cuartos para dormir) + `P6008` (personas) | **Corregido 2026-10-28** — antes usaba `P5020` (servicio sanitario) por error. Umbral >3 personas/cuarto, el mismo de antes, pero ahora sobre la variable correcta. |
| `sin_alcantarillado` | Vivienda | `P4030S3`, 1=Sí/2=No | Confirmado: "¿Con cuáles servicios cuenta la vivienda? c.Alcantarillado 1 Sí 2 No". |
| `sin_acueducto` | Vivienda | `P4030S5`, 1=Sí/2=No | Confirmado: "¿Con cuáles servicios cuenta la vivienda? e.Acueducto 1 Sí 2 No". |

Cobertura por dimensión: Educación (2), Niñez (1), Salud (1), Trabajo (1),
Vivienda (3) — 5 de las 5 dimensiones del IPM oficial (antes solo 4
dimensiones con 1 indicador cada una). `viv_paredes`/`viv_pisos`
(`P4010`/`P4020`) NO entran aquí — quedan solo como covariable de
heterogeneidad en `X` (`5_estimacion.py`), ver nota de tautología arriba.

⚠️ **`sin_cotizacion_pension_jefe` sigue mezclando causas distintas**
(informalidad, desempleo, inactividad) — limitación que no cambia con el
diccionario de GEIH porque no es un problema de código, es un problema de
qué pregunta existe en la encuesta. Sigue documentada, no resuelta.

## Qué sigue sin poder construirse

Las 5 privaciones restantes del IPM oficial (rezago escolar, barreras a
atención primera infancia, trabajo infantil, desempleo de larga duración,
barreras de acceso a salud) requerirían variables que o no están en GEIH
con el detalle necesario, o necesitan reglas de elegibilidad más
complejas (edades, historial laboral) que no se construyeron en este
corte — quedan para una iteración futura, no por falta del diccionario
esta vez sino por alcance de tiempo.

Tratamiento: `Grupo_hotdeck` / `Clasificacion_hotdeck`
(`data/2_models/geih_sisben_fusionado_2024.parquet`).

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
UMBRAL_HACINAMIENTO = 3  # personas por cuarto para dormir
EDAD_MIN_ESCOLAR, EDAD_MAX_ESCOLAR = 6, 16  # universo de "inasistencia_escolar_menores"
NIVEL_MIN_SECUNDARIA = 4  # P3042: 1=Ninguno,2=Preescolar,3=Primaria,4=Secundaria... privación si < 4
K_POBRE = 3  # umbral adoptado (de 8 privaciones). Ver sensibilidad en `_validar`.
PRIVACIONES = [
    "analfabetismo", "bajo_logro_educativo_jefe", "inasistencia_escolar_menores",
    "sin_aseguramiento_salud", "sin_cotizacion_pension_jefe",
    "hacinamiento", "sin_alcantarillado", "sin_acueducto",
]
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
    hv = pd.read_parquet(
        path_hv, columns=[*k3, "P4030S3", "P4030S5", "P5010", "P6008"]
    ).replace("", pd.NA)
    for c in k3:
        hv[c] = _norm_llave(hv[c])

    cg = pd.read_parquet(
        path_cg, columns=[*k3, "ORDEN", "P6050", "P6040", "P6160", "P6090", "P3042", "P6170"]
    ).replace("", pd.NA)
    for c in [*k3, "ORDEN"]:
        cg[c] = _norm_llave(cg[c])

    # Inasistencia escolar: TODOS los miembros entre 6 y 16 años, no solo el jefe.
    edad_num = pd.to_numeric(cg["P6040"], errors="coerce")
    es_menor_escolar = edad_num.between(EDAD_MIN_ESCOLAR, EDAD_MAX_ESCOLAR)
    no_asiste = cg["P6170"] == "2"
    inasistencia = (
        (es_menor_escolar & no_asiste).groupby([cg[c] for c in k3]).any()
        .rename("inasistencia_escolar_menores").reset_index()
    )

    jefes = cg[_norm_llave(cg["P6050"]).astype("string") == "1"][
        [*k3, "ORDEN", "P6160", "P6090", "P3042"]
    ].copy()

    if path_oc.exists():
        oc = pd.read_parquet(path_oc, columns=[*k3, "ORDEN", "P6920"]).replace("", pd.NA)
        for c in [*k3, "ORDEN"]:
            oc[c] = _norm_llave(oc[c])
        jefes = jefes.merge(oc[[*k3, "ORDEN", "P6920"]], on=[*k3, "ORDEN"], how="left")
    else:
        jefes["P6920"] = pd.NA

    df = jefes.merge(hv, on=k3, how="left").merge(inasistencia, on=k3, how="left")

    df["analfabetismo"] = (df["P6160"] == "2").astype("Int8")
    df["sin_aseguramiento_salud"] = (df["P6090"] == "2").astype("Int8")

    nivel_edu = pd.to_numeric(df["P3042"], errors="coerce")
    # 99 = "no sabe/no informa" -> se trata como NO privado (conservador), no como faltante.
    df["bajo_logro_educativo_jefe"] = ((nivel_edu < NIVEL_MIN_SECUNDARIA) & (nivel_edu != 99)).astype("Int8")

    df["inasistencia_escolar_menores"] = df["inasistencia_escolar_menores"].fillna(False).astype("Int8")

    personas = pd.to_numeric(df["P6008"], errors="coerce")
    cuartos_dormir = pd.to_numeric(df["P5010"], errors="coerce")
    personas_cuarto = personas / cuartos_dormir.replace(0, pd.NA)
    df["hacinamiento"] = (personas_cuarto > UMBRAL_HACINAMIENTO).astype("Int8")

    df["sin_alcantarillado"] = (df["P4030S3"] == "2").astype("Int8")
    df["sin_acueducto"] = (df["P4030S5"] == "2").astype("Int8")

    # Privado si NO está ocupado y cotizando a pensión (combina informalidad +
    # desempleo/inactividad del jefe en un solo indicador de trabajo).
    df["sin_cotizacion_pension_jefe"] = (df["P6920"] != "1").astype("Int8")

    df["ipm_geih_score"] = df[PRIVACIONES].sum(axis=1, min_count=1)
    df["POBRE_GEIH"] = (df["ipm_geih_score"] >= K_POBRE).astype("Int8")
    # Variantes de umbral para análisis de sensibilidad (ver _validar) — el
    # mismo score, distinto corte. K_POBRE=3 es el umbral adoptado.
    for k in range(1, len(PRIVACIONES) + 1):
        df[f"POBRE_GEIH_K{k}"] = (df["ipm_geih_score"] >= k).astype("Int8")

    cols_salida = ["llave_directorio", "llave_secuencia_p", "llave_hogar", *PRIVACIONES,
                   "ipm_geih_score", "POBRE_GEIH", *[f"POBRE_GEIH_K{k}" for k in range(1, len(PRIVACIONES) + 1)]]
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

    print(f"\nCobertura por privación (% con valor 1, sobre el total — 0% de faltantes en las {len(PRIVACIONES)}):")
    for c in PRIVACIONES:
        print(f"  {c}: {df[c].mean()*100:.1f}%")

    print(f"\nDistribución del score (0-{len(PRIVACIONES)}):")
    print((df["ipm_geih_score"].value_counts(normalize=True).sort_index() * 100).round(1).astype(str) + " %")

    print("\nSensibilidad al umbral K (tasa de pobreza según dónde se corte el score):")
    for k in range(1, len(PRIVACIONES) + 1):
        tasa = df[f"POBRE_GEIH_K{k}"].mean() * 100
        marca = " <- adoptado (K_POBRE)" if k == K_POBRE else ""
        print(f"  K>={k}: {tasa:.1f}%{marca}")
    print(
        f"  Referencia externa: IPM oficial (Hogares Nacional 2024, 15 privaciones) = "
        f"{IPM_OFICIAL_TASA_POBREZA*100:.1f}% — K={K_POBRE} es el más cercano en orden de "
        f"magnitud entre los {len(PRIVACIONES)} cortes probados; no se ajustó el umbral para "
        f"igualarlo, es una verificación de plausibilidad ex post, no una calibración."
    )


def main() -> None:
    if not FUSIONADO.exists():
        raise SystemExit(f"Falta {FUSIONADO}: corra src.emparejamiento.emparejamiento_hotdeck_geih_sisben")

    tablas = [t for mes in MESES if (t := _outcome_mes(mes)) is not None]
    outcome = pd.concat(tablas, ignore_index=True)
    logger.info("Outcome IPM-GEIH (ampliado, %s privaciones) construido: %s hogares", len(PRIVACIONES), f"{len(outcome):,}")

    fus = pd.read_parquet(FUSIONADO)
    for c in ("llave_directorio", "llave_secuencia_p", "llave_hogar"):
        fus[c] = fus[c].astype("string")
    df = fus.merge(outcome, on=["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"], how="left")

    n_sin = df["ipm_geih_score"].isna().sum()
    assert n_sin == 0, f"{n_sin} hogares del Hot-Deck sin outcome tras el cruce — revisar llaves"
    logger.info("Hogares sin outcome tras el cruce: %s de %s (0.0%%)", n_sin, len(df))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)

    print(f"\n=== Outcome real: IPM-GEIH ({len(PRIVACIONES)} privaciones, verificadas contra el diccionario oficial) ===")
    print(f"Hogares: {len(df):,}")
    print(f"Score medio: {df['ipm_geih_score'].mean():.2f} (0-{len(PRIVACIONES)})")

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
