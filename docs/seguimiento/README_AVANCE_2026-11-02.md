# Avance del 2026-11-02

Corte del trabajo hecho el 2 de noviembre de 2026: los 17 commits del día,
los resultados de los modelos, el estado en que queda el proyecto y lo que
falta. El detalle de cada cambio está en
[`CHANGELOG_PENDIENTES.md`](CHANGELOG_PENDIENTES.md) (entradas 2026-11-02
a (11)); el estado completo y vigente, en
[`RESUMEN_AVANCES.md`](RESUMEN_AVANCES.md).

## 1. Resumen del día

- **Se corrigieron tres errores que cambiaban resultados.**
  - Agosto de GEIH traía los códigos como `"1.0"` en vez de `"1"`.
  - En la propensión del DML, la celda y el departamento entraban como
    números en lugar de categorías.
  - En la reconstrucción monetaria, `P6430 = 7` se leía como "sin
    remuneración", pero es jornalero.
  
  Con el pipeline regenerado, **los efectos que se reportaban antes
  (+0,0235 en IPM-GEIH y +0,0158 en pobreza monetaria) desaparecen**. El
  DML da ≈0 en los cuatro outcomes.
- **Nuevo outcome: pobreza monetaria reconstruida.** Da 33,2 % de
  personas pobres frente al 31,8 % oficial. Comparada hogar por hogar con
  la base oficial del DANE, clasifica igual al 93,9 % de los hogares. La
  clasificación oficial queda como prueba de robustez.
- **Paredes y pisos homologados entre GEIH y Sisbén** con la ficha del
  Sisbén IV. **Pisos entra a la celda del Hot-Deck**, que pasa de 376 a
  993 celdas.
- **OE1 iniciado:** selección de variables con LASSO, Ridge y SHAP sobre
  el Sisbén. `viv_pisos` es la variable más importante en los tres
  métodos.
- **Simulaciones.**
  - **Simulación de identificación** (datos sintéticos): el diseño
    actual devuelve ≈0 sea cual sea el efecto verdadero. Solo una
    discontinuidad con el puntaje continuo lo recupera.
  - **Primera versión de la evaluación semisintética**, sobre hogares
    reales de GEIH: con Hot-Deck, cualquier estimador lleva el efecto a
    ≈0 (efecto verdadero: 0,095).
- **Comparación de proxies del IPM, Fases 1 y 2:** auditoría de
  variables y matriz de homologación de las 15 privaciones. La
  construcción de indicadores nuevos está en espera de revisión.

## 2. Commits del día, en orden

Todos están en `main`. El PR #9 y el PR #11 fueron fusionados.

