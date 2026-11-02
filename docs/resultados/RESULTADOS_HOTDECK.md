# Resultados del Hot-Deck GEIH ← Sisbén IV

*Actualizado el 2026-10-28 (corregido `viv_cuartos`, ver nota). Descripción de variables y llaves en [`DICCIONARIO_HOTDECK.md`](../insumos/DICCIONARIO_HOTDECK.md); de las tablas, en [`DESCRIPCION_TABLAS.md`](../insumos/DESCRIPCION_TABLAS.md).*

## Resultado

| Concepto | Valor |
|---|---|
| Hogares receptores (GEIH 2024, 12 meses) | 290.968 |
| Hogares donantes (Sisbén nacional + Bogotá, filtro de vigencia) | 3.106.489 |
| Celda exacta (departamento + ciclo de vida del jefe + tramo de cuartos) | 100 % |
| Hogares en `solo_depto_edad`, `solo_depto` o `pool_nacional` | 0 |

Grupo asignado, ponderado por el factor de expansión de GEIH:

| Grupo | A | B | C | D |
|---|---|---|---|---|
| % de hogares (`viv_cuartos` corregido, 2026-10-28) | **22,0** | 33,8 | 28,7 | **15,6** |
| % de hogares (`viv_cuartos` con el código equivocado, hasta 2026-10-27) | 31,2 | 35,2 | 23,2 | 10,3 |
| % de hogares (celda sin vivienda, hasta 2026-10-21) | 28,0 | 34,4 | 24,9 | 12,7 |

**`viv_cuartos` tenía un código equivocado hasta el 2026-10-28** (tomaba
`P5010`, "cuartos para dormir", en vez de `P5000`, "cuartos en total" —
ver `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`). La celda estaba
matcheando por número de alcobas, no por tamaño total de la vivienda. Con
el código correcto, Grupo D sube de 10,3 % a 15,6 % — un cambio mayor que
el de sumar vivienda a la celda en primer lugar, porque antes la variable
ni siquiera medía lo que se pensaba que medía.

## Cómo leerlo

- **El 100 % en celda exacta no demuestra por sí solo un buen emparejamiento** — el donante (3,1 millones) es ~11 veces más grande que el receptor. Con el sorteo al azar dentro de la celda, el DML sobre el grupo imputado da ≈0 por construcción (`DIAGNOSTICO_W_CELDA_EXACTA.md`).
- **La distribución A/B/C/D no es la nacional.** El Sisbén solo cubre hogares registrados, de modo que A y B quedan sobrerrepresentados.
- **El emparejamiento solo es válido a nivel poblacional.** No identifica al mismo hogar en las dos fuentes.

## ¿Sumar pisos y paredes a la celda? (2026-11-02)

Con pisos y paredes ya homologados
(`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`) se compararon tres
celdas sin cambiar la oficial
(`src/validacion/comparar_celdas_hotdeck_vivienda.py`,
`docs/reports/comparacion_celdas_hotdeck_vivienda.csv`). Pisos y paredes
entran en tres niveles de la escala común (pisos: acabado / cemento o
madera burda / tierra; paredes: ladrillo / tapia o bahareque / precarias),
para no fragmentar las celdas.

| | 1. Depto + edad + cuartos (actual) | 2. + pisos | 3. + pisos + paredes |
|---|---|---|---|
| Celdas con receptores | 376 | 993 | 2.081 |
| Hogares en celda exacta | 99,999 % | 99,976 % | 99,946 % |
| Donantes por celda (mediana / p5) | 9.437 / 1.301 | 2.353 / 183 | 1.898 / 140 |
| Hogares en celdas con < 30 donantes | 0,06 % | 0,83 % | 1,38 % |
| P(T \| celda): sd (p5-p95) | 0,170 (0,36-0,86) | 0,223 (0,15-0,84) | 0,224 (0,15-0,85) |
| Correlación de P(T \| celda) con pobreza monetaria | 0,20 | 0,29 | 0,29 |
| Pobreza T=1 − T=0 (sin controles) | +9,0 pp | +13,3 pp | +13,6 pp |
| Grupos A / B / C / D (%) | 22,0 / 33,8 / 28,7 / 15,6 | 14,2 / 29,4 / 34,4 / 22,0 | 14,0 / 29,0 / 34,5 / 22,5 |

