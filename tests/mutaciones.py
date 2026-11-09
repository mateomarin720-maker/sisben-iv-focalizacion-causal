"""Prueba de mutación: reintroduce cada error ya documentado del proyecto
(CLAUDE.md, "Bugs ya encontrados") y comprueba que alguna prueba falle.
Una prueba que pasa con el error de vuelta no protege nada.

Restaura cada archivo después de su mutación (con respaldo `.bak_mut`).
No lo recoge pytest (el nombre no empieza por `test_`).

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe tests/mutaciones.py
Resultado del 2026-11-04: 42 de 42 mutaciones detectadas.
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
    # P3/OE3 (reglas de focalización)
    ("OE3: error de inclusión dividido por los pobres", "src/validacion/reglas_focalizacion.py",
     "error_inclusion=float(np.sum(w * t * (1 - pobre)) / max(np.sum(w * t), 1e-12)),",
     "error_inclusion=float(np.sum(w * t * (1 - pobre)) / max(np.sum(w * pobre), 1e-12)),",
     "tests/test_reglas_focalizacion.py"),
    ("OE3: la regla trata a los de menor puntaje", "src/validacion/reglas_focalizacion.py",
     "orden = np.lexsort((rng.random(len(puntaje)), -np.asarray(puntaje, float)))",
     "orden = np.lexsort((rng.random(len(puntaje)), np.asarray(puntaje, float)))",
     "tests/test_reglas_focalizacion.py"),
    ("OE3: la reducción esperada ignora la incertidumbre del proxy", "src/validacion/reglas_focalizacion.py",
     "y = media[:, None] + residuos[None, :]", "y = media[:, None] + 0 * residuos[None, :]",
     "tests/test_reglas_focalizacion.py"),
    ("OE3: el monto fijo se aplica como proporcional", "src/validacion/reglas_focalizacion.py",
     "    return ingreso_relativo(y0, lp) + efecto\n", "    return ingreso_relativo(y0 + efecto, lp)\n",
     "tests/test_reglas_focalizacion.py"),
    # Cotas con supuestos de monotonía
    ("Cotas: la dependencia positiva no recorta P11", "src/estimacion/cotas_frechet_manski.py",
     "lo11_dep = np.maximum(lo11, p_y * p_t)", "lo11_dep = lo11", "tests/test_cotas_frechet_manski.py"),
    ("Cotas: MTS con la cota del contraste en el extremo equivocado", "src/estimacion/cotas_frechet_manski.py",
     "hi = np.minimum(hi, contraste(hi11))", "hi = np.minimum(hi, contraste(lo11_s))", "tests/test_cotas_frechet_manski.py"),
    # Sensibilidad: RD difusa
    ("RD difusa: la participación se instrumenta consigo misma (MCO)", "src/simulacion/estimadores.py",
     "Z = np.column_stack([np.ones_like(dd), z, dd, z * dd])", "Z = np.column_stack([np.ones_like(dd), tt, dd, z * dd])",
     "tests/test_sensibilidad_semisintetica.py"),
    ("RD difusa: error estándar sin los residuos", "src/simulacion/estimadores.py",
     "Zwe = Z * (w * e)[:, None]", "Zwe = Z * (w * 0.1)[:, None]", "tests/test_sensibilidad_semisintetica.py"),
    # Módulo de simulación
    ("Simulación: código de celda int8 desborda los grados de libertad", "src/simulacion/estimadores.py",
     "gl = len(y) - D.shape[1] - (int(celda.max()) + 1)", "gl = len(y) - D.shape[1] - (celda.max() + 1)",
     "tests/test_simulacion_semisintetica.py"),
    ("Simulación: sin donantes en la celda sortea en todo el registro (versión anterior)", "src/simulacion/vinculo.py",
     "for k in range(r.shape[1]):", "for k in range(1):", "tests/test_simulacion_semisintetica.py"),
    # Variables candidatas
    ("Candidatas: discapacidad cuenta \"alguna dificultad\"", "src/estimacion/variables_candidatas_pobreza.py",
     'dificultad = p[DIFICULTADES].isin(["1", "2"]).any(axis=1)', 'dificultad = p[DIFICULTADES].isin(["1", "2", "3"]).any(axis=1)',
     "tests/test_variables_candidatas.py"),
    ("Candidatas: el ingreso entra como predictor", "src/estimacion/variables_candidatas_pobreza.py",
     'DERIVADAS = ["n_menores",', 'DERIVADAS = ["ingreso_percapita", "n_menores",', "tests/test_variables_candidatas.py"),
    ("Candidatas: categóricas como número", "src/estimacion/variables_candidatas_pobreza.py",
     'CATEGORICAS = set(FICHA_CAT) | {"estrato"}', 'CATEGORICAS = set()', "tests/test_variables_candidatas.py"),
    ("Candidatas: el IPM se predice con sus componentes", "src/estimacion/variables_candidatas_pobreza.py",
     'fuera = MECANICAS_IPM if outcome == "POBRE_GEIH" else set()', 'fuera = set()', "tests/test_variables_candidatas.py"),
    ("Candidatas: exclusión mide los elegidos no pobres", "src/estimacion/variables_candidatas_pobreza.py",
     'return float(1 - aciertos / pobres), float(1 - aciertos / (w * elegidos).sum())',
     'return float(1 - aciertos / (w * elegidos).sum()), float(1 - aciertos / pobres)', "tests/test_variables_candidatas.py"),
    ("Candidatas: Holm sin corregir", "src/estimacion/variables_candidatas_pobreza.py",
     'ajustados = (orden * (len(orden) - np.arange(len(orden)))).cummax().clip(upper=1)', 'ajustados = orden',
     "tests/test_variables_candidatas.py"),
    ("Candidatas: se recomienda sin exigir estabilidad", "src/estimacion/variables_candidatas_pobreza.py",
     'if significativo and mejora_clara and estable:', 'if significativo and mejora_clara:', "tests/test_variables_candidatas.py"),
    ("Candidatas: una vivienda en varios pliegues", "src/estimacion/variables_candidatas_pobreza.py",
     'return np.random.default_rng(seed).permutation(len(unicos))[inv] % n',
     'return np.random.default_rng(seed).permutation(len(grupos)) % n', "tests/test_variables_candidatas.py"),
    # Incidencia de las ayudas declaradas
    ("Incidencia: el código de no sabe se cuenta como dinero", "src/estimacion/incidencia_transferencias.py",
     'valido = p["P750S2"].eq(SI) & ~monto.isin(NO_SABE) & p["P6050"].ne(EMPLEADO_DOMESTICO)',
     'valido = p["P750S2"].eq(SI) & p["P6050"].ne(EMPLEADO_DOMESTICO)', "tests/test_incidencia_transferencias.py"),
    ("Incidencia: la ayuda anual se suma como mensual", "src/estimacion/incidencia_transferencias.py",
     'p["ayuda_mes"] = monto.where(valido, 0.0).fillna(0.0) / MESES_ANIO', 'p["ayuda_mes"] = monto.where(valido, 0.0).fillna(0.0)',
     "tests/test_incidencia_transferencias.py"),
    ("Incidencia: personas contadas como hogares", "src/estimacion/incidencia_transferencias.py",
     'personas_que_declaran=directos[programa],\n            hogares_receptores=h[r].sum(), personas_en_receptores=n[r].sum(),',
     'personas_que_declaran=directos[programa],\n            hogares_receptores=h[r].sum(), personas_en_receptores=h[r].sum(),',
     "tests/test_incidencia_transferencias.py"),
    ("Candidatas: los pobres que salen no se restan del neto", "src/estimacion/variables_candidatas_pobreza.py",
     'hogares_pobres_neto=h[entran].sum() - h[salen].sum(),', 'hogares_pobres_neto=h[entran].sum(),',
     "tests/test_variables_candidatas.py"),
    ("Simulación: el contrato acepta un alias de columna", "src/simulacion/contrato.py",
     'faltan = [c for c in obligatorias if c not in tabla.columns]',
     'faltan = [c for c in obligatorias if c not in tabla.columns and c.replace("jefe_sexo", "sexo_jefe") not in tabla.columns]',
     "tests/test_simulacion_contrato.py"),
    ("Simulación: el contrato no revisa dominios", "src/simulacion/contrato.py",
     "ok = col.validar(filas[nombre]).fillna(False).astype(bool)", "ok = filas[nombre].notna()",
     "tests/test_simulacion_contrato.py"),
    # Variabilidad de la imputación del Hot-Deck
    ("Variabilidad: concordancia con el estimador sesgado (incluye el par consigo mismo)",
     "src/validacion/variabilidad_hotdeck.py",
     "return (conteos * (conteos - 1)).sum(axis=1) / (r * (r - 1))", "return (conteos * conteos).sum(axis=1) / (r * r)",
     "tests/test_variabilidad_hotdeck.py"),
    ("Variabilidad: reglas de Rubin sin el factor (1 + 1/m)", "src/validacion/variabilidad_hotdeck.py",
     "total = w + (1 + 1 / m) * b", "total = w + b", "tests/test_variabilidad_hotdeck.py"),
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
