"""Prueba de mutación: reintroduce cada error ya documentado del proyecto
(CLAUDE.md, "Bugs ya encontrados") y comprueba que alguna prueba falle.
Una prueba que pasa con el error de vuelta no protege nada.

Restaura cada archivo después de su mutación (con respaldo `.bak_mut`).
No lo recoge pytest (el nombre no empieza por `test_`).

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe tests/mutaciones.py
Resultado del 2026-11-04: 16 de 16 mutaciones detectadas.
Al agregar una prueba por un error nuevo, agregar aquí su mutación.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
PY = sys.executable  # el mismo intérprete que corre este script (local o en la integración continua)

MUTACIONES = [
    ("Vivienda GEIH: paredes lee P4020 (error anterior)", "src/armonizacion/armonizar_geih_hogar_2024.py",
     '"P4010": "viv_paredes",', '"P4010": "viv_pisos_x",', "tests/test_armonizacion.py"),
    ("Vivienda GEIH: cuartos lee P5010 (error anterior)", "src/armonizacion/armonizar_geih_hogar_2024.py",
     '"P5000": "viv_cuartos",           # cuartos en total (incl. sala-comedor) — mismo concepto que VIV009 del Sisbén\n    "P5010": "viv_cuartos_dormir",',
     '"P5010": "viv_cuartos",\n    "P5000": "viv_cuartos_dormir",', "tests/test_armonizacion.py"),
    ("Vivienda GEIH: pisos lee energía P4030S1 (error anterior)", "src/armonizacion/armonizar_geih_hogar_2024.py",
     '"P4020": "viv_pisos",', '"P4030S1": "viv_pisos",', "tests/test_armonizacion.py"),
    ("DML: la celda entra como número (error anterior)", "src/5_estimacion.py",
     'partes = [("cat", OneHotEncoder(handle_unknown="ignore"), [idx[c] for c in categoricas])]',
     'partes = [("cat", "passthrough", [idx[c] for c in categoricas])]', "tests/test_estimacion_dml.py"),
    ("Fréchet-Manski: cota superior de P(Y=1,T=0) mal escrita", "src/estimacion/cotas_frechet_manski.py",
     "pyt0_hi = np.minimum(p_y, 1 - p_t)", "pyt0_hi = np.minimum(p_y, p_t)", "tests/test_cotas_frechet_manski.py"),
    ("Fréchet-Manski: ATE sin ponderar por peso de celda", "src/estimacion/cotas_frechet_manski.py",
     'w = df["peso_fex"] / df["peso_fex"].sum()', 'w = 1 / len(df)', "tests/test_cotas_frechet_manski.py"),
    ("OE1: una privación del Sisbén entra como predictor", "src/estimacion/seleccion_variables_lasso_shap.py",
     'NUMERICAS = ["hog_num_personas", "viv_cuartos", "jefe_edad"]', 'NUMERICAS = ["hog_num_personas", "viv_cuartos", "jefe_edad", "I1"]',
     "tests/test_armonizacion.py"),
    ("SDP: filtro por año exacto en vez de vigencia", "src/armonizacion/armonizar_sisben_bogota_sdp.py",
     "mask = fec_encuesta <= FECHA_CORTE", "mask = fec_encuesta.dt.year == ANIO_CORTE", "tests/test_armonizacion.py"),
    ("SDP: jefe por otro parentesco", "src/utils/variables_canonicas.py",
     '"sdp": ("tip_parentesco", "1"),', '"sdp": ("tip_parentesco", "2"),', "tests/test_armonizacion.py tests/test_variables_canonicas.py"),
    ("Llaves sin normalizar", "src/utils/variables_canonicas.py",
     'return pd.to_numeric(texto, errors="coerce").astype("Int64").astype("string")', 'return serie.astype("string")',
     "tests/test_variables_canonicas.py tests/test_ingesta_y_validacion.py"),
    ("Ciclo de vida: corte 28 cambiado a 29", "src/utils/variables_canonicas.py",
     "CORTES_CICLO = [-1, 17, 28, 59, 200]", "CORTES_CICLO = [-1, 17, 29, 59, 200]", "tests/test_variables_canonicas.py"),
    ("GEIH: prefijo de No ocupados en plural (marzo viene en singular)", "src/ingesta/geih_loader.py",
     '"No ocupado": "no_ocupados",', '"No ocupados": "no_ocupados",', "tests/test_ingesta_y_validacion.py"),
    ("GEIH: sin respaldo en .DTA", "src/ingesta/geih_loader.py",
     'archivo_dta = _buscar_archivo_modulo(carpeta_mes, prefijo, "DTA")', "archivo_dta = None", "tests/test_ingesta_y_validacion.py"),
    ("GEIH: CSV leído como UTF-8", "src/ingesta/geih_loader.py",
     'GEIH_ENCODING = "latin1"', 'GEIH_ENCODING = "utf-8"', "tests/test_ingesta_y_validacion.py"),
    ("Contraste oficial: cruce sin normalizar mes", "src/validacion/comparar_pobreza_monetaria_oficial.py",
     'r["llave_directorio"], r["llave_secuencia_p"], r["mes"] = _llave(r["DIRECTORIO"]), _llave(r["SECUENCIA_P"]), _llave(r["mes"])',
     'r["llave_directorio"], r["llave_secuencia_p"], r["mes"] = _llave(r["DIRECTORIO"]), _llave(r["SECUENCIA_P"]), r["mes"]',
     "tests/test_ingesta_y_validacion.py"),
    ("Hot-Deck: tramo de edad propio distinto al del Sisbén", "src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py",
     'return edad_a_ciclo(df["jefe_edad"]).map(CODIGO_A_CICLO).fillna("NA")',
     'return pd.cut(pd.to_numeric(df["jefe_edad"], errors="coerce"), bins=[0, 17, 29, 59, 200], labels=list(CODIGO_A_CICLO.values())).astype("object").fillna("NA")',
     "tests/test_variables_canonicas.py"),
]

resultados = []
for nombre, archivo, viejo, nuevo, pruebas in MUTACIONES:
    ruta = ROOT / archivo
    original = ruta.read_text(encoding="utf-8")
    if viejo not in original:
        resultados.append((nombre, "NO APLICADA (texto no encontrado)"))
        continue
    respaldo = ruta.with_suffix(ruta.suffix + ".bak_mut")
    shutil.copy2(ruta, respaldo)
    try:
        ruta.write_text(original.replace(viejo, nuevo, 1), encoding="utf-8")
        r = subprocess.run([PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *pruebas.split()],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        resultados.append((nombre, "detectada" if r.returncode != 0 else "NO DETECTADA"))
    finally:
        shutil.move(respaldo, ruta)
    assert ruta.read_text(encoding="utf-8") == original

for nombre, estado in resultados:
    print(f"{estado:>34} | {nombre}")
n = sum(e == "detectada" for _, e in resultados)
print(f"\n{n} de {len(resultados)} mutaciones detectadas")
sys.exit(0 if n == len(resultados) else 1)