**Lectura:**
- **Pisos aporta información; paredes casi nada encima.** Con pisos, el
  grupo imputado sigue mejor la pobreza del receptor (correlación 0,20 →
  0,29) y la cobertura apenas cambia. Paredes triplica las celdas sin
  mejorar la correlación (0,29 → 0,29).
- **La distribución de grupos se mueve bastante** (A cae de 22 % a 14 %):
  en GEIH predominan los pisos con acabado, y con pisos en la celda los
  hogares reciben donantes del Sisbén con viviendas parecidas, que son
  menos pobres. Es un cambio de nivel que se arrastraría a todo lo que
  usa el grupo imputado.
- Nada de esto cambia el problema de identificación: dentro de cualquier
  celda el sorteo sigue siendo al azar y el contraste del DML sigue
  siendo un placebo. Lo que mejora es la concordancia **entre celdas**
  (útil para P1/OE1 y para la simulación semisintética).
- **Propuesta:** adoptar la celda 2 (+ pisos) como especificación de
  sensibilidad del Hot-Deck, y decidir si pasa a ser la oficial. No se ha
  cambiado la celda oficial.

## Historial de la cobertura

| Momento | Celda exacta | Causa |
|---|---|---|
| Primera ejecución | 10,8 % | La edad de GEIH (años) se comparaba con códigos de grupo de edad del Sisbén |
| Edad por ciclo de vida | 91,6 % | El 8,4 % restante eran los hogares de agosto sin jefe cruzado |
| Con llaves de GEIH normalizadas | 100 % | Corrección de las llaves de agosto |

## Verificación de `PER002` (edad del jefe en el Sisbén)

`PER002` no es la edad en años: toma los valores 1 a 6 (los jefes solo 3 a 6). Para verificar que es un código **ordinal** de grupo de edad se cruzó con variables cuyo comportamiento por edad se conoce. Muestra: las primeras 1.500.000 personas del archivo de personas, que no son representativas a nivel nacional; lo que importa es el patrón entre grupos.

| Código `PER002` | Personas | % con `PER016` = 1 | % con `PER004` = 1 | % con `PER012` = 1 |
|---|---|---|---|---|
| 1 | 146.152 | 11,2 | 0,0 | 0,0 |
| 2 | 165.918 | 95,8 | 0,0 | 0,3 |
| 3 | 136.590 | 86,6 | 1,1 | 2,0 |
| 4 | 287.865 | 22,4 | 25,3 | 27,8 |
| 5 | 555.523 | 2,5 | 57,3 | 47,0 |
| 6 | 207.952 | 0,8 | 50,3 | 43,9 |

`PER016` es "actualmente estudia" y `PER004` estado civil; `PER012` es "ha tenido hijos". La lectura del valor `1` en cada variable es la que sugiere el patrón (estudia en las edades escolares, pareja e hijos en las adultas) y debe confirmarse contra la etiqueta oficial.

**Conclusión.** El orden de los códigos es el de la edad creciente: 3 corresponde a adolescentes, 4 a adultos jóvenes, 5 a adultos y 6 a adultos mayores. Los cortes exactos (12–17, 18–28, 29–59 y 60 o más) siguen sin confirmar en ANDA. El riesgo es de borde: si el corte entre 4 y 5 no es 28 años, algunos jefes de GEIH quedarían en la celda contigua a la de su par del Sisbén.

## Pendientes
- [ ] Sensibilidad del Hot-Deck: mover los cortes de edad, sortear donantes ponderados por `FEX` y medir donantes por receptor y reutilización de donantes.
- [ ] Validar con el IPM sin usarlo en la celda: comparar privaciones medias por grupo asignado.
- [x] Sumar variables de vivienda a la celda — hecho con `viv_cuartos` (2026-10-21), código corregido el 2026-10-28.
- [x] Homologar alcantarillado/acueducto/número de personas en GEIH — hecho 2026-10-28 (`P4030S3`, `P4030S5`, `P6008`), ver `DICCIONARIO_HOTDECK.md` §4.
- [x] Homologar `viv_paredes`/`viv_pisos` (2026-11-02) y comparar celdas con ellos (ver arriba).
- [ ] Decidir si la celda con pisos pasa a ser la oficial.
- [ ] Confirmar en ANDA los códigos de `PER002`.
