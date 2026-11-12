"""Validación del IPM-GEIH (8 privaciones) contra la ECV y el IPM oficial.

El IPM oficial del DANE se calcula con la Encuesta Nacional de Calidad de
Vida (ECV), que usa los mismos códigos de pregunta que la GEIH para las
8 privaciones del proxy. Eso permite calcular el proxy, con las mismas
reglas (`src/indicadores/ipm_proxy.py`), en hogares de la ECV.

  A. Hogar por hogar, contra el IPM oficial 2024. La base del IPM 2024
     sale de la misma ECV 2024 (coinciden el 100 % de los `DIRECTORIO` y
     de los factores de expansión) y trae, para cada hogar, las
     respuestas crudas y la clasificación oficial (15 privaciones, corte
     33 %). Se calcula el proxy en esos hogares y se compara con `POBRE`
     oficial: concordancia, sensibilidad, especificidad, kappa, por zona
     (la zona sale del módulo de vivienda de la ECV), por umbral K y por
     privación. Como contraste, lo mismo con la base del IPM 2025.
  B. Mismo año, ECV 2024 frente a GEIH 2024. El proxy en los módulos
     crudos de la ECV 2024 frente al de la GEIH 2024: prevalencias,
     nacional, por zona y por departamento sobre el mismo marco.

Todo se lee directo de Azure, en memoria (`leer_bytes`); nada se guarda en
`data/`. Cifras de hogares, ponderadas por el factor de expansión.

Uso:  python -m src.validacion.validar_ipm_geih_ecv
Entradas (Azure): 0_raw/ipm/2024/BasesDatos-IMP-2024.zip (IPM 2024),
          0_raw/ipm/nacional/*.csv (IPM 2025), ecv/*.zip (ECV 2024);
          local: data/2_models/muestra_estimacion_2024.parquet
Salidas: docs/reports/validacion_ipm_geih_ecv.txt y _privaciones.csv,
         _departamentos.csv, _umbrales.csv
"""
from __future__ import annotations

import io
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from src.indicadores.ipm_proxy import K_POBRE, PRIVACIONES, inasistencia_escolar, privaciones
from src.utils.azure_storage import leer_bytes
from src.validacion.verificar_representatividad_sisben import solo_capital

GEIH = Path("data/2_models/muestra_estimacion_2024.parquet")
REPORTES = Path("docs/reports")
ECV = "ecv/"
IPM_2024 = "0_raw/ipm/2024/BasesDatos-IMP-2024.zip"
# Archivos de cada base del IPM (nacional) y la columna del hogar que cruza con
# `SECUENCIA_P` de personas: en 2024 es SECUENCIA_ENCUESTA (como en la ECV),
# en 2025 es SECUENCIA_P.
BASES_IPM = {
    2024: dict(zip=IPM_2024, hogares="Nacional/Hogares (Nacional)/Hogares (Nacional) 2024.csv",
               personas="Nacional/Personas (Nacional)/Personas (Nacional) 2024.csv",
               viviendas="Nacional/Viviendas (Nacional)/Viviendas (Nacional) 2024.csv", hogar="SECUENCIA_ENCUESTA"),
    2025: dict(zip=None, hogares="0_raw/ipm/nacional/hogares.csv", personas="0_raw/ipm/nacional/personas.csv",
               viviendas="0_raw/ipm/nacional/viviendas.csv", hogar="SECUENCIA_P"),
}
# Nombres de la base 2024 que difieren de los de 2025.
RENOMBRAR_IPM = {"personas": "PERSONAS", "inansistencia_escolar": "inasistencia_escolar"}

# Privación del proxy -> privación oficial del IPM que mide lo mismo (con su propia definición).
OFICIAL = {
    "analfabetismo": "analfabetismo",
    "bajo_logro_educativo_jefe": "logro_educativo",
    "inasistencia_escolar_menores": "inasistencia_escolar",
    "sin_aseguramiento_salud": "aseguramiento_salud",
    "sin_cotizacion_pension_jefe": "empleo_formal",
    "hacinamiento": "hacinamiento",
    "sin_alcantarillado": "alcantarillado",
    "sin_acueducto": "acueducto",
}
# La ECV llama P8587 al nivel educativo (P3042 en la GEIH) y P8520S3/S5 al
# alcantarillado y acueducto (P4030S3/S5): mismas categorías.


