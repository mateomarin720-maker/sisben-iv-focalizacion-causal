# Pruebas

134 pruebas en 12 archivos (2026-11-04). Casi todas usan datos
sintéticos y corren sin el banco de datos; las que necesitan datos reales
se saltan solas si no están (`skipif`).

```bash
poetry run pytest tests/                                            # suite completa (≈15 s)
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe tests/mutaciones.py  # prueba de mutación (≈3 min)
```

## Integración continua

`.github/workflows/pruebas.yml` corre la suite y la prueba de mutación
en GitHub Actions en cada push a `main` o `ediciones-hotdeck-sdp` y en
cada PR (Python 3.11, dependencias de `requirements-pruebas.txt`,
fijadas a las versiones con las que pasan). Allí no está el banco de
datos: **92 pruebas corren y 7 se saltan** (las que leen enero real de
GEIH). Se comprobó antes de subirlo con un entorno limpio y un clon del
repositorio sin datos: 92 pasan, 7 se saltan y se detectan todas las
mutaciones.

Si una prueba falla en GitHub, el PR queda marcado en rojo. Para agregar
una dependencia nueva a las pruebas, sumarla a `requirements-pruebas.txt`
con su versión, además de `pyproject.toml`.

## Qué cubre cada archivo

Las de prioridad alta protegen contra errores que ya ocurrieron en el
proyecto y que no daban error: producían números plausibles pero
equivocados (CLAUDE.md, "Bugs ya encontrados").

| Archivo | Módulo | Qué fija | Error que evita |
|---|---|---|---|
| `test_armonizacion.py` | `armonizacion/*`, `seleccion_variables_lasso_shap.py` | Cada código de GEIH y del Sisbén contra la etiqueta del diccionario oficial; que cada variable de vivienda salga de su columna; jefe por `P6050`/`PER003`/`tip_parentesco`; Bogotá filtrada por vigencia, no por año exacto; OE1 sin `I1`-`I15` ni `H_5` | Mapeo de vivienda equivocado (hasta 2026-10-28); sesgo hacia actualizaciones recientes del SDP; circularidad |
| `test_estimacion_dml.py` | `5_estimacion.py` | Categóricas como indicadoras; propensión = P(T \| celda) (correlación > 0,99); el error anterior no la reproduce (< 0,6); LinearDML recupera 0 y 0,5 con confusión entre celdas | Celda como número en la propensión (ATE falsos de +0,02, hasta 2026-11-02) |
| `test_cotas_frechet_manski.py` | `estimacion/cotas_frechet_manski.py` | Con supuestos de monotonía: la cota contiene el ATE de toda población que cumple el supuesto (25 configuraciones) y cada supuesto la angosta o la deja igual. Casos exactos (P(Y) = 0 o 1 → [0; 0]); la cota contiene el efecto de toda distribución conjunta compatible y alcanza sus extremos (2.000 conjuntas × 5 semillas); ATE ponderado por peso de celda; cada probabilidad de su fuente | El resultado de identificación central no tenía pruebas |
| `test_variables_canonicas.py` | `utils/variables_canonicas.py` | Llaves con formatos distintos ("01", "1.0", " 1 "); jefe por fuente; cortes del ciclo de vida de `PER002`; GEIH y Sisbén en los mismos tramos del Hot-Deck | `mes` "01" frente a "1" (2026-11-02); celdas que no empatan entre fuentes |
| `test_ingesta_y_validacion.py` | `ingesta/geih_loader.py`, `validacion/comparar_pobreza_monetaria_oficial.py`, `4_dag_identificacion.py` | Los 8 módulos de los 12 meses con las variantes reales ("No ocupado" en marzo, agosto desde `.DTA`, carpetas vacías); Latin-1; cruce uno a uno con la base oficial; d-separación del DAG | Meses incompletos sin aviso; cruce vacío con la base oficial |
| `test_hotdeck_celda.py` | `emparejamiento/…` | Celda con nivel de pisos; falla si falta `viv_pisos` | Celda que cae al respaldo sin avisar |
| `test_local_csv_parser.py` | `ingesta/local_csv_parser.py` | Códigos de `.DTA` como "1", no "1.0" | Agosto con `POBRE_GEIH` 6,9 % (hasta 2026-11-02) |
| `test_preprocesamiento.py` | `3_preprocesamiento.py` | IPM-GEIH con enero real: una fila por hogar, privaciones binarias sin faltantes, puntaje = suma, umbrales monótonos (se salta sin los datos) | |
| `test_preprocesamiento_monetario.py` | `indicadores/pobreza_monetaria_geih.py`, `3b_…` | Unidad de gasto, jornalero (`P6430` = 7), imputación, líneas, cruce con la oficial | `P6430` = 7 leído como sin remuneración |
| `test_homologacion_ipm.py` | `indicadores/homologacion_ipm.py` | Matriz GEIH ↔ Sisbén de las 15 privaciones: cada código existe en su diccionario oficial, pesos oficiales | Citar un código que no existe |
| `test_reglas_focalizacion.py` | `validacion/reglas_focalizacion.py` | Brecha y efecto (proporcional y monto fijo), reducción esperada sobre los residuos, elección de los k mejores, errores de inclusión/exclusión ponderados por personas, la regla ideal nunca pierde, el proxy de medios sin el ingreso | |
| `test_simulacion_semisintetica.py` | `validacion/simulacion_semisintetica.py` | Generador, Hot-Deck simulado, RD, MCSE | |

