# Seguimiento del proyecto: cambios y avances

Focalización del Sisbén IV y pobreza monetaria en hogares colombianos
usando un enfoque de inferencia causal.

Mateo Roncancio y Juan Sebastián Fonseca. Maestría en Ciencia de Datos,
Universidad Santo Tomás. Tutor: Carlos Isaac Zainea Maya.
Corte: 3 de noviembre de 2026.

Este documento reúne los cambios y avances del proyecto desde su inicio
(4 de agosto de 2026) hasta el corte. Para el detalle técnico de cada
cambio ver [`CHANGELOG_PENDIENTES.md`](CHANGELOG_PENDIENTES.md); para el
estado completo de fuentes y pendientes,
[`RESUMEN_AVANCES.md`](RESUMEN_AVANCES.md); para el corte del último día,
[`README_AVANCE_2026-11-02.md`](README_AVANCE_2026-11-02.md); para los
resultados interpretados, [`../resultados/README.md`](../resultados/README.md).

## 1. Qué se hace y con qué enfoque

El proyecto evalúa qué tan bien focaliza el Sisbén IV y qué efecto
tiene sobre la pobreza de los hogares. No existe una llave común entre
la GEIH (que mide ingresos y condiciones de vida) y el Sisbén (que
clasifica a los hogares en grupos A a D). La vinculación se hace por
emparejamiento estadístico (Hot-Deck): cada hogar de la GEIH recibe el
grupo de un donante del Sisbén que comparte su celda.

En la tutoría del 27 de octubre el enfoque se reencuadró:

- El resultado pasa a ser la **pobreza monetaria** (ingreso per cápita,
  FGT0 y FGT1), con el IPM-GEIH como indicador complementario.
- El componente causal se evalúa con **simulación** de efectos
  conocidos, además de la estimación sobre datos reales.
- Título de trabajo: «Focalización del Sisbén IV y pobreza monetaria en
  hogares colombianos usando un enfoque de inferencia causal».

Objetivos vigentes en el repositorio: P1/OE1 (determinantes y validez
del Sisbén, con LASSO, Ridge y SHAP), P2/OE2 (efecto causal sobre el
bienestar, con DML y Causal Forest) y P3/OE3 (reglas de focalización con
FGT1). Los objetivos del anteproyecto se están ajustando con el tutor;
OE3 y OE5 no se satisfacen con su formulación actual.

## 2. Resumen

- **Pipeline completo y reproducible.** Va de las fuentes al
  emparejamiento, los dos outcomes (IPM-GEIH y pobreza monetaria), la
  estimación y las cotas. Las dependencias están fijadas con Poetry
  (Python 3.11 a 3.13) y las corridas usan semillas fijas.
- **Resultado con datos reales.** El DML da efectos de cero en los
  cuatro outcomes (7 de 8 intervalos de confianza incluyen el 0). Con un
  grupo imputado al azar dentro de la celda, este resultado es una prueba
  placebo del emparejamiento y no una estimación del efecto del Sisbén.
- **Cotas sin supuesto de independencia.** El efecto sobre pobreza
  monetaria queda entre −0,418 y +0,648. Ninguna de las 921 celdas
  excluye el 0.
- **Simulaciones.** Con efecto verdadero conocido, el diseño actual
  devuelve cero sin importar el efecto. Solo una discontinuidad con el
  puntaje continuo del Sisbén lo recupera.
- **Correcciones documentadas.** Entre el 28 de octubre y el 2 de
  noviembre se detectaron y corrigieron siete errores que cambiaban
  resultados (sección 4). Las conclusiones que dependían de ellos se
  retiraron.
- **OE1 iniciado.** LASSO, Ridge y SHAP sobre el Sisbén: exactitud de
  0,53 frente a 0,30 de la línea base.

## 3. Línea de tiempo

63 commits en `main`, 9 pull requests fusionados.

