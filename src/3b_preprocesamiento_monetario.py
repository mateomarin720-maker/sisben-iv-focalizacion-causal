"""Outcome: pobreza monetaria (ingreso per cápita, FGT0/FGT1) sobre GEIH.

Construye el outcome que pide el giro propuesto por el tutor el
2026-10-27 (ver `docs/seguimiento/CHANGELOG_PENDIENTES.md`): en vez de
(o además de) el IPM-GEIH de `3_preprocesamiento.py`, el resultado pasa a
ser la pobreza monetaria — ingreso per cápita del hogar comparado contra
la línea de pobreza oficial del DANE, con los indicadores FGT (Foster,
Greer y Thorbecke, 1984).

## Líneas de pobreza — fuente oficial verificada

`docs/insumos/DANE_boletin_PM_2024.pdf` (DANE, *Pobreza Monetaria en
Colombia, año 2024*, Tabla 1 y Tabla 4), pesos corrientes mensuales por
persona:

| Dominio | Línea de pobreza | Línea de pobreza extrema |
|---|---|---|
| Total nacional | 460.198 | 227.220 |
| Cabeceras (urbano) | 510.161 | 242.389 |
| Centros poblados y rural disperso (rural) | 291.998 | 176.154 |

El esquema canónico de este proyecto solo distingue urbano/rural
(`geo_zona`, `CLASE` de GEIH: 1=Urbano/2=Rural, confirmado — ver
`docs/insumos/DICCIONARIO_HOTDECK.md` §4) — no los sub-dominios "13
ciudades y A.M." / "otras cabeceras" que usa el DANE dentro de
"cabeceras". Se usan las líneas de cabeceras/resto, más gruesas que las 5
líneas oficiales por dominio — ver "Limitaciones".

Incidencia (FGT0) y brecha (FGT1) oficiales 2024, para validar por
plausibilidad (mismo criterio que la tasa de IPM oficial en
`3_preprocesamiento.py`): nacional 31,8 % / 12,6 % (pobreza), 11,7 % /
4,5 % (pobreza extrema); por dominio: cabeceras 28,6 %, centros poblados
y rural disperso 42,5 %.

## Qué SÍ y qué NO replica de la metodología oficial del DANE

El DANE construye el "ingreso per cápita de la unidad de gasto" en 5
pasos (boletín técnico, nota 2): (1) agregar ingresos por fuente, (2) un
MODELO DE IMPUTACIÓN para corregir subreporte, (3) consolidar a nivel de
Población en Edad de Trabajar, (4) agregar a nivel de "unidad de gasto"
(el hogar SIN pensionistas ni empleados domésticos internos), (5) un
AJUSTE POR PROPIEDAD DE LA VIVIENDA (arriendo imputado a propietarios).

Este script solo hace el paso (1): suma directa de los ingresos
reportados en los módulos `ocupados`, `otros_ingresos` y `no_ocupados`
de GEIH, agregados al HOGAR completo (`hog_num_personas`, no la "unidad
de gasto" exacta). **No imputa subreporte ni arriendo imputado** — es,
por diseño, una aproximación más cruda que la oficial, que
previsiblemente SUBESTIMA el ingreso real (más aún en informalidad, con
subreporte conocido) y por tanto puede SOBREESTIMAR la pobreza. Se valida
por plausibilidad contra las cifras oficiales (arriba), no se espera que
coincidan exactamente.

## Ingreso laboral: `INGLABO`, no `P6500` solo (corregido 2026-11-02)

**Primer intento (descartado):** reconstruir el ingreso laboral sumando
`P6500` (empleo principal) + horas extra/primas/bonificaciones (si no
estaban ya incluidas, según la sub-pregunta de cada una) + subsidios +
pago en especie. Al correr esto, el indicador daba FGT0=53,6% y
FGT1=39,0% — muy por encima de lo oficial (31,8%/12,6%), no por el
margen esperable de una aproximación sin imputación, sino por un orden
de magnitud distinto.

**Causa encontrada:** `P6500` por sí solo tiene **47,7 % de no
respuesta** entre las personas ocupadas (13.751 de 28.815 en enero). El
script trataba esos vacíos como ingreso $0 (en vez de "no informa"), lo
que: (a) inflaba artificialmente el conteo de hogares con ingreso 0, y
(b) especialmente inflaba FGT1, porque un hogar con ingreso real alto
pero P6500 vacío contribuía una brecha de pobreza del 100% en vez de 0%.

**Corrección:** el módulo `ocupados` trae `INGLABO` ("Ingresos
Laborales"), la variable de ingreso laboral que el DANE ya construye y
**imputa** internamente (reduce la no respuesta de 47,7% a 4,3%) — es
precisamente el paso (2) de la metodología oficial (nota 2 arriba) que
este script no replica por su cuenta. Se usa `INGLABO` directo como
ingreso laboral de cada persona ocupada, sin reconstruirlo a mano. El
diccionario del proyecto no detalla su composición exacta, pero su
cobertura y orden de magnitud (mediana ≈ $1.160.000/mes en enero,
coherente con el salario mínimo 2024 de $1.300.000) son consistentes con
que ya incluye horas extra, primas, bonificaciones, subsidios y pago en
especie — sumarlos aparte sería doble conteo.

## Otras fuentes — `otros_ingresos` (por hogar, todos los miembros) y `no_ocupados`

- `P7500S1A1`/`S2A1`/`S3A1`: arriendos, pensiones/jubilaciones, pensión
  alimenticia — mensuales, se suman tal cual.
- `P7510S1A1`...`S7A1`: dinero de otros hogares, ayudas institucionales,
  intereses/dividendos, cesantías, otras fuentes — la pregunta es "en los
  ÚLTIMOS DOCE MESES", se divide entre 12 para un equivalente mensual.
- `P7422S1` (módulo `no_ocupados`): ingreso del mes pasado por trabajo de
  personas NO clasificadas como ocupadas (trabajo ocasional) — no está en
  `ocupados` porque esas personas no pasan por ese módulo.

Tratamiento de sí/no: si la pregunta de "¿recibió...?" es "No" o está
vacía, el monto correspondiente se trata como 0 (no como faltante) — es
la lectura natural de la secuencia de filtro del cuestionario, no una
imputación.

Uso:
    poetry run python src/3b_preprocesamiento_monetario.py
Salida: data/2_models/muestra_estimacion_monetaria_2024.parquet (la
tabla de `3_preprocesamiento.py` + `ingreso_percapita`,
`POBRE_MONETARIO`, `POBRE_EXTREMO_MONETARIO`, `brecha_pobreza_monetaria`,
`brecha_pobreza_extrema`).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
BASE = Path("data/2_models/muestra_estimacion_2024.parquet")
OUT = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
REPORT_DIR = Path("docs/reports")
MESES = [f"{m:02d}" for m in range(1, 13)]

# DANE, Pobreza Monetaria en Colombia 2024 (bol-PM-2024.pdf), Tabla 1 y Tabla 4.
# Pesos corrientes per cápita mensuales. geo_zona (CLASE): 1=Urbano/2=Rural.
LINEA_POBREZA = {"1": 510_161.0, "2": 291_998.0}
LINEA_EXTREMA = {"1": 242_389.0, "2": 176_154.0}
FGT0_OFICIAL, FGT1_OFICIAL = 0.318, 0.126
FGT0_EXTREMA_OFICIAL, FGT1_EXTREMA_OFICIAL = 0.117, 0.045


def _norm_llave(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce").astype("Int64").astype("string")


def _si(serie: pd.Series) -> pd.Series:
    return serie == "1"


def _ingreso_mes(mes: str) -> pd.DataFrame | None:
    path_oc = GEIH_DIR / mes / "ocupados.parquet"
    path_oi = GEIH_DIR / mes / "otros_ingresos.parquet"
    path_no = GEIH_DIR / mes / "no_ocupados.parquet"
    if not path_oc.exists():
        logger.warning("GEIH %s: falta módulo ocupados — se omite", mes)
        return None

    k3 = ["DIRECTORIO", "SECUENCIA_P", "HOGAR"]

    oc = pd.read_parquet(path_oc, columns=[*k3, "ORDEN", "INGLABO"]).replace("", pd.NA)
    for c in [*k3, "ORDEN"]:
        oc[c] = _norm_llave(oc[c])
    oc = oc.assign(ingreso_persona=pd.to_numeric(oc["INGLABO"], errors="coerce").fillna(0))
    ing_oc = oc.groupby(k3)["ingreso_persona"].sum().rename("ingreso_laboral_hogar")

    cols_oi = [
        *k3, "ORDEN",
        "P7500S1", "P7500S1A1", "P7500S2", "P7500S2A1", "P7500S3", "P7500S3A1",
        "P7510S1", "P7510S1A1", "P7510S2", "P7510S2A1", "P7510S3", "P7510S3A1",
        "P7510S5", "P7510S5A1", "P7510S6", "P7510S6A1", "P7510S7", "P7510S7A1",
    ]
    ing_oi = None
    if path_oi.exists():
        oi = pd.read_parquet(path_oi, columns=cols_oi).replace("", pd.NA)
        for c in [*k3, "ORDEN"]:
            oi[c] = _norm_llave(oi[c])

        def num_oi(col: str) -> pd.Series:
            return pd.to_numeric(oi[col], errors="coerce").fillna(0)

        ingreso_no_laboral = (
            np.where(_si(oi["P7500S1"]), num_oi("P7500S1A1"), 0)
            + np.where(_si(oi["P7500S2"]), num_oi("P7500S2A1"), 0)
            + np.where(_si(oi["P7500S3"]), num_oi("P7500S3A1"), 0)
            + np.where(_si(oi["P7510S1"]), num_oi("P7510S1A1"), 0) / 12
            + np.where(_si(oi["P7510S2"]), num_oi("P7510S2A1"), 0) / 12
            + np.where(_si(oi["P7510S3"]), num_oi("P7510S3A1"), 0) / 12
            + np.where(_si(oi["P7510S5"]), num_oi("P7510S5A1"), 0) / 12
            + np.where(_si(oi["P7510S6"]), num_oi("P7510S6A1"), 0) / 12
            + np.where(_si(oi["P7510S7"]), num_oi("P7510S7A1"), 0) / 12
        )
        oi = oi.assign(ingreso_persona=ingreso_no_laboral)
        ing_oi = oi.groupby(k3)["ingreso_persona"].sum().rename("ingreso_no_laboral_hogar")

    ing_no = None
    if path_no.exists():
        no = pd.read_parquet(path_no, columns=[*k3, "ORDEN", "P7422", "P7422S1"]).replace("", pd.NA)
        for c in [*k3, "ORDEN"]:
            no[c] = _norm_llave(no[c])
        no = no.assign(
            ingreso_persona=np.where(_si(no["P7422"]), pd.to_numeric(no["P7422S1"], errors="coerce").fillna(0), 0)
        )
        ing_no = no.groupby(k3)["ingreso_persona"].sum().rename("ingreso_otros_no_ocupados_hogar")

    fuentes = [s for s in (ing_oc, ing_oi, ing_no) if s is not None]
    out = fuentes[0].to_frame()
    for s in fuentes[1:]:
        out = out.join(s, how="outer")
    out = out.fillna(0)
    out["ingreso_hogar_mensual"] = out.sum(axis=1)

    out = out.reset_index().rename(columns={
        "DIRECTORIO": "llave_directorio", "SECUENCIA_P": "llave_secuencia_p", "HOGAR": "llave_hogar",
    })
    out["mes"] = mes
    return out[["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes", "ingreso_hogar_mensual"]]


def _clasificar_pobreza(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega ingreso_percapita, POBRE_MONETARIO/POBRE_EXTREMO_MONETARIO y
    las brechas FGT1 por hogar, a partir de `ingreso_hogar_mensual`,
    `hog_num_personas` y `geo_zona` ya presentes en `df`."""
    df = df.copy()
    personas = pd.to_numeric(df["hog_num_personas"], errors="coerce")
    df["ingreso_percapita"] = df["ingreso_hogar_mensual"] / personas.replace(0, pd.NA)

    zona = df["geo_zona"].astype(str)
    linea_pobreza = zona.map(LINEA_POBREZA)
    linea_extrema = zona.map(LINEA_EXTREMA)

    df["POBRE_MONETARIO"] = (df["ingreso_percapita"] < linea_pobreza).astype("Int8")
    df["POBRE_EXTREMO_MONETARIO"] = (df["ingreso_percapita"] < linea_extrema).astype("Int8")
    df["brecha_pobreza_monetaria"] = ((linea_pobreza - df["ingreso_percapita"]) / linea_pobreza).clip(lower=0)
    df["brecha_pobreza_extrema"] = ((linea_extrema - df["ingreso_percapita"]) / linea_extrema).clip(lower=0)
    return df