def codigo(s: pd.Series) -> pd.Series:
    """Respuesta numérica como el texto de la GEIH ("2"), con pd.NA si falta."""
    return pd.to_numeric(s, errors="coerce").astype("Int64").astype("string")


def proxy_hogares(personas: pd.DataFrame, hogares: pd.DataFrame, hogar: list[str]) -> pd.DataFrame:
    """Proxy por hogar a partir de personas (con `es_jefe`, P6040, P6160,
    P6090, P3042, P6920, asiste) y hogares (P6008, P5010, P4030S3/S5).
    Si el jefe no está ocupado, P6920 falta y cuenta como privado, igual que
    en la GEIH (donde no aparece en el módulo de ocupados)."""
    ina = inasistencia_escolar(personas["P6040"], personas["asiste"], [personas[c] for c in hogar]).reset_index()
    jefes = personas[personas["es_jefe"]][[*hogar, "P6160", "P6090", "P3042", "P6920"]].copy()
    jefes["P6920"] = jefes["P6920"].astype(object).where(jefes["P6920"].notna(), np.nan)
    df = jefes.merge(hogares, on=hogar, how="inner").merge(ina, on=hogar, how="left")
    return privaciones(df)


@lru_cache(maxsize=None)
def _zip(ruta_azure: str) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(leer_bytes(ruta_azure)))


def _leer_csv(fuente, columnas: list[str] | None = None) -> pd.DataFrame:
    """CSV con separador detectado (la ECV usa ";", el IPM ",")."""
    crudo = fuente.read()
    sep = ";" if crudo[:500].count(b";") > crudo[:500].count(b",") else ","
    return pd.read_csv(io.BytesIO(crudo), sep=sep, encoding="latin1", usecols=columnas, low_memory=False)


def _csv_zip(ruta_azure: str, columnas: list[str] | None = None, miembro: str | None = None) -> pd.DataFrame:
    z = _zip(ruta_azure)
    miembro = miembro or next(x for x in z.namelist() if x.upper().endswith(".CSV"))
    with z.open(miembro) as f:
        return _leer_csv(f, columnas)


def _csv_ipm(anio: int, cual: str, columnas: list[str] | None = None) -> pd.DataFrame:
    base = BASES_IPM[anio]
    if base["zip"]:
        df = _csv_zip(base["zip"], miembro=base[cual])
    else:
        df = _leer_csv(io.BytesIO(leer_bytes(base[cual])))
    df = df.rename(columns=RENOMBRAR_IPM)
    return df[columnas] if columnas else df


# --------------------------------------------------------------------------
# A. Base del IPM: proxy frente a la clasificación oficial, hogar por hogar
# --------------------------------------------------------------------------

def base_ipm(anio: int = 2024) -> pd.DataFrame:
    """Hogares de la base del IPM con el proxy y la clasificación oficial."""
    sec = BASES_IPM[anio]["hogar"]
    hog = ["DIRECTORIO", "SECUENCIA_P"]
    p = _csv_ipm(anio, "personas", [*hog, "P6051", "P6040", "P6160", "P8587", "P8586", "P6090", "P6920"])
    h = _csv_ipm(anio, "hogares")
    h = h.drop(columns=[c for c in h.columns if c == "SECUENCIA_P" and sec != "SECUENCIA_P"]).rename(
        columns={sec: "SECUENCIA_P"})
    v = _csv_ipm(anio, "viviendas", ["DIRECTORIO", "P8520S3", "P8520S5"])
    personas = pd.DataFrame({**{c: p[c] for c in hog}, "es_jefe": p["P6051"] == 1, "P6040": p["P6040"],
                             "asiste": codigo(p["P8586"]), "P6160": codigo(p["P6160"]), "P6090": codigo(p["P6090"]),
                             "P3042": codigo(p["P8587"]), "P6920": codigo(p["P6920"])})
    hogares = h[[*hog, "PERSONAS", "P5010"]].merge(v, on="DIRECTORIO", how="left")
    hogares = pd.DataFrame({**{c: hogares[c] for c in hog}, "P6008": hogares["PERSONAS"], "P5010": hogares["P5010"],
                            "P4030S3": codigo(hogares["P8520S3"]), "P4030S5": codigo(hogares["P8520S5"])})
    proxy = proxy_hogares(personas, hogares, hog)
    oficial = h[[*hog, "FEX_C", "IPM", "POBRE", *OFICIAL.values()]].rename(
        columns={c: f"oficial_{c}" for c in OFICIAL.values()})
    return proxy.merge(oficial, on=hog, how="inner")