| Fecha | Avance |
|---|---|
| 4 a 7 de agosto | Estructura inicial del repositorio. Datos del IPM 2025 procesados a Parquet, limpieza con llave de hogar y diccionario de datos consolidado. |
| 15 a 24 de septiembre | Carga del Sisbén IV 2024 y estandarización de GEIH y Sisbén a un esquema común. Primer Hot-Deck validado. Conexión a Azure Blob Storage. Hallazgo de la cobertura de Bogotá. |
| 9 y 10 de octubre | Llaves de la GEIH normalizadas, edad del Sisbén por ciclo de vida, incorporación de Bogotá (SDP). Scripts de Azure. Código reorganizado por etapa de la tesis. Se descubre que el SDP es un registro continuo 2019-2026 y no un corte único. Verificación empírica de los códigos de edad `PER002`. |
| 21 de octubre | Acceso de solo lectura a los datos en Azure con token SAS. Diagrama causal (DAG) con chequeo formal de d-separación. Primera estimación real: ATE, ATT, ATU y CATE. Poetry con Python 3.11. |
| 27 de octubre | Cotas de Fréchet-Manski. Pipeline reproducido de punta a punta. Sensibilidad del indicador de pobreza, representatividad del Sisbén y pruebas automatizadas. Tutoría con el tutor y reencuadre del enfoque. |
| 28 de octubre | Se consigue el diccionario oficial de la GEIH. Se corrige el mapeo de vivienda y el indicador de pobreza pasa de 4 a 8 de las 15 privaciones del IPM. |
| 2 de noviembre | Día con 21 commits. Pobreza monetaria reconstruida, OE1 con LASSO, Ridge y SHAP, homologación de paredes y pisos, comparación de proxies del IPM, simulación de identificación, evaluación semisintética y tres correcciones de fondo (sección 4). |
| 3 de noviembre | Consolidación de este seguimiento. |

## 4. Errores detectados y corregidos

Cada corrección cambió cifras del pipeline. Se documentan aquí porque
los resultados reportados antes de ellas no son vigentes.

| Fecha | Qué se detectó | Efecto en los resultados |
|---|---|---|
| 28 oct | `viv_paredes`, `viv_pisos` y `viv_cuartos` apuntaban a columnas equivocadas de la GEIH. Se verificó con el diccionario oficial. | Cambió la celda del Hot-Deck, el indicador y todas las estimaciones. El patrón por sexo del jefe se invirtió. |
| 28 oct | Dos de las privaciones de vivienda recién incorporadas usaban los mismos códigos que covariables del Causal Forest. | Se retiraron del indicador (queda en 8 de 15). |
| 2 nov | Los controles del DML usaban `jefe_edad` y `viv_cuartos` continuos como aproximación de la celda discreta del Hot-Deck. | Con la celda exacta, el efecto sobre el puntaje IPM-GEIH cae 63 %. |
| 2 nov | Los meses de la GEIH cargados desde `.DTA` traían los códigos como `"1.0"` en vez de `"1"`. Afectaba a agosto. | Se regeneró todo el pipeline. Cambiaron porcentajes de privaciones y de pobreza. |
| 2 nov | En la propensión del DML, la celda (0 a 375) y el departamento entraban como números y no como categorías. | La propensión no reproducía la empírica. Con el arreglo, la correlación es 0,998. Los efectos que se reportaban (+0,0235 y +0,0158) desaparecen. |
| 2 nov | En la reconstrucción monetaria, `P6430 = 7` se leía como «sin remuneración» y es jornalero. | La pobreza monetaria baja de 37,6 % a 33,2 % junto con las demás decisiones de la metodología. |
| 2 nov | ATT y ATU se rotulaban como errores de inclusión y exclusión. | Solo el rótulo: son el efecto en tratados y en no tratados. |

Conclusiones que se retiraron: que el efecto residual con la celda exacta
fuera la evidencia de robustez más fuerte del proyecto, y los patrones de
heterogeneidad del CATE por zona y sexo del jefe, que cambiaron de signo
entre corridas.

## 5. Resultados vigentes

Cifras de la última corrida (2 de noviembre). Las salidas crudas están en
[`../reports/`](../reports/).

### 5.1 Emparejamiento Hot-Deck

290.968 hogares de la GEIH 2024 y 3.106.489 hogares donantes del Sisbén
(nacional y Bogotá, con filtro de vigencia a 2024). La celda vigente es
departamento, ciclo de vida del jefe, cuartos y nivel de pisos.

| Celda | Celdas | % en celda exacta | A / B / C / D (%) |
|---|---|---|---|
| Departamento, edad y cuartos | 376 | 99,999 | 22,0 / 33,8 / 28,7 / 15,6 |
| **Con pisos (vigente)** | **993** | **99,976** | **14,2 / 29,4 / 34,4 / 22,0** |
| Con pisos y paredes | 2.081 | 99,946 | 14,0 / 29,0 / 34,5 / 22,5 |

