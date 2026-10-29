# Resultados — índice y hallazgos consolidados

*Actualizado 2026-10-28 (dos veces el mismo día): se obtuvo el diccionario
oficial de variables de GEIH (antes bloqueado, ver §5 de
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`) y se descubrió que
`viv_paredes`/`viv_pisos`/`viv_cuartos` en
`src/armonizacion/armonizar_geih_hogar_2024.py` apuntaban a columnas GEIH
equivocadas desde el inicio del proyecto — no por adivinar, sino por una
hipótesis sin verificar que resultó incorrecta. Con el diccionario se
corrigieron los tres mapeos y se amplió el indicador de pobreza de 4 a 10
privaciones. Horas después se detectó que 2 de esas 10 (vivienda) eran
tautológicas con las covariables `viv_paredes`/`viv_pisos` usadas en el
Causal Forest/DML y se retiraron, dejando el indicador en **8 de 15**
privaciones oficiales del IPM. Se volvió a correr TODO el pipeline de
punta a punta tras cada cambio. Los números de este README reemplazan la
corrida del 2026-10-21/27 — ver "Qué cambió y por qué" más abajo antes de
citar cualquier hallazgo anterior.*

## El pipeline, de un vistazo

| # | Paso | Script | Documento | Estado |
|---|---|---|---|---|
| 1 | Emparejamiento (Hot-Deck) | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | [`RESULTADOS_HOTDECK.md`](RESULTADOS_HOTDECK.md) | ✅ |
| 1b | Filtro del SDP (Bogotá) | `src/validacion/comparar_filtros_sdp.py` | [`COMPARACION_FILTROS_SDP.md`](COMPARACION_FILTROS_SDP.md) | ✅ |
| 2 | Identificación causal (DAG) | `src/4_dag_identificacion.py` | [`IDENTIFICACION_CAUSAL.md`](IDENTIFICACION_CAUSAL.md) | ✅ |
| 3 | Outcome (IPM-GEIH, 8 de 15 privaciones) | `src/3_preprocesamiento.py` | — (resumen abajo, detalle en `RESULTADOS_DML_ATE_ATT_ATU.md`) | ✅ (ampliado, ver limitación) |
| 4 | Estimación: ATE/ATT/ATU | `src/5_estimacion.py` | [`RESULTADOS_DML_ATE_ATT_ATU.md`](RESULTADOS_DML_ATE_ATT_ATU.md) | ✅ |
| 4b | Estimación: CATE | `src/5_estimacion.py` | [`RESULTADOS_CAUSALFOREST_CATE.md`](RESULTADOS_CAUSALFOREST_CATE.md) | ✅ |
| 5 | Cotas de Fréchet-Manski (robustez, sin CIA) | `src/estimacion/cotas_frechet_manski.py` | [`RESULTADOS_FRECHET_MANSKI.md`](RESULTADOS_FRECHET_MANSKI.md) | ✅ |
| 6 | Representatividad del Sisbén frente a GEIH | `src/validacion/verificar_representatividad_sisben.py` | [`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`](RESULTADOS_REPRESENTATIVIDAD_SISBEN.md) | ✅ |

Metodología completa del indicador de pobreza (qué se incluyó, qué no, y
por qué — incluye el historial del bloqueo, ahora resuelto):
[`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`](../insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md).
Diccionarios oficiales (nuevos, de referencia permanente):
[`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`](../insumos/DICCIONARIO_GEIH_2024.xlsx),
[`docs/insumos/DICCIONARIO_SISBEN_2024.xlsx`](../insumos/DICCIONARIO_SISBEN_2024.xlsx).

Lo que **no** está en esta carpeta todavía porque no está implementado:
LASSO/Ridge/SHAP sobre el Sisbén (P1/OE1), discontinuidad de regresión B/C
(en duda — no hay puntaje continuo), diseño de una sola tabla Sisbén
III→IV (falta el corte III), vecino más cercano con distancia de Gower,
reglas contrafactuales FGT1 (P3/OE3), y las 5 dimensiones del IPM que
todavía no se pueden construir sobre GEIH (trabajo infantil, acceso a
fuente de agua mejorada, eliminación de excretas, material de combustible
para cocinar, desempleo de larga duración — ver
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` §2). Ver también Tabla 1
del documento de pipeline (Roncancio y Fonseca, 2026) y la sección
"Pendiente" de `docs/README.md`.

