# Resumen de Avances — Efecto Causal del Sisbén IV

Última actualización: 2026-11-02 | Ramas `main` y `ediciones-hotdeck-sdp`
sincronizadas.

**Versión consolidada.** Este documento se reescribió el 2026-11-02 para
que conviva una sola versión metodológica. Las cifras de corridas
anteriores, con sus errores, quedan en el historial de
`CHANGELOG_PENDIENTES.md` y en git, no aquí.

## 0. Estado en una frase

Las fuentes están integradas y los outcomes construidos (IPM-GEIH y
pobreza monetaria reconstruida, a 1,4 puntos de la cifra oficial). Con
datos reales, el DML sobre el grupo Sisbén imputado da ≈0, que es lo
esperado: el Hot-Deck sortea al azar dentro de la celda y el contraste
es un placebo. Las cotas de Fréchet-Manski no fijan ni el signo del
efecto. **La pieza central pendiente es la evaluación semisintética**
(guía del tutor del 2026-10-27).

## 1. Fuentes de datos

| Fuente | Estado | Detalle |
|---|---|---|
| **IPM (DANE)** | ✅ 2024 | 77.568 hogares nacional / 85.387 departamental. |
| **GEIH (DANE)** | ✅ 12 meses | 290.968 hogares, 8 módulos por mes. Agosto se carga desde `.DTA` con el mismo formato de texto que el CSV. |
| **Sisbén IV nacional (DNP-ANDA)** | ✅ | 1.833.166 hogares, 1.098 municipios, corte mayo 2024. |
| **Sisbén IV Bogotá (SDP)** | ✅ | Registro continuo; se usan los vigentes al 31-dic-2024 (1.274.578 de 1.458.468). Reemplaza al municipio 11001 del nacional. |
| **Pobreza monetaria oficial (DANE, catálogo 874)** | ⏳ | `BDatos-Pobreza_Monetaria_Desigualdad-2024.zip`: descargar a mano a `data/0_raw/pobreza_monetaria/` (D1). |
| **Banco de datos** | ✅ Azure Blob Storage | `src/utils/publicar_banco_datos_azure.py` / `restaurar_banco_datos_azure.py`. |

## 2. Pipeline

| Etapa | Script | Estado |
|---|---|---|
| Ingesta, limpieza, armonización | `src/1_integracion.py`, `src/ingesta/`, `src/2_limpieza.py`, `src/armonizacion/` | ✅ |
| Hot-Deck GEIH ← Sisbén | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | ✅ celda depto + ciclo de vida + cuartos |
| Comparación de celdas con pisos y paredes | `src/validacion/comparar_celdas_hotdeck_vivienda.py` | ✅ 2026-11-02 |
| DAG e identificación | `src/4_dag_identificacion.py` | ✅ |
| Outcome IPM-GEIH (8 de 15 privaciones) | `src/3_preprocesamiento.py` | ✅ |
| Outcome pobreza monetaria | `src/indicadores/pobreza_monetaria_geih.py` → `src/3b_preprocesamiento_monetario.py` | ✅ 2026-11-02 |
| DML y Causal Forest (diagnóstico placebo) | `src/5_estimacion.py` | ✅ corregido 2026-11-02 |
| Cotas de Fréchet-Manski | `src/estimacion/cotas_frechet_manski.py` | ✅ |
| Representatividad del Sisbén | `src/validacion/verificar_representatividad_sisben.py` | ✅ |
| Selección de variables (OE1) | `src/estimacion/seleccion_variables_lasso_shap.py` | ✅ con métricas por grupo |
| Simulación de identificación | `src/validacion/simulacion_identificacion.py` | ✅ (datos sintéticos) |
| **Evaluación semisintética** | — | ⏳ **pendiente, prioridad** |
| Pruebas | `tests/` (`pytest`) | ✅ |

## 3. Resultados vigentes

### 3a. Hot-Deck

