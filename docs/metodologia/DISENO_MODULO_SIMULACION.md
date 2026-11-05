# Diseño del módulo de simulación (`src/simulacion/`)

Fecha: 2026-11-04. Prioridad 2 de
`docs/seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md`. Este documento se
escribe antes del código: fija qué hace el módulo, qué exige a quien lo
use y cómo se migra lo que ya existe sin mover los resultados publicados.

## 1. Para qué

Que una institución pueda evaluar un subsidio o una transferencia con el
mismo procedimiento de la tesis sin depender de la GEIH ni del Sisbén de
este proyecto. Hay dos modos:

| Modo | Quién lo usa | Qué trae | Qué obtiene |
|---|---|---|---|
| **Simulado** | Cualquiera, sin microdatos | Nada (o un número de hogares y una semilla) | La evaluación semisintética completa sobre una población sintética\*: qué estimador recupera un efecto conocido y cuánto se pierde según el vínculo |
| **Datos propios** | Una entidad con sus registros ya enlazados | Una tabla de hogares y, si la tiene, el registro con el grupo del Sisbén | La misma evaluación\* sobre sus hogares reales y, si su tabla trae el tratamiento observado, la estimación con datos reales (sin asterisco) |

**Datos de la tesis:** no se solicitarán más datos. La réplica usa solo
las fuentes que ya están en el banco de datos (GEIH 2024, Sisbén IV
nacional y de Bogotá, IPM), y el módulo se diseña con lo que ellas traen.

La simulación es una pieza del framework, no su fin: responde «¿con mis
datos y mi forma de enlazarlos, se puede recuperar el efecto?» antes de
estimar nada.

## 2. Regla de nombres: el módulo exige, no traduce

Regla del tutor (2026-11-03): los nombres estandarizados de GEIH y Sisbén
no se cambian ni se hacen configurables. Hasta el 2026-11-04,
`src/validacion/simulacion_semisintetica.py` tenía un diccionario
`COLUMNAS` que permitía mapear otros nombres; **ese diccionario
desapareció**. En su lugar:

- El módulo publica la lista de columnas que exige cada tabla
  (`contrato.py`, sección 3).
- `validar(tabla, rol)` revisa que estén todas, que los códigos estén en
  el dominio esperado y que no haya columnas duplicadas. Si falta algo,
  falla con un mensaje que nombra cada columna faltante o cada código
  fuera de dominio. **No renombra ni adivina.**
- Las variables derivadas (zona urbana 0/1, jefe mujer 0/1, celda del
  Hot-Deck, logit de P(T | celda)) las calcula el módulo a partir de las
  canónicas. Nunca se reciben ya calculadas: así la celda de una
  institución se construye con la misma regla que la de la tesis.

Quien tenga otros nombres los convierte antes, en su propia
armonización, como hizo este proyecto en `src/armonizacion/`.

## 3. Contrato de datos

Los nombres son los de `data/2_models/` (`docs/insumos/DESCRIPCION_TABLAS.md`).
Los dominios salen de los diccionarios oficiales y de las homologaciones
ya verificadas; no se agregan códigos nuevos sin verificar.

### Tabla de hogares (rol `hogares`; obligatoria en modo datos propios)

Una fila por hogar, como la GEIH estandarizada.

| Columna | Dominio | Uso |
|---|---|---|
| `geo_depto` | Código DANE de 2 dígitos (texto) | Celda |
| `geo_zona` | `1` urbano, `2` rural (`CLASE` de la GEIH) | X; dominio de la línea |
| `jefe_sexo` | `1` hombre, `2` mujer (`P3271`) | X |
| `jefe_edad` | Años (entero ≥ 0) | Celda (ciclo de vida con `edad_a_ciclo`) |
| `viv_cuartos` | Conteo ≥ 1 | Celda |
| `viv_pisos` | Códigos GEIH de `P4020` (1-7) | Celda (nivel común, `HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`) |
| `viv_paredes` | Códigos GEIH de `P4010` | X |
| `ingreso_percapita` | Pesos, ≥ 0 | Y0 (log) |
| `dominio_pm` | `13_ciudades`, `otras_cabeceras`, `rural` | Línea de pobreza |
| `fex` | > 0 (opcional) | Ponderación de los agregados |

Opcionales que activan la estimación con datos reales:

| Columna | Dominio | Uso |
|---|---|---|
| `Grupo` | `A`, `B`, `C`, `D` | T observado = A o B |
| `vinculo` | `llave` (cruce hogar a hogar) o `hotdeck` | Cómo se obtuvo `Grupo`; con `hotdeck` el resultado se marca como placebo, no como efecto |

### Tabla de registro (rol `registro`; opcional)

Una fila por hogar del registro (Sisbén estandarizado). Solo se usa para
calcular P(T | celda), que fija la tasa de tratados y la confusión por
celda en el generador.