def _validar(df: pd.DataFrame) -> pd.DataFrame:
    n_sin_personas = df["ingreso_percapita"].isna().sum()
    assert n_sin_personas < len(df) * 0.01, (
        f"{n_sin_personas} hogares sin ingreso_percapita calculable (hog_num_personas "
        "faltante o 0) — revisar, es más del 1% de la muestra"
    )

    w = pd.to_numeric(df["fex"], errors="coerce").fillna(0)

    def fgt(serie_pobre: pd.Series, serie_brecha: pd.Series, mascara: pd.Series | None = None) -> tuple[float, float]:
        m = mascara if mascara is not None else pd.Series(True, index=df.index)
        ww = w[m]
        return (ww * serie_pobre[m]).sum() / ww.sum(), (ww * serie_brecha[m]).sum() / ww.sum()

    fgt0, fgt1 = fgt(df["POBRE_MONETARIO"], df["brecha_pobreza_monetaria"])
    fgt0x, fgt1x = fgt(df["POBRE_EXTREMO_MONETARIO"], df["brecha_pobreza_extrema"])

    print("\n=== Validación FGT (ponderado por fex) vs. DANE oficial 2024 ===")
    print(f"Hogares: {len(df):,} | sin ingreso_percapita calculable: {n_sin_personas} ({n_sin_personas/len(df)*100:.2f}%)")
    print(f"FGT0 pobreza monetaria:        {fgt0*100:5.1f}%  (oficial: {FGT0_OFICIAL*100:.1f}%)")
    print(f"FGT1 brecha pobreza monetaria: {fgt1*100:5.1f}%  (oficial: {FGT1_OFICIAL*100:.1f}%)")
    print(f"FGT0 pobreza extrema:          {fgt0x*100:5.1f}%  (oficial: {FGT0_EXTREMA_OFICIAL*100:.1f}%)")
    print(f"FGT1 brecha pobreza extrema:   {fgt1x*100:5.1f}%  (oficial: {FGT1_EXTREMA_OFICIAL*100:.1f}%)")

    filas = [dict(indicador="FGT0_pobreza", construido=fgt0, oficial=FGT0_OFICIAL),
             dict(indicador="FGT1_pobreza", construido=fgt1, oficial=FGT1_OFICIAL),
             dict(indicador="FGT0_pobreza_extrema", construido=fgt0x, oficial=FGT0_EXTREMA_OFICIAL),
             dict(indicador="FGT1_pobreza_extrema", construido=fgt1x, oficial=FGT1_EXTREMA_OFICIAL)]

    print("\nPor zona (oficial: cabeceras FGT0=28.6%, centros poblados y rural disperso FGT0=42.5%):")
    for codigo, nombre in [("1", "Cabeceras (urbano)"), ("2", "Centros poblados y rural disperso")]:
        m = df["geo_zona"].astype(str) == codigo
        f0, f1 = fgt(df["POBRE_MONETARIO"], df["brecha_pobreza_monetaria"], m)
        print(f"  {nombre}: FGT0={f0*100:.1f}%  FGT1={f1*100:.1f}%  (n={m.sum():,})")
        filas.append(dict(indicador=f"FGT0_{nombre}", construido=f0, oficial=np.nan))
        filas.append(dict(indicador=f"FGT1_{nombre}", construido=f1, oficial=np.nan))

    return pd.DataFrame(filas)


