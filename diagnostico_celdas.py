"""Por que solo ~11% cae en celda_exacta? (solo lectura)
Uso: poetry run python diagnostico_celdas.py"""
import pandas as pd
from src.hotdeck.hotdeck_estandarizado import construir_celda
r = pd.read_parquet("data/2_models/geih_estandarizado_2024.parquet", columns=["geo_depto", "jefe_edad"])
d = pd.read_parquet("data/2_models/sisben_estandarizado_2024.parquet", columns=["geo_depto", "jefe_edad", "Clasificacion"])
for n, x in (("GEIH", r), ("SISBEN", d)):
    print(f"\n== {n} ==")
    print(x.dtypes.to_dict())
    print("jefe_edad muestra:", x["jefe_edad"].dropna().astype(str).head(8).tolist())
    e = pd.to_numeric(x["jefe_edad"], errors="coerce")
    print("edad num: nulos=", e.isna().sum(), "min/mediana/max=", e.min(), e.median(), e.max())
    print("geo_depto muestra:", sorted(x["geo_depto"].astype(str).unique())[:10])
    c = construir_celda(x, edad_en_codigos=(n=="SISBEN"))
    print("tramos:", c.str.split("|").str[1].value_counts(dropna=False).to_dict())
cr, cd = construir_celda(r), construir_celda(d[d.Clasificacion.notna()], edad_en_codigos=True)
print("\nceldas GEIH:", cr.nunique(), "| celdas Sisben:", cd.nunique(), "| GEIH con celda en Sisben:", round(cr.isin(set(cd)).mean() * 100, 1), "%")
print("deptos GEIH sin donante:", sorted(set(r.geo_depto.astype(str).str.zfill(2)) - set(d.geo_depto.astype(str).str.zfill(2))))
