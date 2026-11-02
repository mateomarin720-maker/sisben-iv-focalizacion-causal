# Resumen de Avances — Efecto Causal del Sisbén IV

Última actualización: 2026-11-02 | Rama: `main` (sincronizada con
`ediciones-hotdeck-sdp`) — `hotdeck-azure-avances` ya está fusionada,
este encabezado quedó desactualizado

**2026-10-28 (dos veces el mismo día):** se obtuvo el diccionario oficial
de variables de GEIH (antes bloqueado, ver §3e) y se descubrió que
`viv_paredes`/`viv_pisos`/`viv_cuartos` apuntaban a columnas GEIH
equivocadas desde el inicio del proyecto. Se corrigieron los mapeos y se
amplió el indicador de pobreza de 4 a 10 de las 15 privaciones oficiales
del IPM. Horas después se detectó que 2 de esas 10 (vivienda) eran
tautológicas con las covariables `viv_paredes`/`viv_pisos` del Causal
Forest/DML y se retiraron, dejando el indicador en **8 de 15**
privaciones. Se repitió todo el pipeline tras cada cambio — ver
`docs/resultados/README.md` para el detalle completo ("Qué cambió y por
qué"). Los números de este documento ya reflejan la corrección final.

## 1. Fuentes de datos — estado

| Fuente | Estado | Detalle |
|---|---|---|
| **IPM (DANE)** | ✅ Completo, año 2024 | 77.568 hogares nacional / 85.387 departamental. Limpieza en `src/2_limpieza.py` (Hogares, Personas, Viviendas). |
| **GEIH (DANE)** | ✅ Completo, 12 meses | 290.968 hogares (12 meses apilados), 8 módulos por mes. Cargador: `src/ingesta/geih_loader.py`. |
| **Sisbén IV nacional (DNP-ANDA)** | ✅ Obtenido | 1.833.166 hogares, 1.098 municipios. Corte mayo 2024. |
| **Sisbén IV Bogotá (SDP)** | ✅ Recibido, lote 03/08/2026; filtrado por vigencia el 2026-10-10 | El archivo es un registro continuo (`fec_fin_encuesta` 2019-2026), no un corte único. Se filtran los hogares vigentes al 31-dic-2024 (`fec_fin_encuesta <= esa fecha`): 1.274.578 de 1.458.468 (87,4 %); se descartan 183.890 posteriores a 2024. (Se descartó filtrar por año exacto de encuesta: solo deja 75.488 hogares y sesga hacia actualizaciones recientes, no representativo del registro vigente). Reemplaza al municipio 11001 del nacional (que traía 1.255). |
| **Banco de datos** | ✅ Azure Blob Storage (`datos-inferencia-causal`) | Publicación y restauración: `src/utils/publicar_banco_datos_azure.py` y `restaurar_banco_datos_azure.py`. Los datos no se versionan en GitHub. |

## 2. Pipeline por etapas (estructura del código)

| Etapa | Carpeta / script | Qué hace |
|---|---|---|
| Ingesta | `src/1_integracion.py`, `src/ingesta/` | CSV/TXT crudos → Parquet con trazabilidad |
| Limpieza | `src/2_limpieza.py` | Tipado, deduplicación y faltantes estructurales (no imputados) |
| **Armonización** | `src/armonizacion/` | Lleva GEIH, Sisbén nacional y Sisbén Bogotá a un esquema canónico por hogar (jefe de hogar) |
| **Emparejamiento estadístico** | `src/emparejamiento/` | Hot-Deck GEIH ← Sisbén por celdas (departamento + ciclo de vida del jefe + tramo de `viv_cuartos`, desde 2026-10-21) |
| **Validación** | `src/validacion/` | Cobertura de celdas, esquema armonizado, faltantes por módulo |
| Banco de datos | `src/utils/azure_storage.py` + publicar/restaurar | Sincronización con Azure |
| **Identificación causal** | `src/4_dag_identificacion.py` ✅ | Los dos DAG del pipeline (principal y de una sola tabla) + chequeo formal de d-separación — ver `docs/resultados/IDENTIFICACION_CAUSAL.md` |
| **Preprocesamiento** | `src/3_preprocesamiento.py` ✅ | Outcome real: IPM-GEIH ampliado (8 de 15 privaciones, 2026-10-28 — empezó en 10, 2 se retiraron por tautología con `X`) — ver `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` |
| **Estimación causal** | `src/5_estimacion.py` ✅ | DML (ATE/ATT/ATU) + Causal Forest (CATE), primera corrida real — ver §3b |
| **Robustez** | `src/estimacion/cotas_frechet_manski.py` ✅ | Cotas de Fréchet-Manski, sin suponer independencia condicional — ver §3c |
| **Representatividad** | `src/validacion/verificar_representatividad_sisben.py` ✅ | Cobertura del Sisbén vs. GEIH por departamento — ver §3d |
| **Selección de variables (OE1)** | `src/estimacion/seleccion_variables_lasso_shap.py` ✅ | LASSO/Ridge/SHAP sobre el Sisbén — qué variables predicen `Grupo` — ver §3f |
| **Pobreza monetaria** | `src/3b_preprocesamiento_monetario.py` ✅ | Nuevo outcome principal (giro del tutor) — ingreso per cápita, FGT0/FGT1 — ver §3g |
| **Pruebas automatizadas** | `tests/` ✅ | `pytest tests/` — valida las transformaciones críticas de `3_preprocesamiento.py` sobre datos reales |
| Refutación | `src/6_refutacion.py` | Placebo, random common cause, sensibilidad a confusores — **no iniciado** |

## 3. Resultado del Hot-Deck (datos reales, 12 meses, Bogotá filtrada por vigencia a 2024, vivienda en la celda, `viv_cuartos` corregido 2026-10-28)

- 290.968 hogares GEIH receptores; **3.106.489** hogares Sisbén donantes (nacional + 1.274.578 de Bogotá vigentes al 31-dic-2024 — ver §1).
- **Celda exacta: 100 %** (departamento + ciclo de vida del jefe + tramo de `viv_cuartos`, ahora cuartos EN TOTAL, antes cuartos para dormir por un código equivocado), también 100 % dentro de Bogotá.
- Grupo asignado, ponderado por factor de expansión: **A 22,0 % · B 33,8 % · C 28,7 % · D 15,6 %** (con el código de `viv_cuartos` equivocado, hasta 2026-10-27: A 31,2/B 35,2/C 23,2/D 10,3; antes de sumar vivienda a la celda: A 28,0/B 34,4/C 24,9/D 12,7). El cambio al corregir `viv_cuartos` es mayor que el de haber sumado vivienda en primer lugar — la variable original ni siquiera medía lo que se pensaba.
- Dentro de Bogotá (depto 11): **A 3,0 % · B 18,9 % · C 46,8 % · D 31,3 %** (filtro de vigencia del SDP; con año exacto de encuesta, descartado, D sale en 19,0 %).
- Crosswalk geográfico confirmado: `DPTO` (GEIH) = primeros 2 dígitos de `cod_mpio` (Sisbén).

**Cómo leerlo.** La celda incluye vivienda (`viv_cuartos`, código corregido), pero sigue sin incluir `viv_paredes`/`viv_pisos` (código GEIH ya confirmado, categorías Sisbén sin homologar todavía — ver §4). El 100 % de celda exacta no demuestra por sí solo un buen emparejamiento: el chequeo real de validez está en §3b, con DML/Causal Forest. La distribución de grupos refleja a los hogares *registrados* en el Sisbén, no a toda la población; no debe reportarse como prevalencia nacional. El emparejamiento solo es válido a nivel poblacional (no identifica el mismo hogar).

## 3b. Resultado de la estimación (corrida 2026-10-28, outcome y vivienda corregidos)

Outcome: `ipm_geih_score` (IPM-GEIH ampliado, 8 de 15 privaciones, 0-8 —
empezó en 10, 2 se retiraron el mismo día por tautología con `X`, ver
abajo) y `POBRE_GEIH` (binario, score≥3, 16,3 % de los hogares).
Tratamiento: `T=1` si `Grupo_hotdeck ∈ {A,B}`. `W` = celda completa del
Hot-Deck (depto+edad+cuartos, `viv_cuartos` corregido); `X` = `geo_zona`,
`jefe_sexo`, `viv_paredes`, `viv_pisos` (código GEIH corregido).

| Modelo | `ipm_geih_score` | `POBRE_GEIH` |
|---|---|---|
| ATE (`LinearDML`) | +0,0206 [IC95% +0,0141;+0,0272] | +0,0052 [IC95% +0,0029;+0,0075] |
| ATT | +0,0214 [+0,0146;+0,0281] | +0,0055 [+0,0032;+0,0079] |
| ATU | +0,0193 [+0,0130;+0,0256] | +0,0046 [+0,0025;+0,0067] |
| CATE medio (`CausalForestDML`) | +0,0237 (rural +0,0538 vs. urbana +0,0193) | +0,0041 (rural +0,0203 vs. urbana +0,0017) |

**Chequeo de tautología (2026-10-28):** 2 de las 10 privaciones
originales (`material_pisos_inadecuado`/`material_paredes_inadecuado`)
usaban los MISMOS códigos GEIH que `viv_pisos`/`viv_paredes` de `X` —
riesgo de que su importancia en el Causal Forest fuera mecánica, no
causal. Se retiraron del outcome y se repitió la corrida: la importancia
de `viv_paredes`/`viv_pisos` NO bajó (subió levemente, de 0,600 a 0,617
sumadas en `ipm_geih_score`) — evidencia de que la señal de vivienda es
real, no un artefacto de la definición del score. Ver
`docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md`, "Chequeo de
tautología".

**Cómo leerlo:** ambos IC95% excluyen 0 — hay una asociación pequeña pero
estadísticamente distinta de cero entre el grupo asignado y las
privaciones, incluso controlando por la celda completa del Hot-Deck con
`viv_cuartos` ya corregido. Según el chequeo formal de d-separación
(`IDENTIFICACION_CAUSAL.md`) esto no debería pasar si `W` capturara todo
lo relevante — la pista más fuerte es que `viv_pisos`/`viv_paredes` son
las variables más importantes del Causal Forest: la vivienda sigue
colándose por fuera de la celda, ahora con un diagnóstico más confiable
porque el código GEIH ya está verificado. **La heterogeneidad del CATE
cambió de foco:** antes se concentraba en jefatura femenina (36 veces
jefe hombre); con el código corregido se concentra en zona rural/urbana,
y el patrón por sexo del jefe se invierte y se achica — evidencia de que
el hallazgo anterior sobre jefatura femenina era probablemente un
artefacto de las variables mal mapeadas (ver
`docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md`, "Qué cambió y por
qué"). **No se puede leer como efecto causal del Sisbén todavía** — ver
`docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` y
`RESULTADOS_CAUSALFOREST_CATE.md` para el detalle y las limitaciones
completas.

## 3b-bis. Diagnóstico: `W` proxy continuo vs. celda exacta del Hot-Deck (2026-11-02)

`W` usaba `jefe_edad`/`viv_cuartos` CONTINUOS, un proxy de la celda
discreta real (`geo_depto + ciclo de vida + tramo de cuartos`). Se probó
con la celda EXACTA (`_hotdeck_celda`, 376 celdas, 99,999 % cobertura
exacta, confirmado sorteo uniforme random sin ponderar nada del
receptor) como `W` categórico, corriendo ambas especificaciones en el
mismo script para comparar directo:

| Outcome | `W` proxy (ATE) | `W` celda exacta (ATE) | Cambio |
|---|---|---|---|
| `ipm_geih_score` | +0,0206 [+0,0141;+0,0272] | **+0,0076 [+0,0008;+0,0143]** | -63 %, ATU deja de excluir 0 |
| `POBRE_GEIH` | +0,0052 [+0,0029;+0,0075] | +0,0049 [+0,0026;+0,0072] | -6 %, sigue excluyendo 0 |

**El proxy SÍ inflaba el efecto para `ipm_geih_score`, pero NO para
`POBRE_GEIH`.** La simulación de identificación predice ≈0 bajo un
sorteo limpio (independiente del efecto verdadero) — `ipm_geih_score` se
acerca mucho a esa predicción con la celda exacta; `POBRE_GEIH` no se
mueve, lo que es la evidencia más fuerte hasta ahora de que ese outcome
binario tiene algo que el mecanismo limpio del Hot-Deck no debería
producir. La heterogeneidad por sexo del jefe cambia de signo otra vez
(tercer patrón distinto en tres corridas de esta semana) — no citar
ninguna versión como robusta. Detalle completo:
`docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`.

## 3c. Cotas de Fréchet-Manski — robustez sin suponer independencia condicional (refrescado 2026-10-28)

El DML del punto anterior asume que, dentro de la celda del Hot-Deck, el
grupo asignado es como-si-aleatorio. Para ver qué tan fuerte es esa
suposición, se calcularon cotas de Fréchet-Manski usando `P(Y|X)` directo
de GEIH y `P(T|X)` directo de Sisbén, sin pasar por el Hot-Deck:

| | Estimador | Rango (`POBRE_GEIH`) |
|---|---|---|
| Fréchet-Manski (sin CIA) | Cota | **[-0,4083; +0,3080]** |
| DML con Hot-Deck (con CIA) | Punto + IC95% | +0,0052 [+0,0029; +0,0075] |

La cota sin CIA es **~156 veces más ancha**, y ninguna de las 365 celdas
individuales (celda con `viv_cuartos` corregido) logra excluir el cero
por su cuenta. **Confirma que toda la precisión del resultado del DML
depende de la suposición del Hot-Deck, no de los datos crudos** — no es
un hallazgo negativo, es la honestidad matemática esperable sin supuestos
adicionales. Detalle y propuesta para angostar la cota (supuestos de
monotonía) en `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`.

## 3d. Representatividad del Sisbén frente a GEIH (2026-10-27)

La razón de cobertura (hogares registrados en el Sisbén ÷ población GEIH)
**varía 32,3 veces entre departamentos**: de 0,4 % en Valle del Cauca a
12,8 % en Putumayo; departamentos rurales con mayor pobreza estructural
muestran cobertura relativa más alta que departamentos urbanos grandes.
Confirma con datos reales (no solo como supuesto narrativo) que el
registro del Sisbén no es una muestra uniforme de GEIH — refuerza por qué
la cota de Fréchet-Manski (§3c) sale tan ancha. Detalle en
`docs/resultados/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`.

## 3e. Sensibilidad del indicador de pobreza y ampliación (resuelto 2026-10-28)

Se agregaron variantes de umbral al outcome (`POBRE_GEIH_K1`...`K8`,
`src/3_preprocesamiento.py`) y validaciones obligatorias automatizadas
(`_validar()` + `tests/test_preprocesamiento.py`). La tasa de pobreza
cambia de 79,8 % (K≥1) a ~0 % (K≥7-8) según el corte — K=3 (16,3 %) se
mantiene por ser el más cercano en orden de magnitud a la tasa oficial de
IPM (13,0 %).

**El bloqueo por falta del diccionario oficial de GEIH, reportado el
2026-10-27, se resolvió el 2026-10-28.** El diccionario
(`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`, 761 filas) confirmó que los
candidatos esperados para educación y servicios de vivienda SÍ existen,
solo que con códigos distintos a los que se habían probado antes
(`P3038`/`P3039` eran orientación sexual/identidad de género, no
educación; `P5100`-`P5140` eran valor monetario de arriendo/compra, no
acceso a servicio). Con los códigos correctos (`P3042` nivel educativo,
`P6170` asistencia escolar, `P4030S3`/`P4030S5` alcantarillado/acueducto)
el indicador pasó de 4 a 10 de las 15 privaciones oficiales del IPM,
cubriendo ya las 5 dimensiones (antes solo 2). El mismo diccionario
también reveló que `viv_paredes`/`viv_pisos`/`viv_cuartos` en el
armonizador de GEIH apuntaban a columnas equivocadas desde el inicio del
proyecto — corregido, ver `docs/resultados/README.md`.

**Horas después se detectó y corrigió un segundo problema introducido por
la propia ampliación:** 2 de las 10 privaciones nuevas
(`material_pisos_inadecuado`/`material_paredes_inadecuado`) usaban los
MISMOS códigos GEIH (`P4020`/`P4010`) que `viv_pisos`/`viv_paredes`,
usadas como covariable de heterogeneidad en `5_estimacion.py` — una
tautología parcial entre outcome y covariable. Se retiraron, dejando el
indicador en **8 de 15 privaciones** — ver §3b para el chequeo empírico
de que la importancia de vivienda en el Causal Forest no dependía de esa
tautología. Quedan 7 privaciones del IPM sin construir sobre GEIH (5 por
alcance/tiempo, 2 por tautología) — detalle en
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` §2.

### Errores encontrados y corregidos durante la ejecución
1. **Doble jefe en Sisbén:** 65 hogares con dos jefes marcados → se conserva el primero.
2. **Edad del Sisbén en códigos, no en años:** `PER002` ∈ {3,4,5,6}. Con tramos de años, 89 % caía a `solo_depto`. Corregido comparando por ciclo de vida.
3. **GEIH agosto sin jefe:** llaves con formato distinto entre módulos (24.402 hogares). Corregido normalizando identificadores.
4. **Tipos mixtos al fusionar Bogotá:** corregido convirtiendo a texto.

## 3f. Selección de variables: LASSO, Ridge y SHAP sobre el Sisbén (OE1, 2026-11-02)

Responde al OE1 por separado del pipeline causal — no estima ningún
efecto, solo qué variables del hogar predicen mejor el `Grupo` (A-D) del
Sisbén. Sobre 150.000 hogares (submuestra estratificada de 3,09
millones), usando `hog_num_personas`, `viv_cuartos`, `jefe_edad`
(numéricas) y `viv_paredes`, `viv_pisos`, `viv_alcantarillado`, `viv_
acueducto`, `jefe_sexo`, `geo_zona` (one-hot, dirección sin verificar) +
`geo_depto` como control:

| Método | Exactitud | F1 macro | Variable más importante (sin contar `geo_depto`) |
|---|---|---|---|
| LASSO (L1) | 0,530 | 0,526 | `viv_pisos` |
| Ridge (L2) | 0,530 | 0,526 | `viv_pisos` |
| SHAP (RandomForest) | 0,527 | 0,499 | `viv_pisos` |

Spearman LASSO-Ridge=0,988 (casi idéntico); LASSO-SHAP=0,794,
Ridge-SHAP=0,806 — SHAP sube notablemente `hog_num_personas` y `viv_
alcantarillado` frente a los modelos lineales, evidencia de interacciones
no lineales. Ninguna variable eliminada por LASSO. Línea base (predecir
siempre `B`, la clase mayoritaria): ~30 % — las tres exactitudes (~53 %)
están muy por encima, pero lejos de perfectas: las variables disponibles
(el esquema canónico del Hot-Deck) explican una parte real pero parcial
de la clasificación; el resto depende de las privaciones internas del
Sisbén (`I1`-`I15`/`H_5`), que no se usan como predictores por
circularidad. Detalle completo en
`docs/resultados/RESULTADOS_SELECCION_VARIABLES_OE1.md`.

## 3g. Pobreza monetaria: ingreso per cápita, FGT0/FGT1 (2026-11-02)

El nuevo outcome principal según el giro del tutor (2026-10-27).
Ingreso laboral desde `INGLABO` (ya imputado por el DANE) + ingreso no
laboral (`otros_ingresos`/`no_ocupados`), agregado al hogar y dividido
entre `hog_num_personas`; clasificado contra las líneas oficiales del
DANE 2024 por zona (urbano $510.161/rural $291.998 mensual per cápita,
boletín técnico Pobreza Monetaria, `docs/insumos/DANE_boletin_PM_2024.pdf`).

**Primer intento descartado:** reconstruir el ingreso laboral sumando
`P6500` + componentes adicionales dio FGT0=53,6%/FGT1=39,0% — muy por
encima de lo oficial, no por el margen esperable de una aproximación sin
imputación. Causa: `P6500` solo tiene 47,7% de no respuesta entre
ocupados, y el script trataba esos vacíos como ingreso $0. Corregido
usando `INGLABO` (la variable ya imputada por el DANE, solo 4,3% de
faltantes).

| Indicador | Construido | Oficial DANE 2024 |
|---|---|---|
| FGT0 pobreza | 38,7% | 31,8% |
| FGT1 brecha pobreza | 19,5% | 12,6% |
| FGT0 pobreza extrema | 18,8% | 11,7% |
| FGT1 brecha pobreza extrema | 10,7% | 4,5% |

Sobreestimación sistemática de 6-7 puntos porcentuales en las cuatro
métricas — consistente con no replicar la imputación de subreporte no
laboral ni el ajuste por vivienda propia de la metodología oficial (ver
"Qué SÍ y qué NO replica" en el detalle), no con un error de
construcción. El patrón urbano/rural (rural más pobre) se mantiene en la
dirección correcta. Detalle completo en
`docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`.

## 3h. Pobreza monetaria conectada a DML/Causal Forest (2026-11-02)

Se agregaron `log_ingreso_percapita` (`log1p(ingreso_percapita)`, para
evitar que la cola derecha extrema del ingreso domine el ajuste por
error cuadrático) y `POBRE_MONETARIO` a `5_estimacion.py` como tercer y
cuarto outcome, y se repitió sobre ellos el diagnóstico `W` proxy vs.
celda exacta (§3b-bis). Resultado — un patrón nuevo, distinto al de
`ipm_geih_score`/`POBRE_GEIH`:

| Outcome | ATE (W=PROXY) | ATE (W=CELDA EXACTA) |
|---|---|---|
| `log_ingreso_percapita` | -0,0317 [-0,0539;-0,0096] | -0,0468 [-0,0689;-0,0246] |
| `POBRE_MONETARIO` | +0,0136 [+0,0101;+0,0171] | +0,0152 [+0,0118;+0,0187] |

A diferencia de `ipm_geih_score` (el efecto se encogió 63 % con la celda
exacta), los dos outcomes monetarios se **amplían** (+48 % y +12 % en
magnitud) sin cambiar de signo. Bajo el sorteo aleatorio limpio del
Hot-Deck, lo esperable es que el efecto se acerque a 0 con la celda
exacta sin importar el efecto verdadero — que se aleje en cambio es la
evidencia de robustez más fuerte producida hasta ahora en el proyecto, no
solo para pobreza monetaria sino en general. No confirma causalidad por
sí solo (sigue pendiente la homologación de `viv_paredes`/`viv_pisos` con
Sisbén, ver punto siguiente, y confusores no observados DPS/RUI). Detalle
completo: `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md` y
`docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`.

## 4. Pendientes técnicos
- [x] **Verificar los códigos de `PER002`** (hipótesis: 3=12–17, 4=18–28, 5=29–59, 6=60+) — corroborada indirectamente el 2026-10-10 cruzando contra escolaridad/estado civil/pensión en la base completa de Personas; falta la ficha oficial de ANDA. Ver `docs/insumos/DICCIONARIO_HOTDECK.md` §5.
- [x] **Sumar variables de vivienda a la celda** — hecho parcialmente el 2026-10-21: se sumó `viv_cuartos` (conteo, seguro de usar sin homologar categorías; código corregido el 2026-10-28). `viv_paredes`/`viv_pisos` siguen fuera — ver el punto siguiente.
- [x] **Conseguir la ficha técnica/diccionario oficial de variables de GEIH** — resuelto 2026-10-28 (`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`, 761 filas, portal de microdatos DANE). Permitió corregir `viv_paredes`/`viv_pisos`/`viv_cuartos` y ampliar el indicador de 4 a 8 privaciones (pasó por 10 el mismo día, 2 se retiraron por tautología con `X`) — ver §3e y `docs/resultados/README.md`.
- [ ] **Corregir el bug de agosto (códigos `"1.0"` del `.DTA`) y regenerar todos los resultados** — ver CHANGELOG 2026-11-02 (7). Prioritario: invalida los números actuales de `POBRE_GEIH`, `POBRE_MONETARIO` y todo lo que depende de ellos.
- [x] **Homologar `viv_paredes`/`viv_pisos` con Sisbén** — hecho 2026-11-02 con la ficha del Sisbén IV, ver `docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`. `geo_zona` también verificada (1 = urbano en las dos fuentes). Pendiente decidir si se suman a la celda del Hot-Deck.
- [ ] (Histórico, superado por el punto anterior) Verificar categorías de `geo_zona`, `jefe_sexo` entre fuentes (sin cambios, código GEIH de `viv_paredes`/`viv_pisos` ya confirmado el 2026-10-28) — **sigue siendo el bloqueador principal para sumar vivienda categórica a la celda**: el ATE/ATT/ATU/CATE real (§3b) no colapsa a 0 y la pista más fuerte apunta a `viv_pisos`/`viv_paredes`, ahora con el código correcto pero categorías Sisbén sin homologar. Revisado otra vez el 2026-11-02 contra la auditoría de `docs/metodologia/comparacion_proxies/` (PR #9): esa matriz homologa `P4010`/`P4020` contra la regla oficial del IPM (DANE, `met-IPM.pdf`), no contra las categorías de `VIV002`/`VIV003` del Sisbén, y deja la columna Sisbén pendiente por la misma razón — falta el documento metodológico del DNP. Siguen sin ser equivalentes verificadas.
- [x] Ubicar en GEIH los equivalentes de `HOG027`, `VIV005`, `VIV008` — resuelto 2026-10-28 (`P6008`, `P4030S3`, `P4030S5`).
- [ ] Documentar como limitación la diferencia de corte (Bogotá 2026 vs. resto 2024).
- [ ] 6 hogares de Bogotá con doble jefe y 227 con `Clasificacion` distinta entre miembros: confirmar con SDP cuál es la oficial.
- [ ] Robustez: NND por distancia de Gower.
- [x] **Fase 2 (oficial): DML y Causal Forest** — primera corrida real completa el 2026-10-21, repetida el 2026-10-28 con outcome y vivienda corregidos (ver §3b). Pendiente: homologar categorías de vivienda contra Sisbén antes de interpretar el resultado como efecto causal.
- [ ] Refinar `sin_cotizacion_pension_jefe` (mezcla informalidad con desempleo/inactividad, ver `src/3_preprocesamiento.py` — sin cambios por la corrección del 2026-10-28).
- [ ] Construir las 5 dimensiones del IPM que todavía faltan sobre GEIH (trabajo infantil, fuente de agua mejorada, eliminación de excretas, combustible de cocina, desempleo de larga duración) — ver `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` §2.
- [ ] Fase 3: RD en la frontera B/C (en duda, no hay puntaje continuo en la microdata).
- [x] **OE1 (LASSO/Ridge/SHAP sobre el Sisbén)** — hecho 2026-11-02, ver §3f y `docs/resultados/RESULTADOS_SELECCION_VARIABLES_OE1.md`.
- [x] **Construir pobreza monetaria (ingreso per cápita, FGT0/FGT1)** — hecho 2026-11-02, ver §3g y `docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`.
- [x] **Conectar pobreza monetaria a `5_estimacion.py`** — hecho 2026-11-02, con el diagnóstico `W` proxy vs. celda exacta repetido sobre `log_ingreso_percapita`/`POBRE_MONETARIO` (ver §3h). Los dos efectos se amplían con la celda exacta en vez de encogerse.
- [x] **Cotas de Fréchet-Manski sobre `POBRE_MONETARIO`** — hecho 2026-11-02: [-0,5886; +0,7035], más ancha que la de `POBRE_GEIH` (las dos marginales están más cerca de 0,5). Ninguna celda excluye el 0 de forma informativa; el +0,0152 del DML depende por completo de la CIA. Ver `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`.
- [ ] Angostar las cotas con supuestos MTS/MTR (Manski, 2003) — la cota sin supuestos no es informativa para ningún outcome.
- [x] **Especificación de `W`: probar la celda EXACTA del Hot-Deck, no solo el proxy continuo** — hecho 2026-11-02, ver §3b-bis y `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`. Resultado dividido: explica el 63 % del efecto de `ipm_geih_score` pero casi nada del de `POBRE_GEIH`.
- [x] **Rotulado ATT/ATU** ("error de inclusión"/"error de exclusión" era una etiqueta engañosa, no un error de cómputo) — corregido 2026-11-02 en `src/5_estimacion.py` y `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md`.
- [x] **Advertencias:** se probó quitar `warnings.filterwarnings("ignore")` de `src/5_estimacion.py` (con `-W always`, incluido un `CausalForestDML` completo a 80.000 filas) — no genera ningún warning en este entorno; el filtro no estaba ocultando nada real. Eliminado 2026-11-02.
- [ ] **Rehacer `corrige-controles-celda` y `simulacion-identificacion`** sobre `main` actual — ambas se bifurcaron antes del diccionario GEIH (2026-10-28) y fusionarlas tal cual revertiría esta semana de correcciones. `simulacion-identificacion` trae código valioso (`simulacion_identificacion.py`) que no existe en `main` y que sustenta el diagnóstico de §3b-bis — rescatar ese archivo primero.

## 5. Higiene del repositorio

Resuelto. `NACIONAL/`/`DEPARTAMENTAL/` (microdatos IPM) ya no están
versionadas (`git ls-files` las confirma ausentes); `.git` pesa 23 MB. El
historial previo a la limpieza las sigue conteniendo (no reescrito, por
decisión explícita de no tocar commits ya publicados).

## 6. Gestiones institucionales
| Solicitud | Estado |
|---|---|
| Sisbén IV (DNP-ANDA) | Resuelto — acceso vía ANDA |
| Sisbén Bogotá (SDP) | Resuelto — base recibida (corte 03/08/2026) |

## 7. Documentación de referencia
- `docs/insumos/DICCIONARIO_DATOS.md` — diccionario general IPM/GEIH
- `docs/insumos/DICCIONARIO_HOTDECK.md` — variables y llaves del emparejamiento
- `docs/insumos/CODIGOS_LOCALIDAD_BOGOTA.md` — localidades de Bogotá
- `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` — construcción del indicador de pobreza, sensibilidad y qué 5 dimensiones del IPM siguen sin poder construirse
- `docs/insumos/DICCIONARIO_GEIH_2024.xlsx`, `docs/insumos/DICCIONARIO_SISBEN_2024.xlsx` — diccionarios oficiales de variables (obtenidos 2026-10-28)
- `docs/resultados/README.md` — **índice y resumen ejecutivo de todos los resultados** (empezar por aquí)
- `docs/resultados/IDENTIFICACION_CAUSAL.md` — los dos DAG y el chequeo formal de d-separación
- `docs/resultados/COMPARACION_FILTROS_SDP.md` — vigencia vs. año exacto del SDP, lado a lado
- `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` — primera corrida real de ATE/ATT/ATU
- `docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md` — primera corrida real de CATE
- `docs/resultados/RESULTADOS_FRECHET_MANSKI.md` — cotas sin suponer independencia condicional (robustez)
- `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md` — proxy continuo vs. celda exacta del Hot-Deck como `W`
- `docs/resultados/RESULTADOS_SELECCION_VARIABLES_OE1.md` — LASSO/Ridge/SHAP sobre el Sisbén (OE1)
- `docs/resultados/RESULTADOS_POBREZA_MONETARIA.md` — ingreso per cápita, FGT0/FGT1 (nuevo outcome principal)
- `docs/resultados/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md` — cobertura del Sisbén por departamento
- `src/estimacion/README.md` — prueba exploratoria que precedió a la corrida real
- `docs/seguimiento/CHANGELOG_PENDIENTES.md` — historial de cambios y pendientes