## Qué cambió y por qué (corrección del 2026-10-28)

Hasta el 2026-10-27, `viv_paredes` leía en realidad la columna GEIH de
**material de pisos** (`P4020`), `viv_pisos` leía "¿tiene energía
eléctrica? Sí/No" (`P4030S1`), y `viv_cuartos` leía "cuartos para dormir"
(`P5010`) en vez de cuartos en total. No fue un error de tipeo visible —
los nombres de columna sonaban correctos y los scripts corrían sin
fallar; el error solo se podía detectar comparando contra la ficha
oficial, que el proyecto no tenía. Al conseguir el diccionario
(`docs/insumos/DICCIONARIO_GEIH_2024.xlsx`, 761 filas) se corrigieron los
tres mapeos en `armonizar_geih_hogar_2024.py` y se recalculó todo lo que
dependía de ellos: la celda del Hot-Deck, el indicador de pobreza, y las
dos estimaciones causales.

**Esto cambia números en cascada, pero no cambia la conclusión
cualitativa principal** (el efecto no colapsa a 0 al corregir la celda) —
de hecho la refuerza, porque ahora ese resultado ya no se puede atribuir
a una variable mal mapeada. Lo que sí cambia de forma sustantiva es el
patrón de heterogeneidad del CATE (§4b): antes se concentraba en
jefatura femenina, ahora en zona urbana/rural, con el sentido del
sexo del jefe invertido. Ese hallazgo anterior no se puede seguir
citando.

El mismo diccionario también permitió ampliar el indicador de pobreza:
educación (nivel educativo del jefe, asistencia escolar de menores) y
servicios de vivienda (alcantarillado, acueducto) estaban bloqueados
hasta ahora porque los candidatos obvios (`P3038`/`P3039`, `P5100`-
`P5140`) resultaron ser, al verificarlos contra el diccionario, preguntas
de orientación sexual/identidad de género y de valor monetario de
arriendo/compra — no lo que sus posiciones en el cuestionario sugerían.
El indicador pasó de 4 a 10 de las 15 privaciones oficiales del IPM.

**Horas después, al revisar la validez de la estimación con el outcome
ampliado, se encontró un segundo problema introducido por la misma
ampliación:** 2 de las 10 privaciones nuevas
(`material_pisos_inadecuado`, `material_paredes_inadecuado`) se
calculaban con los MISMOS códigos GEIH (`P4020`/`P4010`) que
`viv_pisos`/`viv_paredes`, usadas como covariable de heterogeneidad (`X`)
en el Causal Forest/DML. Eso creaba una tautología parcial: un hogar con
piso de tierra sumaba un punto al outcome por definición, y la
"importancia" de `viv_pisos`/`viv_paredes` en el Causal Forest podía ser,
en parte, el modelo redescubriendo esa relación mecánica, no
heterogeneidad causal real. Se retiraron esos dos componentes del
outcome (queda en **8 de 15** privaciones) y se volvió a correr la
estimación — ver §4b para el resultado del chequeo: la importancia de
vivienda NO bajó al quitar la tautología, lo que es evidencia de que la
señal es real, no mecánica.

## El hilo conductor: qué explica que el efecto no colapse a 0

**La vivienda (`viv_paredes`, `viv_pisos`) ya tiene el código GEIH
correcto, pero sus categorías siguen sin homologar contra el Sisbén — y
eso se sigue notando en cada paso:**

1. El Hot-Deck solo pudo sumar `viv_cuartos` (un conteo, seguro de usar
   sin homologar categorías) a su celda — `viv_paredes`/`viv_pisos`
   quedaron fuera porque son categóricas y, aunque el código GEIH ya está
   confirmado, el lado Sisbén (`VIV002`/`VIV003`) todavía no tiene su
   lista de categorías verificada en el mismo nivel de detalle (§1).
2. El DAG de identificación (§2) muestra formalmente que, si la celda
   capturara TODO lo que dice el documento de pipeline (depto+edad+vivienda
   completa), el grupo asignado debería quedar independiente del
   resultado. Como la celda implementada es más angosta, queda una rendija.
