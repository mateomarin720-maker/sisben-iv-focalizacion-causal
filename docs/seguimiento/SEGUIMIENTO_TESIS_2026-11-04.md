# Seguimiento de la tesis: tutoría y avances al 4 de noviembre de 2026

Fecha de corte: 2026-11-04. Autores: Mateo Roncancio y Juan Sebastián Fonseca. Tutor: Carlos Isaac Zainea Maya.

> **Documento guía vigente** de la tesis desde el 2026-11-04 (enfoque
> acordado en la tutoría del 2026-11-03). Las reglas del tutor están
> también en `CLAUDE.md`. Notas de verificación al final.

## Contexto

La tesis evalúa la focalización del Sisbén IV y su relación con la pobreza monetaria con un enfoque de inferencia causal. Con las fuentes públicas el efecto del Sisbén no se identifica, por lo que el trabajo se organiza como un framework de ingeniería y simulación. Este documento recoge lo acordado en la tutoría y el estado del repositorio al 4 de noviembre de 2026.

No existe una llave común entre la GEIH y el Sisbén. Se vincularon 290.968 hogares de la GEIH 2024 con 3.106.489 hogares donantes del Sisbén (nacional y Bogotá) por emparejamiento estadístico (Hot-Deck). Título de trabajo: «Focalización del Sisbén IV y pobreza monetaria en hogares colombianos usando un enfoque de inferencia causal».

## Enfoque acordado en la tutoría

La tesis se organiza en tres bloques, y la simulación es un módulo independiente dentro del proceso, no su fin.

1. **Arquitectura e ingeniería:** enlazar las dos bases anonimizadas y correr los modelos, de forma reutilizable por otras instituciones.
2. **Simulación semisintética y framework:** una organización lo corre con datos simulados o trae sus propios datos ya enlazados.
3. **Discusión de focalización:** qué variables podrían incorporarse al modelo del Sisbén, para pobreza monetaria y multidimensional. Se plantea como pregunta abierta y recomendación, no como conclusión causal.

Aporte declarado: un framework para evaluar subsidios y transferencias monetarias. Las reglas que fijó el tutor:

- Los nombres de las variables estandarizadas de GEIH y Sisbén no se cambian ni se hacen configurables; lo flexible es el resto del framework.
- El DML sobre el grupo imputado no se presenta como efecto causal del Sisbén.
- La entrega final es el repositorio y el documento escrito, y el repositorio debe poder revisarlo un jurado: limpio y sin ruido.
- Los resultados simulados se distinguen de los datos reales con un asterisco (\*).

## Estado de las tareas de la tutoría

| Tarea | Estado al 4 nov | Evidencia |
| --- | --- | --- |
| Variabilidad de la imputación del Hot-Deck (error relativo y coeficiente de variación) | Hecha el 4 nov | `RESULTADOS_VARIABILIDAD_HOTDECK.md` |
| Simulación como módulo independiente, con modo de datos propios y modo simulado | En curso (pasos 1-4 de 7) | `src/simulacion/`, con contrato de columnas canónicas validado (`contrato.py`); diseño en `docs/metodologia/DISENO_MODULO_SIMULACION.md` |
| Evaluación semisintética completa | Hecha el 8 nov | 432 repeticiones de 30.000 hogares hasta la convergencia, pobreza monetaria binaria, tres niveles de confusión no observada y regla de corte con RD; sensibilidad en 228 repeticiones. Regenerada con la cadena de respaldos del Hot-Deck y con asterisco |
| Reglas de focalización (OE3) y cotas con monotonía | Hechas el 4 nov; mismo dinero y heterogeneidad ampliada el 9 nov | `RESULTADOS_REGLAS_FOCALIZACION.md`, `RESULTADOS_HETEROGENEIDAD_AMPLIADA.md` y `RESULTADOS_FRECHET_MANSKI.md` |
| Cotas de Fréchet por parámetro y errores de focalización con datos reales | Hechas el 9 y 10 nov | `RESULTADOS_FRECHET_MANSKI.md` y `RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md` |
| Recomendación de variables | Primera versión el 6 nov | `RECOMENDACION_VARIABLES_POBREZA.md`, con la pobreza de la GEIH como resultado |
| Arquitectura de datos (bronce, plata, oro) y guía de replicación | Primera versión el 8 nov | `docs/metodologia/ARQUITECTURA_Y_REPLICACION.md` |
| Depuración del repositorio para el jurado | Hecha el 8 nov | Quedan `main` y `ediciones-hotdeck-sdp`; prueba exploratoria de octubre retirada |
| Pruebas | Hechas en su mayor parte | 204 pruebas al 6 nov, con integración continua |

