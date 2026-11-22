# Resultados — ¿Representa el Sisbén a la misma población que GEIH?

Generado por `src/validacion/verificar_representatividad_sisben.py`.
Detalle completo por departamento:
`docs/reports/representatividad_sisben_por_depto.csv`.

## La pregunta

El Hot-Deck y las cotas de Fréchet-Manski asumen, cada uno a su manera,
que el registro del Sisbén dice algo útil sobre la población de GEIH. Pero
el Sisbén solo cubre hogares que se inscribieron — **no es una muestra
aleatoria de la población de GEIH, es un registro administrativo de
demanda**. Si la tasa de inscripción fuera pareja entre departamentos, el
supuesto de "cobertura parcial pero uniforme" sería razonable. Si varía
mucho, hay sesgo de cobertura y hay que tenerlo presente al interpretar
cualquier resultado que compare ambas fuentes.

## Resultado

Razón de cobertura = hogares registrados en el Sisbén (con `Clasificacion`
observada, el pool donante real del Hot-Deck), **expandidos con su factor
`fex`**, ÷ hogares de la GEIH en un mes promedio (expandidos con
`FEX_C18`), por departamento y **sobre el mismo marco**: en los 9
departamentos de la Orinoquía, la Amazonía y San Andrés (81, 85, 86, 88,
91, 94, 95, 97, 99) la GEIH solo encuesta la cabecera de la capital, y el
Sisbén se cuenta también solo ahí.

| | Razón de cobertura | Departamento (código DIVIPOLA) |
|---|---|---|
| Nacional (agregada) | 68,3 % | — |
| Nacional sin Bogotá | 73,9 % | — |
| Mínima | 41,5 % | 11 — Bogotá (registro completo del SDP) |
| Máxima | 97,3 % | 54 — Norte de Santander |
| Departamentos completos sin Bogotá (23) | 55,3 % a 97,3 % | 27 — Chocó a 54 — Norte de Santander |
| Cabeceras de las capitales (9) | 45,6 % a 83,9 % | 97 — Vaupés a 81 — Arauca |

**Corrección del 2026-11-21: el Sisbén nacional es una muestra.** El
archivo de ANDA trae 1,83 millones de hogares con un factor de expansión
(`fex`, "Factor de expansión" en `DICCIONARIO_SISBEN_2024.xlsx`) que suma
11,4 millones de hogares y 29,4 millones de personas. Hasta esa fecha se
contaban las filas, y la cobertura salía 16,8 % nacional y 11,7 % sin
Bogotá, entre 2,2 % y 41,5 % por departamento. Bogotá no cambia: el
archivo del SDP es el registro completo (`fex` = 1). Prueba y mutación en
`tests/test_ingesta_y_validacion.py`.

**Corrección del 2026-11-11: el mismo marco en las dos fuentes.** Hasta
esa fecha, en esos 9 departamentos se dividía el Sisbén de todo el
departamento entre la GEIH de la capital, y la razón pasaba del 100 %. En
la GEIH todos sus hogares ahí son urbanos (`CLASE` 1, `AREA` igual al
código del departamento); en el Sisbén, entre la mitad y el 90 % de los
registrados de esos departamentos viven fuera de la cabecera de la
capital. Prueba y mutación en `tests/test_ingesta_y_validacion.py`.

**Corrección del 2026-11-10.** Hasta esa fecha el denominador sumaba los
factores de expansión de los 12 meses de la GEIH, y cada mes se expande a
toda la población: los hogares salían 12 veces más (214,9 millones en vez
de 17,9) y las coberturas 12 veces menores.

**Bogotá es la cobertura más baja.** Su 41,5 % viene de otra fuente (el
registro del SDP filtrado a los hogares vigentes al 31 de diciembre de
2024), y Bogotá tiene la menor pobreza del país.