| Columna | Dominio |
|---|---|
| `geo_depto` | Código DANE de 2 dígitos |
| `jefe_edad` | Código de ciclo de vida de `PER002` (3-6) |
| `viv_cuartos` | Conteo ≥ 1 |
| `viv_pisos` | Códigos del Sisbén (1-6, orden inverso al de la GEIH; 6 = otro, sin par en la GEIH) |
| `Grupo` | `A`-`D` |
| `Clasificacion` | No nula en los hogares clasificados |

Sin registro, el modo de datos propios usa la tabla agregada de P(T |
celda) del modo simulado (sección 4).

## 4. Modo simulado: población sintética calibrada con agregados

El modo simulado no puede usar microdatos (no se versionan). Genera
hogares con las columnas canónicas de la sección 3 a partir de
**parámetros agregados** calculados una vez con los datos reales:

1. `calibrar.py` (corre solo quien tiene los datos) produce
   `src/simulacion/parametros/poblacion_2024.json`:
   - distribución de departamentos, y de zona dentro del departamento;
   - distribución conjunta de ciclo de vida, cuartos y nivel de pisos
     dentro de departamento × zona;
   - distribución de paredes dentro de zona × nivel de pisos;
   - sexo del jefe por zona;
   - log-ingreso: media y desviación por departamento × zona × nivel de
     pisos, más el coeficiente de las X;
   - P(T | celda) del Sisbén.
2. `generador.py` sortea hogares en ese orden (cadena de condicionales),
   con semilla.
3. **Protección de datos:** toda casilla con menos de 30 hogares en la
   fuente se fusiona con la de su nivel superior (la misma cadena de
   respaldo del Hot-Deck: celda → sin pisos → depto + edad → depto) antes
   de guardarse. El JSON solo tiene proporciones y momentos, nunca un
   hogar.

Lo que se pierde frente a los hogares reales es la dependencia fina entre
variables no modelada en la cadena. Por eso los resultados del modo
simulado se comparan con los del modo de datos propios con la GEIH antes
de usarlos (sección 8, prueba de equivalencia de agregados).

## 5. Componentes

```
src/simulacion/
  __init__.py
  contrato.py       columnas exigidas por rol, dominios y validar()
  base.py           de tabla canónica a tabla de trabajo: celda, X 0/1,
                    Y0, línea, logit P(T|celda), U, tau
  generador.py      modo simulado: población sintética desde parametros/
  calibrar.py       produce parametros/poblacion_2024.json (datos reales)
  escenarios.py     ESCENARIOS, VINCULOS, TAU, B_X, umbrales de MCSE
  asignacion.py     asignar(): T verdadero, puntaje y corte
  vinculo.py        sortear_donante() con la cadena de respaldos del
                    pipeline (celda → sin pisos → depto+edad → depto →
                    nacional); vínculo parcial
  estimadores.py    diferencia de medias, efectos fijos, LinearDML,
                    CausalForestDML, RD nítida y difusa
  evaluacion.py     una_repeticion(), resumir() con MCSE, bucle de
                    convergencia por lotes, firma y reanudación
  reportes.py       tablas y figura; todo resultado simulado con *
  parametros/       poblacion_2024.json (solo agregados)
  __main__.py       línea de comandos
```

Línea de comandos:

```bash
# Modo simulado (sin datos)
poetry run python -m src.simulacion simulado --hogares 300000 --semilla 2026

# Modo datos propios
poetry run python -m src.simulacion propios --hogares ruta/hogares.parquet [--registro ruta/registro.parquet]
```

Lo que **sí** es configurable (el «resto del framework»): escenarios,
tipos de vínculo, efecto verdadero y su heterogeneidad, estimadores,
tamaño de la encuesta, umbrales de convergencia y número de procesos. Se
pasan como argumentos o como un archivo de configuración; los nombres de
columnas no.

## 6. Asterisco en los resultados simulados

Regla del tutor: todo resultado simulado lleva `*` cuando aparece con
resultados reales o cerca de ellos. En el módulo:

- `reportes.py` agrega `*` a cada cifra simulada de las tablas Markdown y
  una nota al pie: «\* Resultado simulado (semisintético): efecto
  verdadero fijado por el investigador; no es una estimación con datos
  reales».
- Los CSV llevan una columna `simulado` (`True` en todas las filas de la
  evaluación) y el nombre del modo; la figura lleva `*` en el título.
- En el modo de datos propios, la estimación con el tratamiento observado
  va en una tabla aparte, sin asterisco, y si `vinculo == "hotdeck"` con
  el rótulo «placebo del emparejamiento».
- Una prueba revisa que ninguna tabla de la evaluación salga sin el
  asterisco.

## 7. Migración desde `src/validacion/`