def concordancia(proxy: pd.Series, oficial: pd.Series, w: pd.Series) -> dict:
    """Tabla 2x2 ponderada: tasa de cada uno, concordancia, sensibilidad
    (de los pobres oficiales, cuántos marca el proxy), especificidad,
    precisión y kappa de Cohen."""
    ok = proxy.notna() & oficial.notna()
    a, b, w = proxy[ok].astype(int).to_numpy(), oficial[ok].astype(int).to_numpy(), w[ok].to_numpy(float)
    t = w.sum()
    p11, p10 = w[(a == 1) & (b == 1)].sum() / t, w[(a == 1) & (b == 0)].sum() / t
    p01, p00 = w[(a == 0) & (b == 1)].sum() / t, w[(a == 0) & (b == 0)].sum() / t
    pa, pb = p11 + p10, p11 + p01
    acuerdo = p11 + p00
    azar = pa * pb + (1 - pa) * (1 - pb)
    return dict(tasa_proxy=pa, tasa_oficial=pb, concordancia=acuerdo,
                sensibilidad=p11 / pb if pb else np.nan, especificidad=p00 / (1 - pb) if pb < 1 else np.nan,
                precision=p11 / pa if pa else np.nan, kappa=(acuerdo - azar) / (1 - azar) if azar < 1 else np.nan,
                hogares=int(ok.sum()))


def _spearman_ponderado(x: pd.Series, y: pd.Series) -> float:
    return float(pd.Series(x).rank().corr(pd.Series(y).rank()))


# --------------------------------------------------------------------------
# B. ECV 2024 frente a GEIH 2024
# --------------------------------------------------------------------------

def ecv_2024() -> pd.DataFrame:
    """Proxy en la ECV 2024. Personas: DIRECTORIO + SECUENCIA_P (hogar) +
    ORDEN; hogar (servicios): DIRECTORIO + SECUENCIA_ENCUESTA; vivienda:
    DIRECTORIO."""
    per = ["DIRECTORIO", "SECUENCIA_P", "ORDEN"]
    comp = _csv_zip(ECV + "DBF-ENCV-Caracteristicas_composicion_hogar-2024.zip", [*per, "P6040", "P6051"])
    edu = _csv_zip(ECV + "DBF-ENCV-Educacion-2024.zip", [*per, "P6160", "P8586", "P8587"])
    sal = _csv_zip(ECV + "DBF-ENCV-Salud2024.zip", [*per, "P6090"])
    ft = _csv_zip(ECV + "DBF-ENCV-Fuerza_trabajo-2024.zip", [*per, "P6920"])
    serv = _csv_zip(ECV + "DBF-ENCV-Servicios_hogar-2024.zip", ["DIRECTORIO", "SECUENCIA_ENCUESTA", "FEX_C", "P5010"])
    viv = _csv_zip(ECV + "DBF-ENCV-Datos_vivienda-2024.zip", ["DIRECTORIO", "CLASE", "P1_DEPARTAMENTO", "P1_MUNICIPIO", "P8520S3", "P8520S5"])

    p = comp.merge(edu, on=per, how="left").merge(sal, on=per, how="left").merge(ft, on=per, how="left")
    hog = ["DIRECTORIO", "SECUENCIA_P"]
    personas = pd.DataFrame({**{c: p[c] for c in hog}, "es_jefe": p["P6051"] == 1, "P6040": p["P6040"],
                             "asiste": codigo(p["P8586"]), "P6160": codigo(p["P6160"]), "P6090": codigo(p["P6090"]),
                             "P3042": codigo(p["P8587"]), "P6920": codigo(p["P6920"])})
    n = p.groupby(hog).size().rename("P6008").reset_index()
    hogares = (serv.rename(columns={"SECUENCIA_ENCUESTA": "SECUENCIA_P"}).merge(n, on=hog, how="left")
               .merge(viv, on="DIRECTORIO", how="left"))
    hogares = pd.DataFrame({**{c: hogares[c] for c in hog}, "P6008": hogares["P6008"], "P5010": hogares["P5010"],
                            "P4030S3": codigo(hogares["P8520S3"]), "P4030S5": codigo(hogares["P8520S5"]),
                            "fex": hogares["FEX_C"], "zona": np.where(hogares["CLASE"] == 1, "Cabecera", "Resto"),
                            "depto": hogares["P1_DEPARTAMENTO"].astype(int).astype(str).str.zfill(2),
                            "capital": hogares["P1_MUNICIPIO"].astype(int) % 1000 == 1})  # 001 = capital
    return proxy_hogares(personas, hogares, hog)