Fuente: tutoría del 3 de noviembre de 2026 y `docs/seguimiento/README.md` del repositorio.

## Pipeline de datos y modelos

El flujo va de las dos fuentes al emparejamiento, de ahí a la medición de pobreza, a la estimación y a la simulación (6 etapas).

El Hot-Deck copia a cada hogar de la GEIH el grupo A a D de un donante del Sisbén de su misma celda: departamento, ciclo de vida del jefe, cuartos y nivel de pisos (993 celdas, 99,98 % de los hogares en celda exacta). El indicador IPM-GEIH usa 8 de las 15 privaciones, y la pobreza monetaria se reconstruye con ingreso per cápita, arriendo imputado y las líneas del DANE. La estimación usa DML, Causal Forest y cotas de Fréchet-Manski.

## Resultados con datos reales

El DML da efectos de cero en todos los resultados, y las cotas no fijan ni el signo del efecto. Con un grupo imputado al azar dentro de la celda, el DML es una prueba placebo del emparejamiento y no una estimación del efecto del Sisbén.

| Paso | Resultado | Lectura |
| --- | --- | --- |
| Hot-Deck | Grupos A / B / C / D: 14,2 / 29,4 / 34,4 / 22,0 % | El grupo se sortea dentro de la celda y no lleva información del hogar receptor |
| IPM-GEIH | 8 de 15 privaciones; 17,1 % de hogares con 3 o más | Es un proxy del IPM oficial |
| Pobreza monetaria (personas) | 33,2 % frente a 31,8 % oficial; FGT1 13,5 % frente a 12,6 %; igual clasificación en 93,9 % de 275.057 hogares | El arriendo imputado es la decisión que más pesa: sin él la tasa sube a 38,8 % |
| DML, ATE con celda exacta | Puntaje IPM-GEIH −0,0021 [−0,0092; +0,0051]; pobreza monetaria −0,0002 [−0,0036; +0,0033] | Efectos despreciables; es un placebo |
| Cotas de Fréchet-Manski (921 celdas) | `POBRE_GEIH` [−0,261; +0,380]; `POBRE_MONETARIO` [−0,418; +0,648] | Ninguna celda excluye el 0. Con los tres supuestos de monotonía, pobreza monetaria queda en [−0,405; 0] |
| Cotas de Fréchet por parámetro | ATE, ATT, ATU y CATE por zona, sexo del jefe y paredes, en los cinco resultados | Ninguno de los 50 parámetros excluye el 0; las cotas son 140 a 210 veces más anchas que los IC del DML |
| Errores de focalización (A/B frente a pobreza monetaria, cotas por celda) | Exclusión [0,9 %; 75,0 %]; inclusión [38,6 %; 84,5 %] | Al menos 39 % de los A/B no son pobres monetarios; la exclusión solo tiene piso en Putumayo, San Andrés y Bogotá |
| OE1: LASSO, Ridge y SHAP | Exactitud 0,53 frente a 0,30 de la línea base; `viv_pisos` es la variable más importante | Predice el grupo asignado, no la pobreza real |
| Representatividad del Sisbén | Cobertura de 0,4 % (Valle del Cauca) a 12,8 % (Putumayo), 32 veces | El registro no es una muestra uniforme de la GEIH |

Fuente: `docs/resultados/` y `docs/reports/` del repositorio, corrida del 2 de noviembre (cotas con monotonía, 4 de noviembre).

## Por qué los datos reales no identifican el efecto

| Causa | Evidencia en el repositorio | Consecuencia |
| --- | --- | --- |
| El grupo Sisbén se imputa, no se observa | El Hot-Deck sortea un donante de la celda | El grupo es independiente del resultado dada la celda |
| No hay puntaje continuo del Sisbén | El microdato solo trae el grupo A a D | No se puede aplicar discontinuidad en la regresión con datos reales; no se solicitarán más datos, así que queda como limitación y la discontinuidad solo se evalúa en la simulación\* |
| No hay participación en programas del DPS | Los cruces con Familias en Acción y similares no están en las fuentes | No se mide el paso de elegibilidad a participación y bienestar |
| El resultado es una reconstrucción | Pobreza monetaria propia, 1,4 puntos sobre la oficial | Se usa la clasificación oficial del DANE como prueba de robustez |