**Estado (2026-11-04): pasos 1 a 4 hechos.** Paso 4: la cadena se
define una vez (`claves_por_nivel`, en el módulo del Hot-Deck) y la usan
`hotdeck()` y `vinculo.sortear_donante`; el Hot-Deck del pipeline
reproduce el Parquet guardado. Con la base real, el 0,03 % de la encuesta
usa un respaldo. Si no hay celdas vacías, el sorteo es el mismo de antes
(no consume más números aleatorios). Las firmas de configuración subieron
de versión: las repeticiones guardadas no se mezclan con las nuevas.
Pasos 1 a 3: Comprobación: con los datos
reales, la tabla de trabajo (290.968 hogares) y las 150 filas de la
repetición 0 son idénticas a las de la versión anterior; la repetición 0
de la sensibilidad y de las reglas de focalización coincide con los CSV
publicados (diferencia máxima 1e-16 con un hilo de BLAS; con varios
hilos, 1e-6, por el orden de las sumas). Al mover el código apareció un
error que no daba aviso: los códigos de celda en `int8`/`int16` se
desbordaban en `regresion_efectos_fijos` (con 993 celdas, por encima de
32.767 hogares en la encuesta); se corrigió con prueba y mutación. Además,
`tablas_markdown` no se llamaba en `main`: ahora sí.

El código ya existe y produjo cifras publicadas (432 repeticiones,
`SIMULACION_SEMISINTETICA.md`). La migración no puede moverlas en
silencio.

| Paso | Qué | Comprobación |
|---|---|---|
| 1 | Crear `contrato.py` y `base.py`; `preparar_base` lee las columnas canónicas sin `COLUMNAS` | Misma tabla de trabajo que hoy, columna por columna, sobre la base real |
| 2 | Mover escenarios, asignación, vínculo, estimadores y evaluación sin cambiar la lógica | `una_repeticion(b, rep)` da filas idénticas a las de la versión anterior para 3 repeticiones (semillas fijas) |
| 3 | Pasar `reglas_focalizacion.py`, `sensibilidad_semisintetica.py` y las pruebas a importar de `src/simulacion/`; borrar `src/validacion/simulacion_semisintetica.py` | Suite completa y mutaciones en verde; sin módulo puente que quede de ruido |
| 4 | Cadena de respaldos en `vinculo.py` (prioridad 3 de la guía) | Prueba: con celdas sin donantes, el nivel usado coincide con el del `hotdeck()` del pipeline |
| 5 | Asterisco en `reportes.py` y en los documentos de `docs/resultados/` que mezclan cifras | Prueba de asterisco (sección 6) |
| 6 | `calibrar.py`, `generador.py` y el modo simulado | Prueba de agregados (sección 8) |
| 7 | Modo de datos propios con estimación real | Correrlo con la GEIH enlazada reproduce el DML de `5_estimacion.py` |

El paso 4 cambia la simulación: antes, una celda sin donantes sorteaba en
todo el registro; con la cadena, sortea en la celda de respaldo. Afecta
a pocos hogares (0,02 % en el pipeline real), pero las cifras se
regeneran y el cambio se documenta en `SIMULACION_SEMISINTETICA.md`.

## 8. Pruebas nuevas

| Prueba | Qué detecta |
|---|---|
| Falta una columna exigida → error que la nombra | Volver a aceptar nombres distintos o a completar en silencio |
| Código fuera de dominio (`geo_zona = 3`, pisos 9) → error | Mezclar códigos de GEIH y Sisbén (en pisos el orden es inverso) |
| La tabla con columnas extra o en otro orden da el mismo resultado | Dependencia del orden de las columnas |
| Equivalencia con la versión anterior en 3 repeticiones | Que la migración cambie resultados |
| Cadena de respaldos igual a la del pipeline | Que la simulación y el Hot-Deck real diverjan |
| Toda tabla simulada tiene `*` | Cifras simuladas sin marcar |
| Población sintética: las marginales y P(T | celda) reproducen el JSON (tolerancia por tamaño) | Generador desalineado con la calibración |
| JSON sin casillas de menos de 30 hogares | Fuga de datos en los parámetros |

Cada error que se encuentre en la implementación agrega su mutación en
`tests/mutaciones.py`, como el resto del proyecto.

## 9. Fuera de alcance

- Cambiar los nombres canónicos o aceptar alias.
- Leer formatos distintos de Parquet o CSV con los nombres canónicos.
- Ajustar por diseño muestral en los estimadores (`fex` solo pondera
  agregados descriptivos, como hoy).
- El generador 100 % sintético de `simulacion_identificacion.py` (mundo
  abstracto con 20 departamentos): se deja como está, porque responde
  otra pregunta (qué diseño identifica) y no usa columnas canónicas.

## 10. Decisiones abiertas

1. **Umbral de protección del JSON (30 hogares).** Es el mínimo usual
   para publicar celdas de encuesta; se cambia en `calibrar.py` si hace
   falta.
2. **Si P(T | celda) del Sisbén puede versionarse** como agregado de las
   993 celdas (con la fusión de celdas pequeñas). Viene de microdatos
   anonimizados públicos; se propone versionarlo.
3. **Estimación real en el modo de datos propios.** Se limita a los
   estimadores de `5_estimacion.py` (DML con celda exacta y cotas de
   Fréchet-Manski); no se agregan otros en esta prioridad.