Pisos mejora la separación de hogares pobres sin perder cobertura.
Paredes no agrega nada encima.

### 5.2 Outcomes

| Outcome | Resultado |
|---|---|
| IPM-GEIH | 8 de las 15 privaciones. 17,1 % de los hogares con 3 o más privaciones (`POBRE_GEIH`). |
| Pobreza monetaria reconstruida (FGT0, personas) | 33,2 % frente a 31,8 % oficial. FGT1: 13,5 % frente a 12,6 %. |
| Contraste hogar por hogar con la base oficial del DANE | Clasificación igual en el 93,9 % de los 275.057 hogares comparables. |

La decisión que más pesa en la reconstrucción es imputar el arriendo:
sin esa imputación, la tasa nacional sube a 38,8 %. La clasificación
oficial del DANE se usa como prueba de robustez.

### 5.3 DML y Causal Forest

ATE con intervalo de confianza del 95 %, controlando por la celda exacta
(n = 290.968; 275.057 en la oficial).

| Outcome | ATE |
|---|---|
| `ipm_geih_score` (0 a 8) | −0,0021 [−0,0092; +0,0051] |
| `POBRE_GEIH` | −0,0026 [−0,0049; −0,0002] |
| `log_ingreso_percapita` | +0,0006 [−0,0128; +0,0141] |
| `POBRE_MONETARIO` | −0,0002 [−0,0036; +0,0033] |
| `POBRE_MONETARIO_OFICIAL` (robustez) | −0,0005 [−0,0041; +0,0030] |

Todos los efectos son despreciables. Los únicos intervalos que no incluyen
el 0 son los de `POBRE_GEIH` (ATE y ATT), por un margen mínimo. El Causal
Forest no muestra heterogeneidad estable entre corridas.

### 5.4 Cotas de Fréchet-Manski

| Outcome | Celdas | Cota del ATE |
|---|---|---|
| `POBRE_GEIH` | 921 | [−0,261; +0,380] |
| `POBRE_MONETARIO` | 921 | [−0,418; +0,648] |
| `POBRE_MONETARIO_OFICIAL` | 712 | [−0,407; +0,620] |

Ninguna celda excluye el 0. Sin el supuesto del Hot-Deck, los datos no
determinan ni el signo del efecto.

### 5.5 Selección de variables (P1/OE1)

Predice el grupo Sisbén (A a D) con 10 variables del hogar, sobre 150.000
hogares (70 % entrenamiento, 30 % evaluación).

| Modelo | Exactitud | F1 macro |
|---|---|---|
| LASSO | 0,530 | 0,526 |
| Ridge | 0,530 | 0,526 |
| Random Forest (base de SHAP) | 0,527 | 0,499 |
| Clase mayoritaria | 0,30 | — |

`viv_pisos` es la variable más importante en los tres métodos. El grupo D
se confunde con C: el 45 % de los hogares D se predice como C. Estos
resultados predicen el grupo asignado, no la pobreza real.

### 5.6 Simulaciones

**Simulación de identificación** (datos sintéticos, 20 repeticiones),
estimación media según el efecto verdadero.

| Estimador | 0 | −0,15 | −0,30 |
|---|---|---|---|
| Hot-Deck con celda (pipeline actual) | 0,000 | −0,004 | +0,002 |
| Hot-Deck sin celda | +0,933 | +0,893 | +0,876 |
| Vínculo perfecto con celda | +1,459 | +1,312 | +1,159 |
| Vínculo perfecto con discontinuidad (puntaje continuo) | +0,004 | −0,160 | −0,297 |
| Vínculo perfecto con grupos A a D vecinos | +0,806 | +0,662 | +0,516 |

**Evaluación semisintética.** Usa los hogares reales de la GEIH y simula
solo el tratamiento y el efecto (+0,095 sobre el log-ingreso, −0,033
sobre la pobreza monetaria). Se corrió hasta la convergencia el
2026-11-03: 432 repeticiones de 30.000 hogares (Causal Forest en 216),
hasta que el error Monte Carlo de cada celda quedó bajo el umbral.

- Con el tratamiento verdadero y confusión observable, los estimadores
  recuperan el efecto (0,089 a 0,094; −0,031 a −0,033 en pobreza).