290.968 hogares GEIH, 3.106.489 donantes. 100 % en celda exacta (376
celdas). Grupo asignado (ponderado): **A 22,0 · B 33,8 · C 28,7 · D
15,6 %**. Refleja a los hogares registrados en el Sisbén, no a la
población; válido solo a nivel poblacional.

**¿Sumar pisos y paredes a la celda?** (homologados con la ficha del
Sisbén IV, `docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`). Con
pisos, la correlación entre P(T | celda) y la pobreza monetaria del
receptor sube de 0,20 a 0,29 y la cobertura apenas cambia (99,98 %);
paredes no agrega nada encima. Pisos cambia mucho la distribución de
grupos (A 22 % → 14 %). **Decisión pendiente** de si la celda con pisos
pasa a ser la oficial. Detalle: `docs/resultados/RESULTADOS_HOTDECK.md`.

### 3b. Outcomes

- **IPM-GEIH:** 8 de las 15 privaciones oficiales; 17,1 % de hogares con
  `POBRE_GEIH` (score ≥ 3). `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`.
- **Pobreza monetaria reconstruida** (unidad de gasto, líneas por
  dominio, hot-deck de no respuesta laboral, arriendo imputado; D1-D7
  cerradas): **33,2 %** de personas pobres frente a 31,8 % oficial;
  rural 41,3 % frente a 42,5 %; extrema 12,5 % frente a 11,7 %. Es una
  reconstrucción experimental, no la medición oficial (el DANE usa
  registros administrativos no públicos). La decisión que más pesa es el
  arriendo imputado (5,6 puntos). `docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`.

### 3c. DML y Causal Forest: diagnóstico placebo

Con las categóricas como indicadoras en los modelos auxiliares
(corregido 2026-11-02), siete de los ocho ATE incluyen el cero y todos
son despreciables:

| Outcome | ATE, W = celda exacta [IC 95 %] |
|---|---|
| `ipm_geih_score` | +0,0011 [−0,0060; +0,0081] |
| `POBRE_GEIH` | +0,0004 [−0,0020; +0,0028] |
| `log_ingreso_percapita` | −0,0132 [−0,0264; −0,0001] |
| `POBRE_MONETARIO` | +0,0025 [−0,0009; +0,0058] |

Es lo que predice la simulación: dentro de la celda el grupo imputado no
depende del hogar receptor, así que el contraste da ≈0 sea cual sea el
efecto verdadero. **No es una estimación del efecto del Sisbén.** Los
efectos que se reportaban antes (+0,0235 en IPM y +0,0158 en pobreza
monetaria, con IC sin el 0, y la afirmación de que los monetarios eran
"la evidencia de robustez más fuerte") venían de pasar la celda como
número a la propensión. `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`.

### 3d. Cotas de Fréchet-Manski: el resultado de identificación con datos reales

| Outcome | Cota del ATE sin suponer independencia condicional |
|---|---|
| `POBRE_GEIH` | [−0,411; +0,323] |
| `POBRE_MONETARIO` | [−0,538; +0,503] |

Ninguna de las 365 celdas excluye el cero. Sin el supuesto del
Hot-Deck, los datos no determinan ni el signo del efecto. No es un
fracaso del modelo: es lo que dos fuentes sin llave común permiten
decir. `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`.

### 3e. Representatividad

La cobertura del Sisbén frente a GEIH varía 32 veces entre departamentos
(0,4 % Valle a 12,8 % Putumayo). `docs/resultados/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`.

### 3f. Selección de variables (OE1)

LASSO, Ridge y SHAP sobre 150.000 hogares del Sisbén: `viv_pisos` es la
variable más importante en los tres métodos. Exactitud ≈53 % (línea base
30 %), bien calibrada, pero desigual por grupo: sensibilidad 0,64 en A y
0,39 (LASSO) o 0,22 (RandomForest) en D, que se confunde con C. Con
partición por municipio el F1 macro cae de 0,50 a 0,44. Predice el grupo
asignado, no la pobreza real. `docs/resultados/RESULTADOS_SELECCION_VARIABLES_OE1.md`.

