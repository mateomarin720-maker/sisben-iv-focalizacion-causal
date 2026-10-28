# Resultados — índice y hallazgos consolidados

*Corrida completa reproducida el 2026-10-27 (todos los scripts, de punta a
punta, dieron los mismos números que la corrida original del 2026-10-21 —
ver "Cómo se generó" al final). Cada documento de esta carpeta es el
resultado interpretado de **un** paso del pipeline; este README es el
resumen de los cinco juntos.*

## El pipeline, de un vistazo

| # | Paso | Script | Documento | Estado |
|---|---|---|---|---|
| 1 | Emparejamiento (Hot-Deck) | `src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py` | [`RESULTADOS_HOTDECK.md`](RESULTADOS_HOTDECK.md) | ✅ |
| 1b | Filtro del SDP (Bogotá) | `src/validacion/comparar_filtros_sdp.py` | [`COMPARACION_FILTROS_SDP.md`](COMPARACION_FILTROS_SDP.md) | ✅ |
| 2 | Identificación causal (DAG) | `src/4_dag_identificacion.py` | [`IDENTIFICACION_CAUSAL.md`](IDENTIFICACION_CAUSAL.md) | ✅ |
| 3 | Outcome (IPM-GEIH reducido) | `src/3_preprocesamiento.py` | — (resumen abajo, detalle en `RESULTADOS_DML_ATE_ATT_ATU.md`) | ✅ (reducido, ver limitación) |
| 4 | Estimación: ATE/ATT/ATU | `src/5_estimacion.py` | [`RESULTADOS_DML_ATE_ATT_ATU.md`](RESULTADOS_DML_ATE_ATT_ATU.md) | ✅ |
| 4b | Estimación: CATE | `src/5_estimacion.py` | [`RESULTADOS_CAUSALFOREST_CATE.md`](RESULTADOS_CAUSALFOREST_CATE.md) | ✅ |
| 5 | Cotas de Fréchet-Manski (robustez, sin CIA) | `src/estimacion/cotas_frechet_manski.py` | [`RESULTADOS_FRECHET_MANSKI.md`](RESULTADOS_FRECHET_MANSKI.md) | ✅ |

Lo que **no** está en esta carpeta todavía porque no está implementado:
LASSO/Ridge/SHAP sobre el Sisbén (P1/OE1), discontinuidad de regresión B/C
(en duda — no hay puntaje continuo), diseño de una sola tabla Sisbén
III→IV (falta el corte III), vecino más cercano con distancia de Gower,
reglas contrafactuales FGT1 (P3/OE3). Ver Tabla 1 del documento de
pipeline (Roncancio y Fonseca, 2026) y la sección "Pendiente" de
`docs/README.md`.

## El hilo conductor: un solo hallazgo explica casi todo lo demás

**La vivienda (`viv_paredes`, `viv_pisos`) está sin verificar entre GEIH y
Sisbén, y eso se nota en cada paso siguiente:**

1. El Hot-Deck solo pudo sumar `viv_cuartos` (un conteo, seguro de usar) a
   su celda — `viv_paredes`/`viv_pisos` quedaron fuera porque son
   categóricas y sus códigos no calzan entre fuentes (§1).
2. El DAG de identificación (§2) muestra formalmente que, si la celda
   capturara TODO lo que dice el documento de pipeline (depto+edad+vivienda
   completa), el grupo asignado debería quedar independiente del
   resultado. Como la celda implementada es más angosta, queda una rendija.
3. Por esa rendija se cuela exactamente lo que predice el DAG: en la
   estimación real (§4 y §4b), el efecto de ATE/ATT/ATU no colapsa del
   todo a 0, y en el CATE **`viv_paredes` es la segunda variable más
   importante** en los dos outcomes.

Conclusión práctica: antes de poder leer cualquier número de §4/§4b como
*efecto causal* del Sisbén, hay que resolver `viv_paredes`/`viv_pisos`
contra la ficha oficial de GEIH. Mientras tanto, son asociaciones pequeñas
y estadísticamente distintas de cero, no efectos causales confirmados.

## Resumen por paso

### 1. Hot-Deck (emparejamiento)

290.968 hogares GEIH, 3.106.489 donantes Sisbén (nacional + Bogotá
vigente). Celda: `geo_depto + jefe_edad (ciclo de vida) + viv_cuartos`.
**100 % en celda exacta.**

| Grupo | A | B | C | D |
|---|---|---|---|---|
| % de hogares | 31,2 | 35,2 | 23,2 | 10,3 |

(Antes de sumar `viv_cuartos` a la celda: A 28,0 / B 34,4 / C 24,9 / D 12,7
— sumar vivienda corrió la distribución hacia A y en contra de D.)

### 1b. Filtro del SDP (Bogotá): vigencia vs. año exacto

El archivo de Bogotá es un registro continuo (`fec_fin_encuesta`
2019-2026), no un corte único. Se adoptó **vigencia** (`<=31-dic-2024`,
1.274.578 hogares, 87,4 %) sobre año exacto (75.488, 5,2 %, sesgado hacia
actualizaciones recientes). Con la celda que incluye vivienda, la brecha
entre ambos filtros en Bogotá bajó de 10,2 a **5,5 puntos** en Grupo D
(21,0 % vigencia vs. 15,5 % año exacto) — la celda más fina diluye parte
de la sensibilidad al filtro, pero no la elimina.

### 2. Identificación causal (DAG)

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

### 3. Outcome: IPM-GEIH reducido

Sin llave común entre GEIH e IPM, se construyó un índice de privaciones
**sobre GEIH mismo** — pero reducido a **4 de 15** privaciones oficiales,
las únicas con una interpretación de código razonablemente verificable:

| Privación | % de jefes privados | Verificación |
|---|---|---|
| Analfabetismo (`P6160`) | 4,7 % | Código compartido con IPM, calza con cifras nacionales |
| Sin aseguramiento de salud (`P6090`) | 3,4 % | Código compartido con IPM, calza con cobertura ~95-96 % |
| Hacinamiento (`P5020` + personas/hogar) | 23,3 % | Umbral >3 personas/cuarto — **aproximado, no verificado** |
| Sin cotización a pensión del jefe (`P6920`) | 75,4 % | Tasa de no cotización entre ocupados (56,3 %) calza con informalidad nacional, pero el indicador final mezcla informalidad con desempleo/inactividad — ver limitación en `src/3_preprocesamiento.py` |

Score medio: 1,07/4. **23,5 % de los hogares clasifican como `POBRE_GEIH`**
(score ≥ 2 — umbral arbitrario, documentado).
`viv_paredes`/`viv_pisos` se excluyeron del outcome por la misma razón que
de la celda: adivinar la dirección de la privación habría sido fabricar un
indicador, no construirlo.

### 4. ATE / ATT / ATU (`LinearDML`)

| Outcome | ATE | ATT | ATU |
|---|---|---|---|
| `ipm_geih_score` (0-4) | +0,0137 [+0,008; +0,019] | +0,0136 [+0,008; +0,019] | +0,0139 [+0,009; +0,019] |
| `POBRE_GEIH` (0/1) | +0,0074 [+0,004; +0,011] | +0,0074 [+0,004; +0,011] | +0,0073 [+0,004; +0,011] |

IC95 % excluye 0 en los dos outcomes, controlando por la celda completa
del Hot-Deck. Los tres efectos son casi idénticos entre sí (esperable con
pocas covariables de heterogeneidad). **Hallazgo colateral:** el primer
intento de ATT/ATU con `LinearDRLearner` dio valores absurdos (+56, -191
en una escala 0-4) por inestabilidad del estimador doblemente robusto —
corregido reutilizando el `LinearDML` evaluado sobre cada subpoblación.
Detalle en `RESULTADOS_DML_ATE_ATT_ATU.md`.

### 4b. CATE (`CausalForestDML`)

CATE medio +0,0149 (`ipm_geih_score`) / +0,0031 (`POBRE_GEIH`), con
heterogeneidad fuerte por sexo del jefe: **+0,0293 en hogares con jefa
mujer vs. +0,0008 con jefe hombre** (36 veces más grande), consistente en
ambos outcomes. `viv_paredes` es la segunda variable más importante del
forest — no se puede descartar que el patrón por sexo sea en realidad
vivienda/geografía colándose por esa covariable. Detalle en
`RESULTADOS_CAUSALFOREST_CATE.md`.

### 5. Cotas de Fréchet-Manski (robustez, sin suponer independencia condicional)

El DML asume que, dentro de la celda del Hot-Deck, el grupo asignado es
como-si-aleatorio. Las cotas de Fréchet-Manski quitan esa suposición y
preguntan: ¿qué dicen los datos SIN ella? Resultado para `POBRE_GEIH`:

| | Estimador | Rango |
|---|---|---|
| Fréchet-Manski (sin CIA) | Cota | **[-0,627 ; +0,360]** |
| DML con Hot-Deck (con CIA) | Punto + IC95% | +0,0074 [+0,004 ; +0,011] |

El intervalo sin CIA es **145 veces más ancho** que el IC95% del DML, y
ni una sola de las 342 celdas individuales logra excluir el cero por su
cuenta. No es un error — es la confirmación honesta de que **toda la
precisión del resultado del DML viene de confiar en la suposición del
Hot-Deck, no de los datos crudos**. Detalle en
`RESULTADOS_FRECHET_MANSKI.md`, incluida una propuesta concreta para
angostar la cota con supuestos más débiles que la CIA completa (monotonía
en la selección o en la respuesta al tratamiento).

## Limitaciones que aplican a TODO lo anterior

- El tratamiento (`Grupo_hotdeck`) es imputado por emparejamiento
  estadístico, no observado en GEIH.
- El outcome es un proxy reducido (4 de 15 privaciones del IPM oficial).
- Sin ajuste por diseño muestral de GEIH ni de Sisbén.
- Selección: el Sisbén solo cubre hogares inscritos.
- Falta DPS/RUI como confusores (el canal "elegibilidad → participación
  DPS → resultado" de la Figura 2 del documento de pipeline no tiene
  datos todavía).
- `viv_paredes`/`viv_pisos`, `geo_zona`, `jefe_sexo`: categorías sin
  verificar contra la ficha oficial de cada fuente.

## Cómo se generó (reproducible)

```bash
poetry run python -m src.emparejamiento.emparejamiento_hotdeck_geih_sisben
poetry run python -m src.validacion.comparar_filtros_sdp
poetry run python src/4_dag_identificacion.py
poetry run python src/3_preprocesamiento.py
poetry run python src/5_estimacion.py
poetry run python -m src.estimacion.cotas_frechet_manski
```

Salidas crudas de esta corrida (2026-10-27): `docs/reports/resultado_hotdeck.txt`,
`docs/reports/resultado_comparacion_filtros_sdp.txt`,
`docs/reports/resultado_dag_identificacion.txt`,
`docs/reports/resultado_preprocesamiento.txt`,
`docs/reports/estimacion_ate_att_atu_cate.txt` — todas idénticas a la
corrida del 2026-10-21 (semillas fijas, mismos datos de entrada).