def main() -> None:
    if not BASE.exists():
        raise SystemExit(f"Falta {BASE}: corra src/3_preprocesamiento.py primero")

    tablas = [t for mes in MESES if (t := _ingreso_mes(mes)) is not None]
    ingreso = pd.concat(tablas, ignore_index=True)
    logger.info("Ingreso de hogar construido: %s hogares-mes", f"{len(ingreso):,}")

    base = pd.read_parquet(BASE)
    for c in ("llave_directorio", "llave_secuencia_p", "llave_hogar"):
        base[c] = base[c].astype("string")
        ingreso[c] = ingreso[c].astype("string")

    df = base.merge(ingreso, on=["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"], how="left")
    df["ingreso_hogar_mensual"] = df["ingreso_hogar_mensual"].fillna(0)
    df = _clasificar_pobreza(df)

    print(f"\n=== Outcome: pobreza monetaria (ingreso per cápita, FGT0/FGT1) ===")
    print(f"Hogares: {len(df):,}")
    print(f"Ingreso per cápita mensual — media: ${df['ingreso_percapita'].mean():,.0f} | "
          f"mediana: ${df['ingreso_percapita'].median():,.0f}")

    validacion = _validar(df)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    validacion.to_csv(REPORT_DIR / "validacion_fgt_pobreza_monetaria.csv", index=False)
    print(f"\nGuardado: {OUT}")
    print(f"Guardado: {REPORT_DIR / 'validacion_fgt_pobreza_monetaria.csv'}")


if __name__ == "__main__":
    main()