## 4. Pendientes, en orden

1. **Evaluación semisintética** (componente central de la tesis). Sobre
   hogares reales de GEIH: tratamiento verdadero y resultados potenciales
   simulados con efecto heterogéneo conocido; escenarios de asignación
   aleatoria, confusión observada, confusión no observada, solapamiento
   débil y tratamiento reconstruido por Hot-Deck; estimadores diferencia
   de medias, regresión ajustada, DML y Causal Forest; métricas sesgo,
   RMSE, cobertura, error del CATE y degradación por la integración. El
   tratamiento verdadero nunca entra a los modelos que reciben el
   reconstruido. Diseñado para que una entidad pueda cambiar GEIH por sus
   propios registros. Base: `src/validacion/simulacion_identificacion.py`
   (ya en `main`, PR #11).
2. **Decidir la celda del Hot-Deck** (actual o + pisos).
3. **D1:** descargar la base oficial de pobreza monetaria (catálogo 874)
   y, si trae llaves de GEIH, usarla como referencia hogar por hogar.
4. **D7, versión A:** líneas por área de los anexos del boletín.
5. **Fase 5 de pobreza monetaria:** comparación con IPM-GEIH y el grupo
   imputado, por celda (D6).
6. Angostar las cotas con supuestos de monotonía (MTS/MTR).
7. Construir las 5 privaciones del IPM que faltan en GEIH; refinar
   `sin_cotizacion_pension_jefe`.
8. Confirmar en ANDA los cortes de `PER002`; 6 hogares de Bogotá con doble
   jefe y 227 con `Clasificacion` distinta entre miembros (SDP).
9. Actualizar el anteproyecto con el enfoque vigente.

## 5. Errores encontrados y corregidos (los que cambiaron resultados)

| Fecha | Error | Efecto |
|---|---|---|
| 2026-10-10 | Edad del Sisbén en códigos de ciclo de vida, no años | Cobertura del Hot-Deck 10,8 % → 100 % |
| 2026-10-28 | `viv_paredes`/`viv_pisos`/`viv_cuartos` leían columnas GEIH equivocadas | Cambió la celda, el IPM-GEIH y la estimación |
| 2026-10-28 | Dos privaciones tautológicas con `X` | Retiradas; IPM-GEIH en 8 de 15 |
| 2026-11-02 | Agosto cargado desde `.DTA` con códigos `"1.0"` | Corregido en el parser; pipeline regenerado |
| 2026-11-02 | `INGLABO` descrito como imputado por el DANE | Es un consolidado sin imputar |
| 2026-11-02 | Celda y departamento como números en la propensión del DML | Los ATE pasaron a ≈0 |
| 2026-11-02 | `P6430` = 7 leído como sin remuneración (es jornalero) | Corregido en la reconstrucción monetaria |

## 6. Gestiones institucionales

| Solicitud | Estado |
|---|---|
| Sisbén IV (DNP-ANDA) | Resuelto |
| Sisbén Bogotá (SDP) | Resuelto (corte 03/08/2026) |
| Puntaje continuo del Sisbén (para RD) | No solicitado; es lo único que recuperaría el efecto en la simulación |

## 7. Documentación de referencia

- `docs/resultados/README.md` — índice de resultados (empezar aquí)
- `docs/metodologia/pobreza_monetaria/` — auditoría (`00`) y decisiones y diccionario del ingreso (`01`)
- `docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md` — paredes y pisos entre fuentes
- `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` — IPM-GEIH
- `docs/insumos/DICCIONARIO_GEIH_2024.xlsx`, `DICCIONARIO_SISBEN_2024.xlsx`, `FICHA_SISBEN_IV_FCS_2017.pdf`
- `docs/seguimiento/CHANGELOG_PENDIENTES.md` — historial