- Con Hot-Deck, todo estimador devuelve cerca de cero en los ocho
  escenarios y los dos resultados.
- Con un vínculo del 50 %, el efecto se atenúa a la mitad (0,041 a 0,048).
- Con confusión no observada, ningún estimador la corrige, ni siquiera
  con el tratamiento verdadero, y en pobreza el signo se invierte
  (+0,138 con confusión fuerte).
- Solo la discontinuidad en el corte la resiste (+0,086 frente a +0,090),
  y solo con vínculo hogar por hogar; con Hot-Deck también da cero.

Detalle en [`SIMULACION_SEMISINTETICA.md`](../resultados/SIMULACION_SEMISINTETICA.md).

### 5.7 Representatividad del Sisbén

La cobertura frente a la población de la GEIH varía 32 veces entre
departamentos: de 0,4 % en Valle del Cauca a 12,8 % en Putumayo.

## 6. Lectura de conjunto

1. El Hot-Deck asigna el grupo al azar dentro de la celda. Por eso el
   contraste dentro de la celda es un placebo y los datos reales dan
   cero, como predicen las dos simulaciones.
2. Sin ese supuesto, las cotas de Fréchet-Manski no fijan el signo del
   efecto.
3. La simulación permite evaluar estimadores y reglas de focalización
   con efecto verdadero conocido, y reportar rangos de efectos sobre el
   bienestar. Los resultados simulados se distinguen de los datos reales.
4. La infraestructura (pipeline, simulaciones y pruebas) queda
   replicable para quien cuente con la estructura de datos.

## 7. Estado de los objetivos

| Objetivo | Estado |
|---|---|
| P1/OE1: determinantes y validez del Sisbén | Implementado (LASSO, Ridge y SHAP). Falta definir grupos y subgrupos de variables y la concordancia con la pobreza. |
| P2/OE2: efecto causal sobre el bienestar | Estimación y cotas implementadas con indicador proxy de pobreza y con pobreza monetaria. Con los datos actuales el efecto no se identifica; la simulación cierra la parte metodológica. |
| P3/OE3: reglas de focalización (FGT1) | Hecho en la simulación (2026-11-04): el proxy de medios logra 82-85 % de la reducción ideal de FGT1; las reglas con CATE estimado son peores. Ver [`RESULTADOS_REGLAS_FOCALIZACION.md`](../resultados/RESULTADOS_REGLAS_FOCALIZACION.md). |

## 8. Pendientes

1. Evaluación semisintética: hecha hasta la convergencia el 2026-11-03.
   Quedan ajustes menores: sensibilidad al tamaño del efecto,
   discontinuidad difusa y la causa del sesgo pequeño de LinearDML.
2. Reglas de focalización (P3/OE3): hechas el 2026-11-04. Quedan
   presupuestos menores que la población pobre y heterogeneidad más
   fuerte.
3. Pobreza monetaria, fase 5: comparación con el IPM-GEIH y con el grupo
   imputado, por celda.
4. Comparación de proxies del IPM, fases 3 a 5: decisiones pendientes
   sobre las privaciones I5, I6 e I10 (ver
   [`00_auditoria_variables.md`](../metodologia/comparacion_proxies/00_auditoria_variables.md)).
5. Angostar las cotas con supuestos de monotonía.
6. Construir las privaciones del IPM que faltan y refinar la de pensión.
7. Confirmar en ANDA los cortes de `PER002` y revisar los hogares de
   Bogotá con doble jefe.
8. Actualizar el anteproyecto con el enfoque y los objetivos vigentes.
9. Arreglo de las pruebas: `pytest` falla al importar en 4 archivos si se
   corre con `poetry run pytest`; agregar `pythonpath = ["."]` en
   `pyproject.toml`. Con `python -m pytest tests/` pasan las 35 pruebas.

## 9. Ramas y pull requests

- `main` contiene todo el trabajo vigente. Los PR #1 a #7, #9 y #11
  están fusionados.
- Tres ramas remotas tienen un commit que no está en `main` y se pueden
  archivar: `arregla-lock-openpyxl` (su arreglo entró por otro commit),
  `simulacion-identificacion` (la reemplazó la v2) y
  `corrige-controles-celda` (se bifurcó antes de la corrección del
  diccionario de la GEIH y no debe fusionarse).
