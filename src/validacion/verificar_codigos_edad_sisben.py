"""Verifica el significado de PER002 (Edad) en Sisben IV cruzandolo con variables conocidas.
Trae el archivo de personas desde Azure Blob Storage (no usa copia local)."""
import sys, tempfile, csv
from pathlib import Path
import pandas as pd
from src.utils.azure_storage import _cliente_contenedor

cont = _cliente_contenedor()
cands = [b for b in cont.list_blobs(name_starts_with="0_raw/sisben")
         if "pers" in b.name.lower() and b.name.lower().endswith((".csv", ".txt"))
         and "bog" not in b.name.lower()]
if not cands:
    print("No encontre archivo de personas. Blobs bajo 0_raw/sisben:")
    for b in cont.list_blobs(name_starts_with="0_raw/sisben"):
        print(" ", b.name, round(b.size / 1e6, 1), "MB")
    sys.exit(1)

blob = max(cands, key=lambda b: b.size)
print("Usando:", blob.name, round(blob.size / 1e6, 1), "MB")

with tempfile.TemporaryDirectory() as tmp:
    ruta = Path(tmp) / "personas.csv"
    with open(ruta, "wb") as f:
        cont.download_blob(blob.name, max_concurrency=2, timeout=900).readinto(f)
    with open(ruta, encoding="utf-8-sig", errors="replace") as f:
        sep = csv.Sniffer().sniff(f.readline(), delimiters=";,|\t").delimiter
    df = pd.read_csv(ruta, sep=sep, dtype=str, nrows=1_500_000, encoding="utf-8-sig",
                     encoding_errors="replace")

df.columns = [c.strip().upper() for c in df.columns]
print("Filas leidas:", len(df))
print("\nPER002 valores:\n", df["PER002"].value_counts(dropna=False).sort_index().head(20))

for v, desc in [("PER016", "estudia"), ("PER017", "nivel educativo"),
                ("PER018", "cotiza pension"), ("PER004", "estado civil"),
                ("PER012", "ha tenido hijos")]:
    if v in df.columns:
        print(f"\n== PER002 x {v} ({desc}), % por fila ==")
        print((pd.crosstab(df["PER002"], df[v], normalize="index") * 100).round(1))
