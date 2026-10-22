# Resultados del Hot-Deck GEIH ← Sisbén IV

*Actualizado el 2026-10-21 (celda con vivienda sumada). Descripción de variables y llaves en [`DICCIONARIO_HOTDECK.md`](../insumos/DICCIONARIO_HOTDECK.md); de las tablas, en [`DESCRIPCION_TABLAS.md`](../insumos/DESCRIPCION_TABLAS.md).*

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
| % de hogares (celda con vivienda) | **31,2** | 35,2 | 23,2 | **10,3** |
| % de hogares (celda sin vivienda, hasta 2026-10-21) | 28,0 | 34,4 | 24,9 | 12,7 |

Sumar `viv_cuartos` a la celda corrió la distribución hacia A (+3,2 p.p.) y
en contra de D (-2,4 p.p.) — los hogares con menos cuartos tienden a estar
en departamentos/grupos de edad donde el Sisbén también registra más
Grupo A, así que antes de sumar vivienda ese patrón se perdía dentro de
celdas más gruesas.

## Cómo leerlo

- **El 100 % en celda exacta sigue sin demostrar por sí solo un buen emparejamiento** — ahora hay más celdas (depto×edad×cuartos, no solo depto×edad), pero el donante (3,1 millones) sigue siendo ~11 veces más grande que el receptor. El chequeo real de validez está en `RESULTADOS_DML_ATE_ATT_ATU.md` y `RESULTADOS_CAUSALFOREST_CATE.md`: dado W=celda completa, el efecto estimado no colapsa del todo a 0 — señal de que falta algo (la pista más fuerte: `viv_paredes`, sin verificar y fuera de la celda).
- **La distribución A/B/C/D no es la nacional.** El Sisbén solo cubre hogares registrados, de modo que A y B quedan sobrerrepresentados.
- **El emparejamiento solo es válido a nivel poblacional.** No identifica al mismo hogar en las dos fuentes.

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
- [x] Sumar variables de vivienda a la celda — hecho con `viv_cuartos` (2026-10-21). `viv_paredes`/`viv_pisos` siguen fuera (categorías sin verificar) y alcantarillado/acueducto/número de personas siguen sin homologar en GEIH.
- [ ] Confirmar en ANDA los códigos de `PER002`.