Entre el 28 de octubre y el 2 de noviembre se detectaron y corrigieron siete errores que cambiaban resultados (mapeo de vivienda, celda de los controles del DML, códigos de mes, propensión, jornalero, entre otros). Las cifras anteriores a esas correcciones no son vigentes.

## Por qué simulamos y qué muestran

En datos reales nunca se conoce el efecto verdadero, así que no se puede saber si un estimador acierta. En una simulación sí.

Con efecto verdadero de −0,30, −0,15 o 0, el pipeline actual devuelve cerca de cero (−0,004 con −0,15)\*. Solo la discontinuidad con el puntaje continuo recupera el efecto (−0,160 y −0,297)\*, y ese puntaje no está en las fuentes.

## Propósito de la simulación

La simulación cumple cuatro funciones, según lo acordado con el tutor.

- Definir reglas de asignación de transferencias bajo supuestos realistas y comparar su desempeño.
- Construir rangos de efectos plausibles para reportar en las respuestas de bienestar, en lugar de un efecto puntual no identificado.
- Dejar montada la infraestructura del análisis causal, replicable por quienes cuenten con la estructura de datos necesaria.
- Cerrar la parte metodológica del objetivo de recuperar efectos causales, con una respuesta parcial pero válida.

Los resultados simulados se marcan con asterisco (\*) y no sustituyen la evidencia empírica.

## Evaluación semisintética\*

Usa los hogares reales de la GEIH y simula solo el tratamiento y el efecto (+0,095 sobre el log-ingreso, −0,033 sobre la pobreza monetaria). Corrió hasta la convergencia: 432 repeticiones de 30.000 hogares, con el Causal Forest en 216.

- Con el tratamiento verdadero y confusión observable, los estimadores recuperan el efecto (0,089 a 0,094 en log-ingreso; −0,031 a −0,033 en pobreza)\*.
- Con Hot-Deck, todo estimador devuelve cerca de cero en los ocho escenarios y los dos resultados\*.
- Con un vínculo parcial del 50 %, el efecto se reduce a la mitad (0,040 a 0,048)\*.
- Con confusión no observada ningún estimador la corrige, y en pobreza el signo se invierte (+0,138 con confusión fuerte)\*.
- Solo la discontinuidad en el corte la resiste (+0,086 frente a +0,090), y solo con vínculo hogar por hogar; con Hot-Deck también da cero\*. La versión difusa, con 80 % de participación entre elegibles, recupera 0,086 frente a 0,090\*.
- La pérdida es proporcional al tamaño del efecto: con Hot-Deck se pierde todo, y con vínculo del 50 % algo menos de la mitad\*.

La lectura para la tesis: recuperar el efecto exige a la vez un vínculo hogar por hogar y un diseño que resista la confusión no observada. Para una entidad que integre sus propios registros, conviene medir la fracción de hogares bien vinculados antes de estimar.

Fuente: `SIMULACION_SEMISINTETICA.md` (corrida y sensibilidad regeneradas el 8 de noviembre).

## Reglas de focalización (OE3)\*

Un proxy de medios con variables del hogar logra 82 % de la reducción ideal de FGT1 y reduce el error de exclusión de 43,5 % a 18,6 %. Usar los efectos heterogéneos estimados empeora la focalización. Presupuesto igual para todas las reglas; 300 repeticiones; efecto proporcional.

| Regla | Error de inclusión | Error de exclusión | % de la reducción ideal de FGT1 |
| --- | --- | --- | --- |
| Vigente (Hot-Deck) | 58,1 %\* | 43,5 %\* | 59,7\* |
| Aleatoria | 66,9 %\* | 53,3 %\* | 46,7\* |
| PMT por ingreso | 48,5 %\* | 18,6 %\* | 82,1\* |
| PMT + CATE (vínculo) | 51,8 %\* | 26,1 %\* | 72,6\* |
| PMT + CATE (Hot-Deck) | 67,7 %\* | 54,9 %\* | 44,6\* |
| Ideal | 34,3 %\* | 0 %\* | 100\* |

El grupo imputado solo lleva la información de la celda, así que su desempeño no es el del Sisbén real. Fuente: `RESULTADOS_REGLAS_FOCALIZACION.md`.

