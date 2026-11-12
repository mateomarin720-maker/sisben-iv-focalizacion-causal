"""Reglas del IPM-GEIH (8 privaciones) en un solo lugar.

Las usan `src/3_preprocesamiento.py` (GEIH) y
`src/validacion/validar_ipm_geih_ecv.py` (ECV y base del IPM del DANE),
para que el proxy que se valida sea exactamente el que se estima.

`privaciones` recibe una fila por hogar con los códigos de la GEIH como
texto (la ECV usa los mismos códigos de pregunta; quien la llama renombra
`P8587` → `P3042` y `P8520S3/S5` → `P4030S3/S5`):

  P6160    jefe: ¿sabe leer y escribir? (1 sí, 2 no)
  P6090    jefe: ¿afiliado a salud? (1 sí, 2 no, 9 no sabe)
  P3042    jefe: nivel educativo más alto (1 ninguno, 2 preescolar,
           3 primaria, 4 secundaria, ...; 99 no sabe)
  P6920    jefe: ¿cotiza a pensión? (1 sí, 2 no, 3 pensionado); falta si
           no está ocupado
  P6008    personas del hogar
  P5010    cuartos donde duermen
  P4030S3  alcantarillado (1 sí, 2 no)
  P4030S5  acueducto (1 sí, 2 no)
  P5020    servicio sanitario (1 inodoro a alcantarillado, 2 a pozo séptico,
           3 sin conexión, 4 letrina, 5 bajamar, 6 no tiene)
  P5050    fuente del agua para consumo (1 acueducto por tubería, 2 otra
           fuente por tubería, 3 pozo con bomba, 4 pozo sin bomba, 5 lluvia,
           6 río o manantial, 7 pila pública, 8 carro tanque, 9 aguatero,
           10 embotellada)
  CLASE    1 urbano (cabecera), 2 rural
  inasistencia_escolar_menores  algún miembro de 6 a 16 años no asiste

Las tres privaciones de vivienda siguen la definición oficial del IPM, que
cambia con la zona (DANE, «Algoritmo para la construcción del índice de
pobreza multidimensional», sección 4.5; Azure, `0_raw/ipm/2024/docs_ipm/`):

  sin_alcantarillado  (inadecuada eliminación de excretas) urbano: sin
                      alcantarillado; rural: inodoro sin conexión, bajamar o
                      sin servicio sanitario (la letrina y el pozo séptico no
                      cuentan).
  sin_acueducto       urbano: sin acueducto; rural: agua de pozo sin bomba,
                      lluvia, río, carro tanque, aguatero o embotellada.
  hacinamiento        urbano: 3 o más personas por cuarto para dormir;
                      rural: más de 3.

Hasta el 2026-11-11 las tres usaban la regla urbana en todo el país: el
proxy marcaba sin alcantarillado al 84 % de los hogares rurales (19,5 % en
el IPM oficial) y daba 63,7 % de pobres rurales frente a 21,5 %
(`docs/resultados/1_datos_y_enlace/VALIDACION_IPM_GEIH_ECV.md`).
"""
from __future__ import annotations

import pandas as pd

UMBRAL_HACINAMIENTO = 3  # personas por cuarto para dormir: urbano >= 3, rural > 3
SANITARIO_RURAL_PRIVADO = {"3", "5", "6"}  # P5020: sin conexión, bajamar, no tiene
AGUA_RURAL_PRIVADA = {"4", "5", "6", "8", "9", "10"}  # P5050: pozo sin bomba, lluvia, río, carro tanque, aguatero, embotellada
EDAD_MIN_ESCOLAR, EDAD_MAX_ESCOLAR = 6, 16  # universo de "inasistencia_escolar_menores"
NIVEL_MIN_SECUNDARIA = 4  # 1=Ninguno, 2=Preescolar, 3=Primaria, 4=Secundaria... privación si < 4
K_POBRE = 3  # umbral adoptado (de 8 privaciones)
PRIVACIONES = [
    "analfabetismo", "bajo_logro_educativo_jefe", "inasistencia_escolar_menores",
    "sin_aseguramiento_salud", "sin_cotizacion_pension_jefe",
    "hacinamiento", "sin_alcantarillado", "sin_acueducto",
]


def inasistencia_escolar(edad: pd.Series, asiste: pd.Series, hogar: list[pd.Series]) -> pd.Series:
    """Por hogar: algún miembro de 6 a 16 años que no asiste (`asiste` == "2")."""
    menor = pd.to_numeric(edad, errors="coerce").between(EDAD_MIN_ESCOLAR, EDAD_MAX_ESCOLAR)
    return (menor & (asiste == "2")).groupby(hogar).any().rename("inasistencia_escolar_menores")


def privaciones(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega las 8 privaciones, `ipm_geih_score`, `POBRE_GEIH` y las
    variantes `POBRE_GEIH_K1..K8` (mismo puntaje, otro corte)."""
    df = df.copy()
    df["analfabetismo"] = (df["P6160"] == "2").astype("Int8")
    df["sin_aseguramiento_salud"] = (df["P6090"] == "2").astype("Int8")

    nivel_edu = pd.to_numeric(df["P3042"], errors="coerce")
    # 99 = "no sabe/no informa" -> se trata como NO privado (conservador), no como faltante.
    df["bajo_logro_educativo_jefe"] = ((nivel_edu < NIVEL_MIN_SECUNDARIA) & (nivel_edu != 99)).astype("Int8")

    df["inasistencia_escolar_menores"] = df["inasistencia_escolar_menores"].fillna(False).astype("Int8")

    urbano = df["CLASE"] == "1"
    personas = pd.to_numeric(df["P6008"], errors="coerce")
    cuartos_dormir = pd.to_numeric(df["P5010"], errors="coerce")
    personas_cuarto = personas / cuartos_dormir.replace(0, pd.NA)
    hacinado = (personas_cuarto >= UMBRAL_HACINAMIENTO).where(urbano, personas_cuarto > UMBRAL_HACINAMIENTO)
    df["hacinamiento"] = hacinado.astype("Int8")

    df["sin_alcantarillado"] = (df["P4030S3"] == "2").where(urbano, df["P5020"].isin(SANITARIO_RURAL_PRIVADO)).astype("Int8")
    df["sin_acueducto"] = (df["P4030S5"] == "2").where(urbano, df["P5050"].isin(AGUA_RURAL_PRIVADA)).astype("Int8")

    # Privado si NO está ocupado y cotizando a pensión (combina informalidad +
    # desempleo/inactividad del jefe en un solo indicador de trabajo).
    df["sin_cotizacion_pension_jefe"] = (df["P6920"] != "1").astype("Int8")

    df["ipm_geih_score"] = df[PRIVACIONES].sum(axis=1, min_count=1)
    df["POBRE_GEIH"] = (df["ipm_geih_score"] >= K_POBRE).astype("Int8")
    for k in range(1, len(PRIVACIONES) + 1):
        df[f"POBRE_GEIH_K{k}"] = (df["ipm_geih_score"] >= k).astype("Int8")
    return df