3. Por esa rendija se cuela exactamente lo que predice el DAG: en la
   estimación real (§4 y §4b), el efecto de ATE/ATT/ATU no colapsa del
   todo a 0, y en el CATE **`viv_pisos` y `viv_paredes` son las dos
   variables más importantes** en `ipm_geih_score` (y la segunda y
   tercera en `POBRE_GEIH`, detrás de `geo_zona_urbana`).

Conclusión práctica: antes de poder leer cualquier número de §4/§4b como
*efecto causal* del Sisbén, hay que terminar de homologar
`viv_paredes`/`viv_pisos` contra las categorías del Sisbén. Mientras
tanto, son asociaciones pequeñas y estadísticamente distintas de cero,
**con un diagnóstico más confiable que antes** (ya no dependen de una
variable mal mapeada), pero todavía no efectos causales confirmados.

## Resumen por paso

### 1. Hot-Deck (emparejamiento)

290.968 hogares GEIH, 3.106.489 donantes Sisbén (nacional + Bogotá
vigente). Celda: `geo_depto + jefe_edad (ciclo de vida) + viv_cuartos`
(ahora cuartos en total, no cuartos para dormir). **100 % en celda
exacta.**

| Grupo | A | B | C | D |
|---|---|---|---|---|
| % de hogares (`viv_cuartos` corregido) | 22,0 | 33,8 | 28,7 | 15,6 |
| % de hogares (`viv_cuartos` con el código equivocado, hasta 2026-10-27) | 31,2 | 35,2 | 23,2 | 10,3 |

El cambio de Grupo D (10,3 % → 15,6 %) es mayor que el de haber sumado
vivienda a la celda en primer lugar — la variable original ni siquiera
medía lo que se pensaba que medía.

### 1b. Filtro del SDP (Bogotá): vigencia vs. año exacto

El archivo de Bogotá es un registro continuo (`fec_fin_encuesta`
2019-2026), no un corte único. Se adoptó **vigencia** (`<=31-dic-2024`,
1.274.578 hogares, 87,4 %) sobre año exacto (75.488, 5,2 %, sesgado hacia
actualizaciones recientes). Con `viv_cuartos` corregido, la brecha entre
ambos filtros en Bogotá para Grupo D es **12,3 puntos** (31,3 % vigencia
vs. 19,0 % año exacto) — si acaso más grande que antes de la corrección;
la celda más fina no elimina la sensibilidad al filtro.

### 2. Identificación causal (DAG)

Sin cambios por la corrección de variables — el chequeo es estructural
(d-separación sobre el grafo), no depende de los valores de los datos.
Dos diseños, con chequeo **formal** de d-separación (`networkx`), no solo
narrado:
- El grafo *literal* de la Figura 2 del documento de pipeline (un solo
  nodo "elegibilidad real") **no** queda d-separado condicionando solo en
  X — hay un camino sin bloquear que el texto no menciona.
- Separando "elegibilidad del donante" de "elegibilidad del receptor" (lo
  que el Hot-Deck realmente hace) el grafo **sí** queda d-separado — la
  afirmación del documento es correcta, pero necesita ese matiz para
  sostenerse formalmente.
- El diseño de una sola tabla (transición Sisbén III→IV) queda bloqueado:
  no se tiene el corte III.

### 3. Outcome: IPM-GEIH ampliado (8 de 15 privaciones)

Sin llave común entre GEIH e IPM, se construyó un índice de privaciones
**sobre GEIH mismo**. Con el diccionario oficial se amplió de 4 a 8 de
las 15 privaciones del IPM, cubriendo ya las 5 dimensiones oficiales
(antes solo 2). `material_pisos_inadecuado`/`material_paredes_inadecuado`
se construyeron y se retiraron el mismo día por tautología con `X` (ver
"Qué cambió y por qué" arriba):

| Privación | % de hogares privados | Verificación |
|---|---|---|
| Analfabetismo (`P6160`) | 4,7 % | Código compartido con IPM, calza con cifras nacionales |
| Bajo logro educativo del jefe (`P3042`) | 29,9 % | Nuevo — nivel educativo < secundaria |
| Inasistencia escolar de menores (`P6170`, 6-16 años, cualquier miembro) | 2,1 % | Nuevo |
| Sin aseguramiento de salud (`P6090`) | 3,4 % | Código compartido con IPM, calza con cobertura ~95-96 % |
| Sin cotización a pensión del jefe (`P6920`) | 75,4 % | Mezcla informalidad con desempleo/inactividad — limitación documentada, sin cambios |
| Hacinamiento (`P6008`/`P5010`) | 3,1 % | **Corregido** — antes usaba `P5020` (tipo de servicio sanitario) por error, daba 23,3 % sin significado real |
| Sin alcantarillado (`P4030S3`) | 18,1 % | Nuevo |
| Sin acueducto (`P4030S5`) | 8,1 % | Nuevo |