## Pruebas y calidad del código

La suite pasa en GitHub Actions: 214 pruebas al 8 de noviembre; 7 se saltan allí porque necesitan los datos reales de enero de la GEIH.

| Aspecto | Estado |
| --- | --- |
| Integración continua | `.github/workflows/pruebas.yml` corre la suite y la prueba de mutación en cada push a `main` y en cada PR (Python 3.11). Últimas corridas en verde |
| Prueba de mutación | Se reintroducen 43 errores y los 43 hacen fallar alguna prueba |
| Cobertura | Armonización contra los diccionarios oficiales, DML, cotas de Fréchet-Manski, reglas de focalización, simulación semisintética y su sensibilidad |
| Estabilidad | Cinco corridas seguidas sin fallos; pruebas con azar usan semillas fijas |
| Comando del proyecto | `poetry run pytest` pasa desde el 4 de noviembre (`pythonpath` en `pyproject.toml`); ningún script usa ya `warnings.filterwarnings("ignore")` |

El detalle de cada prueba está en `tests/README.md`.

## Estado de los objetivos específicos

| Objetivo | Situación | Ajuste |
| --- | --- | --- |
| OE1 | Implementado con LASSO, Ridge y SHAP | Definir grupos y subgrupos de variables y la concordancia con la pobreza; alimenta la recomendación de variables |
| OE2 | Estimación y cotas implementadas; el efecto no se identifica con los datos actuales | La simulación cierra la parte metodológica |
| OE3 | Reglas de focalización evaluadas en la simulación el 4 de noviembre | El tutor enviará el objetivo ajustado |
| OE4 | Prioritario | Framework apoyado en el módulo de simulación independiente y en la arquitectura de datos |
| OE5 | No se satisface en su formulación actual | Salvar el componente de efectos causales con una respuesta parcial: cotas y simulación |

Fuente: notas de la reunión del 27 de octubre de 2026 y estado del repositorio al 4 de noviembre.

## Próximos pasos

| Prioridad | Tarea | Resultado esperado |
| --- | --- | --- |
| 1 | ~~Variabilidad de la imputación del Hot-Deck: estabilidad por hogar, coeficiente de variación y error relativo por celda~~ **Hecha el 2026-11-04** | Cifra para la pregunta del tutor |
| 2 | Módulo `src/simulacion/` con dos modos (datos propios y simulado), con diseño previo en `docs/metodologia/`. Pasos 1 a 5 hechos; faltan los pasos 6 y 7 (los dos modos) | Framework replicable por otras instituciones |
| 3 | ~~Completar la semisintética: cadena de respaldos del Hot-Deck simulado y asterisco en todas las tablas~~ **Hecha el 2026-11-08** | Evaluación cerrada |
| 4 | ~~Recomendación de variables con LASSO, Ridge y SHAP~~ **Primera versión el 2026-11-06** | Pregunta abierta y recomendación, sin lenguaje causal |
| 5 | ~~Arquitectura de datos (bronce, plata, oro) y guía de replicación~~ **Primera versión el 2026-11-08** | Anexo con evidencia de calidad |
| 6 | ~~Depuración del repositorio y archivo de las ramas obsoletas~~ **Hecha el 2026-11-08** | Repositorio limpio para la entrega |
| 7 | ~~Arreglar `poetry run pytest` y quitar `warnings.filterwarnings`~~ **Hecha el 2026-11-04** | Pruebas verdes con el comando del proyecto |
| 8 | ~~Enviar la solicitud del puntaje continuo~~ **Descartada el 2026-11-04:** no se solicitarán más datos; la réplica usa solo las fuentes ya disponibles | — |
| 9 | Documento escrito: primera versión el sábado 7 de noviembre; revisión del tutor el lunes o martes siguiente | Entrega a revisión |

## Notas de verificación (2026-11-04)

- **Prioridad 6, revisión del 2026-11-08:** se retiró `prueba_ate_att_cate.py`, con su
  preparación y salida (siguen en el historial de git). De las 11 ramas remotas viejas,
  8 estaban integradas; `simulacion-identificacion` y `arregla-lock-openpyxl`, superadas
  en `main`. Las 11 se borraron; `corrige-controles-celda` traía un documento propio y
  queda en la etiqueta `archivo/corrige-controles-celda`.

