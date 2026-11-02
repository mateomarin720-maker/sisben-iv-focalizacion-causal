"""Inventario de las variables de ingreso de GEIH 2024 (Fase 1 de pobreza
monetaria, ver `docs/metodologia/pobreza_monetaria/00_auditoria_y_metodologia.md`).

Para cada variable candidata a entrar en el ingreso corriente de la unidad
de gasto: etiqueta oficial (diccionario DANE), componente, periodicidad,
si ya viene dentro de `INGLABO` y tratamiento propuesto. La clasificación
es de la auditoría (verificada con datos, ver el documento); la cobertura
se calcula aquí sobre los 12 meses apilados.

No construye ningún agregado.

Uso:
    poetry run python -m src.indicadores.inventario_ingresos_geih
Salida: docs/reports/inventario_ingresos_geih.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
DICCIONARIO = Path("docs/insumos/DICCIONARIO_GEIH_2024.xlsx")
OUT = Path("docs/reports/inventario_ingresos_geih.csv")
MESES = [f"{m:02d}" for m in range(1, 13)]

# (variable, módulo parquet, componente, periodicidad, en INGLABO, tratamiento propuesto)
INVENTARIO = [
    ("INGLABO", "ocupados", "laboral: consolidado DANE", "mensual", "—",
     "base del ingreso laboral; NO imputado: vacío = no informa o sin remuneración"),
    ("P6500", "ocupados", "laboral: salario asalariados", "mensual", "sí", "no sumar (ya en INGLABO)"),
    ("P6750", "ocupados", "laboral: ganancia neta independientes", "mensual", "sí", "no sumar (ya en INGLABO)"),
    ("P6760", "ocupados", "laboral: meses a que corresponde P6750", "—", "sí", "solo verificación"),
    ("P550", "ocupados", "laboral: ganancia neta 12 meses (solo rural)", "anual", "por verificar",
     "decisión pendiente: alternativa a P6750 en rural (/12)"),
    ("P7070", "ocupados", "laboral: segundo trabajo", "mensual", "sí", "no sumar (ya en INGLABO)"),
    ("P6590S1", "ocupados", "especie: alimentos", "mensual", "sí", "no sumar (ya en INGLABO)"),
    ("P6600S1", "ocupados", "especie: vivienda", "mensual", "sí", "no sumar (ya en INGLABO)"),
    ("P6610S1", "ocupados", "especie: transporte empresa", "mensual", "sí", "no sumar (ya en INGLABO)"),
    ("P6620S1", "ocupados", "especie: otros", "mensual", "sí", "no sumar (ya en INGLABO)"),
    ("P6510S1", "ocupados", "laboral: horas extra", "mensual", "no si P6510S2=2", "sumar solo si P6510S2=2"),
    ("P6545S1", "ocupados", "laboral: primas mensuales", "mensual", "no si P6545S2=2", "sumar solo si P6545S2=2"),
    ("P6580S1", "ocupados", "laboral: bonificaciones mensuales", "mensual", "no si P6580S2=2", "sumar solo si P6580S2=2"),
    ("P6585S1A1", "ocupados", "laboral: auxilio alimentación", "mensual", "no si S1A2=2", "sumar solo si P6585S1A2=2"),
    ("P6585S2A1", "ocupados", "laboral: auxilio transporte", "mensual", "no si S2A2=2", "sumar solo si P6585S2A2=2"),
    ("P6585S3A1", "ocupados", "laboral: subsidio familiar", "mensual", "no si S3A2=2", "sumar solo si P6585S3A2=2"),
    ("P6585S4A1", "ocupados", "laboral: subsidio educativo", "mensual", "no si S4A2=2", "sumar solo si P6585S4A2=2"),
    ("P6630S1A1", "ocupados", "laboral: prima de servicios", "anual", "no", "sumar /12"),
    ("P6630S2A1", "ocupados", "laboral: prima de navidad", "anual", "no", "sumar /12"),
    ("P6630S3A1", "ocupados", "laboral: prima de vacaciones", "anual", "no", "sumar /12"),
    ("P6630S4A1", "ocupados", "laboral: viáticos permanentes / bonif. anuales", "anual", "no", "sumar /12"),
    ("P6630S6A1", "ocupados", "laboral: pagos por accidente de trabajo", "anual", "no",
     "decisión pendiente: ¿corriente u ocasional?"),
    ("P3051", "ocupados", "laboral: honorarios brutos independientes", "mensual", "no",
     "NO sumar: bruto; P6750 (neto) ya lo cubre"),
    ("P3052", "ocupados", "laboral: ingresos/comisiones brutos independientes", "mensual", "no",
     "NO sumar: bruto, >= P6750 en 99 %"),
    ("P3054S1", "ocupados", "especie independientes: alimentos", "mensual", "por verificar", "decisión pendiente"),
    ("P3055S1", "ocupados", "especie independientes: vivienda", "mensual", "por verificar", "decisión pendiente"),
    ("P7422S1", "no_ocupados", "laboral: ingreso por trabajo de no ocupados", "mensual", "no", "sumar"),
    ("P7500S1A1", "otros_ingresos", "no laboral: arriendos", "mensual", "no", "sumar"),
    ("P7500S2A1", "otros_ingresos", "no laboral: pensiones y jubilaciones", "mensual", "no", "sumar"),
    ("P7500S3A1", "otros_ingresos", "no laboral: pensión alimenticia", "mensual", "no", "sumar"),
    ("P7510S1A1", "otros_ingresos", "transferencias: otros hogares en el país", "anual", "no", "sumar /12"),
    ("P7510S2A1", "otros_ingresos", "transferencias: remesas del exterior", "anual", "no", "sumar /12"),
    ("P7510S3A1", "otros_ingresos", "transferencias: ayudas institucionales (total)", "anual", "no",
     "sumar /12; es el total de P750S1-S3"),
    ("P750S1A1", "otros_ingresos", "transferencias: ayudas privadas (detalle)", "anual", "no", "NO sumar: contenido en P7510S3A1"),
    ("P750S2A1", "otros_ingresos", "transferencias: ayudas del gobierno (detalle)", "anual", "no", "NO sumar: contenido en P7510S3A1"),
    ("P750S3A1", "otros_ingresos", "transferencias: ayudas del exterior (detalle)", "anual", "no", "NO sumar: contenido en P7510S3A1"),
    ("P1661S1A1", "otros_ingresos", "transferencias: Más Familias en Acción", "anual", "no", "NO sumar: contenido en P750S2A1"),
    ("P1661S2A1", "otros_ingresos", "transferencias: Jóvenes en Acción", "anual", "no", "NO sumar: contenido en P750S2A1"),
    ("P1661S3A1", "otros_ingresos", "transferencias: Colombia Mayor", "anual", "no", "NO sumar: contenido en P750S2A1"),
    ("P1661S4A2", "otros_ingresos", "transferencias: otro programa", "anual", "no", "NO sumar: contenido en P750S2A1"),
    ("P7510S5A1", "otros_ingresos", "capital: intereses, dividendos, utilidades", "anual", "no", "sumar /12"),
    ("P7510S6A1", "otros_ingresos", "cesantías e intereses a las cesantías", "anual", "no",
     "decisión pendiente: ¿corriente u ocasional?"),
    ("P7510S7A1", "otros_ingresos", "ocasional: loterías, indemnizaciones, venta de bienes", "anual", "no",
     "EXCLUIR: ingreso ocasional (boletín DANE)"),
    ("P5130", "hogar_vivienda", "vivienda: arriendo estimado por el hogar", "mensual", "no",
     "ajuste por vivienda propia (regla exacta pendiente)"),
    ("P5100", "hogar_vivienda", "vivienda: cuota de amortización", "mensual", "no", "decisión pendiente (propia pagando)"),
    ("P5090", "hogar_vivienda", "vivienda: tenencia", "—", "no", "define a quién se ajusta"),
]


def _cobertura(modulo: str, variables: list[str]) -> pd.DataFrame:
    partes = []
    for mes in MESES:
        path = GEIH_DIR / mes / f"{modulo}.parquet"
        if not path.exists():
            continue
        cols = pq.ParquetFile(path).schema.names
        presentes = [v for v in variables if v in cols]
        partes.append(pd.read_parquet(path, columns=presentes).apply(pd.to_numeric, errors="coerce"))
    df = pd.concat(partes, ignore_index=True)
    filas = []
    for v in variables:
        if v not in df:
            filas.append({"variable": v, "existe_en_datos": False})
            continue
        s = df[v]
        filas.append({
            "variable": v,
            "existe_en_datos": True,
            "filas_modulo_12m": len(s),
            "n_valor_positivo": int((s > 0).sum()),
            "pct_valor_positivo": round((s > 0).mean() * 100, 2),
            "n_codigo_98": int((s == 98).sum()),
            "n_codigo_99": int((s == 99).sum()),
            "mediana_positivos": float(s[s > 0].median()) if (s > 0).any() else None,
        })
    return pd.DataFrame(filas)


def main() -> None:
    inv = pd.DataFrame(INVENTARIO, columns=["variable", "modulo", "componente", "periodicidad", "en_INGLABO", "tratamiento_propuesto"])
    dic = pd.read_excel(DICCIONARIO).drop_duplicates("Nombre").set_index("Nombre")
    inv["en_diccionario"] = inv["variable"].isin(dic.index)
    inv["etiqueta_oficial"] = inv["variable"].map(dic["Etiqueta"])

    cobertura = pd.concat(
        [_cobertura(mod, g["variable"].tolist()) for mod, g in inv.groupby("modulo")],
        ignore_index=True,
    )
    inv = inv.merge(cobertura, on="variable", how="left")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    inv.to_csv(OUT, index=False)
    logger.info("Inventario: %s variables (%s fuera del diccionario, %s sin datos) -> %s",
                len(inv), int((~inv["en_diccionario"]).sum()), int((~inv["existe_en_datos"]).sum()), OUT)


if __name__ == "__main__":
    main()