def geih_2024() -> pd.DataFrame:
    g = pd.read_parquet(GEIH, columns=["geo_depto", "geo_zona", "fex", *PRIVACIONES, "ipm_geih_score", "POBRE_GEIH"])
    return g.assign(fex=pd.to_numeric(g["fex"], errors="coerce"), depto=g["geo_depto"].astype(str),
                    zona=np.where(g["geo_zona"].astype(str) == "1", "Cabecera", "Resto"))


def _tasa(df: pd.DataFrame, col: str) -> float:
    ok = df[col].notna()
    return float(np.average(df.loc[ok, col].astype(float), weights=df.loc[ok, "fex"]))


# --------------------------------------------------------------------------

def main() -> None:
    REPORTES.mkdir(parents=True, exist_ok=True)
    lineas = ["Validación del IPM-GEIH (8 privaciones, corte K = %d) contra la ECV y el IPM oficial" % K_POBRE,
              "Generado por src/validacion/validar_ipm_geih_ecv.py. Hogares, ponderados por el factor de expansión.", ""]

    # A
    a = base_ipm(2024)
    w = a["FEX_C"]
    c = concordancia(a["POBRE_GEIH"], a["POBRE"], w)
    lineas += ["A. Base del IPM 2024 (sale de la ECV 2024): proxy frente a POBRE oficial, hogar por hogar",
               f"   Hogares: {c['hogares']:,}".replace(",", "."),
               f"   Tasa de pobreza: proxy {c['tasa_proxy']:.1%}, oficial {c['tasa_oficial']:.1%}",
               f"   Concordancia {c['concordancia']:.1%}; sensibilidad {c['sensibilidad']:.1%}; "
               f"especificidad {c['especificidad']:.1%}; precisión {c['precision']:.1%}; kappa {c['kappa']:.3f}",
               f"   Correlación de rangos entre el puntaje del proxy y el IPM oficial: "
               f"{_spearman_ponderado(a['ipm_geih_score'], a['IPM']):.3f}"]
    zona = _csv_zip(ECV + "DBF-ENCV-Datos_vivienda-2024.zip", ["DIRECTORIO", "CLASE"])
    az = a.merge(zona, on="DIRECTORIO", how="left")
    lineas.append(f"   Hogares de la base con zona en la ECV 2024: {az['CLASE'].notna().mean():.1%}")
    for nombre, clase in (("Cabecera", 1), ("Resto", 2)):
        d = az[az["CLASE"] == clase]
        r = concordancia(d["POBRE_GEIH"], d["POBRE"], d["FEX_C"])
        lineas.append(f"   {nombre}: proxy {r['tasa_proxy']:.1%}, oficial {r['tasa_oficial']:.1%}; concordancia "
                      f"{r['concordancia']:.1%}; sensibilidad {r['sensibilidad']:.1%}; kappa {r['kappa']:.3f}")
    a25 = base_ipm(2025)
    c25 = concordancia(a25["POBRE_GEIH"], a25["POBRE"], a25["FEX_C"])
    n25 = f"{c25['hogares']:,}".replace(",", ".")
    lineas += [f"   Contraste con la base del IPM 2025 ({n25} hogares): proxy {c25['tasa_proxy']:.1%}, "
               f"oficial {c25['tasa_oficial']:.1%}; concordancia {c25['concordancia']:.1%}; sensibilidad "
               f"{c25['sensibilidad']:.1%}; kappa {c25['kappa']:.3f}", ""]

    filas = []
    for k in range(1, len(PRIVACIONES) + 1):
        filas.append(dict(k=k, **concordancia(a[f"POBRE_GEIH_K{k}"], a["POBRE"], w)))
    umbrales = pd.DataFrame(filas)
    umbrales.to_csv(REPORTES / "validacion_ipm_geih_ecv_umbrales.csv", index=False)
    lineas += ["   Por umbral K (privaciones del proxy) frente a POBRE oficial 2024:",
               umbrales[["k", "tasa_proxy", "tasa_oficial", "concordancia", "sensibilidad", "especificidad", "kappa"]]
               .to_string(index=False, float_format=lambda x: f"{x:.3f}"), ""]

    priv = []
    for p, o in OFICIAL.items():
        r = concordancia(a[p], a[f"oficial_{o}"], w)
        priv.append(dict(privacion=p, oficial=o, prevalencia_proxy=r["tasa_proxy"], prevalencia_oficial=r["tasa_oficial"],
                         concordancia=r["concordancia"], kappa=r["kappa"]))
    priv = pd.DataFrame(priv)

    # B
    e, g = ecv_2024(), geih_2024()
    for nombre, df in (("ecv_2024", e), ("geih_2024", g)):
        priv[f"prevalencia_{nombre}"] = [_tasa(df, p) for p in PRIVACIONES]
    priv.to_csv(REPORTES / "validacion_ipm_geih_ecv_privaciones.csv", index=False)
    lineas += ["   Cada privación del proxy frente a la oficial que le corresponde (base del IPM 2024), y su prevalencia",
               "   en la ECV 2024 y la GEIH 2024 (B):",
               priv.to_string(index=False, float_format=lambda x: f"{x:.3f}"), ""]

    lineas += [f"B. Mismo año: proxy en la ECV 2024 ({len(e):,} hogares) frente a la GEIH 2024 ({len(g):,} hogares)".replace(",", "."),
               f"   POBRE_GEIH: ECV {_tasa(e, 'POBRE_GEIH'):.1%}, GEIH {_tasa(g, 'POBRE_GEIH'):.1%}; "
               f"puntaje medio: ECV {_tasa(e, 'ipm_geih_score'):.2f}, GEIH {_tasa(g, 'ipm_geih_score'):.2f}"]
    for z in ("Cabecera", "Resto"):
        lineas.append(f"   {z}: ECV {_tasa(e[e.zona == z], 'POBRE_GEIH'):.1%}, GEIH {_tasa(g[g.zona == z], 'POBRE_GEIH'):.1%}")

    dep = pd.DataFrame({
        "hogares_ecv": e.groupby("depto").size(), "hogares_geih": g.groupby("depto").size(),
        "pobre_ecv": e.groupby("depto").apply(lambda d: _tasa(d, "POBRE_GEIH"), include_groups=False),
        "pobre_geih": g.groupby("depto").apply(lambda d: _tasa(d, "POBRE_GEIH"), include_groups=False),
    }).dropna()
    # Donde la GEIH solo encuesta la cabecera de la capital (todos sus hogares
    # urbanos), la ECV se compara solo en su cabecera: es el mismo marco.
    capital = solo_capital(g)
    dep["marco"] = ["cabecera de la capital" if d in capital else "departamento" for d in dep.index]
    cab = e[(e["zona"] == "Cabecera") & e["capital"] & e["depto"].isin(capital)]
    for d in capital & set(dep.index):
        dep.loc[d, "pobre_ecv"] = _tasa(cab[cab["depto"] == d], "POBRE_GEIH")
        dep.loc[d, "hogares_ecv"] = int((cab["depto"] == d).sum())
    dep["diferencia"] = dep["pobre_geih"] - dep["pobre_ecv"]
    dep.round(4).to_csv(REPORTES / "validacion_ipm_geih_ecv_departamentos.csv", index_label="depto")
    for marco, d in dep.groupby("marco"):
        lineas.append(f"   {marco.capitalize()} ({len(d)}): correlación {d['pobre_ecv'].corr(d['pobre_geih']):.3f}; "
                      f"diferencia media GEIH − ECV {d['diferencia'].mean():+.3f}; "
                      f"diferencia absoluta mediana {d['diferencia'].abs().median():.3f}")
    lineas += ["   Detalle: validacion_ipm_geih_ecv_departamentos.csv", ""]

    texto = "\n".join(lineas)
    (REPORTES / "validacion_ipm_geih_ecv.txt").write_text(texto + "\n", encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
