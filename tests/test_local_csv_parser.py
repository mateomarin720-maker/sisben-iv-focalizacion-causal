"""El fallback .DTA debe producir el mismo formato de texto que el CSV:
GEIH agosto 2024 se cargó desde .DTA con códigos "1.0" y faltantes "nan",
y todas las comparaciones `== "1"` fallaron ese mes sin dar error."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.ingesta.local_csv_parser import parse_stata_a_parquet


def test_stata_queda_con_formato_csv(tmp_path):
    original = pd.DataFrame({
        "P4030S3": [1.0, 2.0, np.nan],
        "DIRECTORIO": [7893865.0, 7893866.0, 7893867.0],
        "FEX_C18": [480.27, 265.5, 100.0],
        "DPTO": ["11", "05", None],
    })
    dta = tmp_path / "modulo.dta"
    original.to_stata(dta, write_index=False)

    salida = tmp_path / "modulo.parquet"
    assert parse_stata_a_parquet(dta, salida, "geih")["status"] == "success"
    df = pd.read_parquet(salida)

    assert df["P4030S3"].tolist() == ["1", "2", ""]
    assert df["DIRECTORIO"].tolist() == ["7893865", "7893866", "7893867"]
    assert pd.to_numeric(df["FEX_C18"]).tolist() == [480.27, 265.5, 100.0]
    assert df["DPTO"].tolist() == ["11", "05", ""]