Score medio: 1,45/8. **16,3 % de los hogares clasifican como
`POBRE_GEIH`** (score ≥ 3 de 8 — umbral adoptado por sensibilidad:
K≥1=79,8 %, K≥2=40,5 %, K≥3=16,3 %, K≥4=6,3 %, K≥5=1,7 %, K≥6=0,3 %,
K≥7-8≈0 %). Quedan 5 dimensiones del IPM sin construir sobre
GEIH (trabajo infantil, fuente de agua mejorada, eliminación de
excretas, combustible de cocina, desempleo de larga duración) — ver
`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` §2 para el detalle de
qué falta y por qué.

### 4. ATE / ATT / ATU (`LinearDML`)

| Outcome | ATE | ATT | ATU |
|---|---|---|---|
| `ipm_geih_score` (0-8) | +0,0206 [+0,0141; +0,0272] | +0,0214 [+0,0146; +0,0281] | +0,0193 [+0,0130; +0,0256] |
| `POBRE_GEIH` (0/1, K≥3) | +0,0052 [+0,0029; +0,0075] | +0,0055 [+0,0032; +0,0079] | +0,0046 [+0,0025; +0,0067] |

IC95 % excluye 0 en los dos outcomes, controlando por la celda completa
del Hot-Deck (con `viv_cuartos` corregido). Los tres efectos son casi
idénticos entre sí (esperable con pocas covariables de heterogeneidad), y
casi iguales a los de la corrida con 10 privaciones (+0,0218/+0,0050) —
quitar 2 componentes de 10 mueve poco el score agregado. `viv_paredes`
(0,316) y `viv_pisos` (0,301) siguen siendo las covariables más
importantes para `ipm_geih_score`, y ahora SÍ son las variables
correctas. **Hallazgo colateral (sin cambios):** el primer intento de
ATT/ATU con `LinearDRLearner` dio valores absurdos (+56, -191) por
inestabilidad del estimador doblemente robusto con categóricas sin orden
en `X` — corregido reutilizando el `LinearDML` evaluado sobre cada
subpoblación; no fue afectado por la corrección de variables. Detalle en
`RESULTADOS_DML_ATE_ATT_ATU.md`.

### 4b. CATE (`CausalForestDML`)

CATE medio +0,0237 (`ipm_geih_score`) / +0,0041 (`POBRE_GEIH`). **La
heterogeneidad ahora se concentra en zona, no en sexo del jefe:** hogares
rurales muestran CATE 2,8 veces más grande que urbanos en
`ipm_geih_score` (0,0538 vs. 0,0193) y 12 veces en `POBRE_GEIH` (0,0203
vs. 0,0017). El patrón por sexo del jefe sigue presente pero mucho más
chico y **con el sentido invertido** respecto al reporte anterior (antes:
jefa mujer 36 veces más grande que jefe hombre; ahora: jefe hombre
modestamente más grande que jefa mujer). Esto es evidencia de que el
hallazgo anterior sobre jefatura femenina era probablemente un artefacto
de las variables de vivienda mal mapeadas, no un patrón real — ver
"Qué cambió y por qué" en `RESULTADOS_CAUSALFOREST_CATE.md` para la
explicación completa. `viv_paredes`/`viv_pisos` siguen siendo las dos
variables más importantes del forest (0,316/0,301 en `ipm_geih_score`),
ahora con el código correcto, **y se verificó que esa importancia NO es
tautológica**: al retirar del outcome los 2 componentes que compartían
código con `X`, la importancia de vivienda no bajó, subió levemente — ver
"Chequeo de tautología" en `RESULTADOS_CAUSALFOREST_CATE.md`. Detalle
completo en `RESULTADOS_CAUSALFOREST_CATE.md`.

### 5. Cotas de Fréchet-Manski (robustez, sin suponer independencia condicional)