| # | Commit | Autor | Qué hizo |
|---|---|---|---|
| 1 | `87a06ee` | Mateo Roncancio | Segunda especificación de `W` con la celda exacta del Hot-Deck; corrige el rótulo de ATT/ATU ("efecto en tratados/no tratados", no "error de inclusión/exclusión"). |
| 2 | `b9153ee` | Mateo Roncancio | Quita `warnings.filterwarnings("ignore")` de `5_estimacion.py` (no ocultaba nada). |
| 3 | `a5e7852` | (PR #11) | Simulación de identificación con datos sintéticos: qué diseño recupera el efecto de la elegibilidad. |
| 4 | `884303f` | Mateo Roncancio | OE1: selección de variables con LASSO, Ridge y SHAP sobre el Sisbén; declara `scipy` en `pyproject.toml`. |
| 5 | `465a660` | Juan Sebastián Fonseca | Regenera `poetry.lock` (faltaba `openpyxl`). |
| 6 | `e3508a8` | Juan Sebastián Fonseca | Comparación de proxies del IPM: inventario de variables GEIH, matriz de homologación GEIH ↔ Sisbén de las 15 privaciones y auditoría (PR #9). |
| 7 | `32191ec` | Juan Sebastián Fonseca | Actualiza el hash de `poetry.lock` tras declarar `scipy`. |
| 8 | `393c757` | Mateo Roncancio | Primer outcome de pobreza monetaria (ingreso per cápita, FGT0/FGT1) y boletín oficial del DANE como referencia. |
| 9 | `7657490` | Mateo Roncancio | Conecta la pobreza monetaria a `5_estimacion.py` (4 outcomes × 2 especificaciones de `W`). |
| 10 | `fdc8b35` | Mateo Roncancio | Cotas de Fréchet-Manski también para pobreza monetaria. |
| 11 | `9083a4e` | Mateo Roncancio | Auditoría de las 46 variables de ingreso de GEIH y metodología propuesta de pobreza monetaria (decisiones D1-D7). |
| 12 | `5f3d482` | Mateo Roncancio | Homologa paredes y pisos con la ficha del Sisbén IV; confirma que `geo_zona` vale 1 para urbano en las dos fuentes; documenta el bug de agosto. |
| 13 | `e47e40d` | Mateo Roncancio | Corrige el bug de agosto en el parser de `.DTA` y regenera el pipeline completo. |
| 14 | `40674d8` | Mateo Roncancio | Corrige los modelos auxiliares del DML (categóricas como indicadoras); pobreza monetaria definitiva con D1-D7; consolida la documentación. |
| 15 | `fc3a098` | Mateo Roncancio | Pisos entra a la celda del Hot-Deck; contraste hogar por hogar con la base oficial de pobreza monetaria (catálogo 874). |
| 16 | `527d263` | Mateo Roncancio | Pobreza monetaria oficial como prueba de robustez; evaluación semisintética. |
| 17 | `484422b` | Mateo Roncancio | Corrige el tiempo de ejecución reportado en la simulación semisintética. |

## 3. Estado al cierre del día

### Pipeline

| Etapa | Estado |
|---|---|
| Fuentes (GEIH 12 meses, IPM, Sisbén nacional y Bogotá) | ✅ Integradas. Se suman la base oficial de pobreza monetaria y la marca de víctimas MPMD (catálogo 874), esta última sin usar todavía. |
| Hot-Deck GEIH ← Sisbén | ✅ Celda: departamento + ciclo de vida + cuartos + pisos; 99,98 % en celda exacta. Grupos A/B/C/D: 14,2 / 29,4 / 34,4 / 22,0 %. |
| Outcome IPM-GEIH | ✅ 8 de 15 privaciones; `POBRE_GEIH` 17,1 %. |
| Outcome pobreza monetaria | ✅ Reconstruida: 33,2 % frente a 31,8 % oficial; la clasificación oficial queda como robustez. |
| DML / Causal Forest | ✅ Corregido. Es un **placebo**, no una estimación del efecto: el ATE ≈0 en los 4 outcomes (7 de 8 IC incluyen el 0). |
| Cotas de Fréchet-Manski | ✅ `POBRE_GEIH` [−0,261; +0,380]; `POBRE_MONETARIO` [−0,418; +0,648]. Ninguna celda excluye el 0. |
| OE1: selección de variables | ✅ Exactitud ≈53 % (línea base 30 %); el grupo D se confunde con C. |
| Evaluación semisintética | ✅ Primera versión. |
| Comparación de proxies del IPM | 🔧 Fases 1-2 hechas; Fases 3-5 en espera de revisión (ver §5b). |
| Pruebas | ✅ 35 pasan con `python -m pytest tests/` (ver §5c). |

### Lectura de conjunto

Con dos fuentes sin llave común, el Hot-Deck asigna el grupo Sisbén al
azar dentro de la celda. Por eso cualquier contraste dentro de la celda
da ≈0, sea cual sea el efecto verdadero. Lo muestran las dos
simulaciones y lo confirma la corrida con datos reales. Sin ese supuesto,
las cotas de Fréchet-Manski no fijan ni el signo del efecto. Lo único que
recuperó el efecto en la simulación es una discontinuidad con el puntaje
continuo del Sisbén, que el proyecto no tiene (no se ha solicitado).

### Ramas

- `main` y `ediciones-hotdeck-sdp` están en el mismo commit.
- `comparacion-proxies-ipm` y `simulacion-identificacion-v2` ya están
  fusionadas en `main`.
- Hay tres ramas remotas con un commit que no está en `main`:
  - `arregla-lock-openpyxl`: su arreglo del lock ya entró por otro
    commit (`465a660`).
  - `simulacion-identificacion`: la reemplazó la v2.
  - `corrige-controles-celda`: se bifurcó antes de la corrección del
    diccionario GEIH, así que no debe fusionarse tal cual.
  
  Las tres se pueden archivar o borrar.

## 4. Resultados de los modelos

Son las cifras de la última corrida del pipeline (2026-11-02, después de
las tres correcciones del día). Las salidas crudas están en
[`docs/reports/`](../reports/) y la interpretación completa en
[`docs/resultados/`](../resultados/README.md).

### 4a. Emparejamiento Hot-Deck (GEIH ← Sisbén)

290.968 hogares GEIH reciben el grupo de un donante del Sisbén, sorteado
dentro de su celda (3.106.489 hogares donantes). Se compararon tres
definiciones de celda; quedó la segunda.

| Celda | Celdas | % en celda exacta | Donantes por celda (mediana) | Corr. P(T \| celda) con pobreza monetaria | A / B / C / D (%) |
|---|---|---|---|---|---|
| Depto + edad + cuartos (anterior) | 376 | 99,999 | 9.437 | 0,20 | 22,0 / 33,8 / 28,7 / 15,6 |
| **+ pisos (vigente)** | **993** | **99,976** | **2.353** | **0,29** | **14,2 / 29,4 / 34,4 / 22,0** |
| + pisos + paredes | 2.081 | 99,946 | 1.898 | 0,29 | 14,0 / 29,0 / 34,5 / 22,5 |

Pisos hace que la celda separe mejor a los hogares pobres sin perder
cobertura. Paredes no agrega nada encima, así que no entra. Fuentes:
`resultado_hotdeck.txt` y `comparacion_celdas_hotdeck_vivienda.txt`.

### 4b. Outcomes

- **IPM-GEIH:** 8 de las 15 privaciones; 17,1 % de los hogares con
  `POBRE_GEIH` (3 o más privaciones).
- **Pobreza monetaria reconstruida** (personas, factor `FEX_C18/12`):

| Dominio | FGT0 reconstruida | FGT0 oficial | FGT1 reconstruida | FGT1 oficial | Extrema reconstruida | Extrema oficial | Gini reconstruido | Gini oficial |
|---|---|---|---|---|---|---|---|---|
| Nacional | 33,2 | 31,8 | 13,5 | 12,6 | 12,5 | 11,7 | 0,565 | 0,551 |
| Cabeceras | 30,9 | 28,6 | 12,3 | 11,0 | 9,9 | 8,7 | 0,548 | 0,530 |
| 13 ciudades | 26,4 | 24,0 | 10,2 | 8,9 | 7,0 | 5,9 | 0,545 | 0,522 |
| Otras cabeceras | 36,7 | 34,8 | 15,1 | 13,9 | 13,8 | 12,4 | 0,502 | 0,490 |
| Rural | 41,3 | 42,5 | 17,6 | 17,9 | 21,3 | 21,8 | 0,494 | 0,482 |

  La decisión que más pesa es imputar el arriendo: sin él, la FGT0
  nacional sube a 38,8 %. **Contraste hogar por hogar** con la base
  oficial del DANE (275.057 hogares, 24 departamentos y Bogotá):
  - clasificación igual en el 93,9 % de los hogares (92,5 % rural);
  - razón mediana de ingreso de 1,00;
  - personas mal clasificadas: 3,9 % pobres solo en la reconstrucción y
    2,5 % pobres solo en la oficial.
  
  Fuentes: `pobreza_monetaria_geih.txt` y
  `comparacion_pobreza_monetaria_oficial.txt`.

### 4c. DML y Causal Forest (P2/OE2)

- **Estimadores:** ATE, ATT y ATU con `LinearDML`; CATE con
  `CausalForestDML` (400 árboles, 80.000 hogares).
- **Tratamiento:** T = grupo A/B imputado por el Hot-Deck (46,7 % de los
  hogares).
- **Covariables de heterogeneidad (`X`):** zona, sexo del jefe y paredes.
- **Controles (`W`):** se probaron dos especificaciones.
  - **Proxy:** departamento y pisos como indicadoras, más splines de la
    edad del jefe y los cuartos.
  - **Celda exacta:** indicadoras de la celda del Hot-Deck, la misma con
    la que se sortea el donante. Su propensión reproduce la empírica
    (correlación 0,995).

**ATE [IC 95 %]**, n = 290.968 (275.057 en la oficial):

| Outcome | W = proxy | W = celda exacta |
|---|---|---|
| `ipm_geih_score` (0-8) | −0,0052 [−0,0122; +0,0018] | −0,0021 [−0,0092; +0,0051] |
| `POBRE_GEIH` | +0,0010 [−0,0014; +0,0033] | −0,0026 [−0,0049; −0,0002] |
| `log_ingreso_percapita` | −0,0056 [−0,0190; +0,0077] | +0,0006 [−0,0128; +0,0141] |
| `POBRE_MONETARIO` | +0,0003 [−0,0031; +0,0037] | −0,0002 [−0,0036; +0,0033] |
| `POBRE_MONETARIO_OFICIAL` (robustez) | −0,0005 [−0,0040; +0,0030] | −0,0005 [−0,0041; +0,0030] |

**ATT y ATU con la celda exacta:**

| Outcome | ATT (tratados, n = 135.739) | ATU (no tratados, n = 155.229) |
|---|---|---|
| `ipm_geih_score` | −0,0016 [−0,0095; +0,0062] | −0,0025 [−0,0094; +0,0044] |
| `POBRE_GEIH` | −0,0031 [−0,0059; −0,0003] | −0,0021 [−0,0043; +0,0001] |
| `log_ingreso_percapita` | +0,0007 [−0,0132; +0,0147] | +0,0006 [−0,0130; +0,0141] |
| `POBRE_MONETARIO` | −0,0000 [−0,0037; +0,0036] | −0,0003 [−0,0038; +0,0031] |

**CATE (Causal Forest, celda exacta):**
- la media va de −0,0045 a +0,0084 y la desviación de 0,008 a 0,042 en
  los cuatro outcomes;
- las variables que más pesan son `viv_paredes` (≈0,51-0,58), zona
  (≈0,19-0,29) y sexo del jefe (≈0,20-0,24).

**Lectura:** todos los efectos son despreciables. Los únicos IC que no
incluyen el cero son los de `POBRE_GEIH` con la celda exacta (ATE y
ATT), y por un margen mínimo: −0,26 y −0,31 puntos porcentuales. Es lo
que predicen las
simulaciones (§4f): el grupo imputado se sortea dentro de la celda, así
que el contraste es un **placebo del emparejamiento, no el efecto del
Sisbén**. Tampoco hay que leer la heterogeneidad del CATE como
sustantiva: los patrones por zona y sexo cambiaron de signo entre
corridas y se retiraron como conclusión. Los efectos que se reportaban
antes de hoy (+0,0235 en IPM-GEIH y +0,0158 en pobreza monetaria, con IC
sin el 0) venían de pasar la celda como número a la propensión. Fuente:
`estimacion_ate_att_atu_cate.txt`.

### 4d. Cotas de Fréchet-Manski (sin suponer independencia condicional)

| Outcome | Celdas | P(Y = 1) | Cota del ATE | Ancho |
|---|---|---|---|---|
| `POBRE_GEIH` | 921 | 0,204 | [−0,261; +0,380] | 0,64 |
| `POBRE_MONETARIO` | 921 | 0,270 | [−0,418; +0,648] | 1,07 |
| `POBRE_MONETARIO_OFICIAL` (robustez) | 712 | — | [−0,407; +0,620] | 1,03 |

Ninguna celda excluye el cero. Sin el supuesto del Hot-Deck, los datos
no determinan ni el signo del efecto. Fuente: `cotas_frechet_manski.txt`.

### 4e. Selección de variables (P1/OE1)

- **Qué se predice:** el grupo Sisbén (A-D).
- **Muestra:** 150.000 hogares, 70 % para entrenar y 30 % para evaluar.
- **Predictores:** 10 variables del hogar. Nunca se usan `I1`-`I15` ni
  `H_5`.

| Modelo | Exactitud | F1 macro |
|---|---|---|
| LASSO (L1) | 0,530 | 0,526 |
| Ridge (L2) | 0,530 | 0,526 |
| Random Forest (base de SHAP) | 0,527 | 0,499 |
| Random Forest, partición por municipio | 0,541 | 0,435 |
| Predecir siempre la clase mayoritaria | ≈0,30 | — |

**Importancia (normalizada 0-1 en cada método, sin contar el
departamento):**

| Variable | LASSO | Ridge | SHAP |
|---|---|---|---|
| `viv_pisos` | 0,35 | 0,29 | **1,00** |
| `hog_num_personas` | 0,07 | 0,05 | 0,45 |
| `viv_alcantarillado` | 0,04 | 0,03 | 0,45 |
| `jefe_sexo` | 0,07 | 0,06 | 0,29 |
| `viv_paredes` | 0,09 | 0,09 | 0,24 |
| `viv_cuartos` | 0,05 | 0,03 | 0,24 |

**Por grupo (LASSO):** sensibilidad 0,64 en A, 0,48 en B, 0,58 en C y
0,39 en D. El 45 % de los hogares D se predice como C, y con Random
Forest la sensibilidad en D cae a 0,22. El modelo está bien calibrado:
la probabilidad media predicha coincide con la tasa observada en cada
grupo.

**Rankings:** LASSO y Ridge casi no difieren (Spearman 0,988); SHAP
reordena el tercio medio (0,79-0,81), señal de interacciones no
lineales. LASSO no elimina ninguna variable. Ojo: esto predice el grupo
asignado, no la pobreza real. Fuente:
`seleccion_variables_lasso_ridge_shap.txt`.

### 4f. Simulaciones: ¿qué diseño puede recuperar el efecto?

**Simulación de identificación** (datos 100 % sintéticos, 20
repeticiones, celda con poder alto), estimación media frente al efecto
verdadero:

| Estimador | Verdadero 0 | Verdadero −0,15 | Verdadero −0,30 |
|---|---|---|---|
| Hot-Deck + celda (pipeline actual) | 0,000 | −0,004 | +0,002 |
| Hot-Deck sin controlar la celda | +0,933 | +0,893 | +0,876 |
| Vínculo perfecto + celda | +1,459 | +1,312 | +1,159 |
| **Vínculo perfecto + discontinuidad (puntaje continuo)** | **+0,004** | **−0,160** | **−0,297** |
| Vínculo perfecto + grupos A-D vecinos | +0,806 | +0,662 | +0,516 |

**Evaluación semisintética.**
- **Datos:** los 290.968 hogares reales de GEIH; solo se simulan el
  tratamiento y el efecto, con un ATE verdadero de 0,095 sobre el
  log-ingreso.
- **Repeticiones:** 50, cada una con 30.000 hogares (10 para el Causal
  Forest).
- **Tabla:** estimación media con la cobertura del IC 95 % entre
  paréntesis.

| Escenario | Integración | Regresión EF celda | LinearDML | Causal Forest |
|---|---|---|---|---|
| Aleatoria | Oráculo (T verdadero) | 0,094 (0,98) | 0,092 (0,94) | 0,095 (1,0) |
| | Vínculo 50 % | 0,044 (0,20) | 0,044 (0,20) | 0,042 (1,0) |
| | Hot-Deck | −0,001 (0) | −0,001 (0) | +0,002 (0,7) |
| Confusión observada | Oráculo | 0,092 (1,0) | 0,090 (0,94) | 0,085 (1,0) |
| | Hot-Deck | −0,001 (0) | −0,005 (0,02) | −0,001 (0,6) |
| Confusión no observada fuerte | Oráculo | −0,771 (0) | −0,770 (0) | −0,776 (0) |
| | Hot-Deck | −0,003 (0) | −0,002 (0) | −0,010 (0,8) |

**Lectura de las dos simulaciones:**
- Con el Hot-Deck, todo estimador que controla la celda devuelve ≈0 en
  los cinco escenarios: se pierde el efecto completo. Es el mismo ≈0 que
  dan los datos reales en §4c.
- Con vínculo parcial, el efecto se atenúa en proporción a los hogares
  mal vinculados.
- Si hay confusión no observada, ningún estimador la corrige, ni
  siquiera con el T verdadero.
- Solo recupera el efecto la combinación de vínculo hogar por hogar con
  discontinuidad sobre el puntaje continuo.
- Fuentes: `resultado_simulacion_identificacion.txt` y
  `simulacion_semisintetica.txt`.

### 4g. Representatividad del Sisbén

La cobertura del Sisbén frente a la población de GEIH varía 32 veces
entre departamentos: de 0,4 % en Valle a 12,8 % en Putumayo. El registro
no es una muestra uniforme del país.

## 5. Pendientes

### 5a. Proyecto (de `RESUMEN_AVANCES.md` §4)

1. **Evaluación semisintética, siguientes pasos:** outcome binario de
   pobreza; sensibilidad a gamma y a la fuerza del efecto; más
   repeticiones de Causal Forest; Hot-Deck con toda la cadena de
   respaldos; escenario con discontinuidad.
2. **Pobreza monetaria, Fase 5:** comparación con IPM-GEIH y con el
   grupo imputado, por celda (D6).
3. Angostar las cotas de Fréchet-Manski con supuestos de monotonía
   (MTS/MTR).
4. Construir las privaciones del IPM que faltan en GEIH y refinar
   `sin_cotizacion_pension_jefe`. Se conecta con §5b.
5. Confirmar en ANDA los cortes de `PER002`. Revisar en Bogotá los 6
   hogares con doble jefe y los 227 con `Clasificacion` distinta entre
   miembros.
6. Evaluar la marca de víctimas del DANE como covariable, en lugar del
   RUI.
7. Actualizar el anteproyecto con el enfoque vigente.
8. OE1: falta la concordancia con la pobreza, que con el Hot-Deck solo
   puede medirse por celda. OE3 (reglas de focalización) no ha
   empezado.

### 5b. Comparación de proxies del IPM — decisiones para la Fase 3

Detalle en
[`00_auditoria_variables.md`](../metodologia/comparacion_proxies/00_auditoria_variables.md)
§6 y en la
[matriz de homologación](../metodologia/comparacion_proxies/01_matriz_homologacion.md).
De las 15 privaciones, 12 son homologables, 1 es parcial (I6, trabajo
infantil, solo 15-17 años) y 2 no están disponibles en GEIH (I5, primera
infancia; I10, barreras de salud). Antes de construir `IPM_GEIH_15` e
`IPM_GEIH_ALT` hay que decidir:

1. Cómo repartir el peso de I5 e I10. La propuesta es repartirlo dentro
   de su dimensión.
2. Si I6 entra solo en el indicador alternativo.
3. Qué hacer con la tautología de I13/I14 con las covariables.
   - Revisar a la luz del 2026-11-02: `viv_pisos` salió de `X` y entró a
     `W`.
   - `viv_paredes` sigue en `X`.
4. Cómo convertir semestres de educación superior a años.
5. Cómo identificar a los pensionados.
6. Qué miembros cuentan en el hogar. `P6050` usa los códigos 1-13; la
   auditoría de pobreza monetaria ya resolvió que el 10 es servicio
   doméstico.
7. Agua rural: si "u otra fuente" incluye la pila pública.
8. Hacinamiento: si "cuarto" se toma como cuarto para dormir (`P5010`).
9. Conseguir el documento metodológico del Sisbén del DNP.

### 5c. Mantenimiento del repositorio

- `poetry run pytest tests/` (el comando de `CLAUDE.md`) falla al
  importar en 4 archivos nuevos: `test_hotdeck_celda`,
  `test_local_csv_parser`, `test_preprocesamiento_monetario` y
  `test_simulacion_semisintetica`. Importan `src.*`, y `pytest` no pone
  la raíz del repositorio en el path. Con `python -m pytest tests/`
  pasan las 35 pruebas. Arreglo sugerido: `pythonpath = ["."]` en
  `[tool.pytest.ini_options]` de `pyproject.toml`.
- Archivar o borrar las tres ramas remotas de §3 que no están en `main`.