- **Prioridad 4, primera versión el 2026-11-06:**
  `docs/resultados/2_diagnostico_datos_reales/RECOMENDACION_VARIABLES_POBREZA.md`. No extiende el OE1, que
  predice el grupo asignado: usa la pobreza de la GEIH como resultado.
- **Participación en programas (matiz a la tabla "Por qué los datos reales no
  identifican el efecto"):** faltan los cruces administrativos, pero la GEIH sí
  trae participación **declarada**: `P750S2` (ayudas del gobierno) y `P1661S1`-`S3`
  (Más Familias en Acción, Jóvenes en Acción, Colombia Mayor). El 15,4 % de los
  hogares declara alguna ayuda. Desde el 2026-11-08 se usa como evidencia descriptiva
  de focalización, con cantidades de hogares y personas, en ese documento. No identifica
  un efecto: la participación no es aleatoria y en Colombia Mayor sube gradualmente con
  la edad, sin salto para una discontinuidad.

Comprobado contra el repositorio al incorporar este documento:

- **`poetry run pytest` (prioridad 7): confirmado, son 5 archivos.** Con
  el ejecutable `pytest` directo (lo que corre `poetry run pytest`), la
  raíz del repositorio no queda en el path y no se puede importar `src`;
  fallan al cargar 5 archivos. Con `python -m pytest` (lo que usa la
  integración continua) pasan todas.
- **Ramas (prioridad 6): son 11 remotas además de `main` y
  `ediciones-hotdeck-sdp`**, no tres: `Modelos`, `acceso-lectura-datos`,
  `alinea-readmes`, `arregla-lock-openpyxl`, `comparacion-proxies-ipm`,
  `corrige-controles-celda`, `hotdeck-azure-avances`, `orden-repositorio`,
  `seguimiento-readme`, `simulacion-identificacion` y
  `simulacion-identificacion-v2`. Revisar cuáles están integradas antes
  de archivarlas.
- **Prioridad 2, diseño hecho el mismo día:**
  `docs/metodologia/DISENO_MODULO_SIMULACION.md`. Dos modos (simulado,
  con una población sintética calibrada solo con agregados, y datos
  propios), contrato de columnas canónicas que se valida y no se
  traduce (desaparece `COLUMNAS`), asterisco en toda salida simulada y
  migración en siete pasos con prueba de equivalencia. Pasos 1 a 3
  hechos el mismo día: `src/simulacion/` con el contrato validado,
  resultados idénticos a la versión anterior, módulo anterior borrado.
  Paso 4 hecho el mismo día: la simulación usa la cadena de respaldos
  del pipeline (definida en un solo lugar, `claves_por_nivel`); con los
  datos reales afecta al 0,03 % de la encuesta. Faltaban el asterisco, la
  corrida que regenera las cifras y los dos modos; los dos primeros se
  hicieron el 2026-11-08.
- **Prioridad 1 hecha el mismo día:**
  `docs/resultados/1_datos_y_enlace/RESULTADOS_VARIABILIDAD_HOTDECK.md` (100 sorteos). Por
  hogar, dos sorteos coinciden en el grupo el 34,4 % de las veces y en
  A/B el 62,7 %; por celda, CV mediano 0,091 y error relativo mediano
  0,072 (ponderados: 0,049 y 0,039); a escala nacional, CV ≤ 0,007. El
  −0,0026 del DML en `POBRE_GEIH` (único IC sin el cero) depende de la
  semilla: con 100 sorteos y reglas de Rubin, −0,00003 [−0,0036; +0,0036].
- **Prioridad 7 hecha el mismo día:** `poetry run pytest` pasa (138) tras
  agregar `pythonpath` en `pyproject.toml`; los tres scripts de
  simulación ya no usan `warnings.filterwarnings("ignore")` (sin el
  filtro, una repetición completa de cada uno da 0 advertencias: no
  ocultaba nada). Queda uno en `src/estimacion/prueba_ate_att_cate.py`,
  un script exploratorio del 21 de octubre fuera del pipeline que usa
  `LinearDRLearner`; se decide en la depuración (prioridad 6).
- **Conteo de pruebas:** 138 en total; en GitHub Actions 131 pasan y 7 se
  saltan (sin datos); con los datos, pasan las 138.
- **Regla de nombres fijos y `COLUMNAS` (prioridad 2):** resuelto el
  2026-11-04. `COLUMNAS` desapareció; `src/simulacion/contrato.py` exige
  los nombres canónicos y valida sus códigos, sin renombrar.