El DML asume que, dentro de la celda del Hot-Deck, el grupo asignado es
como-si-aleatorio. Las cotas de Fréchet-Manski quitan esa suposición y
preguntan: ¿qué dicen los datos SIN ella? Resultado para `POBRE_GEIH`:

| | Estimador | Rango |
|---|---|---|
| Fréchet-Manski (sin CIA) | Cota | **[-0,4083 ; +0,3080]** |
| DML con Hot-Deck (con CIA) | Punto + IC95% | +0,0052 [+0,0029 ; +0,0075] |

El intervalo sin CIA es **~156 veces más ancho** que el IC95% del DML, y
ni una sola de las 365 celdas individuales (celda con `viv_cuartos`
corregido) logra excluir el cero por su cuenta. No es un error — es la
confirmación honesta de que **toda la precisión del resultado del DML
viene de confiar en la suposición del Hot-Deck, no de los datos crudos**.
Detalle en `RESULTADOS_FRECHET_MANSKI.md`, incluida una propuesta
concreta para angostar la cota con supuestos más débiles que la CIA
completa (monotonía en la selección o en la respuesta al tratamiento).

### 6. Representatividad del Sisbén frente a GEIH

El Sisbén solo cubre hogares que se inscribieron — no una muestra
aleatoria de GEIH. La razón de cobertura (hogares registrados en Sisbén ÷
población GEIH) **varía 32,3 veces entre departamentos**: de 0,4 % en
Valle del Cauca a 12,8 % en Putumayo. Departamentos rurales con mayor
pobreza estructural tienden a cobertura relativa más alta; departamentos
urbanos grandes, más baja. No depende de las variables de vivienda
corregidas (se calcula sobre `geo_depto`, sin tocar `viv_*`), así que
este resultado no cambió con la corrección del 2026-10-28. Confirma con
datos reales el supuesto que hasta ahora solo estaba como advertencia
narrativa, y refuerza por qué la cota de Fréchet-Manski (§5) sale tan
ancha. Detalle en `RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`.

## Limitaciones que aplican a TODO lo anterior

- El tratamiento (`Grupo_hotdeck`) es imputado por emparejamiento
  estadístico, no observado en GEIH.
- El outcome cubre 8 de 15 privaciones del IPM oficial (antes 4) — ver
  `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md` §2 para las 7 que
  faltan y por qué (5 por alcance/tiempo, 2 retiradas por tautología con
  `X`, ver §1.1 del mismo documento).
- Sin ajuste por diseño muestral de GEIH ni de Sisbén.
- Selección: el Sisbén solo cubre hogares inscritos.
- Falta DPS/RUI como confusores (el canal "elegibilidad → participación
  DPS → resultado" de la Figura 2 del documento de pipeline no tiene
  datos todavía).
- `viv_paredes`/`viv_pisos`: código GEIH ya confirmado contra el
  diccionario oficial, pero las categorías siguen sin homologar contra el
  Sisbén — por eso siguen fuera de la celda del Hot-Deck.
- `geo_zona`, `jefe_sexo`: sin verificar contra la ficha oficial de cada
  fuente (no afectados por la corrección de vivienda).

## Cómo se generó (reproducible)

```bash
poetry run python -m src.emparejamiento.emparejamiento_hotdeck_geih_sisben
poetry run python -m src.validacion.comparar_filtros_sdp
poetry run python src/4_dag_identificacion.py
poetry run python src/3_preprocesamiento.py
poetry run python src/5_estimacion.py
poetry run python -m src.estimacion.cotas_frechet_manski
poetry run python -m src.validacion.verificar_representatividad_sisben
poetry run pytest tests/
```

Salidas crudas de esta corrida (2026-10-28, con `viv_paredes`/`viv_pisos`/
`viv_cuartos` corregidos y el outcome ampliado a 8 privaciones, tras
retirar 2 por tautología con `X`):
`docs/reports/resultado_hotdeck.txt`,
`docs/reports/resultado_comparacion_filtros_sdp.txt`,
`docs/reports/resultado_preprocesamiento.txt`,
`docs/reports/estimacion_ate_att_atu_cate.txt`,
`docs/reports/cotas_frechet_manski.csv` — reemplazan las salidas
equivalentes de la corrida del 2026-10-21/27.