**Factor de variación: 2,3 veces** entre el mínimo y el máximo, y 1,8
veces entre los 23 departamentos completos del archivo nacional. Las
coberturas más altas están en Norte de Santander, Huila, Magdalena,
Córdoba y Caquetá (88 % a 97 %); las más bajas, fuera de Bogotá, en Chocó,
Caldas, Antioquia y Risaralda (55 % a 62 %).

**Cobertura por celda (exploratorio, 2026-11-21).** Con la celda del
Hot-Deck, el 85 % de la población fuera de Bogotá y el 95 % en Bogotá
vive en celdas donde la cobertura es menor que 1, y la cobertura sube con
la pobreza de la celda: entre celdas con al menos 20 hogares de la GEIH,
la correlación ponderada es +0,21 fuera de Bogotá (1.389 celdas) y +0,47
en Bogotá (40 celdas), con p < 0,05 en una permutación dentro de cada
departamento. En Bogotá, el cuartil de celdas más pobre tiene 92 % de
cobertura y el menos pobre 31 %.

## Cómo leerlo

**No es un error de los datos — es exactamente lo esperable de un
registro de demanda**, y confirma empíricamente, con cifras reales, el
supuesto que había quedado solo como advertencia narrativa hasta ahora:
la inscripción al Sisbén no es pareja respecto al tamaño de la población.
Departamentos con más pobreza estructural tienden a tener una fracción
mayor de sus hogares registrados que departamentos más urbanos y de
mayores ingresos — razonable, porque el Sisbén es más relevante para
quien aspira a un subsidio, pero significa que el pool donante del
Hot-Deck no es una muestra representativa de "todos los hogares de ese
departamento", sino de "los hogares de ese departamento que buscaron
registrarse".

**Consecuencia directa para el resto del pipeline:**
- El Hot-Deck ya usa `geo_depto` en su celda, así que este sesgo queda
  parcialmente absorbido (compara GEIH contra Sisbén *dentro* del mismo
  departamento, no a nivel nacional) — pero **dentro** de cada
  departamento, sigue sin garantía de que los hogares registrados sean
  representativos de los no registrados. **Prueba exploratoria
  (2026-11-21), en Bogotá, donde el registro es completo:** dentro de la
  misma celda, los inscritos tienen jefatura femenina en 53,1 % de los
  hogares frente a 46,0 % en la población (diferencia de 7,1 puntos, IC
  95 % [6,1; 8,1], *bootstrap* de 200 réplicas sobre 30.000 hogares de la
  GEIH); con alcantarillado la diferencia es de 1,5 puntos y con acueducto
  no la hay. La inscripción no es aleatoria dentro de la celda.
- **Lo que imputa el Hot-Deck es la clasificación que el hogar tendría si
  estuviera inscrito, no su elegibilidad efectiva.** Un hogar no inscrito
  no puede ser A/B, así que la elegibilidad de la población es menor que la
  imputada y el error de exclusión con datos reales
  (`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`) es un piso del real.
- Refuerza la lectura de `docs/resultados/2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md`:
  la cota tan ancha que se encontró ahí (sin suponer independencia
  condicional) es consistente con este sesgo de cobertura real, no
  solo con una posibilidad teórica.
- Para cualquier interpretación de "a quién representa" el grupo asignado
  por Hot-Deck, hay que ser explícito: representa a los hogares *con
  perfil similar a quienes se registraron*, no a la población general del
  departamento.

## Limitaciones

- La razón de cobertura usa el pool donante COMPLETO del Sisbén (nacional
  + Bogotá, filtro de vigencia) contra la población TOTAL de GEIH —no se
  excluyen los hogares de GEIH que, por nivel de ingreso, nunca
  calificarían para registrarse (no hay forma de saberlo sin la variable
  real de inscripción en GEIH, que no existe).
- No se intenta aquí estimar qué fracción de la población "debería"
  estar registrada — solo se documenta que la cobertura observada no es
  uniforme.