## Cómo se comprobó que las pruebas sirven

1. **Mutación** (`tests/mutaciones.py`): se reintroduce cada error ya
   documentado (22 en total; los 16 de la primera versión: los tres del mapeo de vivienda, la celda
   como número en el DML, dos de las cotas, una privación del Sisbén como
   predictor, el filtro por año exacto, el jefe equivocado, llaves sin
   normalizar, un corte de edad distinto, el prefijo de "No ocupados", sin
   respaldo `.DTA`, UTF-8 en lugar de Latin-1, el cruce con `mes` sin
   normalizar y tramos de edad distintos en el Hot-Deck; y 4 de las reglas
   de focalización: error de inclusión mal dividido, tratar a los de menor
   puntaje, ignorar la incertidumbre del proxy y aplicar el monto fijo
   como proporcional; y 2 de las cotas con monotonía: la dependencia
   positiva sin efecto y el MTS en el extremo equivocado). **Las 22 hacen
   fallar alguna prueba.** Una prueba que pasa con el error de vuelta no
   protege nada.
2. **Estabilidad:** la suite pasó 5 de 5 veces seguidas, cada archivo por
   separado y en orden inverso. Las pruebas con azar usan semillas fijas
   y varias semillas (5 en las de DML y cotas); los umbrales tienen margen
   medido en 10 semillas (error del ATE ≤ 0,018 frente a un umbral de
   0,06).
3. **Sin cambios en los datos:** tras unificar las definiciones
   compartidas, `3_preprocesamiento.py`, la pobreza monetaria, el
   contraste oficial y `3b` regeneran salidas idénticas
   (`assert_frame_equal`), la celda del Hot-Deck coincide en los 290.899
   hogares en celda exacta, las llaves y los jefes en las 2.489.049 filas
   de los 12 meses, y las cotas de Fréchet-Manski byte a byte. Bogotá,
   reconstruida desde el crudo del SDP (Azure,
   `sisben/bogota/Sisben_03082026_bog.zip`), coincide columna por columna
   con la versión en uso en los dos modos: 1.274.578 hogares por vigencia
   y 75.488 por año exacto.

## Al agregar código

- Para llaves de hogar, jefe de hogar o ciclo de vida, usar
  `src/utils/variables_canonicas.py`; no copiar la regla.
- Antes de mapear una columna nueva de GEIH o del Sisbén, agregar su
  etiqueta esperada a `ETIQUETA_GEIH`/`ETIQUETA_SISBEN` en
  `test_armonizacion.py`.
- Si se encuentra un error nuevo, agregar la prueba que lo habría
  detectado y su mutación en `tests/mutaciones.py`.

## Pendiente

- Cobertura medida (`pytest-cov` no está instalado) y pruebas de
  regresión de las cifras documentadas.
